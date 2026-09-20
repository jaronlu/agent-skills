# 更新日志

所有值得注意的变更都将记录在此文件中。

本文件格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
项目遵循 [语义化版本控制](https://semver.org/spec/v2.0.0.html)。

## [未发布]

### 新增

- `chrome-bookmarks` 技能：通用 Chrome 书签整理（分类、去冗余、归档精简），用户自带的分类树优先，仅在浏览器完全退出后写回；附流程图并登记 CC Switch 分发
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
- `chrome-bookmarks` 的 `references/schema.md`：Bookmarks 文档结构（节点字段、`id`/`guid` 规则、1601 起微秒时间戳、
  写后校验方式），作为改动 Bookmarks 文件前的单一参考
- `chrome-bookmarks` 脚本新增 `diff` 子命令：`--old` / `--new` 输出 kept / added / removed / moved / renamed 与顶层变化，
  与 `inspect` 新增的 `top_level_folders=` 一起支撑写回前的交叉核对

### 变更

- `git-commit` 跨模块同一意图改为 subject 加每模块一行 `- scope: desc`；流程图补上该产出、修好被下一框盖住的连接箭头
- `git-commit` 流程图压缩判定步骤，把版面留给使用后结果：8 个 type 的消息示例、跨模块 `&`、breaking footer，以及 commit mode 的 hash + 保留未提交路径
- `git-commit` 流程图对齐精简后的单文件技能：去掉已删除 reference 的步骤（`git ls-files`、默认规则文件、生成噪声/纯二进制专章），补上同一文件混意图则暂停
- `git-commit` 流程图从根目录 `assets/` 挪到 `skills/git-commit/README.md`（图文件在技能包 `assets/`）；根目录 README 改为指向该文档
- `git-commit` 收成单文件：删除 `references/` 下四份参考，`SKILL.md` 压到 500 词以内；同一文件混有多个意图时停下询问，不再教 hunk 分阶。契约测试改为入口预算与短保证，流程图去掉 reference 路由
- `chrome-bookmarks` 用户方案只覆盖文件夹名和树形；每次 Organize 仍用 `<area>·<slug>`（company / platform / topic，子集优先），除非用户另给命名规则。域名与 `dev` 平台建层统一为 4 条；`emit` 拒绝超过三层的 path；同步契约测试与流程图
- `chrome-bookmarks` 默认顶层文件夹保持英文（`work` / `study` / …），不因用户使用中文就翻译成 `工作` / `学习`；用户自定方案仍优先
- `chrome-bookmarks` 将 SKILL.md 收敛为模式、常驻契约、安全边界与输出；定位配置、归档、Inspect / Organize / Writeback / Restore 步骤下沉到 `references/workflow.md`
- `chrome-bookmarks` 整理改为代理写 plan、脚本 `emit` 装配 Bookmarks 文档（分配 `id`/`guid`/时间戳、保留原顶层键与 `other`/`synced`、写出 `manifest.json`）；默认归档根为 `~/ChromeBookmarksArchive/<YYYY-MM-DD>_<profile>/`；Organize 在 Chrome 仍运行时也可进行，默认停在写回确认之前；Restore 优先 `Bookmarks.raw`，`Bookmarks.bak` 仅在 Chrome 尚未再次保存时可用
- `chrome-bookmarks` 增加"顶层未变"闸门与可复用方案记录：归类前对比目标顶层与现有顶层，两者一致时报告首行必须标注
  「顶层未变，仅内部调整」并单独确认，交付报告改为顶层 新增 / 删除 / 未变 三态；归档目录固定为 `<date>_<profile>`，
  同目录写 `manifest.json`（方案名、顶层列表、保留/移动/删除计数、产物哈希），下一轮直接复用已确认方案而不是重新推断
- `chrome-bookmarks` 分类规则补齐三处歧义：兜底桶（`归档`/`Misc`）用户已有则永不为空删除、没有则不新造；
  `company·slug` 只用于产品/站点/仓库叶子，个人文档、政务页与内网系统保留原名；三层深度给出
  `AI / Agent / 官方文档 / leaf` 的合法示例
- `chrome-bookmarks` 采用通用分类与清理规则：用户自带的分类树、同站上限与仓库质量门槛永远优先，也不为没有的分类建空文件夹；默认模式为
  `work / study / ai（agent、relay）/ dev / tools / chore / misc` 并给出判定顺序 `work → study → ai → dev → tools → chore → misc`，
  文件夹最深三层，书签 leaf 统一命名为 `<company>·<slug>`，域名仅在保有 4 条以上时单独建层；清理以原则表述
  （同站去重、官方源与仓库根优先、控制台与会话链接丢弃），不假定任何站点清单或数量阈值；同步更新流程图与契约测试
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

- `chrome-bookmarks` 对齐 Organize 契约：用户方案只覆盖分类树，无方案才读 taxonomy，cleanup 每次整理都应用；`description` 补上写回与同步覆盖恢复；`last_used` 缺失时拒绝并要求 `--profile`，不再静默回退 `Default`；`Bookmarks.raw` 只在缺失时拷贝、禁止覆盖，整理始终读 live；`diff`/`manifest` 报告 `other`/`synced` 计数；`--assume-quit` 不能覆盖「正在运行」；流程图为 Writeback 增加旁路
- `chrome-bookmarks` 统一 `other`/`synced` 契约：写回不再默认清空；`emit` 默认原样保留；将归零时 `write` 在写盘前拒绝，需用户确认后才可 `--allow-empty-roots`
- `chrome-bookmarks` Linux 进程探测补上 `chrome` / `google-chrome` 精确进程名，继续排除其它 Electron 的 `chrome_crashpad_handler`；同步流程图（Inspect 出口、Organize 可开着跑、默认停在 emit、Restore 走写回闸门）
- `chrome-bookmarks` 修复写回链路：`--user-data` / `--profile` 现在放在子命令前后都能解析（此前 `references/writeback.md`
  里的命令会直接报 `unrecognized arguments`）；写回前校验 prepared 是否为完整 Chrome Bookmarks 文档（缺 `roots.bookmark_bar`
  直接拒绝）、用临时文件 + `os.replace` 原子替换 `Bookmarks`、把旧文件留在 `Bookmarks.bak` 作回滚副本，写后回读并输出
  顶层文件夹与 `warning:` 行（其他书签/移动设备书签归零、书签栏存在散落 URL、旧文件无法比对）
- `chrome-bookmarks` 的 `inspect` 覆盖 `bookmark_bar` / `other` / `synced` 三个 root，不再漏报其他书签与移动设备书签；
  `SKILL.md` 相应要求归类时展开全部 root，并在 `other` / `synced` 非空时先请用户确认清空
- `chrome-bookmarks` 明确数据边界：分类与清理默认值全部可被用户覆盖，并禁止把书签数据、归档目录与 prepared 树写进
  技能包或仓库
- `chrome-bookmarks` 解除 macOS 绑定：默认 user-data 目录按 darwin / win32 / linux 解析（Chromium 等其它安装用
  `--user-data` 指定），进程检测改为 POSIX 上探测 `pgrep`/`ps`、Windows 上探测 `tasklist`；所有探测都不可用时
  默认拒绝写回（fail closed），只有用户确认后才可用 `--assume-quit` 放行
- `git-commit` 修复规则发现在 message mode 失效的回归：`references/workflow.md` 的路由改为
  "commit mode，或任何需要读取 diff 的 message mode"，并在 `SKILL.md` 增加常驻的 Repository Rules
  章节；同时补齐未跟踪规则文件与 monorepo 上层目录这两类漏检来源
- `git-commit` 消除语言规则冲突：`SKILL.md` 的 "English imperative" 与 `default-rules.md` 的
  "沿用用户语言"合并为一条规则（默认英文，用户或仓库明显使用其他语言时整轮沿用）
- `git-commit` 的 `commit-execution.md` 增加进行中 merge / rebase / cherry-pick 的前置检查，
  并给出基于补丁的非交互 hunk 暂存路径，取代会让非交互运行挂起的 `git add -p` / `git reset -p`
- `git-commit` 补齐流程图缺失的"无相关改动 → 停止"出口与 porcelain 示例（`A `、`AM`、`D `、`R `），
  并把 `openai.yaml` 与两份 README 的对外文案从"只提交已暂存"改为"选定改动拆成原子提交"
- `chrome-bookmarks` 修复进程探测误判：`ps` 回退分支此前把任何含 `chrome` 的进程都算作 Chrome，VS Code 等
  Electron 应用自带的 `chrome_crashpad_handler` 会让写回被无理由拒绝；现只匹配 `Google Chrome` / `Chromium`
  本体与其 Helper，并在 `SKILL.md`、`references/writeback.md` 明确"探测可疑时用 `pgrep -fl` 复核并报告，
  禁止改守护逻辑放行"
- `chrome-bookmarks` 写回前置条件不再假定 `sync_metadata` 必存（Chrome 会自行增删该键），改为"保留原文档全部顶层键
  与 `other` / `synced`，只替换 `roots.bookmark_bar`"；`references/writeback.md` 补充回滚章节，说明 Chrome 保存后会
  重写 `id` / `checksum`，应按结构与计数核对而非比对哈希

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
