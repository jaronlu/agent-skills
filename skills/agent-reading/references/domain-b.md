> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### B. 上下文工程与 Token 压缩（Context Engineering & Token Compression）（L360–L489）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### B. 上下文工程与 Token 压缩（Context Engineering & Token Compression）

决定「模型每一轮真正看到什么」的工程学——把有限的 context window 当作稀缺资源，做分层组装、预算分配、按需加载、原地裁剪、摘要续期与缓存复用，是 Agent 长任务能力上限与成本曲线背后的隐形主干。工具结果的截断见 C6；子 agent 隔离视角见 E3；会话持久化见 D2。

#### B1. System Prompt 的分层组装（Layered System Prompt Assembly）｜P0

**是什么**：把内置 base prompt、安全与工具规则、项目级指令文件（AGENTS.md / CLAUDE.md / `.clinerules` 一类，常沿「用户主目录 → 仓库根 → cwd」逐级向上发现）、用户自定义规则和环境上下文（cwd、git 状态、时间）按优先级与顺序拼接成最终 system message 的流水线。

**为什么重要**：这是理解「Agent 的行为从哪来」的第一入口——分层决定了谁覆盖谁、项目定制如何不改核心代码就生效、哪些指令每轮固定占 token；多份指令文件并存时的发现层级与加载优先级（立即还是惰性）直接决定指令冲突时谁赢，也是各 CLI 互操作的关键差异点；最前层的稳定性同时是 prompt caching 能否命中的地基（B9）。文件型长期记忆的存储视角见 D3。

**快速信号**：grep `AGENTS.md`、`CLAUDE.md`、`clinerules`、`CONVENTIONS.md`、`system_prompt`、`base_prompt`、`get_instructions`、`build_prompt`、`render_prompt`、`discover`、`find_up`、`instructions`；看 prompts/、templates/ 目录下的 `.md` / `.jinja` / `.j2` 模板与 `{{placeholder}}` 占位符；留意逐级向上发现指令文件的循环。

**代表实现**：openai/codex —— AGENTS.md 沿目录链分层发现（用户主目录、仓库根、到当前目录的路径上）并与内置 instructions 合成最终 system prompt；OpenHands —— system prompt 与 workspace 上下文拼装，另有带触发词的 microagents 按目录被发现；cline/cline 与 RooCodeInc/Roo-Code —— 全局 custom instructions 与工作区规则文件（`.clinerules` / `.roo/rules`）分层注入。

```text
我想弄清这个 Agent 仓库的 system prompt 是如何分层组装的：请定位最终发给模型的 system message / instructions 的拼装入口，包括内置 base prompt、项目级指令文件（如 AGENTS.md、CLAUDE.md 或同类机制）的发现与读取（从哪些目录层级发现、发现后是立即读入还是惰性加载、多份文件冲突时谁覆盖谁）、用户自定义规则、以及环境上下文（cwd、git 状态等）的注入层，引用具体 file:line；然后按数据流顺序讲清每一层从哪里读、按什么优先级和顺序拼进最终 prompt、谁会覆盖谁、各层大致占多少篇幅量级；点出这条链路上的关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B2. Token 计数与估算（Token Counting & Estimation）｜P1

**是什么**：在消息发给模型前对其做 token 计数——精确 tokenizer（常见 tiktoken）或 chars-per-token 启发式——为预算检查、压缩触发和用量统计提供依据。

**为什么重要**：所有上下文管理决策（要不要压缩、截多少、还剩多少空间）都建立在计数之上：估偏高会提前浪费窗口，估偏低会直接撞限报错；tokenizer 与模型绑定，本地计数如何用 API 返回的 usage 校准是最常见的坑。注意与 J5 的分工：这里是「发送前预估」，J5 是「响应后用 usage 字段记账」，两条数据流并存、来源不同、用途不同。

**快速信号**：grep `tiktoken`、`count_tokens`、`token_count`、`estimate_tokens`、`tokenizer`、`prompt_tokens`、`usage`；找 per-model 的 tokenizer 映射表、`/4` 这类启发式除法、以及「发送前估算、响应后用 usage 回填」的双轨模式。

**代表实现**：Aider-AI/aider —— 按模型选择 tokenizer 的精确计数与导入成本核算；openai/codex —— 以请求前后的 usage 字段维护已消耗上下文；langchain-ai/langgraph 生态 —— tiktoken 之上的通用计数工具。

```text
我想弄清这个 Agent 仓库如何做 token 计数与估算：请定位发给模型前的计数入口（用的是精确 tokenizer 还是 chars-per-token 类启发式、是否按模型选择不同 tokenizer），引用具体 file:line；再讲清计数结果在哪些地方被消费（预算检查、压缩触发、用量统计）、请求返回后是否用 API 的 usage 字段回填校准本地估计，把整条数据流用文字串起来；点出关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B3. 上下文窗口预算分配（Context Window Budgeting）｜P1

**是什么**：把模型 context window 显式切成若干配额——system prompt、工具定义、最近历史、必读参考（repo map / memory block）、为模型输出预留的 completion 空间——并在配额之间做调度。

**为什么重要**：没有预算意识的 Agent 会把窗口吃满后才被动压缩；显式预算让 repo map、记忆、观测结果各自有上限可调（如 map-tokens 一类参数），也让「给输出留多少」这个致命细节变成配置项而非运气。摄入侧的第一道闸——工具输出截断——见 C6。

**快速信号**：grep `context_window`、`max_context`、`token_budget`、`map_tokens`、`reserved`、`remaining_tokens`、`max_output_tokens`；找按模型列出窗口大小的常量表，以及「剩余空间 = 窗口 − system − 历史 − 预留」这类计算所在的函数。

**代表实现**：Aider-AI/aider —— repo map 有独立 token 预算并按排名装填到预算为止；letta-ai/letta-code —— core memory 的各 block 带显式大小上限；OpenHands —— 观测截断上限与 condenser 配置共同构成事实上的预算体系。

```text
我想弄清这个 Agent 仓库如何分配 context window 预算：请定位各模型窗口大小的定义处，以及 system prompt、工具定义、对话历史、参考内容（如 repo map 或 memory）、给模型输出预留的空间各自如何被计量和限制，引用具体 file:line；然后讲清每次请求前剩余空间是怎么算出来的、某一项超预算时走哪条分支，用文字描述这条计算与调度流程；点出关键常量、数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B4. 仓库地图（Repo Map / Ranked Repository Summary）｜P1

**是什么**：用静态分析抽取全仓库的符号定义与引用关系（常见 tree-sitter），按图排序算法挑出最重要的文件/函数签名，生成一份固定 token 预算内的仓库结构摘要放进上下文。

**为什么重要**：这是「不预读全仓库也知道去哪找」的核心折衷——给模型可导航的骨架而不预载正文；也是把 PageRank 类算法用于上下文选择的最著名范例，token 预算变化时条目能平滑增减而不是整体重算。

**快速信号**：grep `repo_map`、`repo map`、`tree-sitter`、`treesitter`、`tags`、`rank`、`personalization`、`referenced`；找「对文件建图 → 算重要度 → 按预算装填」的模块，常见于 map / graph / index 命名的文件。

**代表实现**：Aider-AI/aider —— tree-sitter 抽符号加引用图 PageRank 排序的 repo map，token 预算可调；cline/cline —— 更轻量的文件树加 @-mention 机制提供导航骨架。

```text
我想弄清这个 Agent 仓库是否实现 repo map（仓库结构摘要）以及它如何生成：请定位从源码抽取符号/定义（如 tree-sitter）、构建文件间引用关系、排序、再按 token 预算装填生成摘要的整条流水线入口，引用具体 file:line；然后按数据流逐步讲清每一步的输入输出（符号怎么抽、图怎么建、重要度怎么排、装到预算为止时砍谁留谁）；点出关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B5. 按需上下文加载（Just-in-Time Context Loading）｜P1

**是什么**：不预先把代码塞进上下文，而是给模型搜索/读取工具（grep、find、read_file、glob），让它按任务需要逐步拉取正文——上下文是检索来的，不是预载的。

**为什么重要**：这是现代编码 Agent 与「embedding 预取」路线的分水岭：按需拉取控制了 token 消耗并保证读到的是当前文件，代价是把「找什么、怎么找」变成模型要学的技能；一个仓库的工具集设计直接暴露它的上下文哲学。

**快速信号**：看工具定义列表里有没有 `grep` / `search_files` / `read_file` / `glob` 一组；grep `lazy`、`on demand`、`max_lines`、`maxResults`、读取的行号区间参数；留意 system prompt 里「优先搜索、按需读取」类的指令。

**代表实现**：cline/cline —— 刻意选择 regex 搜索加按需读文件（带行数上限）而非 embedding 预取；openai/codex —— 默认 grep/read 为核心的工具集；SWE-agent —— 经典的 search→view 迭代循环设计。

```text
我想弄清这个 Agent 仓库的按需上下文加载策略：请定位它给模型提供了哪些搜索/读取类工具（grep、search、read_file、glob 等），以及这些工具的结果如何控制体积（行数上限、行号区间、分页、结果条数），引用具体 file:line；然后讲清一次典型的「模型搜索→读文件→继续推理」循环里数据如何流动，以及有没有提示词层面的「优先搜索而非预载」指令；点出工具定义与结果处理的关键数据结构和函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B6. 上下文编辑（Context Editing）｜P1

**是什么**：不经摘要、直接对已进入历史的内容做原地改写或删除——把陈旧的大块工具输出换成占位符、烧掉已被后续操作覆盖的旧文件视图、按消息 ID 删除或覆盖消息——保持消息结构不变但缩小体积。

**为什么重要**：它比 compaction 便宜（通常不需要一次额外 LLM 调用）且可增量进行，是对「对话历史不可变」这一默认假设的突破；模型在下一轮看到的是被改写过的历史，理解「内容被动过但痕迹如何标注」是解释行为漂移的关键。

**快速信号**：grep `history_processor`、`squash`、`redact`、`burn`、`placeholder`、`prune`、`drop_message`、`RemoveMessage`、消息 ID 上的 update/delete 操作；看发送请求前对消息列表做的最后一步变换。

**代表实现**：SWE-agent —— 可组合的 history processors（如编辑命令后烧毁旧文件视图行）；langchain-ai/langgraph —— add_messages reducer 支持按消息 ID 覆盖与删除；letta-ai/letta-code —— 模型用工具直接改写自己的 core memory block。

```text
我想弄清这个 Agent 仓库是否有 context editing（对已进入历史的内容做原地改写或删除）机制：请定位发送请求前对消息列表做的变换步骤——是否把陈旧的工具输出替换为占位符、是否按消息 ID 删除或改写历史消息、是否清理已被后续操作覆盖的旧内容，引用具体 file:line；然后讲清这些变换在什么条件下触发、模型在下一轮看到的历史因此变成什么样，用文字描述整条流程；点出关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B7. 历史压缩与摘要（Compaction / Conversation Summarization）｜P1

**是什么**：当历史超过阈值时，用一次 LLM 调用把旧轮次折叠成结构化 summary 消息，替换原历史后继续会话，通常保留最近若干轮原文和关键工作状态（TODO、打开的文件等）——它是会话内短期记忆（D1）的「遗忘侧」。

**为什么重要**：这是 Agent 能「跨小时工作」的续命机制，决定长任务不中断的上限；摘要 prompt 的设计（保什么、丢什么、怎么避免丢任务目标）和触发时机（手动 /compact 还是自动阈值）直接决定长会话质量与 token 成本。

**快速信号**：grep `compact`、`compaction`、`summarize`、`condense`、`condenser`、`summary`；找「生成 summary → 替换历史 → 插入 summary 消息」的函数及其触发条件判断（阈值常量或手动命令分支）；配置项形如 `auto_compact`、`auto-condense`。

**代表实现**：openai/codex —— `/compact` 与逼近上限时的自动 compaction，把历史折叠为带边界的 summary 消息；OpenHands —— 可插拔的 condenser 抽象（NoOp / RecentEvents / LLM 摘要等策略族）在事件流送入 LLM 前统一收敛；cline/cline 与 RooCodeInc/Roo-Code —— 逼近上限时自动整理并压缩对话。

```text
我想弄清这个 Agent 仓库的 compaction（历史压缩/摘要）机制：请定位触发条件的判断处（阈值怎么定、手动命令和自动触发分别走哪条路径）、摘要生成用的 prompt、以及摘要写回历史的位置，引用具体 file:line；然后按调用流程讲清压缩发生时旧消息去了哪里、哪些内容被保留原文（如最近几轮、关键工作状态）、摘要以什么消息形态插回上下文、压缩后与缓存及会话状态如何衔接；点出关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B8. 超限策略（Context Overflow Handling）｜P1

**是什么**：请求真的撞上 context length 上限时的应对链——截头续尾的滑动窗口、自动触发压缩后重试、清空历史重来，或把错误上抛给调用方。

**为什么重要**：超限错误是长任务最常见的硬中断源；各家「先试什么、再试什么」的降级顺序（重试 → 截断 → 压缩 → 放弃）体现可用性与信息保留之间的取舍，是读代码时最值得画成流程图的一条控制流。

**快速信号**：grep `context_length`、`maximum context`、`too long`、`exceeds`、`over.*limit`、`auto.*compact`、`sliding window`、`trim_messages`；看 API 错误处理分支里对超限错误的专门 case 和它的降级路径。

**代表实现**：openai/codex —— 逼近上限先自动触发 compaction 而非等报错；langchain-ai/langgraph —— `trim_messages` 按策略裁剪历史；OpenHands —— condenser 在溢出前后接管历史结构。

```text
我想弄清这个 Agent 仓库在撞上 context length 上限时的处理策略：请定位 API 错误处理中对超限错误的专门分支，以及触发后的降级链（直接重试、截断历史、自动压缩、清空、或上抛给调用方），引用具体 file:line；然后讲清从「请求失败」到「下一次成功请求」之间每一步的顺序和条件，以及自动压缩的触发水位与手动命令的关系，用文字描述整条控制流；点出关键错误码判断、数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个值得继续追问的点。
```

#### B9. Prompt Caching 与前缀稳定性（Prompt Caching & Prefix Stability）｜P1

**是什么**：利用 provider 的 prompt cache（按消息序列前缀命中计费与加速），在工程上保持前缀不变——稳定 system prompt 与工具定义、新内容只追加、摘要类会变动的内容后置。

**为什么重要**：缓存命中可把输入成本降一个数量级、显著降低延迟，等价于「同样的钱跑多几倍轮次」；反过来，任何在中途插入或改写历史的行为（很多压缩策略正是如此）都会让缓存整段失效——缓存约束会反过来塑造压缩与消息排序的设计。

**快速信号**：grep `cache_control`、`cached_tokens`、`prompt_cache`、`cache_read`、`ephemeral`、`prefix`；看请求组装处是否给消息打 cache 断点、是否有「把会变的内容挪到序列尾部」的排序逻辑、usage 里缓存命中字段在哪里被读取统计。

**代表实现**：Aider-AI/aider —— 显式为缓存设计消息顺序（摘要与变动内容后置）；cline/cline —— 标注 cache 断点利用 Anthropic prompt cache；openai/codex —— 保持 instructions 前缀稳定并跟踪缓存命中统计。

```text
我想弄清这个 Agent 仓库如何利用 prompt caching：请定位请求组装处与缓存相关的处理——cache 断点或标记怎么打、system prompt 与工具定义是否保持前缀稳定、会变动的内容是否被挪到消息序列尾部，引用具体 file:line；然后讲清一次命中缓存和一次缓存失效的请求在消息组装上有什么差别、usage 里的缓存命中字段在哪里被读取和统计，用文字串起这条数据流；如果这个仓库没有显式的缓存利用设计，请直说，并指出请求组装中哪些行为事实上影响缓存命中（前缀是否稳定、变动内容放在哪里）；点出关键数据结构与函数名；最后给出 2-3 个值得继续追问的点。
```
