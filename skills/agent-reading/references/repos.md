> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：## 五、附录：推荐精读的开源 Agent 仓库清单（14 个）（L1926–L2237）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

## 五、附录：推荐精读的开源 Agent 仓库清单（14 个）

配套速查表的 10 个领域，选出 14 个值得逐行精读的开源仓库。用法：`git clone` 后 cd 进仓库，把每个仓库的「开场提示词」粘贴给 codex / claude / repoprompt 问出整体架构，再按速查表正文的知识点提示词逐个深入。开场提示词一次问 4 件事，其中第 3) 问（端到端追踪）最重；若回答过长或明显变浅，可把 3) 单独作为第二次粘贴重问。

**核实说明**：所有 owner/name、主语言、维护状态均于 **2026-10-24** 通过 GitHub API（`gh api repos/<owner>/<name>`，取 `full_name` / `pushed_at` / `archived` / `language` / `stargazers_count`）逐个核对，仓库迁移与维护状态另经网络检索确认。四个仓库近期发生过迁移/重组（OpenHands、goose、Letta、AutoGen），旧书签需要更新——见每条说明与文末「落选与迁移说明」。

### 总览

| # | 仓库 | 主语言 | 类别 | 最适合演示的领域 | 难度 |
|---|------|--------|------|------------------|------|
| 1 | openai/codex | Rust | 编码 Agent CLI | 核心循环（生产级 agentic loop） | 进阶 |
| 2 | OpenHands/software-agent-sdk | Python | 编码 Agent CLI | 核心循环（事件流架构 + 沙箱） | 进阶 |
| 3 | SWE-agent/SWE-agent | Python | 编码 Agent CLI | 工具系统（ACI 设计） | 入门 |
| 4 | cline/cline | TypeScript | 编码 Agent CLI | 交互与工程化（审批门/diff 审查） | 入门 |
| 5 | aaif-goose/goose | Rust | 编码 Agent CLI | 工具系统（MCP 扩展体系） | 进阶 |
| 6 | google-gemini/gemini-cli | TypeScript | 编码 Agent CLI | 上下文工程（压缩/预算）+ 配置分层 | 入门 |
| 7 | Aider-AI/aider | Python | 编码 Agent CLI | 上下文工程（repo map 源头） | 进阶 |
| 8 | langchain-ai/langgraph | Python | 编排框架 | 多 Agent 协作（显式图）+ 容错（checkpoint） | 进阶 |
| 9 | ag2ai/ag2 | Python | 编排框架 | 多 Agent 协作（群聊/Handoff） | 进阶 |
| 10 | crewAIInc/crewAI | Python | 编排框架 | 多 Agent 协作（角色分工） | 入门 |
| 11 | huggingface/smolagents | Python | 编排框架（最小实现） | 核心循环（CodeAct） | 入门 |
| 12 | pydantic/pydantic-ai | Python | 编排框架 | 工具系统 + 容错（结构化输出） | 入门 |
| 13 | letta-ai/letta-code | TypeScript | 专项示范 | 记忆系统（分层记忆 MemGPT） | 进阶 |
| 14 | mem0ai/mem0 | Python | 专项示范 | 记忆系统（自动抽取与写入门控） | 入门 |

编号与下方正文条目一一对应（1-7 编码 Agent CLI、8-12 编排框架、13-14 专项示范）；「难度」是独立维度，不表示阅读顺序——新手从哪个仓库开始、按什么路径推进，见文末「建议学习顺序」。

### 一、编码 Agent CLI

#### 1. openai/codex —— 生产级 Rust 编码 Agent 的标杆

- **核实**：Rust，130,692★，最后推送 2026-10-23，活跃维护 ✅
- **一句话学习价值**：OpenAI 官方 CLI 编码 Agent，Rust 多 crate 工程，把「一个能安全跑在用户终端里的 agentic loop」做成了工业品——session/rollout 持久化、审批门、compaction 全都齐。
- **最适合演示**：A 核心循环与执行模型（agentic loop 本体、流式增量解析、中断与恢复、headless）；顺带 B7（compaction）。
- **难度**：进阶（Rust + 多 crate，代码量大，但结构规整）。
- **开场提示词**：

```text
我在精读 openai/codex 来学习生产级编码 Agent 的实现。请先给我整体架构：
1) codex-rs 下的 crate 划分：每个 crate 一句话职责；
2) 程序入口：CLI 从 main() 到 agent 会话循环的调用链是什么；
3) 端到端追踪一次典型请求：用户在终端输入一条修改指令 → prompt 组装 → 模型流式响应 → 工具调用（含一次需要审批的命令）→ 结果回填 → 循环终止，标注每一步的 file:line；
4) 指出你认为最值得精读的 3 个文件及理由。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 2. OpenHands/software-agent-sdk —— 事件流（Event Stream）架构的标准范本

- **核实**：Python，1,300★，最后推送 2026-10-23，活跃维护 ✅。注意：原 `All-Hands-AI/OpenHands` 已迁移为 `OpenHands/OpenHands`，主仓库在 v1 重写后变成 TypeScript 的 Agent Canvas（桌面/控制台产品壳）；**Agent 本体的 Python 实现在本仓库**（v1 拆出的模块化 SDK：agent / tools / workspace 分包，2025-09 官方博客《The Path to OpenHands v1》与 arXiv:2511.03690 论文有架构说明）。
- **一句话学习价值**：把 Agent 的每一步都建模为事件（event stream），Agent 逻辑、LLM 调用、状态、沙箱执行彻底解耦——想理解「事件溯源式 Agent」这一流派，这是最完整的开源实现。
- **最适合演示**：A8（隐式循环 vs 显式图的第三条路：事件流驱动）+ G8/G10（checkpoint 与事件回放）+ C13（CodeActAgent：代码行动交给沙箱 runtime 执行）；沙箱执行模型（H1）也可在此看。
- **难度**：进阶（多包工程，但边界清晰，README/DEVELOPMENT 文档全）。
- **开场提示词**：

```text
我在精读 OpenHands software-agent-sdk 来学习事件流式 Agent 架构。请先给我整体架构：
1) 仓库内 openhands-sdk / openhands-agent-server / clients / examples 各包的职责一句话；
2) 事件（Event）类型的定义在哪里，事件流的发布/订阅机制如何实现；
3) 端到端追踪：一个任务事件进入 → agent 产生 ActionEvent → 工具/命令在沙箱中执行 → ObservationEvent 回填 → 循环终止，标注每一步的 file:line；
4) 指出你认为最值得精读的 3 个文件及理由。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 3. SWE-agent/SWE-agent —— 「少即是多」的工具设计教科书

- **核实**：Python，20,628★，最后推送 2026-10-19，活跃维护 ✅
- **一句话学习价值**：学术出身的 SWE Agent（Princeton），靠一套精心设计、数量极少但好用的 ACI（Agent-Computer Interface）工具拿 benchmark 分——读它能学会「工具不是越多越好，而是要让模型用得对」。
- **最适合演示**：C 工具系统（C1 工具定义 Schema 的极简主义、C2 Prompt 表征、C5 参数校验错误回喂）+ F8（编辑-验证循环）。
- **难度**：入门（学术实现，核心循环短，聚焦度高）。
- **开场提示词**：

```text
我在精读 SWE-agent 来学习 Agent 工具（ACI）设计。请先给我整体架构：
1) 顶层模块/目录划分：每个模块一句话职责；
2) 程序入口：从 CLI 接收一个 GitHub issue 到 agent 主循环启动的调用链；
3) 端到端追踪：issue 输入 → agent 产生第一条 edit/lint 命令 → 命令在环境中执行 → observation 回填 → 循环终止条件，标注每一步的 file:line；
4) 找出它给模型暴露的全部工具清单及每个工具的 prompt 描述，评价这套 ACI 的取舍。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 4. cline/cline —— 审批门与 diff 审查 UX 的完整样本

- **核实**：TypeScript，70,787★，最后推送 2026-10-24，活跃维护 ✅（已从 VSCode 扩展扩展为「SDK / IDE 扩展 / CLI」三形态）
- **一句话学习价值**：把「人在回路」做成了产品：Plan/Act 双模式、每一步文件编辑的 diff 审批、自动批准规则、MCP 接入——交互与工程化领域的知识点几乎都能在这里找到实现。
- **最适合演示**：I 交互与工程化（I2 diff 审批与回滚、I3 编辑器集成、I7 插件/MCP）；也适合看 F1（Plan Mode）与 H5–H7（审批与自动批准）。
- **难度**：入门（核心路径直白：消息解析 → 工具执行 → 审批 UI）。
- **开场提示词**：

```text
我在精读 cline 来学习编码 Agent 的交互与审批设计。请先给我整体架构：
1) 顶层模块/目录划分：每个模块一句话职责；
2) 程序入口：VSCode 扩展的激活入口到 agent 核心任务的调用链；
3) 端到端追踪：用户输入一条指令 → Plan/Act 模式判断 → 模型返回工具调用（含一次文件编辑）→ diff 审批门 → 执行与回填 → 循环终止，标注每一步的 file:line；
4) 找出权限/自动批准（auto-approve）规则的实现位置，说明有哪些可配置档位。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 5. aaif-goose/goose —— MCP 扩展体系的工程化样本

- **核实**：Rust，55,598★，最后推送 2026-10-23，活跃维护 ✅。注意：原 `block/goose` 已迁移至 `aaif-goose/goose`，项目已捐给 Linux 基金会旗下的 Agentic AI Foundation（AAIF），README 有官方说明。
- **一句话学习价值**：Block 出品的通用 Agent（桌面 + CLI + API 三形态），核心卖点是把 70+ 扩展经 MCP（Model Context Protocol）统一接入——想看「MCP 作为扩展机制」如何做成完整工程（注册、发现、生命周期、超时），这是最好的 Rust 范本。
- **最适合演示**：C 工具系统（C7 MCP 接入、C3 tool registry、C8 动态加载、C11 执行生命周期）+ I7（插件机制）。
- **难度**：进阶（Rust + 桌面/CLI 双前端）。
- **开场提示词**：

```text
我在精读 goose 来学习 MCP 扩展机制。请先给我整体架构：
1) 顶层 crate/模块划分：每个模块一句话职责（CLI 与桌面端分别在哪里）；
2) 程序入口：CLI 启动 → 加载 MCP extension → agent 循环启动的调用链；
3) 端到端追踪：用户一条指令 → 模型决定调用某个 MCP 工具 → 请求发往 MCP server → 结果回填 → 循环终止，标注每一步的 file:line；
4) 找出扩展（extension）的注册、发现与生命周期管理（启动/超时/失败隔离）的实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 6. google-gemini/gemini-cli —— TypeScript Agent 的上下文管理范本

- **核实**：TypeScript，107,563★，最后推送 2026-10-24，活跃维护 ✅
- **一句话学习价值**：Google 官方终端 Agent，TypeScript 写得规整易懂：分层 system prompt、上下文压缩（compaction）触发与恢复、分层配置（system/user/project/cwd）+ MCP + 斜杠命令一应俱全，是 TS 读者最好的「第一个完整 Agent」。
- **最适合演示**：B 上下文工程（B2 计数、B3 预算、B7 压缩、B8 超限策略）+ I5（配置分层）、A6/I9（headless 与机器可读输出）。
- **难度**：入门。
- **开场提示词**：

```text
我在精读 gemini-cli 来学习上下文管理。请先给我整体架构：
1) 顶层 packages/目录划分：每个包一句话职责；
2) 程序入口：CLI 从 main 到对话循环的调用链；
3) 端到端追踪：用户输入 → system prompt 分层组装 → 模型流式响应 → 一次工具调用 → 结果回填；随后回答：上下文接近上限时压缩（compaction）如何触发、如何恢复对话，标注每一步的 file:line；
4) 指出配置分层（system/user/project/cwd）的合并优先级实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 7. Aider-AI/aider —— repo map 与 edit format 的源头实现

- **核实**：Python，49,724★，未归档，但**维护明显放缓**：最后推送 2026-05-22，最后一个 release（v0.86.0）发布于 2025-08-09。收录理由：它稳定、算法部分不随时间过期，且是下述两个知识点的公认源头实现；想要「活跃替代」可先读 codex 的 compaction 与 SWE-agent 的工具协议再回来。
- **一句话学习价值**：repo map（基于 tree-sitter 的 ranked repository summary，把整个仓库压进 token 预算的页面排序算法）和一整族 edit format（whole/ diff/ udiff/ search-replace）都诞生在这里——速查表 B4「仓库地图」、C2「工具的 Prompt 表征」与 C12「文件编辑格式与 Patch 应用器」三节的祖师爷。
- **最适合演示**：B4（repo map：ranked summary + token 预算裁剪）+ C2（以文本协议呈现工具的路线）+ C12（edit format 家族：表达「编辑」这个动作的多种设计及其失败回退）。
- **难度**：进阶（tree-sitter 与 edit format 是算法密集区）。
- **开场提示词**：

```text
我在精读 aider 来学习 repo map 与 edit format。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 程序入口：CLI 从 main 到 Chat 循环的调用链；
3) 端到端追踪：用户 /add 一个文件并下达修改指令 → repo map 如何构建与裁剪（tree-sitter 解析、page ranking、token 预算）→ 选中的 edit format 如何生成模型输出格式与解析 diff → 写回文件与 git commit，标注每一步的 file:line；
4) 列出它支持的 edit format 变体及各自的失败回退策略。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

### 二、Agent 编排框架

#### 8. langchain-ai/langgraph —— 显式图模型与 checkpoint 的工业标准

- **核实**：Python，43,794★，最后推送 2026-10-24，活跃维护 ✅
- **一句话学习价值**：把 Agent 编排表达为显式状态图（节点/边/ reducer 状态合并），并原生提供 checkpoint / 时间旅行 / human-in-the-loop interrupt——速查表里「显式图」（A8/E6）与「容错」（G8/G10）两大主题在这一个仓库里闭环。
- **最适合演示**：E 多 Agent 协作（E6 状态图工作流、E4 supervisor、E10 共享状态）+ G8/G10（checkpoint 与崩溃恢复）、J7（时间旅行）。
- **难度**：进阶（核心抽象分层多，建议从 `libs/langgraph` 的 pregel 执行引擎读起）。
- **开场提示词**：

```text
我在精读 langgraph 来学习显式图编排。请先给我整体架构：
1) 仓库/packages 划分：每个包一句话职责；
2) 核心抽象：StateGraph/节点/边/Channel/checkpointer 各自定义在哪里；
3) 端到端追踪：graph.compile() 之后一次 ainvoke() 的执行路径——状态初始化 → 节点调度 → 状态 reducer 合并 → checkpoint 写入 → 条件边决定下一节点 → END，标注每一步的 file:line；
4) 找出 human-in-the-loop 的 interrupt 机制与恢复路径的实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 9. ag2ai/ag2 —— 群聊调度与 Handoff 的正统 AutoGen 延续

- **核实**：Python，5,013★，最后推送 2026-10-24，活跃维护 ✅。注意：`microsoft/autogen` 仓库 2026-10-16 的最新 commit 明确声明「AutoGen is archived and no longer maintained」，活跃开发在 ag2ai/ag2（自述 "AG2 (formerly AutoGen): The Open-Source AgentOS"）——旧教程指向 microsoft/autogen 的部分请对照本仓库。
- **一句话学习价值**：AutoGen 血统的多 Agent 对话框架，把「谁下一个发言」（next-speaker selection）、组内 Handoff、带代码执行工具的双 Agent 协作做成了可直接配置的运行时。
- **最适合演示**：E 多 Agent 协作（E11 群聊与发言者选择、E9 handoff、E8 消息传递、E10 共享状态）。
- **难度**：进阶（群聊调度逻辑分支多）。
- **开场提示词**：

```text
我在精读 ag2 来学习多 Agent 群聊编排。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 核心抽象：ConversableAgent / GroupChat / GroupChatManager / Handoff 各自定义在哪里；
3) 端到端追踪：一次双 agent 对话轮——消息发出 → next-speaker 如何决定 → 被选中 agent 的 reply 生成（含一次工具/代码执行）→ 回到调度，标注每一步的 file:line；
4) 找出 handoff（控制权转移）与注册自定义 agent 的实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 10. crewAIInc/crewAI —— 角色分工编排的最短入门路径

- **核实**：Python，60,041★，最后推送 2026-10-24，活跃维护 ✅
- **一句话学习价值**：以「Crew（团队）/ Agent（角色）/ Task（任务）/ Process（流程）」四个概念组织多 Agent 协作，API 表面积小、心智负担低，是最快的多 Agent 框架入门实现，适合与 langgraph 的图模型对照出「声明式 vs 图式」两种风格。
- **最适合演示**：E 多 Agent 协作（E4 supervisor/角色分工、E12 结果汇总、E5 planner–executor 的轻量版）。
- **难度**：入门。
- **开场提示词**：

```text
我在精读 crewai 来学习角色式多 Agent 编排。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 核心抽象：Crew/Agent/Task/Process 的定义位置与相互关系；
3) 端到端追踪：crew.kickoff() 之后——流程（sequential/hierarchical）如何调度 Task → Agent 的 role/goal/backstory 如何拼进 prompt → 工具调用 → 任务结果如何传给下一个 Task → 全部完成的判定，标注每一步的 file:line；
4) 指出 hierarchical 模式下 manager 的实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 11. huggingface/smolagents —— CodeAct 的最小可读实现

- **核实**：Python，30,017★，最后推送 2026-10-22，活跃维护 ✅（`src/smolagents/` 下 agents.py / tools.py / memory.py / local_python_executor.py 等单文件组织，精读友好）
- **一句话学习价值**：「以代码为行动」（CodeAct：让模型写一段 Python 调用工具，而不是一个个 JSON tool call）的最小完整实现，整个库小到一个下午能读完，却覆盖了 agent、工具、记忆、本地 Python 沙箱执行、MCP client 的全链路。
- **最适合演示**：A 核心循环（CodeAct 变体的 ReAct 循环）+ C 工具系统（C13 CodeAct 的执行与回喂、C1 从函数签名生成 schema、C7 MCP client、C9 工具检索）。
- **难度**：入门（全库代码量最小，建议作为第一个精读的仓库）。
- **开场提示词**：

```text
我在精读 smolagents 来学习 CodeAct 式 agent。请先给我整体架构：
1) src/smolagents 下每个文件的职责一句话；
2) 核心抽象：CodeAgent/ToolCallAgent/Tool 的继承关系与定义位置；
3) 端到端追踪：一次 agent.run() ——system prompt 组装（含工具注入方式）→ 模型生成 thought+code → 本地 Python executor 沙箱执行 → observation 截断与回填 → 循环终止条件，标注每一步的 file:line；
4) 找出工具 schema 如何从 Python 函数签名自动生成，以及 MCP 工具如何被导入。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 12. pydantic/pydantic-ai —— 类型驱动的工具定义与输出校验

- **核实**：Python，20,823★，最后推送 2026-10-24，活跃维护 ✅
- **一句话学习价值**：把 Pydantic 的类型系统用到 Agent 的两个薄弱环节——工具参数 schema 从类型注解直接生成、结构化输出经校验失败自动重试——是「schema 优先」设计哲学最干净的参考实现。
- **最适合演示**：C 工具系统（C1 工具定义 Schema、C5 参数校验错误回喂）+ G6（结构化输出校验与再生成）。
- **难度**：入门（API 面小，类型注解自文档化）。
- **开场提示词**：

```text
我在精读 pydantic-ai 来学习类型驱动的 agent 设计。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 核心抽象：Agent/BaseTool/RunResult 的定义位置；
3) 端到端追踪：一次 agent.run() ——工具如何从 Python 函数（含类型注解）生成 schema 并注入请求 → 模型返回工具调用 → 参数经 pydantic 校验 → 执行回填 → 结构化输出（output_type）校验失败时的重试/修复路径，标注每一步的 file:line；
4) 指出 result_validator 与输出校验重试的实现位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

### 三、专项最佳示范

#### 13. letta-ai/letta-code —— 分层记忆（MemGPT 血统）的现代实现

- **核实**：TypeScript，3,697★，最后推送 2026-10-24，活跃维护 ✅。注意：`letta-ai/letta` 主仓库现在只剩文档（README 明确指向本仓库），经典 MemGPT/Letta V1 的 Python API server 已归档到 `letta-ai/letta` 的 `archive` 分支（只读参考，不要按它理解当前实现）。
- **一句话学习价值**：MemGPT「把 LLM 当操作系统、上下文当内存分页」思想的延续者，现在的形态是一个带持久记忆的编码 Agent：core / recall / archival 分层记忆、记忆自编辑、sleep-time 整理——速查表 D10「分层记忆架构」与 D9「MemGPT 式上下文分页」的对应实现。
- **最适合演示**：D 记忆系统（D10 分层记忆、D5 数据库持久层、D6 写入决策与淘汰、D12 记忆与上下文工程的边界）。
- **难度**：进阶（记忆分层与调度概念多；想先看思想源头可读 archive 分支的 MemGPT 论文实现）。
- **开场提示词**：

```text
我在精读 letta-code 来学习分层记忆。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 记忆模型：core / recall / archival 三层各自的存储位置、数据结构与写入时机；
3) 端到端追踪：一条用户消息进入 → 记忆如何被检索并注入上下文 → agent 回复后记忆如何分层写入（含自编辑与 sleep-time 整理，若有），标注每一步的 file:line；
4) 指出记忆块（memory block）与消息历史的边界在哪里实现。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

#### 14. mem0ai/mem0 —— 自动记忆抽取与写入门控的标杆

- **核实**：Python，67,714★，最后推送 2026-10-23，活跃维护 ✅
- **一句话学习价值**：把「从对话中自动抽取事实、决定 ADD/UPDATE/DELETE/NOOP、再按语义检索回来」做成了独立基础设施——速查表 D4「自动记忆」、D6「写入决策与淘汰策略」、D8「向量检索」三个知识点的工业级对照实现。
- **最适合演示**：D 记忆系统（D4 自动记忆、D6 写入决策、D8 embedding 检索）。
- **难度**：入门（核心 add/search 路径短，其余是集成适配层）。
- **开场提示词**：

```text
我在精读 mem0 来学习自动记忆抽取。请先给我整体架构：
1) 顶层模块划分：每个模块一句话职责；
2) 核心抽象：Memory/add/search 主链路的类与文件位置；
3) 端到端追踪：一次 memory.add() ——对话事实抽取（抽取 prompt 在哪）→ 与已有记忆比对 → ADD/UPDATE/DELETE/NOOP 决策如何产生并执行 → 向量库写入；随后一次 search() 的 embedding 检索与重排路径，标注每一步的 file:line；
4) 指出抽取与更新决策所用的 prompt 模板位置。
所有结论必须引用具体 file:line；找不到的就说找不到，不要猜。
```

### 四、建议学习顺序

按「先看懂一个最小循环 → 再看生产级 CLI → 然后上编排 → 最后攻记忆与专项」的依赖关系排。条目名后的 # 编号对应上方总览表与正文条目编号：

**阶段一 · 最小循环（1-2 周）——先建立「Agent 就是一个循环」的手感**

1. **smolagents**（#11）：代码量最小，CodeAct 循环 + 工具 + 本地沙箱一次看全。关注：thought→code→observation 的交替、工具 schema 自动生成。
2. **SWE-agent**（#3）：换一个流派（受限工具集 + 编辑-验证循环）。关注：ACI 设计——为什么工具少而精。
3. **pydantic-ai**（#12）：补上类型/schema 这条腿。关注：校验失败→错误回喂→再生成。

**阶段二 · 生产级编码 Agent CLI（2-3 周）——看工业品加了哪些「必要的复杂」**

4. **cline**（#4，TS 读者从它进）或 **gemini-cli**（#6）：交互与审批、配置分层、MCP、压缩。关注：权限门控、diff 审批、compaction 触发。
5. **openai/codex**（#1）：Rust 生产级循环。关注：流式解析、session/rollout 持久化、中断恢复、预算上限。
6. **aaif-goose/goose**（#5）：MCP 作为扩展机制。关注：工具注册/发现/生命周期/超时隔离。
7. **Aider-AI/aider**（#7）：算法专场。关注：repo map 的排序与预算裁剪、edit format 家族的取舍（注意其维护放缓，读算法不追新功能）。
8. **OpenHands/software-agent-sdk**（#2）：事件流架构。关注：与「隐式循环」「显式图」的对照——事件溯源如何天然获得回放与恢复。

**阶段三 · 多 Agent 编排（2 周）——比较三种组织范式**

9. **crewai**（#10）：声明式角色分工（最易上手）。关注：Task 间结果传递、hierarchical manager。
10. **ag2ai/ag2**（#9）：对话式群聊。关注：next-speaker 选择、handoff。
11. **langgraph**（#8）：显式图 + checkpoint。关注：状态 reducer、interrupt/human-in-the-loop、时间旅行。

**阶段四 · 记忆与专项收尾（1-2 周）**

12. **mem0**（#14）：自动记忆抽取。关注：ADD/UPDATE 决策 prompt、检索链路。
13. **letta-code**（#13）：分层记忆天花板。关注：core/recall/archival 分页、sleep-time 整理。
14. 收尾作业：回到速查表，任选一个知识点（如 B7 compaction）在 codex / gemini-cli / aider 三处各问一遍同一提示词，对比三家的实现取舍——这是把「读过」变成「懂了」的最后一步。

### 五、落选与迁移说明（核实记录）

- **microsoft/autogen**：不推荐直接精读——其仓库 2026-10-16 最新 commit 明确声明「AutoGen is archived and no longer maintained」（GitHub `archived` 标志虽仍为 false，但维护方已官宣停更）；活跃开发在 **ag2ai/ag2**（见第 9 条）。
- **All-Hands-AI/OpenHands**：GitHub API 重定向显示现名 **OpenHands/OpenHands**；v1 重写后该仓库是 TypeScript 的 Agent Canvas 产品壳，Agent 本体 Python 代码在 **OpenHands/software-agent-sdk**（见第 2 条）。
- **block/goose** → **aaif-goose/goose**：已捐给 Linux 基金会 Agentic AI Foundation（AAIF），旧地址会重定向。
- **letta-ai/letta**：主仓库只剩 README/政策文档，活跃源码在 **letta-ai/letta-code**；经典 MemGPT Python 实现在其 `archive` 分支。
- **FoundationAgents/MetaGPT**：最后推送 2026-01-21（截至核实日已约 9 个月无提交），不满足「仍在维护」标准，未收录。
- **openai/swarm**：教学性实验仓库，官方已被 openai-agents-python 方向取代（swarm 最后推送 2026-04，仓库自述 educational），未收录。
- **Aider-AI/aider**：维护明显放缓（最后推送 2026-05-22、最后 release 2025-08-09），因其 repo map / edit format 是速查表对应知识点的公认源头实现而保留收录，并在条目内如实标注。
