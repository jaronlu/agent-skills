> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### C. 工具系统（Tool System & Tool Calling）（L490–L675）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### C. 工具系统（Tool System & Tool Calling）

Agent 把「模型输出的结构化意图」变成「进程内真实副作用」的那一层——工具如何被定义、注册、校验、授权、执行、并把结果安全地喂回模型上下文。它是读任何 Agent 仓库时调用路径最密集的一条主干。其中频率最高、副作用最重的一个工具——「编辑文件」——的格式与落盘机制单列为 C12；以生成可执行代码为行动表征的第三条路线单列为 C13。权限与审批门的策略细节见 H5–H7。

#### C1. 工具定义 Schema：从函数/声明到模型的工具清单｜P0

**是什么**：把一个本地函数（签名 + docstring/类型注解）或手写声明，转换成模型 API 认的 JSON Schema（name / description / parameters），作为模型每回合可见的「能力清单」。

**为什么重要**：schema 是模型对工具的全部认知——参数描述含糊模型就调错；schema 的生成方式（手写声明 vs 从签名自动推导）直接决定加一个新工具的成本和出错面。

**快速信号**：目录 `tools/`；文件名 `tool*.py|ts`、`*_tool.*`、`registry.*`。grep 关键词：`input_schema`、`"parameters"` + `"properties"`、`json_schema`、`to_openai_schema`、`function_to_schema`、`inspect.signature`、`@tool`、`BaseTool`。

**代表实现**：OpenHands（把普通 Python 函数的签名 + docstring 自动推导成 OpenAI 格式 schema 的典型）；langchain-ai/langgraph（`@tool` 装饰器 + Pydantic 参数模型生成 schema 的事实标准）；google-gemini/gemini-cli（Tool 接口里手写 `declare()` 返回 schema 的显式风格）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具定义 schema」这一个知识点：仓库里的工具是如何声明并转换成模型可见的工具清单（如 OpenAI 的 tools 参数、Anthropic 的 input_schema）的？请定位工具定义与 schema 生成或声明的实现入口并引用具体 file:line；用文字讲清从「一个工具函数或工具声明」到「随请求发给模型的 schema 对象」的完整数据流；点出关键数据结构与函数名（工具对象有哪些字段、schema 是手写还是从 docstring / 类型注解自动推导、转换函数叫什么）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C2. 工具的 Prompt 表征：API tools 字段 vs 文本协议 vs CodeAct｜P0

**是什么**：工具以三种形态进入模型上下文——现代 API 的结构化 tools 参数（原生 tool calling）、写进 system prompt 的文本协议（XML/Markdown 约定 + 输出解析器自行提取调用）、或 CodeAct 路线（工具作为可调用对象注入执行环境、模型直接写代码调用它们，展开见 C13）。

**为什么重要**：这是读老仓库和新仓库最大的分歧点。文本协议仓库里「工具」一半藏在 prompt 模板里、一半藏在输出 parser 里，不先判断走的是哪条路，就会找不到工具系统的入口。协议选型还直接决定流式解析（A3）、并发执行（C10）、错误恢复的实现难度。

**快速信号**：grep `bind_tools`、`tool_choice`、`tools=[`、`tool_use` / `function_call`（结构化路线）；`<tool_call>`、`<function=`、`## Tools`、`edit_format`、`parse`、`extract`（文本协议路线）；`CodeAct`、`python_executor`、`final_answer`（代码行动路线，见 C13）。目录 `prompts/`，文件名 `*format*`、`*parse*`。

**代表实现**：Aider-AI/aider（edit format 文本协议的代表：whole/udiff 等格式靠 prompt 约定而非 schema）；cline/cline（system prompt 里 XML 风格的工具说明 + 流式解析）；langchain-ai/langgraph（`bind_tools` 原生 tool calling 的对照样本）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具如何呈现给模型」这一个知识点：请先判断这个仓库用的是原生 tool calling（API 的 tools 参数）还是把工具说明写进 system prompt 的文本协议（再由输出解析器提取调用），然后定位工具清单被组装进请求或 prompt 的实现入口并引用具体 file:line；用文字讲清「工具说明进入上下文 → 模型产出 tool call 文本或结构化字段 → 解析回可执行调用」的完整数据流；点出格式模板/常量与解析函数的名称；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C3. 注册与发现机制（Tool Registry）｜P1

**是什么**：一个维护 name → handler 映射的注册表，把散落在各处的工具集中登记，供模型侧清单组装和执行侧查表分发使用。

**为什么重要**：registry 的形状回答了「加一个新工具要改几处代码」——是往列表加一行、写个装饰器、还是提交一个插件 manifest；它决定了整个仓库的扩展模型。

**快速信号**：grep `register_tool`、`add_tool`、`@register`、`TOOL_REGISTRY`、`get_tool(`、`tools = [`、`__subclasses__`。目录 `tools/`、`registry/`；留意装饰器和 `__init__` 里的集中 import。

**代表实现**：ag2/AutoGen（`register_for_llm` / `register_for_execution` 双注册的经典范式：一个声明给模型、一个绑定执行器）；letta-ai/letta-code（`@tool` 装饰器登记进工具表、按 agent 附加）；MCP Python/TS SDK（服务端用装饰器声明 tools，`list_tools` 统一吐出清单）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具注册与发现机制」这一个知识点：仓库里的工具是如何登记到一个 registry、执行时又如何按名字查到具体实现的？请定位注册表数据结构与注册/查找的实现入口并引用具体 file:line；用文字讲清「新工具文件落盘 → 被注册 → 出现在模型可见清单 → 被 dispatch 选中执行」的完整链路；点出 registry 的数据结构形态（map/list/装饰器/插件扫描）、注册时机（启动时还是延迟）以及关键函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C4. Tool Call 解析与分发（Dispatch & Result Feedback）｜P0

**是什么**：把模型返回的 tool call（完整 JSON 或流式 partial JSON）解析出来、按 name 查到 handler、用 call_id 关联请求与结果、产出 tool result 消息回喂的桥接层——标准 function calling 的 `tool_calls`/`tool_use` 字段，或自定义文本协议（XML 标签、特殊代码块）的解析结果，都以 `tool` role 消息 / `ToolMessage` / 协议规定的回填格式追加进 messages 喂回模型。

**为什么重要**：这是 agent loop 的「心脏搭桥」——几乎所有调用路径都经过它；解析失败或回填格式错误，模型就"看不到"执行结果，循环退化甚至死循环；流式累积、多调用、call_id 对齐等最容易出 bug 的复杂度也都堆在这里。

**快速信号**：grep `tool_calls`、`tool_use`、`function_call`、`call_id`、`tool_call_id`、`handle_tool_call`、`execute_tool`、`dispatch`、`function.name`、`arguments`、`ToolMessage`、`tool_result`、`accumulate` / `partial`；自定义协议则 grep `<tool`、`SEARCH/REPLACE`、`parse.*block`。目录 `tools/`、`providers/`。

**代表实现**：langchain-ai/langgraph（ToolNode 作为标准化分发节点，串起解析与执行；`ToolMessage` 消息类型的教科书实现）；openai/codex（Rust core 里从模型事件到 shell / apply_patch 的路由）；cline/cline（流式 XML 参数逐段累积、完整后才触发的解析器）；Aider-AI/aider（不用 function calling，直接从流式文本解析 SEARCH/REPLACE 编辑块）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「tool call 解析与分发」这一个知识点：从模型响应里的 tool_calls / function_call（或自定义文本协议）到本地 handler 执行、再到 tool result 消息回喂，这条链路是怎么走的？请定位解析入口与执行入口并分别引用具体 file:line；用文字讲清完整调用流程：call_id 如何关联请求与结果、arguments 字符串如何被解析（如果是流式，partial JSON 如何累积）、回填采用什么消息形态（tool role / ToolMessage / 自定义格式）、name 找不到或解析失败时走哪条分支；点出分发函数名与结果消息的构造函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C5. 参数校验与校验失败的错误回喂｜P1

**是什么**：在真正执行前用 schema（Pydantic / JSON Schema 校验器）核对模型给的参数；失败时不让进程崩溃，而是把格式化后的错误文本作为一条 tool result / observation 喂回模型，让它自我纠正后重试。

**为什么重要**：模型给错参数是常态而非异常；「校验失败 → 变成一个可恢复的对话回合」是 agent 稳定性的关键设计，也是区分 demo 与生产代码的标志之一。最终输出/动作通道的 schema 校验与再生成见 G6，两者对象不同（工具入参 vs 模型输出）。

**快速信号**：grep `ValidationError`、`missing required`、`Invalid arguments`、`invalid_json`、`pydantic`、`validate`、`JSONDecodeError`。留意错误字符串模板（它们最终会出现在模型上下文里）。

**代表实现**：pydantic/pydantic-ai（Pydantic 校验 + `ModelRetry` 把错误回喂给模型重试的显式机制）；google-gemini/gemini-cli（Tool 接口的 validate 阶段 + 校验错误作为结果回传）；OpenHands（校验失败作为 observation 回喂进对话流）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「参数校验与校验失败的错误回喂」这一个知识点：工具执行前参数在哪里被校验、用什么校验？校验失败后错误是怎么变成一条回喂给模型的 tool result / observation，而不是让整个 agent 崩掉的？请定位校验代码路径与失败路径并引用具体 file:line；用文字讲清「模型给出坏参数 → 校验失败 → 错误被格式化 → 作为结果回喂 → 模型重试」的完整流程；点出校验函数名、错误消息模板和相关的数据结构；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C6. 工具结果格式化与大小限制（Tool Output Formatting & Truncation）｜P1

**是什么**：工具的原始输出（stdout、文件内容、报错、图像）被规整成模型可读的 content block / observation 文本，并在超过阈值时截断——常见做法是保留头尾、中间省略、并打上 `[truncated]` 类标记。

**为什么重要**：工具输出是上下文膨胀的第一来源——一次失控的工具输出（cat 了大文件、测试日志爆炸）足以瞬间吃掉整个窗口甚至直接超限；截断是摄入侧的第一道闸：规则简单、零额外成本，却决定后续所有压缩动作（B7）的负担轻重，也决定后续回合里模型还能不能基于结果继续干活。

**快速信号**：grep `truncat`、`MAX_`、`max_lines`、`max_chars`、`max_output`、`output_limit`、`limit`、`truncated`、`too long`、`tool_result`、`content block`；看工具执行返回处对 output 的后处理；上限常量常集中在 config 文件或每个工具定义旁边；留意多模态结果（image content）的分支。

**代表实现**：openai/codex（shell 执行输出有明确的截断上限常量，超限时截断并附带可见提示）；cline/cline（文件读取默认行数上限与搜索结果条数上限）；OpenHands（observation 统一经过截断与规整管道）；langchain-ai/langgraph（`ToolMessage` 的 content 结构，文本与 artifact 的承载方式）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具结果的格式化与大小限制」这一个知识点：工具的原始输出（stdout / 文件内容 / 图像等）是如何被格式化成回喂给模型的结果消息的？超过大小限制时如何截断？请定位格式化与截断的实现代码并引用具体 file:line；用文字讲清「工具执行完成 → 原始输出 → 格式化/序列化 → 截断判断 → 进入模型上下文」的数据流；点出结果的数据结构、截断阈值常量名和截断策略（保留头还是尾、保头保尾还是只留前缀、有没有 truncated 标记）；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C7. MCP（Model Context Protocol）接入｜P1

**是什么**：仓库作为 MCP client，通过 JSON-RPC（stdio 或 HTTP/SSE transport）连接外部 server：`initialize` 做能力协商、`tools/list` 拉取工具清单、`tools/call` 执行远端工具，并把远端工具映射成本地同名工具参与统一 dispatch。

**为什么重要**：MCP 是工具生态的事实标准；看懂一个仓库的 MCP 接入，等于一次看懂 transport 管理、schema 翻译、命名空间防重名、工具列表热更新（C8）这四件事怎么落地。

**快速信号**：grep `mcp`、`tools/list`、`tools/call`、`initialize`、`stdio`、`jsonrpc`、`server`（配置文件里的 server 列表）。目录 `mcp/`；配置文件里的 `mcpServers` 字段。

**代表实现**：MCP 官方 TypeScript / Python SDK（协议与 transport 的参考实现）；cline/cline（接入大量用户自配 MCP server 的实战端，marketplace 一键安装）；aaif-goose/goose（以 MCP 为工具主干）；openai/codex（内置 mcp 子命令管理 server 配置）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「MCP 接入」这一个知识点：仓库作为 MCP client 是如何连接外部 server 的——transport（stdio / HTTP）怎么建立、initialize 能力协商、tools/list 拉清单、tools/call 执行，以及远端工具如何并入本地统一的工具分发和权限体系？请定位 MCP client 的实现入口并引用具体 file:line；用文字讲清一次远端工具调用端到端的数据流（含结果如何回到模型上下文）；点出连接管理、schema 翻译、命名空间 / 重名处理相关的关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C8. 动态加载与热更新工具（Dynamic Tool Loading）｜P1

**是什么**：工具清单不是启动时写死，而是可以在运行时增删——会话中途注册新工具、插件安装即生效、MCP server 侧列表变化后收到 `list_changed` 通知重拉、或运行时从远端 import。

**为什么重要**：工具集静态写死的 agent 扩展性差；动态面带出一串真实工程问题——schema 缓存失效、模型侧 prompt/工具清单何时重建、新旧工具的调用兼容。

**快速信号**：grep `list_changed`、`register_tool`（找运行时调用点而非定义处）、`add_tool`、`reload`、`importlib`、`plugin`。留意 session/agent 对象上有没有可变的工具集合字段。

**代表实现**：huggingface/smolagents（运行时从 Hub import 工具）；letta-ai/letta-code（agent 级动态附加/启用工具）；MCP SDK（`notifications/tools/list_changed` 触发客户端重拉清单的协议侧机制）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「动态加载与热更新工具」这一个知识点：这个仓库的工具清单能否在运行时改变——会话中途注册、插件加载、或外部工具源（如 MCP server）列表变化后如何感知？请定位运行时注册 / 重载的实现路径并引用具体 file:line；用文字讲清一次动态变更发生后，模型侧的工具清单与 prompt 是如何同步刷新的（下一回合才生效还是立即重建）；点出相关函数名与缓存 / 失效处理的数据结构；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C9. 工具太多：检索、筛选与子集注入（Tool Retrieval & Subset Injection）｜P2

**是什么**：当工具数量大到撑爆 schema 预算或稀释模型注意力时，按任务/查询动态选一个子集注入——关键词或 embedding 检索、按域分组命名空间、或提供一个让模型自己按需发现的 meta-tool（如 tool_search）。

**为什么重要**：「所有工具全量塞进每一回合」在几十个工具以上必然劣化（schema 稀释 + token 成本 + 选错率上升）；这是多 MCP server 场景的第一痛点，也是当前仍在活跃演进的方向。

**快速信号**：grep `tool_search`、`search_tools`、`select_tools`、`filter_tools`、`embedding`、`namespace`、`top_k`。留意工具数量上限的配置项，或「全量注入、无筛选」这一反面答案本身。

**代表实现**：huggingface/smolagents（Hub 工具集的 retrieval 子集注入）；langchain-ai/langgraph（tool retrieval / 按 embedding 选子集的通用模式）；letta-ai/letta-code（工具分组与共享工具的命名空间管理）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具过多时的检索与选择」这一个知识点：当工具数量很大时，仓库有没有按任务动态筛选工具子集的机制（关键词 / embedding 检索、分组命名空间、或让模型通过某个 meta-tool 自行搜索工具）？如果没有，是全量注入吗，有没有数量上限？请定位选择逻辑（或明确指出不存在并给出全量注入的证据）并引用具体 file:line；用文字讲清一次请求里工具子集是如何被决定、打分并组装进请求的；点出过滤 / 检索函数名和相关配置项；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C10. 并行工具调用（Parallel Tool Calls）｜P1

**是什么**：模型在一回合里返回多个 tool call 时，客户端并发执行它们、按 call_id 对齐结果、统一回喂——通常只读工具并行加速（`Promise.all` / `asyncio.gather` / 线程池），有副作用的工具串行或加锁防冲突；并发度有无上限、多条结果消息按请求序还是完成序回填。

**为什么重要**：并行是延迟的主要杠杆（多个只读工具本可同时跑），把 agent loop 从「一次一回合的串行 RPC」变成 fan-out / fan-in 模式；也引入一致性问题——写操作并发会竞态、结果顺序影响模型理解。一个仓库在这里的取舍，直接反映它的工具执行模型设计。agent 级的并行派发见 E7，并发治理见 E13。

**快速信号**：grep `parallel_tool_calls`、`Promise.all`、`asyncio.gather`、`parallel`、`concurrent`、`batch`、`fan`、`worker`、`pool`、`p-limit`；看处理 tool call 数组的循环是 `for await` 还是并发原语；留意对工具标注只读/可写属性的枚举或字段；图式框架则 grep `Send`、fan-out、并行节点。

**代表实现**：langchain-ai/langgraph（同一 superstep 内并行执行节点，ToolNode 对一回合多个 tool call 的并发执行与结果对齐，`Send` API 做动态 fan-out）；OpenAI Agents SDK（run loop 里对并行 function calls 的 gather 处理）；ag2/AutoGen 0.4（actor 运行时：agent 之间以异步消息并发协作，单个 agent 内默认顺序处理）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「并行工具调用」这一个知识点：当模型一回合返回多个 tool call 时，仓库是串行还是并发执行它们的？请定位并发执行的代码（或明确指出是串行并给出证据）并引用具体 file:line；用文字讲清从「一回合多个 tool call」到「全部执行完、结果按 call_id 对齐、统一回喂」的 fan-out 到 fan-in 流程；讲清并发用了什么原语（Promise.all / asyncio.gather 等）、并发度有没有上限、只读与有副作用的工具有没有区别对待、有哪些并发安全措施（锁、工作目录隔离）、多条结果消息按什么顺序回填给模型；点出相关函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C11. 工具执行生命周期：超时、取消与异常隔离（Tool Execution Lifecycle）｜P1

**是什么**：把每次工具执行包成一个可治理的执行单元——施加 timeout、支持 cancellation（用户中断 / 新请求到来时取消在跑的工具）、把工具抛出的异常转成 error tool result 而不是崩掉 agent、结束后清理资源。

**为什么重要**：工具是最常见的崩溃源和卡死点；「工具抛异常 ≠ agent 进程死」这条不变量，加上流式场景下取消信号的传播路径，是生产级实现与玩具实现之间的分水岭。分层的超时体系见 G4，中断在循环控制流中的位置见 A7。

**快速信号**：grep `timeout`、`abort`、`AbortController`、`CancelledError`、`SIGINT`、`kill`、`cleanup`、`on_error`。留意包裹 execute 调用的那层 try/except 和它的 catch 范围。

**代表实现**：langchain-ai/langgraph（节点级异常处理与 error state 流转）；openai/codex（turn 取消时打断在跑的子进程）；OpenHands（工具异常作为 error observation 进入事件流）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「工具执行生命周期：超时、取消与异常隔离」这一个知识点：单次工具执行是如何被治理的——timeout 在哪里施加、用户中断或新请求到来时如何取消还在跑的工具、工具内部抛出的异常如何变成一条 error 结果回喂给模型而不是让整个 agent 崩掉？请定位超时 / 取消 / 异常包装的实现代码并引用具体 file:line；用文字讲清从「用户中断」到「在跑的子进程或请求真正停下来、循环回到可控状态」的传播路径；点出 abort / cancel 相关的结构名和异常转换函数名；若本仓库没有独立的工具生命周期治理，请直说并指出最接近的替代实现；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C12. 文件编辑格式与 Patch 应用器（File Edit Formats & Patch Application）｜P1

**是什么**：模型表达「编辑这个文件」这一动作的具体格式，与把该格式落到磁盘的 patch 应用器：SEARCH/REPLACE 块（给出旧文本与新文本，应用器在文件中定位旧文本并替换）、unified diff（标准 hunk + 行号偏移容错）、整文件重写（直接输出完整新文件），以及匹配失败时的处置（模糊匹配降级、报错回喂让模型重出、或放弃）。

**为什么重要**：编辑是编码 Agent 频率最高、副作用最重的工具，格式选择直接决定解析失败率与 token 成本——SEARCH/REPLACE 的旧文本要占 token 但定位准，unified diff 的行号在文件变动后易漂移，整文件重写零歧义但 token 最贵；应用器的匹配算法（精确匹配还是空白归一化、行号容错、多处命中怎么消歧）与失败回喂路径，是 aider/codex/cline 各家差异最大的实现细节之一。与 I2 的分工：I2 讲 diff 审批与回滚的 UX 层，这里讲编辑格式与 patch 应用器本体。

**快速信号**：grep `SEARCH` / `REPLACE`（成对出现在 prompt 模板里）、`<<<<<<<`、`=======`、`>>>>>>>`（SEARCH/REPLACE 围栏）、`apply_patch`、`Begin Patch`、`hunk`、`unified diff` / `udiff`、`whole`、`edit_format`、`fuzzy`、`did not match` / `not found in file`；文件名 `editblock*`、`patch*`、`apply*`；aider 的 edit format 家族（whole/diff/udiff/search-replace 等）是这一族概念的源头实现。

**代表实现**：Aider-AI/aider —— edit format 家族按模型能力选择，SEARCH/REPLACE 块的精确与空白容错匹配、失败后回喂重出的完整回退链；openai/codex —— 自定义 `apply_patch` 格式（`*** Begin Patch` 标记）与应用器；cline/cline —— 工具协议里 old_string/new_string 精确匹配替换，匹配不到即作为错误结果回喂模型。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「文件编辑格式与 patch 应用器」这一个知识点：模型表达「编辑文件」这个动作用什么格式（SEARCH/REPLACE 块、unified diff、整文件重写还是自定义 patch 格式），对应的应用器又是怎么把它落到磁盘的？请定位编辑格式的 prompt 约定（模型被要求按什么格式输出编辑意图）与应用器实现（匹配算法是精确匹配还是带空白归一化/行号容错、旧文本多处命中或匹配不到时走哪条分支、失败是报错回喂让模型重试还是直接放弃）并引用具体 file:line；用文字讲清一次「模型输出编辑块 → 解析 → 定位目标位置 → 应用替换 → 写盘」的完整数据流；点出格式常量与应用器的关键函数名；若本仓库没有独立的编辑格式机制，请直说并指出最接近的替代实现；最后给出 2-3 个基于这个仓库实现的追问点。
```

#### C13. CodeAct：以生成可执行代码为行动表征（CodeAct / Action-as-Code）｜P1

**是什么**：行动表征的第三条路线：模型不逐个发起 JSON tool call，而是直接写出一段可执行代码（通常是 Python），代码里调用以普通函数/对象形式注入执行环境的工具，由受限解释器或沙箱执行，返回值与 stdout 作为 observation 回喂——一次行动天然可组合（变量、循环、条件），不再是一次一调用。

**为什么重要**：推荐清单里两个仓库以它为主范式——OpenHands 的主力 agent 就叫 CodeActAgent，smolagents 整个库围绕 CodeAct 构建；它与 JSON tool call 路线的差异是结构性的：行动从「一次一调用的结构化字段」变成「一段程序」，执行环境的设计（命名空间注入了什么、import 与语法限制、超时与循环上限、Python 异常如何变成 observation）读起来与 C4 的分发桥完全不同。与 C2 的分工：C2 讲工具呈现给模型的三条路线与判别，这里讲代码行动的执行与回喂机制。

**快速信号**：grep `CodeAct`、`code_act`、`python_executor`、`local_python`、`exec(`、`Interpreter`、`ast.parse`（用 AST 解析代码行动）、`final_answer`（代码内自报完成的约定调用）、`authorized_imports`、`namespace`；文件名 `*executor*`、`*interpreter*`、`sandbox*`。

**代表实现**：huggingface/smolagents —— local_python_executor：工具作为可调用对象注入命名空间，受限执行 + `final_answer()` 终止约定的最小完整实现；OpenHands —— CodeActAgent 以代码行动为主范式，执行交给沙箱 runtime；对照面：codex/cline/aider 均为 JSON tool call 或文本协议路线。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「CodeAct（以生成可执行代码为行动表征）」这一个知识点：模型是否被要求直接写一段代码（而非逐个 JSON tool call）来表达行动？请定位代码行动的 prompt 约定、执行环境（受限解释器还是沙箱：命名空间里注入了哪些工具与对象、import 或语法上有什么限制、有没有超时与循环上限）、执行结果如何变成 observation 回喂（返回值、stdout、抛出的异常分别怎么处理）并引用具体 file:line；用文字讲清一次「模型产出代码 → 解析与检查 → 执行 → observation 回填 → 进入下一轮」的完整数据流；点出执行器与命名空间构造的关键函数名；若本仓库不走 CodeAct 路线，请直说并指出它的行动表征属于哪条路线（JSON tool call 还是文本协议）；最后给出 2-3 个基于这个仓库实现的追问点。
```
