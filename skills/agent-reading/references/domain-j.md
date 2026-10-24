> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### J. 可观测与评估（Observability & Evaluation）（L1714–L1887）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### J. 可观测与评估（Observability & Evaluation）

Agent 是「黑盒里的黑盒」——模型的中间决策不可直接读、一次任务几十轮循环、副作用散落在文件系统、网络与子进程里。这个领域回答两个工程问题：跑的时候能不能看见里面发生了什么（tracing、telemetry、结构化日志、transcript、token 与成本、debug 模式），以及怎么客观知道它到底变好没有（评测 harness、判定器、指标、回归对比）。前者决定你能不能修它，后者决定你的每次改动是不是玄学。

#### J1. 执行追踪与 span 树（Execution Tracing & Span Trees）｜P1

**是什么**：给一次 agent 任务的完整执行建立带因果关系的时间线记录——每个 LLM 调用、工具调用、子 agent 各占一个 span，用 trace_id 串成一棵树，可导出到外部查看器分析。

**为什么重要**：Agent 的失败几乎从不是单点错误，而是「第 7 步的工具输出坏了 → 第 9 步的模型基于坏输出做了错误决策」这种跨步骤因果链。日志只有扁平事件流，trace 有父子关系和时间跨度，才能回答「这次任务的时间花在哪、token 烧在哪一步、错误从哪一步开始传播」。没有 trace，调试多步 Agent 等于只看 stdout 猜。OpenTelemetry 正在沉淀 GenAI 语义约定（`gen_ai.*` 属性），这是行业收敛的方向。

**快速信号**：目录名 `tracing/`、`telemetry/`、`observability/`；文件名 `*trace*`、`*span*`。grep 关键词：`opentelemetry|otel`、`start_span|with_span|span!`、`trace_id|span_id`、`tracer|TracerProvider`、`langsmith|langfuse`、`OTLP`。依赖清单里出现 `opentelemetry-*`（Python）或 `tracing` crate（Rust）本身就是最强信号。

**代表实现**：ag2/AutoGen（autogen-core 内建 OpenTelemetry tracing，runtime、agent、模型调用统一进一棵 span 树，一个 helper 就能把 trace 导出到任意 OTLP collector）；langchain-ai/langgraph（图执行的每一步自动产生 trace，stream_mode 里还有专门的 debug 模式逐事件外吐内部状态，接 LangSmith 可看完整调用树）；OpenLLMetry（Traceloop 开源的 OTel instrumentation，不动业务代码就把 LLM SDK 调用包成符合 GenAI 语义约定的 span）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「执行追踪（tracing/span 树）」这一个知识点：请先定位实现入口（可 grep opentelemetry、otel、span、trace_id、start_span、langsmith、langfuse 这类关键词，也看看有没有 tracing/、telemetry/、observability/ 目录）并引用具体 file:line；用文字讲清一次 agent 任务的追踪数据流——span 在哪些代码位置被创建和结束（模型调用、工具调用、子 agent 各在哪一层包 span），trace_id 和父子 span context 是怎么在调用链里传递的，内存里的 span 最终流向哪里（进程内缓冲、本地文件还是 OTLP 导出）；点出承载这些逻辑的关键数据结构（Span/Trace 的字段定义）和函数名（创建、结束、导出各自的函数）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J2. Telemetry 埋点与指标上报（Telemetry Instrumentation）｜P2

**是什么**：在关键路径上采集事件或指标并周期性上报，分两类：面向运维的运行指标（请求数、延迟、token 消耗，常走 OpenTelemetry metrics）和面向维护者的匿名产品使用统计（用户开了哪些功能、跑了多少任务，常走 PostHog/Amplitude 这类分析服务）。

**为什么重要**：埋点位置是「维护者认为什么重要」的官方地图——他们选择在哪里埋点，就说明哪里最容易出问题或最值得度量。它同时是隐私敏感区：好的实现必有显式 opt-out、匿名化和采样控制，这些边界代码本身就是学习素材。读 Agent 仓库时区分这两类 telemetry，能避免把产品统计误读成运行时机制。

**快速信号**：grep 关键词：`telemetry`、`posthog|amplitude|segment`、`track|capture|emit`、`usage_stats|anonymous`、`OTEL_EXPORTER_OTLP`、`counter|histogram|MeterProvider`、`opt.?out|opt.?in`。配置文件或 settings schema 里的 telemetry 开关、`.env.example` 里的上报相关变量都是入口。

**代表实现**：LiteLLM（proxy 层按 API key/team 累计 spend 与请求数，callbacks 机制把每次调用事件转发给 OTel、Langfuse 等后端，是「代理层统一遥测」的代表形态）；Langfuse（开源可自托管，SDK 通过包装 LLM 调用采集 trace 与指标，证明可观测后端可以不绑商业 SaaS）；ag2/AutoGen（tracing 之外支持把 span 与事件经 OTLP 导出，遥测后端的选择权留给用户）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「telemetry 埋点与上报」这一个知识点：请先定位实现入口（可 grep telemetry、posthog、amplitude、track、capture、usage_stats、OTEL_EXPORTER 这类关键词，也看配置或 settings 中有没有遥测开关）并引用具体 file:line；用文字讲清一次埋点的完整数据流——事件或指标在哪些代码位置被采集，中间经过哪些函数做聚合、序列化或匿名化，最终发往哪个 endpoint，opt-in/opt-out 和采样是怎么控制的、默认值是开还是关；点出关键数据结构（事件或指标的 schema 定义）和上报函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J3. 结构化日志（Structured Logging）｜P1

**是什么**：日志事件以带字段的结构（JSON，或 Rust tracing 里挂在 span 上的事件）而非自由文本输出，进程启动时统一初始化 logger、按级别过滤，并把多进程来源（主进程、沙箱 runtime、子进程工具）的日志汇拢到一处。

**为什么重要**：多步 Agent 的日志量巨大且天然并发（流式响应、并行工具调用、子 agent），纯文本日志在这种场景下没法按 session/级别过滤。logger 初始化代码还回答了「为什么我打不开 debug 输出」这类第一分钟就会遇到的问题。子进程与容器里代码的日志怎么回到主进程，是 Agent 仓库独有的日志难点。

**快速信号**：grep 关键词：`tracing_subscriber|RUST_LOG`、`loguru|getLogger|logging.basicConfig`、`pino|winston|bunyan`、`LOG_LEVEL|log_level`、`set_verbose`、`EnvFilter|env_filter`。落点在 CLI/server 启动入口附近的 logger 初始化；业务代码里 `logger.info(` / `tracing::info!` 的调用密度说明日志策略。

**代表实现**：openai/codex（Rust 侧全套 tracing + tracing-subscriber：事件天然挂在 span 上下文上，RUST_LOG 控制级别，是结构化日志教科书式实现）；OpenHands（loguru 统一接管主进程与各组件日志，级别经环境变量配置，容器里 runtime 的日志有专门回收路径）；LiteLLM（可选 JSON structured logs，每次调用一行 JSON，方便直接接外部日志管道）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「结构化日志」这一个知识点：请先定位日志系统的初始化入口（可 grep tracing_subscriber、RUST_LOG、loguru、logging.basicConfig、pino、winston、LOG_LEVEL、set_verbose 这类关键词，重点看 CLI 或服务启动代码附近）并引用具体 file:line；用文字讲清日志的数据流——它是怎么被统一接管的：谁在什么时机初始化 logger，级别和输出目标怎么配置，核心模块里一条典型日志调用长什么样、携带哪些结构化字段，多进程或沙箱 runtime（比如容器里跑的代码）的日志是怎么汇拢回主进程的；点出关键数据结构（logger 初始化与配置的字段定义）和函数名（初始化函数、业务代码里最常用的日志宏或方法）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J4. 会话转录与事件流持久化（Session Transcripts & Event Log）｜P1

**是什么**：把一次会话/任务的每个事件——用户输入、LLM 响应、工具调用与结果、错误——按发生顺序序列化追加到磁盘（典型为 JSONL），形成唯一完整的底层事实记录。

**为什么重要**：transcript 是 Agent 可观测性的物理底座：tracing 面向分析、日志面向诊断，而 transcript 面向「完整重演」——成本统计、debug、resume、评测轨迹全部从它派生。事件 schema（type 枚举、字段、顺序保证）直接暴露了仓库对「agent 状态由什么构成」的理解，是读架构时性价比最高的一份定义。与 G8/G10 的分工：那边看「怎么靠它活过崩溃」，这里看记录本身的格式与写入路径；审计语义见 H12，数据模型见 D11。

**快速信号**：文件名 `*session*`、`*history*`、`*events*`、`*transcript*`、`*rollout*`；目录名 `sessions/`、`events/`、`history/`。grep 关键词：`session_id`、`\.jsonl`、`event_stream|EventSource`、`rollout`、`append`、`flush`。最快路径：直接打开仓库或用户目录里一份已生成的会话文件，逐行看 schema。

**代表实现**：openai/codex（每个会话一份 JSONL rollout 文件逐事件追加，`codex resume` 直接以它为数据源恢复）；OpenHands（一切交互皆 event，事件流按序持久化，UI 与 agent 状态都从事件推导，教科书级 event sourcing）；letta-ai/letta-code（agent 的全部消息、思考与工具调用作为一等公民入库，任何时刻可按时间轴完整回看 agent 的「意识流」）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「会话转录与事件持久化」这一个知识点：请先定位实现入口（可 grep session、events、transcript、rollout、history、.jsonl、persist 这类关键词，也找找本机或仓库里现成的会话文件长什么样）并引用具体 file:line；用文字讲清事件写入的完整数据流——一个事件（用户消息、模型响应、工具调用）在内存里是什么对象，经过哪个函数序列化成什么格式（JSONL 每行有哪些字段、事件 type 的枚举值有哪些），写到哪个目录、什么时候 flush 落盘、并发事件怎么保证顺序；点出关键数据结构（事件对象的类型定义）和函数名（序列化与写入的函数）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J5. Token 用量与成本核算（Usage & Cost Accounting）｜P1

**是什么**：从每次 LLM API 响应回报的 `usage` 字段（prompt/completion/total tokens，以及 cache read/creation tokens）出发做会计：逐响应解析、按任务与会话累计、乘价目表换算成金额，并把窗口占用比例暴露给上下文管理。

**为什么重要**：Agent 的单位经济学决定它是玩具还是工具——一次任务几十轮调用、每轮带全量上下文，成本和单次 chat 差几个数量级；cache 命中折扣又常占总账单的一半。注意这是「响应后记账」：数据来自 API 报回的 usage 字段，与 B2 讲的「发送前用 tokenizer 预估」是两条不同数据流，好仓库里两者并存、来源不同、用途不同。

**快速信号**：grep 关键词：`prompt_tokens|completion_tokens|total_tokens`、`usage`、`cache_read|cache_creation|cached_tokens`、`cost_usd|cost`、`completion_cost`、`price|pricing|model_cost`。文件名 `*token*`、`*usage*`、`*cost*`；CLI 状态栏或报告里显示花费的字符串附近是消费端入口。

**代表实现**：Aider-AI/aider（每次响应后打印 sent/received tokens 与会话累计花费，缓存命中的折扣单列，账目透明度标杆）；cline/cline（每个 task 在 UI 里实时显示本任务累计 token 与开销）；LiteLLM（内置全量模型价目表，`completion_cost` 一算即得，是大量项目成本核算的公共底座）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「token 用量与成本核算」这一个知识点：请先定位实现入口（可 grep usage、prompt_tokens、completion_tokens、cached_tokens、cost、pricing 这类关键词）并引用具体 file:line；用文字讲清会计数据流——LLM 响应里的 usage 字段在哪一层被解析出来，怎么按 turn 累计到任务或会话级别，成本按什么价目表计算、缓存命中的 token 按什么折扣算，这些数字最终在哪里展示给用户（CLI 状态栏、报告还是日志），上下文窗口占用是不是也从同一份数据推导并反过来触发压缩；点出关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J6. Debug 模式与诊断输出（Debug Mode & Diagnostic Output）｜P1

**是什么**：由显式开关（`--verbose`、`--debug`、`RUST_LOG=debug`、`LOG_LEVEL=DEBUG`）打开的增强输出：完整 prompt 与原始 API 响应的 dump、工具调用的 stdin/stderr、事件流逐条打印，以及配套的「出问题时该收集什么」的报障指引。

**为什么重要**：Agent 日常排障三连是「它到底发了什么 prompt」「模型原样回了什么」「工具实际输出了什么」——默认输出全都不含这三样。debug 模式的实现选择（复用日志级别开关，还是走专门的 dump 代码路径）与 dump 的内容取舍，是维护者排障经验的结晶；CLI 参数表里的诊断 flag 列表，就是快速读懂「这个项目怎么被调试」的地图。

**快速信号**：grep 关键词：`--verbose|--debug|-v`、`RUST_LOG|LOG_LEVEL|DEBUG`、`dump|dump_request|log_prompt|show_prompt`、`dry.?run`。落点：CLI 参数定义（clap/click/commander 的 flag 列表）、logger 初始化、README 或 TROUBLESHOOTING 文档的排障章节。

**代表实现**：Aider-AI/aider（`--verbose` 可逐级加码，最详细时完整打印每次 LLM 请求与响应，配套 `--no-stream` 等诊断逃生舱）；openai/codex（RUST_LOG 控制的分级调试日志落本地日志文件，报障流程要求附上它）；cline/cline（VSCode 的 output channel 常驻记录每次 API 请求响应，报 issue 时可直接导出）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「debug 模式与诊断输出」这一个知识点：请先定位实现入口（可 grep --verbose、--debug、RUST_LOG、LOG_LEVEL、dump、log_prompt 这类关键词，重点看 CLI 参数定义和 logger 初始化处）并引用具体 file:line；用文字讲清诊断输出的实现流程——打开 verbose 或 debug 后额外输出了什么（完整 prompt、原始 API 响应、工具调用的 stdin/stderr），实现上是复用日志级别开关还是有专门的 dump 代码路径，这些输出写到哪（终端、本地日志文件还是专门的 dump 目录），出问题时用户被引导收集哪些信息（报障文档或 issue 模板要求贴什么）；点出关键数据结构（诊断开关或 flag 的定义）和函数名（dump 相关函数）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J7. Replay 与时间旅行（Replay & Time Travel）｜P1

**是什么**：从持久化的会话记录（D2）重建执行：或恢复上下文继续对话（resume），或回到任意历史步骤检查当时的状态、改一改再分叉重跑（time travel / fork）；重建方式通常是重放事件推导状态，而不是反序列化一张快照。

**为什么重要**：replay 把「不可复现的黑盒」变成「可重演的白盒」：一个 bug 报告附上会话文件就能稳定重现；评测轨迹可离线重分析；time travel 让你站在出错的第 5 步问「如果当时工具输出是对的会怎样」。实现上最大的坑是外部副作用——重放对话事件绝不能重新执行工具，这条边界怎么画是每个仓库的必答题。容错章的崩溃恢复（G10）看的是同一机制的生存视角。

**快速信号**：grep 关键词：`resume|replay|fork`、`load_session|from_events|load_history`、`state_history|get_state`、`checkpoint`、`time.?travel`、`rehydrate`。CLI 的 resume 子命令和会话加载函数是两个天然入口。

**代表实现**：langchain-ai/langgraph（checkpointer 保存每步图状态，`get_state_history` 可回溯到任意节点检查、重放或分叉，time travel 的标准实现）；OpenHands（agent 状态本身就是事件重放的产物，恢复会话即重放事件流，天然支持从任意事件点续跑）；openai/codex（`codex resume` 从 rollout 文件重建上下文继续会话，并支持从历史点分叉）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「replay 与会话恢复」这一个知识点：请先定位实现入口（可 grep resume、replay、fork、load_session、from_events、checkpoint、state_history 这类关键词，也看 CLI 有没有 resume 子命令）并引用具体 file:line；用文字讲清恢复的完整流程——从磁盘的会话记录读入后是直接重建对话上下文继续，还是通过重放事件逐步推导状态；重放时工具调用这类外部副作用怎么处理（历史工具结果直接复用而不重新执行，这条边界在代码的哪里强制）；恢复完成的状态对象里哪些部分是重放出来的、哪些需要重新初始化；点出关键数据结构（恢复后的状态对象、会话记录的 schema）和函数名（加载、校验、重建状态的函数）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J8. 确定性与可复现（Determinism & Reproducibility）｜P1

**是什么**：让「同输入 → 同轨迹」尽量成立的一组手段：采样参数钉死（temperature=0、seed）、模型与 provider 版本 pin、prompt 模板固定、评测环境（数据集版本、容器镜像、依赖）锁定，以及对剩余不确定性的统计处理（多次运行取分布）。

**为什么重要**：不可复现就没法归因：改了 prompt 分数涨 3 分，是改进还是采样噪声？Agent 的随机性来源比单次调用多得多——模型采样、工具输出、文件系统状态、时间——好仓库会显式区分「能钉死的」和「钉不死只能统计的」，这个区分直接决定它评测结论的可信度。

**快速信号**：grep 关键词：`temperature|top_p|seed`、`deterministic`、`pin|lock`、`snapshot`、`freeze|fake.*clock|freezegun`。落点：LLM 配置结构体的默认值、评测/benchmark 目录里数据集与镜像的版本声明、测试里对时间与随机数的处理方式。

**代表实现**：SWE-agent（config YAML 把 model、temperature、agent 每步行为整体 pin 住，一次实验可原样重跑）；langchain-ai/langgraph（显式图结构加 checkpoint，模型输出固定时可逐步复现整条执行路径）；OpenHands（评测侧固定数据集版本与 runtime 容器镜像，保证跑分环境一致）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「确定性与可复现性」这一个知识点：请先定位相关代码（可 grep temperature、top_p、seed、deterministic、pin、snapshot 这类关键词，也看 LLM 配置结构体的默认值，以及评测或 benchmark 目录里数据集和镜像的版本锁定方式）并引用具体 file:line；用文字讲清仓库对随机性的处理流程——采样参数在哪配置、默认值是多少，模型和数据集版本怎么 pin，测试里时间与随机数这类不确定性来源怎么处理（freeze time 还是注入 clock），仓库有没有显式承认「钉不死」的部分（比如用多次运行取统计而不是单次结果下结论）；点出关键数据结构（采样与版本 pin 相关的配置字段）和函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J9. LLM Mock 与离线测试（LLM Mocking & Offline Tests）｜P1

**是什么**：单元测试里不触真实 API 的替代实现：假模型类实现同一接口返回预设响应、客户端层拦截、或把真实交互录成 fixture 回放，让 agent 主循环、消息组装、工具编排都能离线验证。

**为什么重要**：Agent 的核心逻辑（循环、上下文组装、编排）本不需要网络就能测，但全部耦合在 LLM 调用后面；mock 注入点选在哪一层（模型接口、HTTP 层、还是整个 runtime）直接决定测试能覆盖主循环的哪一段。CI 里能离线跑的测试才是每次提交都会跑的测试——这决定了仓库的回归安全网实际有多大。

**快速信号**：grep 关键词（重点在测试目录）：`mock|fake|stub`、`mock_response`、`FakeChatModel|FakeListChatModel`、`cassette|VCR|recording`、`dummy|echo`。测试里构造 agent 的 fixture/helper 函数是理解注入方式的最佳入口。

**代表实现**：LiteLLM（`mock_response` 参数让 completion 不出网直接返回固定值，很多项目拿它顶住 LLM 客户端做测试）；langchain-ai/langgraph（langchain-core 的 fake_chat_models 家族实现完整模型接口，fake 模型能驱动真实的图逻辑跑完）；ag2/AutoGen（AgentChat 测试指南用 `EchoAgent` 模拟无 LLM 的对话 agent，autogen-ext 的 ReplayChatCompletionClient 回放录制好的模型响应）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「LLM mock 与离线测试」这一个知识点：请先定位实现入口（在测试目录里 grep mock、fake、stub、mock_response、FakeChatModel、cassette、replay 这类关键词）并引用具体 file:line；用文字讲清 mock 的注入流程——是替换模型客户端、拦截 HTTP 层、还是用实现同一接口的假模型类，agent 主循环在测试里能跑到什么程度（完整跑通还是只测单个函数），工具执行的副作用（文件写入、子进程）在测试里怎么隔离，测试怎么断言「发给了模型什么」而不只是「模型回了什么」；点出关键数据结构（fake 模型的类定义和它实现的接口约定）和函数名（测试里装配 fake 的 helper）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J10. 评测 Harness（Evaluation Harness / Benchmark Runner）｜P1

**是什么**：跑基准的流水线：加载数据集实例 → 为每个任务创建隔离环境（容器/沙箱）→ 驱动 agent 完整跑完任务 → 收集产出（patch、答案、轨迹）→ 交给判定器。它与运行时代码是分离的两套架构，是多数 Agent 仓库里代码量最大却最被读者忽略的目录。

**为什么重要**：evals 是这些仓库「产品」的一部分：SWE-agent 之于 SWE-bench、Aider 之于自家 polyglot benchmark，分数就是项目的存在理由。读 harness 能看到运行时接口真正的边界——agent 被当成什么接口驱动、任务怎么注入环境、产出怎么取出——这比读主循环更能看清架构的接缝。

**快速信号**：目录名 `evals/`、`evaluation/`、`benchmark/`、`bench/`。grep 关键词：`harness`、`instance|dataset|split`、`docker|sandbox|container`、`run_evaluation|evaluate`、`swebench`。README 里的跑分数字或 leaderboard 链接会直接指回 harness 入口。

**代表实现**：OpenHands（evaluation/ 下每个 benchmark 一整套 harness：拉数据、起隔离容器、跑 agent、收 patch）；SWE-agent（SWE-bench 的官方主要 baseline，harness 覆盖 repo checkout、agent 部署、轨迹与 patch 产出的全流程）；Aider-AI/aider（自带 225 道 Exercism 习题的 polyglot benchmark 流水线，完成率即产品力声明）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「评测 harness（benchmark runner）」这一个知识点：请先定位入口（看看仓库里有没有 evals/、evaluation/、benchmark/、bench/ 这类目录，可 grep harness、dataset、instance、docker、sandbox、run_evaluation 这类关键词）并引用具体 file:line；用文字讲清一次评测的完整流程——数据集实例怎么加载和切分，每个任务的隔离环境（容器或沙箱）怎么创建和清理，agent 以什么接口被驱动跑完任务，产出（patch、答案、轨迹文件）收集到哪里，单个任务失败或超时怎么处理、会不会中断整个 run；点出 harness 的核心抽象（任务实例的数据结构、runner 主循环的函数名）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J11. 判定器与指标（Graders & Metrics）｜P1

**是什么**：把 agent 产出变成数字的环节：确定性判定（在环境里跑测试、字符串比对）、概率判定（LLM-as-judge 按 rubric 打分）、以及把逐任务的判定聚合成 pass@k、resolved rate、完成率这类指标的统计层。

**为什么重要**：判定器决定「分数」到底度量了什么：SWE-bench 的 resolved（fail-to-pass 全过且 pass-to-pass 不回归）和 LLM-as-judge 的「看起来对」是两种完全不同的可信度。这是读源码时最容易藏偏差的地方——超时怎么归类、部分通过算不算、judge 的 prompt 怎么写，每一项都能直接改变跑分，也常是刷分争议的源头。

**快速信号**：grep 关键词：`pass@|pass_at`、`resolved|resolve_rate`、`fail_to_pass|pass_to_pass`、`grader|judge|metric`、`exact_match|accuracy`、`timeout`。目录名 `metrics/`、`graders/`；评测目录里名字带 report/summarize/metrics 的文件。

**代表实现**：SWE-bench（resolved 判定在重建环境里跑 fail-to-pass 与 pass-to-pass 两组测试，「执行式判定」的标杆）；openai/evals（经典参考实现：dataset + completion function + grader 接口的最小 eval 框架，定义了后来者共用的词汇表）；Aider-AI/aider（以每道习题自带的单元测试通过为完成标准，用确定性判定避开 judge 的主观性）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「评测判定（grading）与指标计算」这一个知识点：请先定位实现入口（可 grep grader、judge、metric、pass@、resolved、fail_to_pass、pass_to_pass、exact_match 这类关键词）并引用具体 file:line；用文字讲清一个任务从产出结果到变成指标数字的完整流程——判定是确定性的（跑测试、字符串比对）还是 LLM-as-judge（judge 的 prompt 在哪定义、按什么 rubric 打分），逐任务的判定结果在哪里聚合成 pass@k 或 resolved rate 这类总量指标，超时、报错、部分通过这些边界情况各归到哪一类；点出关键数据结构（逐任务判定结果的表示）和函数名（判定函数、指标聚合函数的名字与职责）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### J12. 评测产物与结果聚合（Run Artifacts & Metrics Aggregation）｜P2

**是什么**：一次运行或评测落盘的全部产物——轨迹 JSON、日志、逐实例结果、汇总报告——及其目录约定，加上把这些产物聚合成指标报告、并在两次 run 之间做对比（回归检测）的脚本层。

**为什么重要**：跑分只是一瞬间，产物才是可持续资产：失败实例的轨迹是改进 agent 的直接素材，历史 run 的聚合是判断「改动是否真的变好」的唯一依据——没有 run 间对比能力的仓库，每次「优化」都无法证伪。产物目录结构还决定 leaderboard、可视化这类外部工具能不能接上。

**快速信号**：目录名 `runs/`、`results/`、`output/`、`trajectories/`、`reports/`。grep 关键词：`metrics|report|summarize|aggregate`、`leaderboard`、`instance_id`、`trajectory`、`output\.json`。评测目录下名字带 report/summarize/aggregate 的脚本是入口。

**代表实现**：SWE-agent（每次 run 在 trajectories/ 下落完整轨迹 JSON 与日志，逐实例可回放检查）；OpenHands（评测 harness 为每个实例保存输出与日志，配套指标汇总脚本聚合成报告文件）；Aider-AI/aider（benchmark 结果生成 markdown 报告，其公开 leaderboard 就直接建立在这套产物之上）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「评测产物与结果聚合」这一个知识点：请先定位实现入口（可 grep report、metrics、summarize、aggregate、leaderboard、trajectory 这类关键词，也找找 runs/、results/、output/、trajectories/ 这类产物目录和评测目录里的汇总脚本）并引用具体 file:line；用文字讲清一次 run 的产物落盘与聚合流程——落盘了哪些产物（轨迹、日志、逐实例结果 JSON 的目录结构和命名约定各是什么），聚合脚本怎么把多个实例的结果汇总成指标报告，两次 run 之间有没有对比或回归检测能力，报告是给人读的 markdown 还是给机器读的 JSON；点出关键数据结构与函数名（聚合函数、产物文件的数据结构）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```
