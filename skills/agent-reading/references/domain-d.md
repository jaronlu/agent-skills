> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### D. 记忆系统（Memory Systems）（L676–L847）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### D. 记忆系统（Memory Systems）

Agent 在「这一轮 → 这场会话 → 跨会话」三个时间尺度上记住、召回与遗忘信息的机制全集。记忆不是单一模块：它散布在消息历史的追加逻辑、落盘的 session 文件、启动时读入的约定文件、后台抽取事实的任务、以及检索注入上下文的路径里。读懂一个记忆系统，就是把「信息产生 → 持久化 → 召回 → 注入 → 淘汰」这条链路找全。（历史压缩见 B7；项目指令文件的 prompt 组装视角见 B1。）

#### D1. 会话内短期记忆：消息历史与事件流（In-Session Short-Term Memory）｜P0

**是什么**：单次会话中 Agent 维护的有序消息/事件序列，是模型每轮「看见刚才发生了什么」的唯一载体。

**为什么重要**：几乎所有 Agent 的核心运行时状态就是这条列表——多轮推理、工具调用闭环、上下文压缩全部建立在它之上；看不懂它就看不懂其余一切。它作为循环状态的执行视角（单/多轮、持久化）见 A4。

**快速信号**：grep `messages`、`history`、`conversation`、`turns`、`add_message`、`append`、`event_stream`；找 `agent/`、`core/`、`state/` 目录里的大数组或队列结构；留意类型定义 `class Message`、`interface Event`、`enum …Item` 及 pydantic / serde 模型。

**代表实现**：openai/codex — Rust 会话线程里按轮追加模型消息与工具调用结果，作为会话的唯一真相源；OpenHands — append-only EventStream，Action 与 Observation 统一作为事件入列；SWE-agent — `self.history` 列表，配 history processors 把冗长的旧动作改写成短别名省 token。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的会话内短期记忆——单次会话里维护的消息历史或事件序列——是怎么实现的。请在本仓库定位这条消息链的核心数据结构（messages/history/turns 之类的数组、队列或事件流对象）以及每轮的写入点，引用具体 file:line；然后用文字讲清完整数据流：模型输出与工具结果产生后，经过哪些函数被追加进历史，下一轮构造请求时这段历史又如何被序列化发给模型；点出关键类型定义和函数名（如 append、add_message、step 的调用链）；若本仓库没有独立的历史结构，请直说并指出最接近的替代实现；最后给出 2-3 个值得继续追问的切入点。
```

#### D2. 会话持久化与恢复（Session Persistence / Resume）｜P1

**是什么**：把一场会话的完整状态序列化落盘（JSONL rollout、事件流、checkpoint 一类），并在新进程里 resume 时还原回内存；配套用户命令面（`/compact`、`/clear` 一类对持久化数据的操作）、历史回放与校验、以及从历史某点 fork 分叉的能力。

**为什么重要**：它是「跨会话」最基础的一步——没有落盘就没有恢复；长任务的另一半是「跨天存活」：崩溃恢复、断点续跑、让用户在关键时刻手动介入上下文（压缩或清空）。落盘格式决定了崩溃恢复、审计回放和 fork 会话能做到什么程度；会话文件格式也是观察一个 Agent 上下文真实形状的最好窗口。诊断视角的 replay/time travel 见 J7；容错视角的崩溃恢复见 G10。

**快速信号**：grep `rollout`、`session`、`resume`、`fork`、`persist`、`serialize`、`checkpoint`、`jsonl`、`save_session`、`load_session`、`replay`；目录 `sessions/`、`storage/`、`history/`，或用户主目录下 `~/.{app}/sessions` 一类约定；看会话文件的写入与读取两侧的 schema 定义。

**代表实现**：openai/codex — 会话逐事件写入 rollout JSONL 文件，`codex resume` 重放恢复完整线程并支持从历史点分叉；aaif-goose/goose — 每场会话存为本地 JSONL，可列出并恢复继续；OpenHands — 事件流持久化到会话存储，resume 靠重放事件重建状态；letta-ai/letta-code — 会话与消息跨进程持久化。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的会话持久化与恢复机制：一场会话的完整状态如何被序列化落盘，新进程里 resume 时又如何还原。请在本仓库定位会话的存储层（落盘格式、目录组织、写入时机）和恢复逻辑（加载、校验、回放进内存中的消息历史），引用具体 file:line；然后用文字讲清一次「写入→落盘→重启→resume」的完整数据流，并说明哪些状态可恢复、哪些会丢失；点出关键的序列化结构与函数名（如 persist、serialize、load、resume 的调用链）；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点（例如 /compact、/clear 或类似命令分别对持久化数据做了什么、能否从历史某点 fork 分叉）。
```

#### D3. 文件型长期记忆（Memory / Hints / Rules 文件）｜P1

**是什么**：以 markdown / 纯文本文件为载体、跨会话存续的知识与偏好记忆，新会话启动时自动读入。

**为什么重要**：文件型记忆人类可直接审阅和编辑、随 git 版本化，是「用户偏好与项目约定」最常用的持久层；它与会话持久化（D2）的差别在于存的是提炼后的知识而非完整对话。这些文件如何被发现并拼进 system prompt，见 B1；这里聚焦存储与读写约定本身。

**快速信号**：grep `memory`、`memories`、`hints`、`conventions`、`remember`、`learnings`、`facts`；目录 `memory/`、`memories/`、`.config/{app}/`；文件名 `GOOSE.md`、`CONVENTIONS.md`、`*.mdc`。

**代表实现**：Aider-AI/aider — CONVENTIONS.md 若存在则自动读入对话，作为跨会话的持久约定；aaif-goose/goose — `.goosehints` 与 GOOSE.md 分层提示文件，进目录即生效；OpenHands — 用户级与仓库级 microagents markdown，作为长期知识随会话加载。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的文件型长期记忆：跨会话存在 markdown 或纯文本文件里的知识与偏好，新会话如何自动读入。请在本仓库定位这类记忆文件的路径约定（用户级与项目级分别在哪）、写入方（用户手写还是 Agent 自动追加）和加载点，引用具体 file:line；然后用文字讲清双向数据流：记忆条目如何被写进文件（谁触发、什么格式、是否去重），以及新会话启动时文件内容如何被注入上下文；点出关键函数名与文件格式约定；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D4. 自动记忆：从对话中抽取并召回事实（Auto-Memory）｜P1

**是什么**：不经用户显式操作，由 Agent 自动从对话里提取事实/偏好写入长期记忆、并在后续会话自动召回的机制。

**为什么重要**：自动记忆是「越用越懂你」的来源，但也是风险所在——错误抽取会把幻觉洗成「事实」，所以它的提取 prompt、确认环节和注入时机是审读重点。

**快速信号**：grep `auto.*memory`、`extract`、`fact`、`reflect`、`remember`、`memory_manager`、`teachable`、`learn`；后台任务/订阅者模式 `on_event`、`subscribe`、`background`；「每轮 / 会话结束 / 定时」三种触发时机的代码位置。

**代表实现**：mem0ai/mem0 — LLM 自动从对话抽取事实并对记忆库做 ADD / UPDATE / DELETE 决策；letta-ai/letta-code — Agent 用 core_memory_append / core_memory_replace 等工具自己编辑常驻记忆；OpenHands — MemoryCondenser 把事件流滚动摘要成随状态携带的 memory 字段供后续轮次使用。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的自动记忆机制：Agent 是否会不经用户显式要求，自动从对话中提取事实/偏好存入长期记忆，并在后续会话中自动召回。请在本仓库定位记忆提取的触发点（每轮、会话结束还是后台任务）、提取用的 prompt 或工具定义、以及召回时的注入点，引用具体 file:line；然后用文字讲清「对话内容→提取→存储→下次会话检索注入」的完整数据流；点出关键数据结构（记忆条目的 schema）和函数名；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D5. 数据库型长期记忆（SQL / Vector Store 持久层）｜P1

**是什么**：把会话、消息、记忆条目持久化在 SQLite / Postgres 或向量数据库里的存储抽象与实现。

**为什么重要**：文件型记忆在规模、并发检索和结构化查询上都有上限；存储层的抽象设计（repository / store 接口、表结构、事务）决定了记忆系统能否扩展到生产规模。

**快速信号**：grep `sqlite`、`postgres`、`sqlalchemy`、`prisma`、`vector`、`qdrant`、`chroma`、`pgvector`、`collection`、`repository`、`store`、`migration`；目录 `db/`、`storage/`、`store/`、`orm/`。

**代表实现**：letta-ai/letta-code — agent / block / message 等对象全量 ORM 持久化，支持 SQLite 与 Postgres；mem0ai/mem0 — 可插拔的 vector store 后端（Qdrant、Chroma 等），可选图存储；getzep/graphiti — 时序知识图谱（Neo4j）持久化事实、实体与关系。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的数据库型长期记忆：会话、消息、记忆条目是否持久化在 SQLite/Postgres 或向量库里。请在本仓库定位存储层的抽象（repository/store 一类的接口）、具体实现与表结构或 collection 设计，引用具体 file:line；然后用文字讲清一次记忆读写的完整调用链：上层调用哪个 API、经过哪些适配层落到数据库、事务与并发如何处理；点出关键的 ORM 模型或 schema 定义和函数名；若本仓库没有这一层请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D6. 记忆写入决策与淘汰策略（Write Policy & Eviction）｜P1

**是什么**：决定一条候选记忆何时写入（无条件追加还是经过去重/合并/LLM 裁决），以及记忆满了、重复了、过期了之后如何被更新或淘汰的策略。

**为什么重要**：写入不设闸会让记忆库被噪声灌满、检索精度崩塌；淘汰没有策略则记忆无限增长。「ADD / UPDATE / DELETE / NOOP」这类决策逻辑是记忆系统真正的智能所在。

**快速信号**：grep `ADD`、`UPDATE`、`DELETE`、`NOOP`（常出现在决策 prompt 里）、`dedup`、`duplicate`、`evict`、`expire`、`ttl`、`decay`、`forget`、`similarity_threshold`、`recent`、`window`；工具名 `core_memory_append`、`delete_memory`。

**代表实现**：mem0ai/mem0 — 用 LLM 对候选记忆与既有近邻做 ADD / UPDATE / DELETE / NOOP 裁决后再落库；letta-ai/letta-code — core memory 块有容量上限，靠 Agent 自我编辑腾挪，外层再分 recall / archival；OpenHands — RecentEventsCondenser 只保留最近 N 条事件的窗口式淘汰。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的记忆写入与淘汰策略：什么时候写入新记忆、如何避免重复、记忆满了或过期后如何淘汰。请在本仓库定位写入决策逻辑（是无条件追加，还是经过去重、合并或 LLM 判断 ADD/UPDATE/DELETE）以及淘汰机制（容量上限、TTL、衰减、最旧先出等），引用具体 file:line；然后用文字讲清一条候选记忆从产生到最终「写入/更新/丢弃」的完整判定流程；点出关键函数名与比较逻辑（如相似度阈值、哈希去重）；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D7. 关键词式检索：触发词与词法匹配（Keyword / Lexical Retrieval）｜P1

**是什么**：不走 embedding 的记忆召回路线——靠触发词命中、规则/文件名匹配、正则或 BM25 一类的词法检索把相关记忆找回来。

**为什么重要**：关键词检索零成本、可解释、无需向量基础设施，是 microagent 路由和 grep 式记忆的主力；理解它与语义检索（D8）的分工才能看懂一个仓库为什么（不）引入 embedding。

**快速信号**：grep `trigger`、`keyword`、`frontmatter`、`triggers:`、`match`、`contains`、`regex`、`bm25`、`fuzzy`；数据结构常见为触发词表（dict 或 markdown frontmatter 字段）与命中即注入的订阅逻辑。

**代表实现**：OpenHands — microagent 的 trigger 词命中即把对应知识片段注入上下文；Aider-AI/aider — repo map 用 tree-sitter 抽符号加图排序（词法/结构化，非 embedding）选出进上下文的文件。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的记忆检索中不走 embedding 的那一路：关键词/触发词/词法匹配式检索。请在本仓库定位这类检索的实现入口（如 trigger 词表匹配、规则或文件名命中、正则或 BM25 一类词法匹配），引用具体 file:line；然后用文字讲清从「用户输入或上下文出现某个关键词」到「对应记忆内容被注入」的完整数据流；点出关键词表的数据结构和匹配函数名；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D8. 向量检索：embedding 与语义召回（Embedding Retrieval）｜P1

**是什么**：把记忆文本 embed 后存入向量库，检索时用查询向量做相似度（cosine / kNN）搜索并取 top-k 注入上下文的召回路线。

**为什么重要**：语义检索解决「换个说法就搜不到」的问题，是大规模记忆库召回质量的关键；写入时 embed 还是检索时 embed、是否 rerank，直接影响成本与延迟。

**快速信号**：grep `embedding`、`embed`、`vector`、`similarity`、`cosine`、`knn`、`rerank`、`top_k`、`semantic`；目录 `embeddings/`、`vectorstore/`；依赖里的 embedding 模型与向量库客户端。

**代表实现**：letta-ai/letta-code — archival memory 写入即 embed，检索走向量相似 top-k；mem0ai/mem0 — search 走 vector store 相似度加可选 rerank；ag2/AutoGen — 检索增强路径把文档向量化进 Chroma / pgvector 供对话检索。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的向量检索式记忆：记忆如何被 embed、存进哪个向量库、检索时如何构造查询并排序。请在本仓库定位 embedding 的生成点（用哪个模型、在写入时还是检索时生成）、向量存储的抽象与具体实现、以及检索入口（similarity search、rerank），引用具体 file:line；然后用文字讲清「记忆写入→向量化→落库→查询→top-k 结果注入上下文」的完整数据流；点出关键接口与函数名（如 embed、upsert、search 的调用链）；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D9. MemGPT 式上下文分页：main context 与外存换页（Context Paging）｜P1

**是什么**：把 LLM 的上下文窗口当作「内存」、把外部存储当作「磁盘」，Agent 通过工具调用（search / insert / replace）在常驻 main context 与 archival / recall 外存之间主动换入换出内容的思想。

**为什么重要**：它把「上下文装不下」从系统限制变成 Agent 自己管理的资源问题，是 Letta / MemGPT 一脉的核心创新，也是理解一切 self-editing memory 设计的参照系。

**快速信号**：grep `archival`、`core_memory`、`recall`、`main_context`、`in_context`、`heartbeat`、`swap`、`page`；工具名 `core_memory_append`、`core_memory_replace`、`archival_memory_insert`、`archival_memory_search`、`conversation_search`。

**代表实现**：letta-ai/letta-code — 虚拟内存隐喻的原始实现：main context（system + core memory + 消息队列）配 recall / archival 外存与一整套换页工具；ag2/AutoGen — teachable 路径把学到的技能存外部、后续会话再检索回来，是「换页进上下文」的轻量版。

```text
我在阅读一个开源 Agent 项目的源码，想弄清其中 MemGPT 式「上下文分页」思想：把 LLM 上下文窗口当作内存，用工具调用在常驻的 main context 与外部的 archival/recall 存储之间换入换出内容。请在本仓库定位这套机制的核心：常驻上下文里放什么（core memory / 系统指令）、外部存储的读写接口（search / insert / replace 一类工具）、以及 Agent 自我编辑上下文的工具定义，引用具体 file:line；然后用文字讲清一次「上下文装不下→Agent 主动检索或换页→内容进入或离开窗口」的完整数据流；点出关键函数与工具名；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D10. 分层记忆架构：core / recall / archival 与命名空间（Memory Hierarchy）｜P1

**是什么**：按生命周期与访问方式把记忆划成多层——会话内工作区、跨会话的用户/项目记忆、归档检索层——各层独立定义数据结构与读写接口。

**为什么重要**：分层决定了「什么信息常驻、什么按需召回」，直接影响每轮 token 预算的分配；命名空间（用户级 / 项目级 / 线程级）还是多会话隔离与共享的基础。

**快速信号**：grep `block`、`layer`、`namespace`、`short_term`、`long_term`、`thread`、`store`、`working_memory`、`episodic`、`semantic`、`procedural`；接口形如 `Store`、`BaseStore`、`Memory` 的抽象定义处。

**代表实现**：letta-ai/letta-code — core memory（可编辑块）/ recall memory（会话消息检索）/ archival memory（长期向量库）三层；langchain-ai/langgraph — 短期记忆是 thread 内 state（由 checkpointer 持久化），长期记忆是跨线程的 Store 命名空间（可带语义索引）。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的记忆分层架构：不同生命周期的记忆是否放在不同层（如会话内工作区、跨会话的用户/项目记忆、归档检索层），各层如何定义和互通。请在本仓库定位分层的设计（接口、命名空间、block 或 store 的划分方式），引用具体 file:line；然后用文字讲清一条信息在层间的流动：何时从会话内状态沉淀到长期层、何时被检索回到工作区；点出各层的数据结构和读写函数名；若本仓库没有显式分层请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### D11. 记忆的数据模型：message / event / fact 三种形态（Data Model）｜P1

**是什么**：记忆的最小单元在内存与磁盘上的具体形态——message 对象、事件基类（Action / Observation）、item 枚举，或提炼后的事实/知识图谱节点。

**为什么重要**：数据模型决定了序列化格式、重放语义和可扩展性；「原始消息全存」与「只存提炼事实」是两种根本不同的设计立场，比较各仓库时这是最直接的切面。事件流的落盘与审计视角分别见 J4、H12。

**快速信号**：grep `class Message`、`class Event`、`Action`、`Observation`、`enum`、`Item`、`schema`、`to_dict`、`from_dict`、`model_dump`、`serialize`；找 pydantic / dataclass / serde 的定义处和 JSONL 写盘的字段。

**代表实现**：openai/codex — rollout item 枚举（message、function_call、function_call_output 等）逐条写入 JSONL；OpenHands — Action / Observation 事件基类构成的事件溯源（event sourcing）模型；getzep/graphiti — episodic / semantic / entity 三类节点加带双时间戳有效期的边。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它记忆的基本数据模型：一次对话或一轮交互在内存和磁盘上到底长什么样（message 对象、事件基类、item 枚举，还是知识图谱三元组）。请在本仓库定位这些类型的定义处（pydantic、dataclass 或 serde 序列化模型），引用具体 file:line；然后用文字讲清一个对象从产生、序列化到反序列化恢复的完整流程；点出类型之间的继承或组合关系和序列化格式（JSONL、JSON 字段还是表结构）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个追问点。
```

#### D12. 记忆与上下文工程的边界（Memory vs Context Engineering）｜P1

**是什么**：区分「跨轮持久化的部分（记忆）」与「每轮临时组装的部分（system prompt、工具定义、代码库摘要、注入的检索结果）」，以及两者在代码里各自的组装入口。

**为什么重要**：很多机制看似记忆实为每轮重算的上下文组装（如 repo map，B4），混为一谈会误判系统的持久化能力；找准每轮上下文组装函数，才能看清记忆到底在哪个环节被消费。

**快速信号**：grep `system_prompt`、`build_prompt`、`compose`、`assemble`、`inject`、`context_window`、`budget`、`repo_map`、`template`；目录 `prompt/`、`context/`；找每轮调用 LLM 前最后拼接消息列表的那个函数。

**代表实现**：Aider-AI/aider — repo map 每轮按 token 预算重算重排，是上下文工程而非持久记忆的典型样本；langchain-ai/langgraph — thread state（每轮组装）与跨线程 Store（持久记忆）在 API 层面就是分开的两个概念；OpenHands — condenser 管「这一轮给模型看什么」，microagent 管「长期知识何时被召回」，边界清晰可对照。

```text
我在阅读一个开源 Agent 项目的源码，想厘清「记忆系统」与「上下文工程」的边界：跨轮持久化的部分（记忆）与每轮临时组装的部分（system prompt、工具定义、代码库摘要、注入的检索结果）分别在哪里实现。请在本仓库定位每轮请求上下文的组装函数（拼接 system prompt、决定注入哪些记忆或检索结果、裁剪 token 预算的入口），引用具体 file:line；然后用文字讲清一轮请求的组装流程，并明确标出哪些内容来自持久记忆、哪些是每轮重算的；点出关键函数名（如 build_prompt、compose、inject 的调用链）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个追问点。
```
