---
name: agent-reading
description: >
  驱动「按知识点逐条向开源 Agent 仓库提问」的源码学习流程（agent source-code
  reading tour）。适用：已 cd 进任意开源 LLM Agent / coding agent / agent 编排框架仓库
  （如 codex、cline、langgraph、smolagents…），想系统搞懂其实现——agentic loop、工具系统、
  上下文压缩、记忆、多 Agent 协作、规划推理、容错、安全权限、交互工程、可观测共 10 域
  114 个知识点，每点附原样可粘贴的提问提示词与 grep 快速信号；想继续上次的学习进度或
  查询学到哪了；想挑选或规划下一个精读的 Agent 仓库（14 个推荐仓库、逐仓开场提示词、
  四阶段学习顺序）。不适用：与 Agent 系统无关的仓库、无学习意图的一次性代码问答或修改
  任务。Use when studying how an open-source AI agent repo is implemented, one
  knowledge point at a time.
metadata:
  version: "1.0"
  source: "llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md"
---

# agent-reading

## 何时用 / 何时不用

- **用**：已 cd 进一个开源 LLM Agent / coding agent / agent 编排框架仓库，想按 10 域 114 个知识点逐条向仓库提问、系统搞懂其实现；或续学上次进度、查询学到哪了；或挑选/规划下一个精读仓库。
- **不用**：与 Agent 系统无关的仓库；无学习意图的一次性代码问答或修改任务。
- **轻量模式**：用户只想要某个知识点的提示词或一次性答案时，不启动全套流程——从对应 domain 文件取出该点提示词原样给出即可，不写进度。

## 术语锚点与称谓对照

- 切片中的「前言」指本 SKILL.md 的「通用追问模板」一节与通用约定；「附录」「文末附录」指 `references/repos.md`。
- 称谓对照（迁移背景详见 repos.md 落选与迁移说明）：OpenHands = `OpenHands/software-agent-sdk`（agent 本体）；ag2 = `ag2ai/ag2`（`microsoft/autogen` 已官宣停更，勿克隆）；goose = `aaif-goose/goose`（原 `block/goose`）；letta = `letta-ai/letta-code`。

## 硬规则

1. 提示词原样粘贴/执行，一次一条，不改写。
2. 答非所问 → 用「通用追问模板」补挖，不改原提示词（源文档证据边界原话）。
3. 回答必须 file:line、找不到要说找不到（已内置于每条提示词）。
4. 进度只写 `~/.agent-reading/`，绝不写进被读仓库，也不写进本 skill 目录。
5. 速查表是「读代码的地图」不是结论——代表实现未逐仓核验、137 条提示词未逐条试跑。

## 主流程（Step 0–7）

**Step 0 · 定位仓库与进度**：在被读仓库内 `git remote get-url origin` → 归一化 slug（去 `.git`、owner 小写；无 remote 用目录名兜底并在文件头标注 approximate）。读 `~/.agent-reading/progress/{owner}__{repo}.md` 与 `INDEX.md`（存在时）。

**Step 1 · 开场（每仓一次）**：读 `references/opening.md`。仓库在 repos.md 总览 14 仓内 → 优先粘该仓逐仓开场提示词（问过开场可跳过 5 问的第 1 问）；清单外仓库 → 直接按序走 5 问。首次完整走此路线建议选 smolagents。

**Step 2 · 选下一个知识点**：从进度 checklist 找未完成点。优先级 = 先扫完 P0（9 点，见下）→ 该仓「最适合演示」域（repos.md 列）→ P1 → P2。用户点名知识点则直接进。

**Step 3 · 原样执行提示词**：从 `references/domain-{a..j}.md` 取该点提示词，按其字面要求对当前仓库执行（定位实现、file:line、按时间顺序讲数据流、点出数据结构与函数名、找不到要说找不到、给 2-3 个追问切入点）。用户说「给我提示词」时原样输出供复制（到 repoprompt 或别的 CLI 复用）。

**Step 4 · 追问深挖**：每点答完，用下方两条追问模板（调用链展开 / 场景替换推演）向深处挖，直到学习者能自己复述该链路（可主动请用户复述并纠错）。

**Step 5 · 记进度**：勾选 + 一行收获（含 file:line）+ 日期；skip 约定见「进度文件约定」。只写 `~/.agent-reading/`。

**Step 6 · 换仓库 / 会话收束**：更新 INDEX.md（最近日期、完成数、收尾作业状态）。换仓库 = cd 进新仓库后回 Step 0：同 remote → 同 slug → 进度延续（多 clone 不分叉）；新仓库 → 新文件、重走 5 问（速查表原规则「每换一个仓库重复这 5 问」）；INDEX 提供跨仓视角。

**Step 7 · 收尾沉淀（可选，用户说「总结 / 收尾这个仓库」时）**：从进度文件聚合草稿总结（已问点 + 每点一行收获、skip 原因、开放线头、收尾作业状态），会话中给出或存 `~/.agent-reading/progress/{slug}-summary.md`；粘贴回 llm-wiki 等笔记系统由用户自行完成。收尾作业（repos.md）：任选一个知识点在 2-3 个已读仓库各问一遍同一提示词、对比取舍——做完后把进度 header 的「收尾作业」置为完成。

## 域导航表

| 域 | 领域 | 点数 | 文件 | 一句话主旨 |
|---|---|---|---|---|
| A | 核心循环与执行模型（Core Loop & Execution Model） | 8 | domain-a.md | 输入→模型→工具→回填→停止的完整控制流与 REPL/headless 等执行形态 |
| B | 上下文工程与 Token 压缩（Context Engineering & Token Compression） | 9 | domain-b.md | 模型每轮真正看到什么：分层组装、预算分配、按需加载、裁剪、摘要续期、缓存复用 |
| C | 工具系统（Tool System & Tool Calling） | 13 | domain-c.md | 结构化意图变成进程内真实副作用：定义、注册、校验、授权、执行、结果回喂 |
| D | 记忆系统（Memory Systems） | 12 | domain-d.md | 一轮 → 一场会话 → 跨会话三个时间尺度的记住、召回与遗忘链路 |
| E | 单 Agent 与多 Agent 协作（Single-Agent & Multi-Agent Orchestration） | 14 | domain-e.md | 控制流与信息流在单 agent 循环、workflow 图编排、自由派生 multi-agent 间的组织 |
| F | 规划与推理（Planning & Reasoning） | 11 | domain-f.md | 动手前想清楚、之中纠偏、之后验证：计划的产生、驻留、驱动与修正 |
| G | 容错与可靠性（Fault Tolerance & Reliability） | 13 | domain-g.md | 对抗网络抖动、限流、畸形输出、崩溃、循环失控——出错后不死、不重复、不吞错 |
| H | 安全与权限（Security & Permissions） | 13 | domain-h.md | 动作在哪被物理限制、谁授权什么动作、谁的话算指令，加密钥、脱敏、审计、fail-closed |
| I | 交互与工程化（Interaction & Engineering） | 9 | domain-i.md | 循环之外把 Agent 变成可交付产品：交互面、diff 审批、配置扩展、自动化出口 |
| J | 可观测与评估（Observability & Evaluation） | 12 | domain-j.md | 跑时看得见（tracing/日志/成本）+ 客观知道变好没有（评测 harness/指标/回归） |

P0 清单（先扫完 9 点）：A1 A2 A8 B1 C1 C2 C4 D1 F4。

## 通用追问模板

两条 verbatim 自源速查表，填入 `{函数名/机制名}`、`{机制}/{场景}` 后原样使用，不改写：

**模板一 · 调用链展开**（把刚才提到的某个函数讲透）：

```text
把我们刚才提到的 {函数名/机制名} 的完整调用链展开：从最上游的调用者开始，逐层列出每一跳的 file:line、每一步参数如何传递与转换、返回值如何被消费；如果存在多条调用路径、递归或异步分支，请分别讲清各自的触发条件；最后用三句话总结这条链路的核心数据结构；引用不到的位置就明说，不要编造。
```

**模板二 · 场景替换推演**（检验自己是否真懂这个设计）：

```text
把我们刚才分析的 {机制} 换到 {场景} 下会怎样：这个机制的哪些前提假设在新场景下不再成立？哪一段代码会最先出问题（引用 file:line）？要让它在新场景下工作，最小改动需要改哪些点？请基于我们已经读过的代码逐条推理，不要凭空猜测，引用不到的位置就明说，不要编造。
```

## 进度文件约定

- **路径**：`~/.agent-reading/progress/{owner}__{repo}.md`；索引 `~/.agent-reading/progress/INDEX.md`。
- **slug 推导**：`git remote get-url origin` → 去 `.git`、owner 小写。无 remote：目录名兜底，文件头标注 approximate。fork/迁移改名：在 INDEX 手工标注别名归一。同仓多 clone：按 remote 归一为同 slug，进度延续。
- **文件格式**：复制 `references/progress-template.md`（文件头 + 114 点 checklist，格式与勾选形态见该文件）。
- **勾选时机**：该点提示词在本仓库被完整问过并得到回答；勾选时附一行收获（含 file:line）与日期。
- **skip**：`｜skip｜ 原因`（如「已掌握」），同样算关闭。
- **收尾作业状态位**：进度 header「收尾作业」= 未做 / 进行中 / 完成（触发与置位见 Step 7）。
- **INDEX.md**：`| 仓库 | slug | 首次 | 最近 | 完成/114 | 开场 | 收尾作业 | 备注 |` 逐仓一行。
- **收尾总结草稿**：默认在会话中给出；用户要求留存时写同目录 `{slug}-summary.md`。
- **写域**：skill 写入始终限于 `~/.agent-reading/`。

## 维护与同步

- 源在 llm-wiki 速查表（本机路径见包根 README）；本 skill 的 references 是带溯源头的 verbatim 切片，内容修订一律改源再同步，skill 侧不改内容。
- 更新 = 跑包根 `extract.sh` → diff 抽验各片首尾行 →（知识点集合有变时）splice checklist 进 progress-template.md → bump `metadata.version` → 按包根 README 替换式重装。
