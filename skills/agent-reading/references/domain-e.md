> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### E. 单 Agent 与多 Agent 协作（Single-Agent & Multi-Agent Orchestration）（L848–L1047）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### E. 单 Agent 与多 Agent 协作（Single-Agent & Multi-Agent Orchestration）

控制流与信息流如何在「一个 agent 的主循环」与「多个 agent 的协作拓扑」之间组织——什么时候值得派生、派给谁、传什么上下文、结果怎么收回与合并、并行怎么治理。读懂一个 Agent 仓库前，先回答它在这条轴上的位置：单 agent 循环、workflow 图编排，还是自由派生的 multi-agent。

#### E1. 单 Agent 主循环与适用边界（The Single-Agent Loop & Its Limits）｜P1

**是什么**：一个 agent 在「LLM 推理 → 工具调用 → 结果回填 → 再推理」的循环里独立完成全部任务，不派生任何子 agent（循环本体的实现细节见 A1）。

**为什么重要**：codex、Aider、Cline 等主流编码 agent 都是单 agent + 强工具集，因为多 agent 引入的通信、状态合并与 token 成本只有在「任务可并行分解」或「需要上下文隔离」时才划算。读懂单 agent 循环的终止条件（A2）与上下文压缩策略（B7），才能判断一个仓库为什么（不）需要多 agent；一些项目甚至从多 agent 演化回了单 agent。

**快速信号**：找主循环文件——常命名为 `agent.*`、`session.*`、`loop.*`、`run.*`、`coder.*`；grep `max_turns`、`max_iterations`、`tool_call`、`tool_use`、`while`、`spawn`、`delegate`（找不到派生点本身就是答案）。

**代表实现**：openai/codex —— Rust 单会话主循环，工具执行与回填都在一个 loop 内完成；Aider-AI/aider —— 单一 Coder 循环 + git 感知的文件编辑，从不派生子 agent；OpenHands —— 从 OpenDevin 时代的 delegator 多 agent 架构收敛回 CodeActAgent 单 agent + 事件流 + microagents 知识注入，是「多 agent 收敛回单 agent」的典型样本。

```text
我想理解这个仓库里单 agent 主循环的适用边界：请定位 agent 的核心循环入口（通常是 LLM 调用 → 工具执行 → 结果回填的那段 while/loop），引用具体 file:line；然后回答它为什么（不）需要多 agent：这个循环如何独立完成全部任务、它的终止条件与上下文压缩策略是什么、代码里有没有任何派生子 agent 的点（spawn/delegate/new_task 一类的调用）；如果有派生点，列出派生的触发条件；最后给我 2-3 个值得继续追问的点（比如如果任务可并行分解，单循环的瓶颈会先出现在哪里）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E2. Subagent 派生：Agent-as-Tool（Spawning Subagents）｜P1

**是什么**：主 agent 把「启动另一个 agent」包装成一个普通工具调用（常叫 Task / spawn / delegate / new_task），子 agent 跑完把最终结果作为观察/工具返回值交回父循环继续推理——排队与调度（队列、图路由、消息传递）决定并发度与结果汇聚方式，也是规划领域突破单上下文窗口的手段（planner 把子任务派出去、只回收结论摘要）。

**为什么重要**：这是几乎所有多 agent 编码系统的第一原语，也是区分「真 multi-agent」与「工具多、agent 一」的分水岭。派生点决定了三件事：子 agent 拿到什么 prompt 与工具集、它跑在什么上下文里、父 agent 得到什么；看懂派生工具的入参与返回值契约，就看懂了整个父子关系。子 agent 的上下文隔离详见 E3，并发治理详见 E13。

**快速信号**：grep `spawn`、`dispatch`、`delegate`、`subagent`、`sub_agent`、`new_task`、`task_tool`、`queue`、`orchestrat`、`supervisor`；在工具定义目录里找「启动一个 agent」的工具；目录 `orchestrator/`、`team/`、`graph/`、`runtime/`。

**代表实现**：Claude Code 的 Task 工具（设计公开，开源复刻如 opencode 有等价实现）——subagent 作为工具调用派生，结果以工具输出形式回父循环；cline/cline —— `new_task` 工具把子任务委托给一个新的 task 实例，干净上下文跑完再回传；OpenHands —— CodeActAgent 通过 delegate 类 action 把浏览等子任务交给专职 agent；ag2/AutoGen —— nested chats 为子对话提供隔离上下文；langchain-ai/langgraph —— subgraph 以独立 state 隔离上下文。

```text
我想理解这个仓库里 subagent 的派生机制（agent-as-tool）：请定位主 agent 用来启动子 agent 的那个工具或函数（常见名字如 Task、spawn、dispatch、delegate、new_task），以及子任务如何排队或调度（队列、图路由、消息传递），引用具体 file:line；用文字讲清一次派生的完整数据流——主 agent 怎么决定派生、派生调用传入了哪些参数（子任务 prompt、子 agent 身份或配置、工具集）、子 agent 在哪里被构造和运行、它的最终输出以什么形式（全文还是摘要）返回给主 agent 并写回父上下文、哪些信息被刻意留在子上下文里不带回；点出其中的关键数据结构与函数名（如派生请求对象、子 agent 构造函数、结果容器）；若本仓库没有子任务机制，也请指出代码证据并解释它的单体循环如何覆盖这类需求；最后给我 2-3 个值得继续追问的点（比如子 agent 能否嵌套再派生、同时派生的数量有没有上限）。
```

#### E3. 上下文隔离与干净上下文（Context Isolation / Clean Context）｜P1

**是什么**：子 agent 默认不继承父 agent 的对话历史，只拿到派生时构造的一次性 prompt，跑完只把结论回传，中间过程全部丢弃——本质是用隔离边界做上下文压缩：脏上下文随子 Agent 消亡，主线程只留结论。

**为什么重要**：上下文污染是长任务质量杀手——探索性搜索的噪音、失败尝试的痕迹都会在主线程累积；隔离让这些不污染父上下文，对抗 context window 膨胀。读源码要确认隔离的强度：是全新会话/全新 state（硬隔离），还是共享历史但过滤部分消息（软隔离）；工具权限与 system prompt 是否也随派生被替换。

**快速信号**：看派生函数里「子 agent 的初始消息怎么构造」——grep `fresh`、`clean`、`isolat`、`initial_messages`、`new session`；对比父与子的 system prompt 和工具列表差异；看子 Agent 的 prompt 模板（全新 system prompt 长什么样）与结果回传主上下文的数据结构。

**代表实现**：Claude Code——每个 subagent 独立 context window + 独立 system prompt + 裁剪过的工具集；cline/cline——`new_task` 以干净上下文启动新 task 实例，子上下文用完即弃；OpenHands —— delegate 把子任务交给独立 micro-agent 处理后返回结论；letta-ai/letta-code——每个 agent 持有私有 memory（core memory blocks、archival memory），跨 agent 只共享显式声明的 block。

```text
我想理解这个仓库里子 agent 的上下文隔离（context isolation）：请定位派生子 agent 时构造其初始上下文的代码（看它到底给了子 agent 哪些消息、system prompt、工具集），引用具体 file:line；用文字讲清隔离的数据流——父 agent 的对话历史有没有被复制或引用进子 agent？子 agent 运行中产生的中间消息（工具调用、思考）留在哪里，最终有多少内容回传给父 agent？父与子的 system prompt 和工具列表有什么差别；点出其中的关键数据结构与函数名（如初始消息构造函数、上下文对象、回传结果的截断或摘要逻辑）；最后给我 2-3 个值得继续追问的点（比如隔离是硬隔离还是软过滤、子 agent 的中间状态能否被外部检查）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E4. Supervisor / Orchestrator 模式（Supervisor Pattern）｜P1

**是什么**：一个中心 supervisor agent 持有全局视角，每轮决定「下一步把任务交给哪个 worker、带什么指令」，worker 干完汇报，supervisor 再决定，直到宣布完成。

**为什么重要**：supervisor 是最常见也最容易失效的多 agent 拓扑——控制流由 LLM 的路由决策驱动，灵活但容易死循环、重复派发、提前收工。读源码重点是三个问题：supervisor 的输出是什么结构（路由指令、工具调用还是自然语言）、有没有轮次/预算护栏、worker 结果怎么回到 supervisor 的输入。

**快速信号**：grep `supervisor`、`orchestrat`、`router`、`next_agent`、`delegate`、`hand_off`、`manager`；找「决定下一步」的节点或循环。

**代表实现**：langchain-ai/langgraph（langgraph-supervisor 官方示例库）——supervisor 节点输出路由命令，把各 worker 作为图节点调用；ag2/AutoGen——GroupChatManager 本质是带发言者选择的 supervisor 变体；crewAIInc/crewAI——hierarchical process 里由 manager 给 crew 成员分派 task。

```text
我想理解这个仓库里的 supervisor/orchestrator 模式：请定位中心调度者决定「下一步派给谁、带什么指令」的实现入口（常见名字如 supervisor、orchestrator、router、manager），引用具体 file:line；用文字讲清一轮调度的完整流程——supervisor 收到什么输入（任务描述加上哪些历史或 worker 结果）、它的输出是什么数据结构（路由指令、工具调用还是自然语言）、这个输出如何被解析成对某个 worker 的调用、worker 的返回如何写回 supervisor 的输入、循环怎么终止（完成判定、轮次上限、预算）；点出其中的关键数据结构与函数名；最后给我 2-3 个值得继续追问的点（比如防死循环和重复派发的护栏、supervisor 自己的上下文会不会随轮次膨胀）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E5. Planner–Executor 模式（Plan-then-Execute）｜P1

**是什么**：先把任务展开成一份显式的计划（步骤列表 / task list / TODO）并持久化，再由 executor（同一个 agent 换模式，或多个 agent）逐项执行，每步完成后回写计划状态，必要时重新规划。

**为什么重要**：与 supervisor「每轮让 LLM 现场决定下一步」不同，plan-then-execute 把控制流外化成可检查、可恢复、可打勾的数据结构——用户能审查计划，系统崩溃后能从计划处续跑。这是长任务 agent 的主流选择，也是单 agent 系统获得「半个 multi-agent」好处的最便宜方式（同一个 agent 的两个模式）。规划领域的深化见 F1–F3、F10。

**快速信号**：grep `plan`、`todo`、`task_list`、`steps`、`replan`、`checkpoint`；找计划的数据结构定义——常落在 markdown 文件、JSON 或 YAML 里。

**代表实现**：Aider-AI/aider——`--architect` 模式：architect 模型先出方案、editor 模型落盘编辑，两角色分工；cline/cline——PLAN / ACT 双模式切换，先产出显式计划再切到执行模式；langchain-ai/langgraph——plan-and-execute 官方示例：planner 节点产出步骤列表，executor 逐步消费并支持 replan。

```text
我想理解这个仓库里的 planner–executor（先规划后执行）模式：请定位计划（plan/todo/task list）的产生与消费代码——计划用什么数据结构表示（内存对象、文件、JSON）、由谁生成、存在哪里，引用具体 file:line；用文字讲清完整流程——planner 在什么时机被调用、计划里的步骤如何被 executor 逐项领取和执行、每步完成后计划状态如何回写（打勾、追加、replan）、执行失败时计划怎么处理；点出其中的关键数据结构与函数名（如步骤对象、状态字段、replan 入口函数）；最后给我 2-3 个值得继续追问的点（比如计划是否跨会话持久化、replan 有没有次数或触发条件限制）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E6. Pipeline / 状态图工作流（Graph / DAG Workflow）｜P1

**是什么**：把 agent 步骤编排成显式有向图——节点是 agent 或函数，边是（条件）转移，一份共享 state 沿图流动，每个节点只读写 state 的特定字段。

**为什么重要**：很多自称 multi-agent 的系统揭开看其实是「图编排 + 节点里装 agent」。图把控制流从 prompt 里拿出来变成代码可检查的结构，天然支持 checkpoint 恢复与并发分支。先看图怎么定义（命令式 API 还是声明式配置）与 state 怎么流动，就抓住了整个系统的骨架。判别仓库是否属于图式见 A8。

**快速信号**：grep `StateGraph`、`add_node`、`add_edge`、`conditional`、`workflow`、`dag`、`graph`；配置文件里找节点与转移的声明。

**代表实现**：langchain-ai/langgraph——StateGraph + conditional edges + checkpointer 的标杆实现，state 在 channel 上按 superstep 推进（Pregel 模型）；OpenHands——事件流（event stream）作为隐式总线，agent 与环境都是事件的生产者和消费者；crewAIInc/crewAI——process（sequential / hierarchical）把 task 编排成线性流水线或带 manager 的调度。

```text
我想理解这个仓库里的 pipeline / 状态图工作流（graph or DAG workflow）：请定位工作流的定义与执行入口——节点和边是怎么声明的（代码式 API 还是配置文件）、图在哪里被编译或校验、在哪里被驱动执行，引用具体 file:line；用文字讲清一次执行的完整数据流——初始 state 怎么进入图、每个节点读写 state 的哪些字段、条件边如何根据 state 决定下一跳、整个执行在哪结束、失败或中断后能否从 checkpoint 恢复；点出其中的关键数据结构与函数名（如 state schema、节点包装函数、条件路由函数）；最后给我 2-3 个值得继续追问的点（比如 state 字段的合并策略、图是否支持并发分支汇合）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E7. Fan-out 并行派发（Parallel Fan-out / Scatter-Gather）｜P1

**是什么**：把 N 个互不依赖的子任务同时派给 N 个子 agent 并行执行，等全部（或部分）完成后统一收回结果再继续，即 scatter-gather / map-reduce。

**为什么重要**：并行是 fan-out 的核心收益（总时长从串行求和变成最慢者），但放大成本与竞态。读源码看三点：并行单元怎么产生（一个任务拆 N 份，还是 N 个独立任务）、用什么原语等待（Promise.all / asyncio.gather / 同步 barrier）、部分失败怎么办（一个子 agent 挂了是整批作废、跳过还是重试）。工具级的并行（一回合多个 tool call）见 C10。

**快速信号**：grep `Promise.all`、`asyncio.gather`、`parallel`、`concurrent`、`fan_out`、`scatter`、`Send`、`map_reduce`。

**代表实现**：langchain-ai/langgraph——`Send` API 把一个节点 fan-out 成 N 个并行分支，是官方 map-reduce 范式；Claude Code（开源复刻如同 opencode）——一次响应里的多个 Task 工具调用可并行执行 subagent；ag2/AutoGen（0.4+ 异步重写）——asyncio 事件循环下的并发 agent 运行时。

```text
我想理解这个仓库里的并行 fan-out（scatter-gather）派发：请定位把多个子任务同时派给多个子 agent 并行执行、再统一收回结果的代码（常见线索：Promise.all、asyncio.gather、Send、fan_out、scatter），引用具体 file:line；用文字讲清完整流程——并行单元怎么产生的（一个任务拆成 N 份还是 N 个独立任务）、每个单元的 agent 在哪构造、用什么原语等待完成（全部完成还是先到先用、有没有 barrier）、某个子 agent 失败或超时时整批怎么处理（作废、跳过还是重试）、收回的结果按什么顺序进入后续步骤；点出其中的关键数据结构与函数名（如并行任务对象、结果数组、失败标记）；最后给我 2-3 个值得继续追问的点（比如部分失败有没有重试策略、结果顺序是否稳定）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E8. Agent 间通信：消息与 Channel（Message Passing & Channels）｜P1

**是什么**：agent 之间通过结构化消息交换信息——point-to-point 直发、topic 订阅或 broadcast 广播；channel 定义「谁写的什么、谁读得到」。

**为什么重要**：通信原语的粒度直接决定耦合度与上下文成本。两种极端各有代表：共享对话线程（人人可见全部历史，上下文贵但信息全）vs 按字段订阅的 channel（各自只看关心的部分，扩展性好）。看一个系统把「一次交互」建模成什么消息类型，就知道了它的扩展边界。

**快速信号**：grep `message`、`channel`、`publish`、`subscribe`、`topic`、`send`、`broadcast`、`bus`；看消息的类型定义里有没有 sender / recipient / role / type 字段。

**代表实现**：ag2/AutoGen——多 agent 共享对话线程，每条消息（含 tool call）对全体参与者可见；langchain-ai/langgraph——state 的每个 key 是一个 channel，带 LastValue / reducer 等写入策略；letta-ai/letta-code——agent 间 send message 与共享 memory block 两种通道并存。

```text
我想理解这个仓库里 agent 之间的通信机制（message passing / channel）：请定位消息的定义与投递代码——消息是什么数据结构（有没有 sender、recipient、role、type 字段）、通过什么通道投递（直接调用、队列、还是共享事件流），引用具体 file:line；用文字讲清一次跨 agent 通信的完整数据流——发送方怎么构造消息、消息经过哪些中间层（序列化、过滤、路由）、接收方怎么消费（拉取还是推送）、一条消息能否被多个 agent 同时看到；点出其中的关键数据结构与函数名（如消息类、channel 抽象、投递函数）；最后给我 2-3 个值得继续追问的点（比如消息有没有积压或去重处理、通信是同步阻塞还是异步）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E9. Handoff：控制权转移（Handoffs / Control Transfer）｜P1

**是什么**：当前 agent 判断「该别人接手了」，调用 handoff 工具把整个会话的控制权（连同任务与上下文）移交给目标 agent——是接力替换，不是父子派生。

**为什么重要**：handoff 和 subagent 派生（E2）是两种根本不同的拓扑：派生是「我叫人办事、结果归我」，handoff 是「我不干了、你来」。客服路由类系统几乎全用 handoff；混淆两者会导致状态归属错乱（谁对最终结果负责、历史算谁的）。读源码时确认转移后原 agent 是否还活着、上下文是全量交接还是摘要交接。

**快速信号**：grep `handoff`、`hand_off`、`transfer`、`escalate`、`route_to`、`swarm`；看「转移」之后原 agent 的循环是否退出。

**代表实现**：OpenAI Swarm（openai/swarm，教学框架）与其后继 openai-agents-python——agent 返回另一个 agent 即视为 handoff，框架层完成替换；langchain-ai/langgraph（langgraph-swarm 官方示例）——把 handoff 实现为共享 state 上的控制权转移；crewAIInc/crewAI——delegation 机制（allow_delegation）让一个 agent 把任务转给更合适的成员。

```text
我想理解这个仓库里的 handoff（控制权转移）机制：请定位 agent 把会话控制权移交给另一个 agent 的实现（常见名字 handoff、transfer、escalate、route_to），引用具体 file:line；用文字讲清一次 handoff 的完整流程——当前 agent 怎么表达「要转移」（专用工具、返回值约定、还是特殊消息类型）、框架收到后做了什么（原 agent 的循环是否终止、它的局部状态去哪了）、目标 agent 怎么被选中和初始化、它拿到的上下文是完整历史还是摘要、目标 agent 跑完后控制权回到谁手里；点出其中的关键数据结构与函数名（如 handoff 请求对象、转移执行函数）；最后给我 2-3 个值得继续追问的点（比如能不能把控制权再转回原 agent、handoff 链条有没有深度上限）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E10. 共享状态 vs 隔离状态（Shared State / Blackboard vs Isolated State）｜P1

**是什么**：多 agent 系统的「单一事实来源」要么放在全体参与者可读写的共享存储里（blackboard：一个共享 state 对象或 append-only 事件流），要么各 agent 持有私有 state、只靠消息同步差异。

**为什么重要**：共享状态省去消息搬运但引入写冲突——谁后写谁赢？并发写同一字段怎么合并？隔离状态无竞态但要自己处理一致性。这是读任何多 agent 仓库要最先回答的问题：全局状态存在哪、谁能写哪些字段、并发写怎么解决。

**快速信号**：grep `store`、`state`、`blackboard`、`shared`、`global`、`checkpoint`、`reducer`；找 state 的 schema 定义和每个字段的合并/写入函数。

**代表实现**：langchain-ai/langgraph——共享 state，每个字段带 reducer（如 add_messages 追加合并），由 checkpointer 持久化；OpenHands——append-only 的 event stream 作为共享事实来源，所有组件从中读取；letta-ai/letta-code——以 shared block 做跨 agent 共享记忆，其余 memory 保持私有。

```text
我想理解这个仓库里多 agent 的共享状态设计（shared state / blackboard）：请定位全局或跨 agent 共享的状态对象及其读写代码（常见名字 state、store、blackboard、shared memory），引用具体 file:line；用文字讲清状态的生命周期——它在哪被创建、哪些参与者能读哪些字段、并发写同一个字段时怎么解决（last-write-wins、reducer 合并、锁、还是队列化）、状态是否被持久化以便崩溃恢复、worker 对它的修改如何被其他参与者感知；点出其中的关键数据结构与函数名（如 state schema、字段合并函数、checkpoint 读写）；最后给我 2-3 个值得继续追问的点（比如字段有没有写入权限划分、状态体积膨胀怎么处理）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E11. 群聊与发言者选择（Group Chat & Next-Speaker Selection）｜P2

**是什么**：多个 agent 共处一个共享对话线程，每轮由一个 manager（规则、轮转或 LLM 判断）选出下一个发言者，历史对全体可见。

**为什么重要**：这是 AutoGen 的经典多 agent 形态，也是「多个角色讨论出结论」类系统的原型。成败系于发言者选择策略——round-robin 简单但僵化，LLM 选择灵活但会漏人、抢话、跑题。读源码重点看：候选列表怎么维护、选择函数的输入输出、有没有终止条件与最大轮数护栏。

**快速信号**：grep `group_chat`、`select_speaker`、`next_speaker`、`round_robin`、`manager`、`participants`、`team`。

**代表实现**：ag2/AutoGen——GroupChatManager 维护共享历史并实现 select_speaker（LLM 选择 + 规则兜底）；CAMEL——双 agent 任务导向的角色扮演对话（task specifier 与两个角色协作）；ChatDev——以「软件公司角色群聊」串起需求→开发→测试的流水线。

```text
我想理解这个仓库里的群聊模式（group chat）与发言者选择（next-speaker selection）：请定位「决定下一个由哪个 agent 发言」的实现（常见名字 select_speaker、next_speaker、manager），引用具体 file:line；用文字讲清一轮群聊的完整流程——参与者列表在哪维护、选择函数拿到什么输入（全部历史、摘要、还是只有最近几条消息）、选择逻辑是规则（round-robin、关键词匹配）还是 LLM 判断、被选中的 agent 怎么被调用并拿到共享历史、它回复后历史如何追加；点出其中的关键数据结构与函数名（如发言者选择函数、共享历史容器）；最后给我 2-3 个值得继续追问的点（比如选择失败或连续选同一个人怎么处理、群聊有没有终止条件和最大轮数）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E12. 结果汇总与冲突处理（Aggregation & Conflict Resolution）｜P1

**是什么**：多个子 agent 的产出要合并成单一结果——按键 reduce、串接成文档、投票、或再派一个 LLM 仲裁——并且要处理互相矛盾或失败的回答。

**为什么重要**：fan-out（E7）之后必须有 reduce，否则并行没有意义。合并策略直接决定系统可信度：多数投票能滤掉单点幻觉，但前提是产出可比较；last-write-wins 实现最简单，但会静默覆盖分歧。子 agent 失败的传播语义（一个挂了整批怎么算）也在这里决定，是「尽力而为」与「全有全无」的分界。

**快速信号**：grep `reduce`、`merge`、`aggregate`、`vote`、`consensus`、`arbitrat`、`conflict`、`combine`；在 fan-out 调用的下一行找合并函数。

**代表实现**：langchain-ai/langgraph——map-reduce 范式：并行分支的 state 由 channel reducer（如 add_messages）汇总；ag2/AutoGen——多 agent 辩论与投票达成共识的经典示例模式；crewAIInc/crewAI——task 的 output 按顺序串接，作为后续 task 的上下文输入。

```text
我想理解这个仓库里多 agent 结果的汇总与冲突处理（aggregation & conflict resolution）：请定位把多个子 agent 输出合并成最终结果的代码（常见名字 reduce、merge、aggregate、combine、vote），引用具体 file:line；用文字讲清完整流程——汇总发生在什么时机（全部完成后还是流式进行）、用什么策略合并（按键 reduce、顺序串接、投票、还是再调一次 LLM 仲裁）、两个子 agent 给出矛盾结论时按什么规则裁决（多数优先、权威来源优先、还是标记给人）、失败或超时的子 agent 结果怎么补位；点出其中的关键数据结构与函数名（如合并函数、结果容器、失败标记）；最后给我 2-3 个值得继续追问的点（比如合并本身会不会再调一次 LLM、最终结果里会不会保留分歧意见供人复核）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E13. 并行度控制与资源治理（Concurrency Limits & Backpressure）｜P1

**是什么**：限制同时运行的 agent 数量与请求速率——semaphore、worker pool、信号量化的队列——并配套超时、取消传播与退避重试。

**为什么重要**：无界并行会打爆 API 配额、放大 token 成本、触发限流雪崩（429 重试风暴）。并发控制是多 agent 系统从 demo 到生产可用的分水岭，也决定了 fan-out 的实际加速比：并发上限、等待队列与取消传播（能否中断正在跑的 LLM 调用）缺一不可。API 请求层的限流细节见 G2。

**快速信号**：grep `semaphore`、`concurrency`、`max_concurrent`、`max_parallel`、`rate_limit`、`throttle`、`p_limit`、`timeout`、`cancel`、`retry`、`backoff`。

**代表实现**：langchain-ai/langgraph——Pregel 风格的 superstep 同步：每步内并行、步间 barrier，天然约束并发批次；Claude Code——并行 subagent 数量有上限，超出的排队执行；ag2/AutoGen（0.4+）——asyncio 运行时，agent 级并发与速率可配置。

```text
我想理解这个仓库里的并行度控制与资源治理（concurrency limits / backpressure）：请定位限制同时运行的 agent 或请求并发的代码（常见名字 semaphore、concurrency、max_parallel、p_limit、rate_limit、throttle），引用具体 file:line；用文字讲清完整流程——并发上限在哪定义（常量、配置、还是动态调整）、超过上限的任务在哪等待（信号量、队列、worker pool）、超时后任务被怎么处理（取消、放弃、还是标记失败）、取消怎么传播到正在运行的子 agent（能否中断 LLM 调用或工具执行）、限流错误（如 429）有没有退避重试；点出其中的关键数据结构与函数名（如并发原语包装函数、任务队列、取消令牌）；最后给我 2-3 个值得继续追问的点（比如并发数能否运行时调整、排队任务的顺序保证）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```

#### E14. 子代理命名、注册与路由（Agent Registry & Description-Based Routing）｜P1

**是什么**：系统维护一个 agent 注册表——每个 agent 声明 name、description、tools、system prompt——派发方（主 agent 的 LLM 或 supervisor）根据 description 决定这次任务派给谁。

**为什么重要**：注册表是多 agent 系统的 DNS：路由质量完全取决于每个 agent 的 description 写得好不好——名字和描述本质上是写给路由 LLM 看的提示词。声明式注册（目录下的文件、YAML、装饰器）决定可扩展性（新增 agent 不改代码）；「谁读注册表、路由决策是 LLM 调用还是规则匹配」决定路由的成本与准确性。

**快速信号**：grep `registry`、`register`、`agents.yaml`、`agent_file`、`available_agents`、`description`、`route`；找声明 agent 的文件格式（markdown frontmatter、YAML、装饰器）。

**代表实现**：Claude Code——agent 目录下的 `.md` 文件声明 subagent（name + description + tools），主 agent 按 description 路由；OpenHands——file-based agents：Markdown 文件声明专职子 agent 的名字、描述与工具；crewAIInc/crewAI——crew 定义里每个 agent 的 role / goal / backstory 兼作路由与分工描述。

```text
我想理解这个仓库里子 agent 的注册与路由机制（agent registry & description-based routing）：请定位 agent 注册表的实现——agent 是怎么声明的（配置文件、装饰器、还是代码对象）、注册表在哪构建、路由时派发方怎么看到候选 agent 列表，引用具体 file:line；用文字讲清一次路由的完整流程——任务进来后由谁做「派给哪个 agent」的决策（LLM 读 description 判断，还是规则匹配）、决策的输入输出是什么（候选列表长什么样、结果是 agent 名字还是引用）、没匹配到时 fallback 到谁、注册表支持热加载还是启动时固定；点出其中的关键数据结构与函数名（如 agent 定义 schema、注册函数、路由函数）；最后给我 2-3 个值得继续追问的点（比如 description 的措辞对路由准确率的影响、同名或描述含义冲突时怎么处理）。若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造。
```
