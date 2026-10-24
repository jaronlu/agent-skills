> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### I. 交互与工程化（Interaction & Engineering）（L1584–L1713）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### I. 交互与工程化（Interaction & Engineering）

模型循环之外、把 Agent 变成可交付工程产品的那一层——终端/编辑器/GUI 交互面、diff 审批、配置与扩展体系、多模态输入，以及脱离交互终端的自动化出口。（权限与审批门的策略本体见 H5–H7；headless 执行模式的循环视角见 A6；中断的信号传播见 A7。）

#### I1. CLI 交互循环与流式渲染（Streaming REPL Rendering）｜P1

**是什么**：Agent 在终端里的主循环——一边从 LLM 流式接收 token 并增量渲染成 Markdown/代码块，一边维持输入框、快捷键与 spinner。

**为什么重要**：这是用户感知「快不快、稳不稳」的主战场；流式渲染牵扯部分 Markdown 解析、终端 ANSI 转义、网络线程与 UI 线程的分离，读懂它等于读懂整个前端骨架。与 A3 的分工：A3 讲循环如何消费模型流（含半截工具调用解析），这里讲渲染管线。

**快速信号**：目录名 `tui/`、`cli/`、`ui/`、`console/`、`render/`；可 grep：`stream`、`delta`、`on_token`/`onToken`、`text_stream`、`for await`、`spinner`、`markdown`、`ANSI`；依赖面常见 `ratatui`/`crossterm`（Rust）、`prompt_toolkit`/`Textual`（Python）、`ink`（TypeScript）。

**代表实现**：Aider-AI/aider — Python `prompt_toolkit` REPL，token 到达即打印；openai/codex — Rust 终端 UI，流式渲染与 ESC 中断一体；google-gemini/gemini-cli — 用 React Ink 把组件化渲染搬进终端。

```text
我在读一个开源 CLI Agent 的源码，想搞清楚「终端交互循环与流式渲染」是怎么实现的：从模型 API 返回的流式 chunk 到屏幕上增量出现的 Markdown，中间经过哪些环节。请定位实现入口并引用 file:line，用文字讲清完整数据流（chunk 到达 → 解析/缓冲 → 增量渲染 → 终端写出），点出关键数据结构与函数名（比如流式迭代器、渲染缓冲、spinner 状态机在本仓库里对应的实体），并说明输入框与输出区如何在同一条终端连接上共存；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I2. diff/patch 审批与回滚 UX（Diff Review & Undo）｜P1

**是什么**：模型产出编辑意图后，系统把它变成人类可审阅的 diff，批准即落盘、拒绝或反悔时可回滚（借 git 或自建快照）的那套机制。

**为什么重要**：写文件是 Agent 风险最高的动作，diff 审批是用户信任的锚点。编辑格式本身（SEARCH/REPLACE、unified diff、整文件重写）的选型与匹配算法直接决定解析失败率与 token 成本，那是 C12 的主题；这里聚焦编辑意图变成 diff 之后、面向人的审批与回滚。

**快速信号**：目录名 `edit/`、`patch/`；可 grep：`apply_patch`、`SEARCH`、`REPLACE`、`unified diff`、`hunk`、`reject`、`undo`、`checkpoint`、`snapshot`、`git reset`。

**代表实现**：Aider-AI/aider — SEARCH/REPLACE 块解析 + git 自动 commit，`/undo` 即回滚；cline/cline — 编辑写入编辑器原生 diff 视图，checkpoint（影子 git）支持整体回退；openai/codex — 自定义 `apply_patch` 格式与应用器。

```text
我在读一个开源 Agent 的源码，想搞清楚「diff/patch 审批与回滚」是怎么实现的：模型给出编辑意图后，系统如何生成可审阅的 diff、用户批准或拒绝后如何落到文件系统、反悔时如何恢复。请定位实现入口并引用 file:line，用文字讲清从模型输出的编辑格式（如 SEARCH/REPLACE 块、unified diff 或整文件重写）到文件写入与回滚的完整数据流，点出关键数据结构与函数名（如编辑格式解析器、patch 应用器、checkpoint/快照结构），并分别说明批准路径与拒绝路径各走到哪里；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I3. 编辑器与 GUI 前端集成（IDE / GUI Integration）｜P1

**是什么**：Agent 核心之外的前端宿主——IDE 扩展（VS Code/JetBrains）或 Web GUI，通过扩展 API、子进程或 HTTP/WebSocket 通道驱动同一个 agent core。

**为什么重要**：很多用户唯一的入口就是这块前端；集成边界划在哪里（同进程库、子进程 CLI 还是服务化 API）决定了状态同步、审批弹窗与进度通知的全部实现方式。

**快速信号**：目录名 `extension/`、`frontend/`、`gui/`、`web/`、`server/`；可 grep：`vscode`、`webview`、`registerCommand`、`activate(`、`websocket`、`panel`、`api/`、`routes`。

**代表实现**：cline/cline 与 Continue — 在 IDE 扩展宿主里跑 agent，UI 走编辑器扩展 API；OpenHands — React 前端与后端事件流对接的 Web GUI；ag2/AutoGen Studio 与 letta-ai/letta-code ADE — 自带可视化搭建/管理 agent 的完整控制台。

```text
我在读一个开源 Agent 的源码，想搞清楚「编辑器扩展或 GUI 前端与 Agent 核心的集成边界」是怎么划的：前端通过什么通道驱动核心循环、事件又如何流回前端渲染。请定位实现入口并引用 file:line，用文字讲清一次用户请求从前端组件到 agent core 再回到前端的完整调用流程，点出关键数据结构与函数名（如消息/事件的序列化协议、请求 handler 的注册方式、进度通知机制），并说明前端与核心是同进程库、子进程还是跨网络进程；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I4. 斜杠命令与自定义命令（Slash Commands）｜P1

**是什么**：聊天输入里以 `/` 开头的命令体系——内置命令（切换模式、管理文件、查状态）注册分发，用户还可以在配置目录放自定义命令文件，注入成 prompt。

**为什么重要**：它是 Agent 面向用户的「操作系统的 shell」；自定义命令机制是用户把个人工作流固化进 Agent 的最低成本途径，也最能看出输入解析的分层设计。

**快速信号**：目录名 `commands/`、`input/`、`chat/`；可 grep：`slash`、`startsWith('/')`、`builtin`、`custom command`、`registry`、`completion`；配置目录模式形如 `.{project}/commands/`。

**代表实现**：Aider-AI/aider — 内置 `/commands` 一套 plus `read-only` 命令分组；google-gemini/gemini-cli — 项目/全局目录下的自定义命令文件注入为 prompt；opencode — 以 Markdown 文件定义的自定义命令。

```text
我在读一个开源 Agent 的源码，想搞清楚「斜杠命令与自定义命令机制」是怎么实现的：内置命令如何注册与分发，用户放在配置目录里的自定义命令文件如何被扫描、解析并注入成 prompt。请定位实现入口并引用 file:line，用文字讲清从用户敲入 /command 到命令执行或展开的完整调用流程，点出关键数据结构与函数名（如命令注册表、输入解析器、参数处理与补全），并说明自定义命令文件支持哪些占位符或上下文注入；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I5. 配置体系与优先级（Config Layering & Precedence）｜P1

**是什么**：全局配置、项目级配置、环境变量与命令行参数各来源，按确定顺序合并覆盖成一份「最终生效配置」，常有 profile/预设机制切换整体档位。

**为什么重要**：配置层叠是工程化程度的试金石；优先级规则和校验回退行为直接决定「为什么我的配置没生效」这类最难排查的问题，也是 CI 自动化（A6）的前提。与 B1 的分工：B1 讲 system prompt 内容的分层，这里讲运行配置的分层。

**快速信号**：文件名 `config.toml`、`settings.json`、`*.conf.yml`、`.env`；可 grep：`load_config`/`loadConfig`、`merge`、`override`、`profile`、`precedence`、`homedir`、`XDG`、`--global`。

**代表实现**：openai/codex — config.toml 加 profile 预设再被命令行覆盖的层级链；SWE-agent — 整个 agent 的工具与提示都用 YAML 配置模板定义（配置即行为）；google-gemini/gemini-cli — settings 分层合并加命令行开关。

```text
我在读一个开源 Agent 的源码，想搞清楚「配置体系与优先级合并」是怎么实现的：全局配置、项目级配置、环境变量与命令行参数各自从哪里读、按什么顺序覆盖合并成最终生效的配置。请定位实现入口并引用 file:line，用文字讲清配置从各来源加载、合并、校验再到下发使用的完整数据流，点出关键数据结构与函数名（如配置 schema、profile/预设结构、优先级合并函数），并说明校验失败时的报错与回退行为；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I6. Hooks 与生命周期事件（Hooks & Lifecycle Events）｜P1

**是什么**：在工具调用前后、回合开始结束、会话启动关闭等时机触发用户注册的脚本或回调，可观察、部分实现还能拦截或改写主流程。

**为什么重要**：hooks 是不打补丁就能改变 Agent 行为的标准接口——lint/test 自动回喂、审计日志、自定义门禁都靠它；事件枚举的完备度直接反映架构的可观测性设计。

**快速信号**：目录名 `hooks/`、`events/`；可 grep：`hook`、`pre_tool`、`post_tool`、`lifecycle`、`emit`、`dispatch`、`subscribe`、`middleware`、`on_event`。

**代表实现**：Aider-AI/aider — 编辑提交后自动跑 lint/test 命令并把报错回喂模型；google-gemini/gemini-cli — extension 生命周期事件（activate、模型调用前后回调）；openai/codex — `notify` 配置把回合结束等事件推给外部程序。

```text
我在读一个开源 Agent 的源码，想搞清楚「hooks 与生命周期事件机制」是怎么实现的：在工具调用前后、会话开始结束等时机，用户注册的钩子脚本或回调如何被触发、输入输出如何传递、失败如何处理。请定位实现入口并引用 file:line，用文字讲清一次 hook 从事件产生、匹配、到用户代码执行、再到结果回注主流程的完整调用链，点出关键数据结构与函数名（如事件枚举、hook 注册表、匹配器、执行器），并说明 hook 能否拦截或改写主流程（例如阻断一次工具调用）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I7. 插件与扩展机制（Plugins, Extensions & Marketplace）｜P1

**是什么**：外部扩展（插件包、extension、marketplace 分发）被发现、加载、注册进模型工具表的标准通道，常配 manifest 声明。MCP server 作为工具源的协议接入（transport、initialize、tools/call）见 C7，这里看插件生命周期与生态面。

**为什么重要**：工具表的可扩展性决定生态位；理解「第三方能力如何从外部进程流进模型的 tool list、失败如何降级」是看懂现代 Agent 组装方式的关键。

**快速信号**：目录名 `plugins/`、`extensions/`、`providers/`；可 grep：`plugin`、`extension`、`manifest`、`registry`、`marketplace`、`registerTool`、`discover`。

**代表实现**：cline/cline — MCP marketplace 一键安装 server，工具直接进模型工具表；google-gemini/gemini-cli — extensions 与 MCP 双轨扩展；aaif-goose/goose — 以 MCP 为工具主干、另设原生扩展机制（注册、发现、生命周期、超时隔离的完整工程）。

```text
我在读一个开源 Agent 的源码，想搞清楚「插件/扩展机制与工具注册」是怎么实现的：外部扩展（插件、extension、MCP server 等）如何被发现和加载，它们暴露的工具或资源如何进入模型的工具表。请定位实现入口并引用 file:line，用文字讲清从扩展发现、注册到运行时调用的完整数据流，点出关键数据结构与函数名（如 manifest 或注册表、工具 schema 的生成与合并、扩展进程/连接的生命周期管理），并说明第三方扩展的隔离与失败降级策略；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I8. 多模态输入管道（Multimodal Input）｜P2

**是什么**：用户粘贴或指定一张图片/截图后，它被读取、编码（base64/URL）并封装成消息里的 image content block，随对话历史进入 API 请求。

**为什么重要**：截图是「把 UI 问题丢给 Agent」这一核心用例的入口；管道细节（尺寸压缩、格式转换、大小上限、历史里的累积成本）决定了多模态是能用还是摆设。

**快速信号**：可 grep：`image`、`base64`、`image_url`、`media_type`、`clipboard`、`paste`、`png`、`vision`、`multipart`、`resize`、`screenshot`；目录名 `media/`、`attachments/`。

**代表实现**：Aider-AI/aider — 终端里直接粘贴或以命令把图片加入对话；cline/cline — 聊天框粘贴/拖入截图并转成 image content block；OpenHands — 图片消息与浏览器/执行结果截图同走事件流。

```text
我在读一个开源 Agent 的源码，想搞清楚「多模态输入（图片/截图）管道」是怎么实现的：用户粘贴或指定一张图后，它经过什么路径进入对话历史并最终成为发给模型的消息。请定位实现入口并引用 file:line，用文字讲清从输入事件（剪贴板粘贴或路径参数）到消息构造、再到 API 请求体的完整数据流，点出关键数据结构与函数名（如图片读取与编码函数、base64/URL 两种形式、消息里的 content block 结构），并说明是否有尺寸压缩、格式转换或大小上限处理；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```

#### I9. 机器可读事件流输出（Machine-Readable Event Stream）｜P1

**是什么**：把内部事件（turn 开始、工具调用、流式文本、结束原因等）序列化为 JSONL/stream-json 按行写出 stdout，供外部程序消费的结构化输出通道。

**为什么重要**：这是 Agent 嵌入更大系统的集成面；事件 schema 的稳定性与颗粒度决定上层编排（测试断言、UI 代理、流水线日志）能不能写，也是人机两条输出链分叉点最清晰的地方。

**快速信号**：可 grep：`stream-json`、`stream_json`、`output-format`/`output_format`、`jsonl`、`eventType`、`event_type`、`serialize`、`emit`、`schema`。

**代表实现**：openai/codex — headless 执行的 JSONL 事件流输出；google-gemini/gemini-cli — 非交互模式的 stream-json 输出格式；langchain-ai/langgraph — 多种 stream mode（values/updates 等）的流式 API。

```text
我在读一个开源 Agent 的源码，想搞清楚「机器可读的事件流输出（如 stream-json/JSONL）」是怎么实现的：内部事件如何被序列化成结构化输出供外部程序消费。请定位实现入口并引用 file:line，用文字讲清从内部事件产生、过滤或映射、到按行写出 stdout 的完整数据流，点出关键数据结构与函数名（如事件类型枚举、序列化器、输出格式开关的处理），并对照人类可读的交互渲染路径说明两条输出链在哪里分叉；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；结尾给出 2-3 个值得继续追问的点。
```
