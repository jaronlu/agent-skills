# 仓库规则

本文件记录 `agent-skills` 的强制约定。`CONTRIBUTING.md` 描述技能包契约，本文件描述仓库级规则。
两者冲突时，以本文件为准。

## 规则一：每个 skill 必须有且仅有一张 SVG 流程图

**适用范围**：`skills/` 下的每一个技能。没有例外。

**判定标准**：`skills/<skill-name>/` 存在 ⟺ 对应流程图存在。默认文件是 `assets/<skill-name>-flow.svg`（或 `assets/<skill-name>-<topic>.svg`）。`git-commit` 的图改由技能包 README 承载，文件是 `skills/git-commit/assets/git-commit-flow.svg`。
新增技能未配流程图，视为未完成；改动了 `SKILL.md` 的工作流、分支或停止条件，必须同步改图。

### 存放位置

默认放在**仓库根目录的 `assets/`**。`git-commit` 例外：图放在 `skills/git-commit/assets/`，由 `skills/git-commit/README.md` 引用，不放进根目录 `assets/`。

理由：

- 流程图是给人看的仓库文档，不是技能运行时产物。`CONTRIBUTING.md` 已限定技能包内 `assets/`
  只放「复制到输出中的内容」或 README 引用的人读图。
- 技能包经符号链接分发到 `~/.codex/skills` 等目录，保持运行时包小巧可预测。
- 根目录 `assets/` 已在 `README.md` / `README_zh-CN.md` 中以链接清单形式对外暴露；`git-commit` 的清单项指向其 README。

### 命名

```text
assets/<skill-name>-flow.svg          # 默认：一张图覆盖主流程
assets/<skill-name>-<topic>.svg       # 例外：同一技能确需多张图
```

文件名前缀必须与技能目录名完全一致。当前 `communication-formulas-routing.svg` 属历史命名，
保留不动，新增图一律用 `-flow.svg`。

### 内容要求

画**决策路径**，不要复述 `SKILL.md`。一张合格的流程图必须包含：

1. **入口**：技能被触发的起点。
2. **主流程主干**：按顺序编号的步骤（①②③…）。
3. **分支**：条件分叉与各自的走向（`references/` 路由、模式选择、A/B 判定等）。
4. **停止条件**：明确的终止、阻断或上报节点。
5. **出口**：最终交付物或判定输出。

不要画成目录树或概念图；不要把所有 `references/` 细节塞进一张图，细节留在图外的引用文件里。

### 视觉规范

沿用现有七张图的样式，新增图必须一致：

| 项 | 约定 |
| --- | --- |
| 画布 | `viewBox="0 0 680 <height>"`，宽度恒为 680，高度按内容取 |
| 字体 | `font-family="system-ui, -apple-system, sans-serif"` |
| 边距 | 左右各 40，内容宽 600 |
| 标题 | 14px / weight 500 |
| 正文与说明 | 12px |
| 圆角 | 步骤框 `rx="8"`，分组容器 `rx="12"` |
| 描边 | `stroke-width="0.5"` |
| 连线 | `#888780`，`stroke-width="1.5"`，末端用 `#arrow` marker |
| 背景 | `#FFFFFF` |

配色（浅色主题，禁止使用深色底）：

| 语义 | 填充 | 描边 | 文字 |
| --- | --- | --- | --- |
| 普通步骤 / 中性 | `#F1EFE8` | `#5F5E5A` | `#2C2C2A` / `#5F5E5A` |
| 主流程 / 信息 | `#E6F1FB` | `#185FA5` | `#0C447C` / `#185FA5` |
| 判定 / 警示 | `#FAEEDA` | `#854F0B` | `#633806` / `#854F0B` |
| 阻断 / 风险 | `#FCE8E8` | `#A32D2D` | `#822727` / `#A32D2D` |
| 通过 / 产出 | `#EAF3DE` | `#3B6D11` | `#173404` / `#3B6D11` |
| 分组容器 | `fill="none"` | `#B4B2A9` + `stroke-dasharray="4 3"` | — |

无障碍：根元素带 `role="img"`，并有 `<title>` 与 `<desc>`。

### 文本安全边界

SVG 不做自动换行，超长文本会被裁掉。硬性要求：

- 单行在 12px 下，中文按 12px/字、ASCII 按 6.6px/字估算；文本右端必须留在所属框右边界内缩
  8px 以内（`x="40"`、宽 600 的框即不超过 x=632）。原先写作"起点 x=60 时总宽 612"是按 680
  画布算的，与本条边框约束不一致，已按后者统一。
- 超长说明拆成多行，并相应增加所在框高（每加一行 +18，框高 +18，后续元素整体下移）。
- 分组框内的小框文字必须能在框宽内居中放下；放不下就拆行或缩短，不要缩小字号硬塞。

### 自动几何校验

`python3 scripts/validate_skills.py` 会按本节规则检查每张 SVG，不再只靠肉眼：

- 文本必须落在所属框内：右侧留 8px，底部按 0.4em 下沿计算（12px 字约 4.8px）。
- 没有框归属的文本不得越出画布（右侧 40px 边距，底部同样保留）。
- 框高不足时报告溢出像素数。修法是加高该框，并把下方元素整体下移，不要缩小字号。

### 提交前自检

```bash
python3 scripts/validate_skills.py
```

并人工确认：

1. SVG 能被浏览器直接打开，无语法错误。
2. 自动几何校验通过（即上一条命令没有报出文字溢出）。
3. `README.md` 与 `README_zh-CN.md` 的流程图清单已列出该图。
4. `CHANGELOG.md` → `Unreleased` 已记录。

## 规则二：新增 skill 必须发布到 CC Switch 库

技能不会自动分发。新增技能时必须在 `config/skill-links.toml` 的 `[targets.cc-switch]`
中显式加入 `skills` 列表，由 `sync` 发布到 CC Switch 库（`~/.agents/skills`）。

从库到各工具的分发由 CC Switch 负责：它按自身的同步策略（软连接或文件复制）把技能
提供给 Claude Code、Codex、Gemini CLI、Hermes、Zcode、WorkBuddy 等兼容工具。

- 本仓库的发布终点就是 CC Switch 库，不要再登记任何 per-tool 目标。
- 该 target 使用 `mode = "copy"`：库里保存真实目录，而不是指回仓库的软链接，
  这样移动或重命名仓库目录不会让所有下游工具一起失效。
- 改动 `skills/` 后必须重新 `sync`，变更才会进入 CC Switch 库。
- 改完先 `python3 scripts/manage_skill_links.py sync --dry-run`，确认无误再 `sync`。

## 当前流程图清单

| 技能 | 流程图 |
| --- | --- |
| chrome-bookmarks | `assets/chrome-bookmarks-flow.svg` |
| communication-formulas | `assets/communication-formulas-routing.svg` |
| five-dimension-analysis | `assets/five-dimension-analysis-flow.svg` |
| git-commit | `skills/git-commit/assets/git-commit-flow.svg`（见 `skills/git-commit/README.md`） |
| design-convergence-review | `assets/design-convergence-review-flow.svg` |
| first-principles | `assets/first-principles-flow.svg` |
| hermes-context-review | `assets/hermes-context-review-flow.svg` |
| llm-wiki | `assets/llm-wiki-flow.svg` |
