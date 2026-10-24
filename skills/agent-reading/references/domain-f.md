> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### F. 规划与推理（Planning & Reasoning）（L1048–L1205）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### F. 规划与推理（Planning & Reasoning）

Agent 在「动手之前想清楚、动手之中纠偏、动手之后验证」全过程的思考控制机制。Agent 与「一次性补全」的分界线就在这一层：把一个模糊目标变成带顺序的子任务，决定每一步先想什么再做什么，跑完一步之后拿外部结果修正自己。读懂规划与推理，就是把「计划从哪里产生 → 以什么形态驻留 → 如何驱动与约束执行 → 偏离时如何修正」这条链路找全。（子 agent 派发的编排视角见 E2。）

#### F1. Plan Mode（计划模式：只读规划与批准门槛）｜P1

**是什么**：Agent 的一种受限运行模式——只许读代码不许写，产出一份结构化计划，经用户批准后才切换到执行模式解锁写操作。

**为什么重要**：它把「想」和「做」拆成两个阶段，用人类批准作为不可逆操作的闸门，是 Agent 可控性与安全性的第一道防线；同时天然隔离了探索期的上下文污染（翻了一百个文件找线索的噪音不会带进执行阶段）。与审批门的权限策略（H5）联动。

**快速信号**：grep `plan_mode`、`PlanMode`、`exit_plan`、`approval`、`suggest`、`read_only`、`allowed_tools`、`tool_filter`；找模式枚举或配置字段（`mode`、`approval_policy`）；看 `modes/`、`prompts/`、`agents/` 目录下按模式组织的提示词文件。

**代表实现**：cline/cline — VS Code Agent 插件，UI 上显式的 Plan/Act 双模式切换，plan 模式下收窄工具集、以专用响应工具结束规划征求用户确认；openai/codex — Rust CLI，plan 模式与 approval policy 联动，计划获批后才放行写盘与命令执行类工具；Aider-AI/aider — `--architect` 模式：一个模型只出方案（architect），另一个模型负责落地编辑（editor），同一套规划/执行分离思想的另一种切法。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的 plan mode（计划模式）——只读规划、产出计划、批准后再执行——是怎么实现的。请在本仓库定位 plan 模式的定义与切换入口（模式枚举或配置字段、进入与退出的触发条件、该模式下工具集如何被收窄或过滤），引用具体 file:line；然后用文字讲清完整状态流转：用户进入 plan 模式 → Agent 产出计划 → 计划以什么形态呈现与确认 → 批准后如何切换到执行模式并解锁哪些工具；点出承载模式状态的关键数据结构与函数名（如模式枚举、工具过滤逻辑、计划文本的传递路径）；若本仓库没有独立的 plan 模式请直说并指出最接近的替代实现；最后给出 2-3 个值得继续追问的切入点。
```

#### F2. TODO 列表驱动执行（Task List as State Machine）｜P1

**是什么**：把计划物化为一份结构化任务清单（通常每项带 status 字段），Agent 每轮读取它、完成一项就写回更新，作为跨轮次的执行状态机。

**为什么重要**：LLM 没有可靠的跨轮次工作记忆，TODO 列表是最便宜的持久化执行状态：它既是对抗「忘记自己做到哪」的锚点，也是用户观察进度的 UI，还能在上下文压缩后幸存——清单在，任务就不丢。

**快速信号**：grep `todo`、`todos`、`task_list`、`checklist`、`plan.md`、`tasks.json`；找清单条目的类型定义（`status`、`priority`、`in_progress`）；看「每轮把清单渲染进 system prompt 或 user message」的代码（`render`、`format_todos`、`inject`）。

**代表实现**：OpenHands — 计划以人类可读的 markdown 任务清单存在会话 state 里，每个 step 由模型读写更新，并直接渲染给用户看进度；cline/cline — 规划阶段产出带 checkbox 的计划文档，执行阶段逐步勾销对应用户可见；yoheinakajima/babyagi — 极简经典：任务队列 + 每轮重排优先级，把「列表即状态」推到极致。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的 TODO/任务清单驱动执行机制——任务清单作为跨轮次状态，每轮读取、完成一项、写回更新。请在本仓库定位清单的数据结构定义与读写入口（清单存在内存还是落盘、每轮在什么时机读入、什么时机写回），引用具体 file:line；然后用文字讲清一次「读取清单 → 执行一项 → 更新状态」的完整数据流：清单如何被渲染进模型上下文、模型如何表达更新意图、代码侧如何解析并应用更新；点出清单条目的字段与负责增删改的函数名；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点，例如清单在上下文压缩时是否保留。
```

#### F3. 任务分解（Task Decomposition）｜P1

**是什么**：把一个模糊的大目标拆成原子化、可单独验证、有依赖顺序的子任务序列，再交给执行环节消费。

**为什么重要**：分解质量直接决定 Agent 成功率的上限——子任务粒度决定单步难度，依赖顺序决定能否并行，验证点决定错误能否被局部化；planner 的 prompt 写得好不好，很多时候比执行器更影响结果。

**快速信号**：grep `decompose`、`subtask`、`subtasks`、`sub_goal`、`milestone`、`planner`、`plan_steps`；看 prompt 模板里的分解指令（"break down"、"create a step-by-step plan"）；找「planner 产出结构化列表 → executor 逐项消费」的节点或函数对。

**代表实现**：langchain-ai/langgraph — Plan-and-Execute 模板：planner 节点产出子任务列表，executor 逐项执行，replan 节点在偏离时重排剩余任务；ag2/AutoGen — GroupChat 由 manager 把任务拆给不同角色 agent，对话即分解；yoheinakajima/babyagi — 根据目标与已完成任务反复生成「下一个最有价值的任务」。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的任务分解（task decomposition）机制——大目标如何被拆成有顺序的子任务。请在本仓库定位分解发生的位置：是独立的 planner 角色/节点/提示词模板，还是主 agent prompt 里的一段指令，以及分解结果的解析代码在哪里，引用具体 file:line；然后用文字讲清数据流：原始目标与什么上下文一起进入分解环节、模型被要求输出什么格式、解析后得到什么样的子任务数据结构、执行侧按什么顺序消费它；点出子任务条目的字段定义与调度函数名；若本仓库没有显式分解机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点，例如子任务失败时是重试还是重新分解。
```

#### F4. ReAct 循环范式：思考-行动-观察交替（The ReAct Pattern）｜P0

**是什么**：Agent 主循环的经典提示词层形态——模型输出一段 Thought（下一步为什么这么做）加 Action（工具调用），环境返回 Observation（执行结果）拼回上下文，循环直到模型给出最终回答或触发终止条件。

**为什么重要**：几乎所有 coding agent 的「while 循环 + 工具调用 + 结果回填」（工程骨架见 A1）都是 ReAct 的工程化变体；读懂它就读懂了 agent loop 的行为范式——消息历史怎么组织、工具结果怎么裁剪、循环何时停，这是读一切 Agent 仓库的第一课。与 A1 的分工：A1 是工程骨架（messages/工具调用/回填），F4 是提示词协议层的范式（显式思考文本与动作交替）；现代实现里 Thought 常被推理模型的内部推理替代（见 F5），但循环式 Agent 的消息历史组织——thought/action/observation 的排列与裁剪——仍是 ReAct 结构的直接继承，故仍属地基点。

**快速信号**：grep `Thought`、`Action`、`Observation`、`scratchpad`、`agent_loop`、`step`、`run_step`；找 `while` 驱动的 `run/step/execute` 主函数；看工具结果如何被截断、格式化后追加进消息历史。

**代表实现**：SWE-agent — ACI（agent-computer interface）模板显式约定 thought → action 的输出格式，环境观察经过裁剪再回填；langchain-ai/langgraph — 图结构化的 ReAct agent：节点间传递含消息历史的 state，教程级清晰；letta-ai/letta-code — 带 heartbeat 概念的 agent loop，思考与工具调用交替、外部事件可打断。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的 ReAct 式主循环——思考（thought）、行动（action/工具调用）、观察（observation）交替直到任务完成——是怎么实现的。请在本仓库定位这个 agent loop 的主函数（驱动循环的 while/递归结构、每轮构造模型请求的位置、工具结果回填历史的位置），引用具体 file:line；然后用文字讲清一轮完整迭代的调用流程：模型输出如何被解析出思考与工具调用、工具如何被分发执行、观察结果经过什么处理（截断、格式化）后拼回上下文、终止条件在哪判断；点出消息历史的数据结构与关键函数名（如 step、execute、dispatch 一类调用链）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个追问点，例如单轮失败或工具报错时循环如何反应。
```

#### F5. 结构化思考输出（Thought 字段与 Scratchpad 格式）｜P1

**是什么**：要求模型把「思考」写进带明确标记的独立区块——JSON 里的 `thought` 字段、XML tag、或专门围栏——与工具调用参数和最终回答在结构上分离。

**为什么重要**：思考与行动分离，下游代码才能解析、隐藏、持久化或审查推理过程（不分离就只能全量当文本）；显式思考块也是强制「先想后动」的手段——没有它，模型容易直接吐工具调用，规划就退化成了条件反射。

**快速信号**：grep `thought`、`thinking`、`reasoning`、`scratchpad`、`chain_of_thought`；找 JSON schema 或 pydantic/serde 模型里的 thought 字段、`<thinking>` 类 tag 的解析与剥离代码；看 prompt 里「respond in the following format」的输出格式约定。

**代表实现**：SWE-agent — 输出模板强制每个动作前带 thought 字段，解析时单独摘出；openai/codex — 原生 reasoning 模型的 reasoning item 与普通消息分层存放，各自有不同的展示与持久化策略；letta-ai/letta-code — 消息中显式的 reasoning 块，可配置隐藏不进后续上下文。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的结构化思考输出机制——模型的推理过程被要求写进独立标记的区块（如 thought 字段、XML tag、专用围栏），与工具调用和最终回答分离。请在本仓库定位输出格式的约定处（prompt 里的格式指令或 response schema 定义）以及解析/剥离思考块的代码，引用具体 file:line；然后用文字讲清数据流：模型输出在哪里被解析、思考块被摘出后去向哪里（展示给用户？落盘持久化？还是从后续轮次的上下文里剔除）、解析失败时的兜底逻辑是什么；点出承载思考内容的类型定义与解析函数名；若本仓库思考与工具调用混在同一文本里请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F6. 推理预算与思考分级（Reasoning Effort / Thinking Budget）｜P1

**是什么**：让用户或上游代码配置模型「想多深」的旋钮——reasoning effort 级别或思考 token 预算，可按任务难度静态设置或动态调整。

**为什么重要**：规划型 Agent 的成本大头在思考 token；分级旋钮让同一套循环「便宜地扫、贵地想」，直接决定单位预算下能覆盖多少任务；它也影响截断策略与上下文分配，是实战调参的第一入口。

**快速信号**：grep `reasoning_effort`、`effort`、`thinking_budget`、`thinking`、`extended_thinking`、`reasoning`；看配置文件解析（config.toml / config.yaml / settings）里如何读取并透传到 API 请求体的字段；找按档位切换 prompt 或模型的地方。

**代表实现**：openai/codex — 配置里的 `model_reasoning_effort` 从 minimal 到 high 直接透传给模型，控制思考深度；sst/opencode — 把 reasoning effort 作为可切换参数暴露在 CLI/会话层，随会话调整。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的推理预算/思考分级机制——reasoning effort 或 thinking budget 这类控制模型思考深度的配置——是怎么实现和传递的。请在本仓库定位这个配置的定义处（默认值、合法取值、在哪个配置文件或 CLI 参数里）、校验逻辑、以及最终被写进模型 API 请求体的位置，引用具体 file:line；然后用文字讲清数据流：用户设置 → 配置解析 → 会话/请求构造 → API 参数；点出相关字段名与传递链上的函数名；再看一下是否有按任务难度或阶段动态调整 effort 的逻辑（例如规划阶段高、执行阶段低）；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F7. 反思与自我批评（Reflection / Self-Critique）｜P1

**是什么**：让 Agent 对自己刚生成的产物（代码、回答、计划）再跑一轮 critique——换个评审视角挑毛病，产出修正意见后重新生成。

**为什么重要**：单次生成的错误率不可控；自我批评用同一个模型换 persona（评审者、失败模式清单、评分 rubric）来捕错，是成本最低的自我验证层，常与外部验证（跑测试，F8）互补——测试抓「错」，反思抓「不好但不报错」。

**快速信号**：grep `reflect`、`critique`、`self_review`、`reviewer`、`improve`、`revise`、`retry`；找 generator 与 critic 两套 prompt 模板；看状态机里的「生成 → 评审 → 重写」循环或消息里的 reviewer 角色。

**代表实现**：langchain-ai/langgraph — Reflection 教程：generator 节点与 reflector 节点循环互怼，直到达到轮数上限或质量阈值；ag2/AutoGen — 对话式互评：给两个 agent 分配生成者与批评者角色，多轮对话收敛；Aider-AI/aider — architect/editor 双模型分工中，editor 模型对 architect 方案的可落地性构成一道交叉检查。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的反思/自我批评（reflection/self-critique）机制——Agent 对自己刚生成的产物再跑一轮评审并据此修正。请在本仓库定位反思发生的位置：是独立的 critic 角色/节点/第二套 prompt，还是同一次请求里要求模型先自查再改，以及反思结论如何触发重新生成，引用具体 file:line；然后用文字讲清完整调用流程：第一轮产物产生后经过什么路径进入评审、评审 prompt 里给了哪些评判标准或失败模式清单、修正意见与原始产物如何拼在一起送给下一轮、循环何时终止；点出相关角色/节点定义与函数名；若本仓库没有这一机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F8. 编辑-验证循环（Edit-then-Test / Verify Loop）｜P1

**是什么**：每次代码编辑后立即运行测试/lint/构建命令，把失败输出喂回模型修改重试，直到通过或预算耗尽——「改完就跑」是硬约束而不是建议。

**为什么重要**：这是 coding agent 与聊天机器人的分水岭：外部执行器提供模型无法凭空得到的 ground truth，错误修正闭环由此成立；没有验证循环的 agent 改错代码会一路自信狂奔，「改完不跑」的输出必然漂移。

**快速信号**：grep `run_tests`、`test_cmd`、`pytest`、`lint`、`build`、`verify`、`validate`；看编辑/写文件工具的定义里是否自动追加验证步骤；找测试失败输出的截断、解析与回填逻辑；配置项形如 `auto_test`、`test_command`。

**代表实现**：Aider-AI/aider — `--test` 模式：每次编辑后自动跑测试命令，失败则自动回滚到上一个 commit 再让模型重试；SWE-agent — ACI 里内建 lint/测试子命令，提交前强制执行，失败输出回填进循环；OpenHands — 编辑动作后由执行环境跑命令并把 stdout/stderr 作为 Observation 送回模型。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的编辑-验证循环（edit-then-test / verify loop）——每次修改代码后立即跑测试/lint/构建，把失败输出喂回模型重试。请在本仓库定位验证的触发点（编辑工具内部自动触发、还是独立的验证步骤/命令）、测试或构建命令从哪里来（用户配置、自动探测还是内置默认）、以及失败输出如何被处理回填，引用具体 file:line；然后用文字讲清一轮「编辑 → 运行 → 失败 → 修正」的完整调用流程与数据流，点出相关工具定义、命令执行函数与输出截断/解析的函数名；另外看有没有失败次数上限或回滚机制；若本仓库没有自动验证循环请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F9. 探索与收敛的节奏控制（Explore→Converge 与预算约束）｜P1

**是什么**：对 Agent 的注意力做阶段化管理——前期广撒网（搜索、读文件、多假设并存），后期收缩到单一方案深挖；用步数/token/文件数等预算上限防止跑飞。

**为什么重要**：无节制的 Agent 有两个经典死法：「无限探索」（一直 grep 一直读，不动手）和「过早收敛」（第一个看似合理的方案直接改）；节奏控制——步数上限、阶段性提示、探索与编辑工具的分期解锁——是实战中调参收益最大的部分。

**快速信号**：grep `max_steps`、`max_iterations`、`step_limit`、`budget`、`token_budget`、`max_cost`；看系统提示词里的阶段指令（"first explore, then implement"）；找按阶段解锁工具、或到步数阈值时注入「开始收敛」提醒的代码。

**代表实现**：Aider-AI/aider — repo map 的 token 预算决定模型「看得见多少代码」，探索广度成为可调参数；SWE-agent — 先定位再编辑的动作序列设计（search → open → edit → lint/test），把两阶段节奏刻进工具流；OpenHands — condenser 对历史做压缩，为后续步骤保住注意力预算。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它对探索与收敛节奏的控制——如何避免 Agent 无限探索不收敛、或过早锁定单一方案，以及步数/token 等预算上限如何约束循环。请在本仓库定位这些约束的定义与执行处：最大步数或迭代上限在哪定义和检查、预算（token/成本/文件数）如何统计与耗尽时如何反应、是否存在按阶段解锁工具或在特定阶段注入「该收敛了」类提示的逻辑，引用具体 file:line；然后用文字讲清一个接近上限的会话里会发生什么（截断？压缩？强制总结收尾？）；点出相关配置字段、计数器与判断函数名；若本仓库没有显式节奏控制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F10. 计划持久化与重规划（Plan Persistence & Replan）｜P1

**是什么**：把计划与执行状态落盘（checkpoint / state 文件），会话中断后可恢复继续；执行偏离预期或环境变化时触发 replan，重新生成剩余计划。

**为什么重要**：长任务必然遭遇上下文溢出、进程崩溃与需求变更；持久化让计划超越单次会话成为活文档，重规划让计划可以边执行边改——没有这两样，计划只是一次性脚本，agent 就不能真正跑长流程。通用的 checkpoint/resume 机制见 G8。

**快速信号**：grep `checkpoint`、`state.json`、`resume`、`replan`、`persist`、`save_state`、`snapshot`；langgraph 风格的 checkpointer 抽象；找计划文件被读回、与当前进度做 diff 的代码。

**代表实现**：langchain-ai/langgraph — checkpointer 抽象：任意 state graph 的每一步状态可持久化、断点恢复、甚至时间旅行回放；OpenHands — 会话 state（含计划与事件流）整体序列化，恢复后从断点继续；openai/codex — 会话 rollout 落盘，`resume` 重放恢复线程后可基于既有进度继续推进。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的计划持久化与重规划（plan persistence & replanning）机制——计划与执行进度如何落盘以便中断后恢复，执行偏离时如何触发重新规划。请在本仓库定位两处代码：一是计划/执行状态的持久化写入与恢复读取（存成什么格式、何时写、resume 时如何还原）；二是 replan 的触发条件与执行逻辑（什么信号判定计划失效、重规划是全量重生成还是只改剩余步骤），引用具体 file:line；然后用文字讲清一次「计划更新落盘 → 会话中断 → 恢复 → 判定偏离 → 重规划」的完整流程与数据流；点出相关状态结构与函数名；若本仓库没有 replan 机制请直说并指出最接近的替代实现；最后给出 2-3 个追问点。
```

#### F11. 多路径探索与回溯（Tree Search / Backtracking）｜P2

**是什么**：不押注单条推理路径——同时维护多条候选（分支/树/束），用评估器给中间状态打分，扩展最优、剪枝或回溯劣者，最终择优输出。

**为什么重要**：它把「一次生成定生死」升级为搜索问题，在可验证性强的任务（有测试、有评分）上显著提高成功率；代价是预算乘数——读懂它才知道一个 agent 何时值得并行下注、何时纯浪费。

**快速信号**：grep `beam`、`tree_search`、`branch`、`candidate`、`prune`、`backtrack`、`best_of`、`n_samples`、`ensemble`；找对同一任务多次采样再选优的循环（父状态克隆、子状态扩展、评分排序）。

**代表实现**：langchain-ai/langgraph — Tree of Thoughts 风格的图实现：候选状态作为并行分支，评估节点打分后剪枝；SWE-agent — 对同一问题多次独立运行再择优的 ensemble 实践（无共享树的并行下注）。

```text
我在阅读一个开源 Agent 项目的源码，想弄清它的多路径探索与回溯机制（tree search / backtracking）——是否同时维护多条候选推理或解决方案路径，评分后扩展最优、剪枝或回溯劣者。请在本仓库定位候选路径的表示（分支节点、候选状态、采样副本）、评估器（谁给中间状态打分：模型自评、测试结果还是外部函数）、以及扩展/剪枝/回溯的调度逻辑，引用具体 file:line；然后用文字讲清一轮「生成候选 → 评分 → 选择扩展/回溯」的完整调用流程与数据流，点出候选状态的数据结构与调度函数名；若本仓库只走单条路径请直说，并指出最接近的替代实现（例如简单的多次采样择优或失败重试）；最后给出 2-3 个追问点。
```
