> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### A. 核心循环与执行模型（Core Loop & Execution Model）（L238–L359）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### A. 核心循环与执行模型（Core Loop & Execution Model）

Agent 系统的心脏：从用户输入进入、模型调用、工具调用与结果回填、再到停止判定的完整控制流，以及围绕它的 REPL、headless、子任务等执行形态——读懂这段循环，任何 Agent 仓库的主干就通了。工具调用协议与分发细节见 C2/C4，轮数与预算上限见 G12，子任务派发见 E2。

#### A1. Agentic Loop 本体（The Agentic Loop）｜P0

**是什么**：一个 `while` 型主循环：组装 messages → 调用模型 → 解析出工具调用 → 执行工具 → 把结果作为新消息回填 → 再次调用模型，直到模型不再需要工具。

**为什么重要**：这是所有 Agent 仓库最核心的一段代码；工具系统、上下文管理、流式 UI、审批门全都挂在这个骨架上。找到它，其余模块在数据流里的位置就自然浮现。

**快速信号**：目录/文件：`agent/`、`core/`、`agent.py`、`loop.py`、`runner.py`、`task.py`、`session.py`；grep：`agent_loop`、`run_loop`、`main_loop`、`def step`、`run_turn`、`next_action`、`should_continue`、`while True`、`while not done`。

**代表实现**：openai/codex（Rust 的 turn 级循环：一次用户请求触发一个 turn，turn 内部迭代到模型不再请求工具）；OpenHands（以 `step()` 为粒度、由事件流驱动的 agent loop）；SWE-agent（经典 `run() → step()` while 循环，教科书式实现）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚它的 agentic loop 本体。请定位这个主循环的实现入口——即从用户输入出发、组装 messages、调用模型、解析工具调用、执行工具、把结果回填进对话历史、再判断是否进入下一轮的那段代码，引用 file:line 指出循环体和迭代判断的位置；然后用文字按时间顺序讲清一次完整迭代的数据流：输入如何变成请求、每一轮往 messages 里追加了什么、循环的持续条件是什么；点出承载循环状态的关键数据结构（messages/turn/session 对象等）和核心函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的切入点。
```

#### A2. 循环停止条件（Termination Conditions）｜P0

**是什么**：判定"任务完成、可以退出循环"的所有分支：模型不再发起工具调用、模型调用专门的 finish/submit 工具自报完成、终止消息匹配回调、用户中断、轮数或预算耗尽。

**为什么重要**：停止条件设计错了，Agent 要么提前交卷（干不完活），要么永不停止（烧钱死循环）；多 agent 系统里它还决定发言权何时移交、会话何时收束。看懂一个 Agent 的"完成"语义，是理解其任务模型最短的路径。

**快速信号**：grep：`stop_reason`、`finish_reason`、`end_turn`、`terminate`、`is_termination`、`should_stop`、`AgentFinish`、`finish`、`done =`、`break`；注意区分两个层次——单轮结束（turn end）与任务结束（task finish）。

**代表实现**：ag2/AutoGen（`is_termination_msg` 回调判定会话终止）；langchain-ai/langgraph（显式 `END` 节点 + 条件边路由）；SWE-agent（模型调用 `finish` 命令自报完成，同时受步数上限约束）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚它的循环停止条件：agentic loop 靠什么判定任务完成、在哪里退出。请找出所有终止分支的实现——模型不再发起工具调用即视为完成、模型调用专门的 finish/submit/done 工具自报完成、终止消息匹配或终止回调、用户中断、轮数或预算耗尽——引用 file:line 说明每个分支在哪里被评估；然后用文字讲清这些判定在循环数据流的哪个位置触发退出（break/return/抛出异常），退出后最终回复如何确定；点出关键的判定函数名与标志位数据结构；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### A3. 流式输出与增量解析（Streaming & Incremental Parsing）｜P1

**是什么**：模型响应按 chunk 流式到达，Agent 在收完整个响应前就要开始工作：累积 delta 文本、增量渲染 UI，甚至在流式中途就开始解析半截的工具调用参数。

**为什么重要**：交互式 Agent 的体感全靠流式；更关键的是工程难度——工具调用参数是流式中途的半截 JSON，解析器必须容错。自定义文本协议（Aider/Cline 风格）的流式解析是这类仓库里最精巧的代码之一。终端渲染管线（增量 Markdown、ANSI、输入输出共存）见 I1，机器可读事件流输出见 I9。

**快速信号**：grep：`stream`（`stream=True` / `stream: true`）、`delta`、`on_chunk`、`on_text`、`async for`、`text/event-stream`、`data:`、`partial`、`accumulat`；事件类型常定义在 `events.py` / `protocol` / `types` 文件里。

**代表实现**：openai/codex（核心循环产出结构化事件流，TUI 订阅事件增量渲染）；Aider-AI/aider（流式显示正在生成的 SEARCH/REPLACE 块）；cline/cline（边流边解析 XML 工具标签，标签闭合即触发执行）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚它的流式输出链路。请定位：模型请求在哪里开启 stream、增量 chunk 在哪个循环里被消费、delta 事件如何定义与分发给 UI 或调用方、流式过程中工具调用的参数如何在半截状态下被增量解析，引用 file:line；然后用文字讲清一个 chunk 从 API 返回到最终呈现给用户的完整数据流，包括缓冲与累积逻辑在哪里；点出事件类型的数据结构与关键回调或函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### A4. 会话状态与单/多轮对话（Session State & Single/Multi-Turn）｜P1

**是什么**：messages/历史数组是循环的核心可变状态：单轮任务是"一次性跑完循环即退出"，多轮会话在每次用户输入后基于累积历史重新进入循环；会话还涉及持久化（落盘/事件日志）与恢复（resume）。

**为什么重要**：模型 API 本身无状态，Agent 的全部"记忆"就是这个数组——它是理解上下文成本、历史膨胀、compaction/摘要介入时机的钥匙；会话持久化则决定 crash 之后能否续跑。消息历史的数据结构与写入点详见 D1；持久化与 resume 机制详见 D2 与 G8。

**快速信号**：grep：`messages.append`、`history`、`session`、`transcript`、`conversation`、`rollout`、`resume`、`load_session`、`save`；文件：`session.py`、`history.py`、`storage/`；相邻概念（另有专节）：`compact`、`summariz`（B7）。

**代表实现**：letta-ai/letta-code（MemGPT 血统：把会话历史当作受管理的内存层级，自主换页与摘要）；openai/codex（会话以 rollout 事件日志持久化，支持 resume 续跑）；Aider-AI/aider（chat 历史落盘，可切换到摘要历史压缩上下文）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚单轮与多轮对话在执行模型上的差别——会话历史作为循环状态是怎么维护的。请定位：每轮的 messages/历史数组在哪里被累积和追加、新的用户输入如何插入既有历史、多轮之间保留了哪些状态（系统提示、工具定义、摘要、外部状态）、会话如何持久化以及如何 resume 恢复，引用 file:line；然后用文字讲清从第一条用户消息到第 N 轮请求发出时 messages 的演化数据流；点出表示会话与历史的关键数据结构和追加/恢复逻辑的函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### A5. CLI REPL 事件循环（Terminal REPL Event Loop）｜P1

**是什么**：交互式 Agent 的外壳：一个前端事件循环同时应对键盘输入、模型流式输出、工具执行状态，把"用户提交"转成一次 agent 任务的启动，再把 agent 事件回流渲染到终端。

**为什么重要**：REPL 是循环与人的接口，也是并发结构最复杂的一层（终端 UI 框架 + async runtime + 消息通道三件套）；流式渲染、中断、审批提示都发生在这层与 agent 循环的交界处。渲染侧细节（增量 Markdown 解析、ANSI）见 I1。

**快速信号**：grep：`ratatui`、`crossterm`、`ink`、`prompt_toolkit`、`readline`、`stdin`、`mpsc`、`channel`、`tokio::select`、`event loop`；目录：`tui/`、`cli/`、`frontend/`、`ui/`。

**代表实现**：openai/codex（tokio + ratatui：键盘事件与 agent 事件经 channel 汇合驱动 TUI）；Aider-AI/aider（prompt_toolkit 的 REPL 包住同步的 coder 循环，spinner 线程保持活性）；cline/cline（VSCode 扩展宿主里的 async task loop，经 webview 消息与 UI 通信）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚它的 CLI/REPL/前端事件循环如何与 agentic loop 交织——用户敲键盘、模型流式输出、工具在执行，这三件事是如何并存的。请定位：前端事件循环或终端 UI 的实现、用户输入如何触发一次 agent 任务、agent 侧的流式事件如何回流到界面渲染（channel/事件订阅/回调）、两层之间用了什么并发结构（线程、async runtime、消息通道），引用 file:line；然后用文字讲清从「用户按下回车」到「界面开始渲染模型输出」的完整调用流程；点出事件/消息的数据结构与关键函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### A6. Headless / Exec 单次执行模式（Headless One-Shot Execution）｜P1

**是什么**：非交互入口：一条命令携带任务描述，跑完一轮 agentic loop 即退出，结果以最后一条消息 / JSON / 退出码交给调用方；审批由预设策略替代、无人值守时权限收敛到更严的档位——把 Agent 嵌进脚本、CI 与评估框架的形态。

**为什么重要**：headless 与 REPL 共享同一个循环内核但控制流不同（单任务、确定性停止、机器可读输出）；对比两条入口的代码路径，能最快分清哪些逻辑属于"会话层"、哪些属于"循环层"；无人值守时权限收敛到什么程度，是衡量工程成熟度的重要指标。

**快速信号**：grep：`exec`、`--print`、`--message`、`--yes`、`non-interactive`、`headless`、`output-last-message`、`output_format`、`exit code`、`process.exit`、`stdin`、`batch`；CLI 参数定义通常在 `cli`/`main` 入口或 argparse/clap 解析处；目录 `batch/`、`harness/`、`runner/`。

**代表实现**：openai/codex（`codex exec` 子命令单次执行后退出，带 JSON 输出与明确退出码约定）；Aider-AI/aider（`--message` 一次性运行，配 always-yes 参数实现脚本化）；SWE-agent（批量 harness 按 instance 列表跑评测并落 trajectory）；OpenHands（headless/编程式入口，供脚本与评估框架调用）。

这一知识点信息量大，拆成两问粘贴（第一问拿到回答后，再粘第二问）：

```text
我在读这个开源 Agent 仓库的源码，想搞清楚它的 headless/exec 单次执行模式——不进入交互界面、一条命令跑完一个任务就退出的那条路径。请定位非交互模式的入口（exec/print/message 一类的 CLI 参数解析处）、它与交互式模式共享了哪些代码（同一个循环内核还是两套实现）、单次任务的结果以什么形态交给调用方（最后一条消息、JSON 输出、退出码约定），引用 file:line；然后用文字讲清从命令行参数进入、经过一次完整的 agentic loop、到结果写出与进程退出的完整数据流；点出关键函数名与输出数据结构；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

```text
接着上面这个 headless/exec 模式继续深入：无人值守时审批是如何被预设策略替代的？请定位非交互路径上审批门被跳过或代答的代码（预设 approval 策略、--yes 类参数、权限模式如何被强制成某一档）、权限收敛到什么程度（沙箱是否更严、哪些工具被禁用）、预设策略无法裁决某个动作时代码走哪条分支（失败退出还是降级执行），引用 file:line；用文字讲清一次「需要审批的动作出现在 headless 运行中」的完整处置流程；点出权限档位枚举与判定函数名；若本仓库没有 headless 模式，请直说并指出最接近的替代实现；结尾给出 2-3 个值得继续追问的点。
```

#### A7. 中断、审批挂起与恢复（Interrupt, Approval Gates & Resume）｜P1

**是什么**：循环运行中让出控制权的机制：用户中断（Ctrl-C/Esc 经取消信号传递到循环，HTTP 流关闭、工具子进程 kill、回合状态收尾一致）；工具执行前的审批门把循环挂起等用户裁决、用户反馈作为新输入继续循环；以及 checkpoint/resume 把中断的会话从持久化状态续起来。

**为什么重要**：中断是使用频率最高却最易写坏的路径，它考验整个系统的并发与生命周期设计；审批门决定哪些动作需要人点头（也是 prompt injection 防线的实际执行位置，策略细节见 H5–H7）；中断与恢复决定长任务的可控性。机制上它们都是"循环在某一拍 yield 给外部事件，再带着结果继续"。

**快速信号**：grep：`SIGINT`、`ctrl`、`esc`、`interrupt`、`abort`、`cancel`、`AbortController`、`CancellationToken`、`AtomicBool`、`pause`、`approve`、`confirm`、`checkpoint`、`resume`、`pending`、`select!`、`kill`、`shutdown`；审批逻辑常出现在工具执行入口的 guard 处。

**代表实现**：openai/codex（Esc 打断当前 turn，取消信号沿事件通道进入循环，中断后对话可继续）；langchain-ai/langgraph（`interrupt()` 挂起执行 + checkpointer 恢复，图执行的任务取消与节点中断语义）；cline/cline（工具审批被拒后，用户反馈作为新输入继续循环）；google-gemini/gemini-cli（Esc 中断生成与 Ctrl+C 退出的双层信号处理）。

```text
我在读这个开源 Agent 仓库的源码，想搞清楚循环的中断、审批与恢复机制。请定位：用户中断信号（Ctrl-C/Esc 等）从界面到循环的传递路径、取消是如何协作式生效的（循环在哪一拍检查 cancel token，流式响应如何关闭、运行中的工具子进程如何被 kill、回合状态如何收尾一致）、工具执行前的审批门在哪里把循环挂起、用户的选择如何作为输入恢复循环、有没有 checkpoint/resume 机制把中断的会话持久化后续跑，引用 file:line；然后用文字讲清从「用户按下中断」或「审批提示弹出」到「循环终止或继续下一轮」的完整控制流；点出取消/挂起状态的数据结构与关键函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### A8. 执行模型形态：隐式循环 vs 显式图（Implicit Loop vs Explicit Graph）｜P0

**是什么**：两类执行骨架：多数 Agent 是一个隐式 while-loop（循环体即全部控制流）；langchain-ai/langgraph、ag2/AutoGen 一类框架把执行建模为显式的图/状态机——节点、边、条件路由、superstep 迭代、checkpoint 写入。事件流（OpenHands 式）是第三条路：循环由事件驱动。

**为什么重要**：读懂一个仓库前先判断它属于哪一类，决定了你该去 grep 什么：循环类看 `while`/`step`，图类看 `add_node`/`compile`/`superstep`。图式模型的 superstep 概念还解释了并行节点为何天然同步——同一拍内并发、拍间汇合。图工作流的编排细节见 E6。

**快速信号**：grep：`StateGraph`、`add_node`、`add_edge`、`conditional`、`compile(`、`superstep`、`Pregel`、`checkpoint`、`transition`、`fsm`；如果没有这些而只有 `while True` + `step()`，就是循环类。文件：`graph.py`、`workflow/`、`runtime/`。

**代表实现**：langchain-ai/langgraph（Pregel 式 superstep 循环驱动节点图，checkpoint 内建）；ag2/AutoGen（actor 运行时 + 声明式 Workflows 图）；对照面：codex/Cline/Aider 均为隐式循环，全部控制流内联在主循环里。

```text
我在读这个开源 Agent 仓库的源码，想先判断它的执行模型是隐式 while-loop 还是显式图/状态机。请给出判断与证据：如果存在节点/边/编译/执行引擎一类概念（如 add_node、conditional edge、compile、superstep、checkpoint），请定位图的定义方式、编译产物、以及驱动节点执行的循环，讲清一次调用如何在节点间流转、条件路由在哪里评估、状态与检查点在哪里读写，引用 file:line；如果它只是单个 agent 的 while-loop（step 一直跑到停止条件），也请指出代码证据，并说明每轮 turn 内部是否存在局部的状态机成分（如状态枚举的转换）；两种情况都点出关键数据结构与执行函数名；结尾给出 2-3 个值得继续追问的点。
```
