# 更新日志

所有值得注意的变更都将记录在此文件中。

本文件格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
项目遵循 [语义化版本控制](https://semver.org/spec/v2.0.0.html)。

## [未发布]

### 新增

- `paper-learning` 技能（由 `rsi-paper` 重构更名）：通用论文学习流程——识别论文、抓取通读、按 `references/paper-template.md` 蒸馏为工作区 `papers/<slug>.md`（笔记是产出物，不放技能包内）、按问题类型路由回答；demo 可选且语言随论文生态，无意义的论文明确记 "no demo"。首篇产出 `papers/rsi-2609-11873.md` + `papers/rsi-2609-11873_demo.py`（原 RSI 论文内容，arXiv:2609.11873），附通用流程图并登记 CC Switch 分发
- 仓库规则文件 `RULES.md`：规定每个技能必须配一张 SVG 流程图，并明确存放位置、命名、配色与文本安全边界
- 剩余五个技能的流程图：`git-commit`、`design-convergence-review`、`first-principles`、`hermes-context-review`、`llm-wiki`
- `git-commit` 加入 WorkBuddy 分发目标
- 可配置的增量符号链接分发，支持 Codex、Claude 和 Hermes
- 文件系统测试：路径重定位、去重、冲突、修剪与幂等性
- 设计一致性评审技能，支持单文档和多文档设计文件夹
- 第一性原理分析技能，覆盖决策、诊断和沟通任务
- Git 提交技能，支持提交消息生成与受控提交执行
- llm-wiki 技能，支持本地 Wiki 的检索、验证和维护
- Hermes 长期上下文审查技能，检查规则、记忆、配置与项目上下文的一致性
- 仓库架构契约、技能包验证器和 GitHub Actions 验证工作流
- 五维分析技能（史/经/政/军/哲），产出可证伪判断与可执行动作
- 沟通公式技能，按沟通目的选用 SCQA、FAB、BACC、3W、PREP 五套表达顺序
- WorkBuddy 分发目标，并随仓库附带两张技能流程图

### 变更

- `paper-learning` 精简重复质量规则与逐篇回答路由，合并笔记模板；按问题覆盖度和论文版本复用笔记（arXiv 按 id + `vN`/日期与笔记 Source 核对），补充来源定位与证据缺口，已请求的资料核验无需重复确认；明确 demo 不等于结果复现并同步流程图；局限段增加新颖性/证据力度/可复现性提示，示例笔记扩为两篇（论证型 + 实验型，关键数字逐一对照对应 arXiv 版本核实），并加入填好的示例笔记；工作区 RSI 笔记改对齐新模板、修正 demo 路径
- hermes-context-review 精简入口，将取证、运行时加载与分发、记忆计数细节下沉至 references；修正缺省配置误报、固定限额与 home AGENTS 加载表述，明确证据缺口及 verdict，并同步流程图与契约测试
- 修复六张流程图的文字溢出：`first-principles`、`git-commit`、`hermes-context-review`、`llm-wiki` 中框高不足的方框按实际行数补足高度并把后续元素整体下移；`five-dimension-analysis`、`design-convergence-review` 的超宽文本改为收窄措辞或加宽所属框。`validate_skills.py` 新增几何校验（文字必须落在所属框内、无框文本不得越出画布），把 RULES.md 的文本安全边界从人工自检变成可执行检查，并补充 6 个回归测试
- README 的流程图改为直接嵌入 SVG（原来是文字链接），顺序与技能表对齐，点击可打开原图，
  并补上每张图的一句话说明
- 分发收敛到 CC Switch：`config/skill-links.toml` 只保留 `[targets.cc-switch]`（`~/.agents/skills`），
  删除 codex / claude / hermes / zcode / workbuddy 五个 per-tool 目标；链接管理器新增 `mode = "copy"`
  发布模式（库中保存真实目录，按内容比对实现幂等与"落后检测"），`distribution.source` 改为可省略并
  默认取仓库根目录，避免仓库移动后残留失效路径
- git-commit 将 SKILL.md 收敛为常驻契约（消息契约、提交范围 A/B 判定、安全边界、输出与引用路由），取证与切分步骤移入 `references/workflow.md`，`default-rules.md` 只保留契约留白的默认决策，并新增"每个引用都必须由 SKILL.md 直接链接"的契约测试
- git-commit 合并 Message Contract 的精简方案：scope 改为必填且必须指向真实模块，单一意图跨模块用 `&` 连接（`feat(common&share&tool): ...`）并在正文按模块分行，一次运行内所有消息强制同语种且不翻译标识符；其中保留 diff 取证、仓库规则发现、原子切分与提交后验证的工作流主线
- git-commit 契约测试改为断言稳定契约片段而非整句散文，并补充 porcelain `XY` 列规则的回归测试
- llm-wiki 修正默认 layout 在三处文档中的不一致：真值收敛到 `scripts/_wiki_common.py`，`SKILL.md` 与检索参考不再复述默认 glob，并补充文档与脚本常量的一致性测试
- llm-wiki 在 `SKILL.md` 中指向 `assets/examples.llm-wiki.json`，并补充 `SKILL_DIR` 解析失败时的定位方式
- hermes-context-review 将本机个人 home 约定标记为非契约的观察内容，缺失不再作为发现项；参考文件补充来源复检提示
- design-convergence-review 将报告骨架、评分分档表与发现质量基准移入 `references/report-format.md`，减少常驻上下文
- first-principles 收紧触发条件，排除常规实现选型与代码级调试；三个任务参考补充正反校准示例
- 将仓库重新定位为 `agent-skills`，作为自我维护的技能源和分发基础
- 将面向用户的项目文档移至 llm-wiki workshop，并通过 `docs` 暴露
- 将每个技能包统一为 `SKILL.md`、`agents/openai.yaml` 和可选的 `references/`、`scripts/`、`assets/`
- 将面向用户的技能指南从运行时包移至 `docs/skills/`
- 将模板和代理可读示例移至其正确的资源目录
- 定位从"个人公司"转变为"AI 增强的独立开发者"
- 更新理念以强调 AI 下的 10 倍生产力
- 通过 AI 优先方法增强价值主张

### 修复

- `git-commit` 修复规则发现在 message mode 失效的回归：`references/workflow.md` 的路由改为
  "commit mode，或任何需要读取 diff 的 message mode"，并在 `SKILL.md` 增加常驻的 Repository Rules
  章节；同时补齐未跟踪规则文件与 monorepo 上层目录这两类漏检来源
- `git-commit` 消除语言规则冲突：`SKILL.md` 的 "English imperative" 与 `default-rules.md` 的
  "沿用用户语言"合并为一条规则（默认英文，用户或仓库明显使用其他语言时整轮沿用）
- `git-commit` 的 `commit-execution.md` 增加进行中 merge / rebase / cherry-pick 的前置检查，
  并给出基于补丁的非交互 hunk 暂存路径，取代会让非交互运行挂起的 `git add -p` / `git reset -p`
- `git-commit` 补齐流程图缺失的"无相关改动 → 停止"出口与 porcelain 示例（`A `、`AM`、`D `、`R `），
  并把 `openai.yaml` 与两份 README 的对外文案从"只提交已暂存"改为"选定改动拆成原子提交"

### 移除

- 移除了低价值、过于通用或已过时的技能：`a-share-value-investing`、`thinking-toolkit`、`github-actions`、`governance-layer-review`、`indie-hacker-methodology` 和 `zshrc-secrets`

## [1.0.0] - 2026-03-05

### 新增

- 初始仓库结构
- 独立开发者方法论技能
- 核心文档（理念、最佳实践）
- 贡献指南
- MIT 许可证
- 项目概述 README

### 文档

- OPC 理念深度解析
- 独立开发者的最佳实践
- 技能开发指南
