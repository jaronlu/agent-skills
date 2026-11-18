# 仓库规则

本文件记录 `agent-skills` 的强制约定。`CONTRIBUTING.md` 描述技能包契约，本文件描述仓库级规则。
两者冲突时，以本文件为准。

## 规则一：每个 skill 必须有主 SVG 流程图

**适用范围**：`skills/` 下的每一个技能。

**判定标准**：每个 `skills/<skill-name>/` 必须有一张主流程图 `assets/<skill-name>-flow.svg`。
同一技能确需更多图时，额外图命名为 `assets/<skill-name>-<topic>-flow.svg`，但主图仍必须有。

新增技能未配主流程图，视为未完成；改动了 `SKILL.md` 的工作流、分支或停止条件，必须同步改图。

### 存放位置

所有技能流程图都放在**仓库根目录的 `assets/`**。技能包内部的 `assets/` 只放输出资源
（模板、媒体或复制到交付物中的内容），不放流程图。

理由：

- 流程图是给人看的仓库文档，不是技能运行时产物。
- 技能包按仓库配置链接到用户级共享技能目录，保持运行时包小巧可预测。
- 根目录 `assets/` 已在 `README.md` / `README_zh-CN.md` 中以链接清单形式对外暴露。

### 命名

```text
assets/<skill-name>-flow.svg          # 必需：主流程图
assets/<skill-name>-<topic>-flow.svg  # 可选：同一技能的额外主题图
```

文件名前缀必须与技能目录名完全一致，且所有技能流程图都以 `-flow.svg` 结尾。
仓库级说明图 `assets/repository-overview.svg` 不属于任何技能，不受本规则约束。

### 内容要求

画**决策路径**，不要复述 `SKILL.md`。一张合格的流程图必须包含：

1. **入口**：技能被触发的起点。
2. **主流程主干**：按顺序编号的步骤（①②③…）。
3. **分支**：条件分叉与各自的走向（`references/` 路由、模式选择、A/B 判定等）。
4. **停止条件**：明确的终止、阻断或上报节点。
5. **出口**：最终交付物或判定输出。

不要画成目录树或概念图；不要把所有 `references/` 细节塞进一张图，细节留在图外的引用文件里。

### 视觉规范

沿用现有流程图的样式，新增图必须一致：

| 项 | 约定 |
| --- | --- |
| 画布 | `viewBox="0 0 680 <height>"`，`width="680"`，高度按内容取 |
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

无障碍：根元素带 `role="img"`，并有非空的 `<title>` 与 `<desc>`。

### 文本安全边界

SVG 不做自动换行，超长文本会被裁掉。硬性要求：

- 单行在 12px 下，中文按 12px/字、ASCII 按 6.6px/字估算；文本右端必须留在所属框右边界内缩
  8px 以内（`x="40"`、宽 600 的框即不超过 x=632）。
- 超长说明拆成多行，并相应增加所在框高（每加一行 +18，框高 +18，后续元素整体下移）。
- 分组框内的小框文字必须能在框宽内居中放下；放不下就拆行或缩短，不要缩小字号硬塞。

### 自动校验

`python3 scripts/validate_skills.py`（需要 Python 3.11+ 或安装 `tomli`）会检查：

- 每个技能都存在主流程图 `assets/<skill-name>-flow.svg`，根目录 SVG 命名合法（额外主题图按命名规则，仓库总览图除外）。
- 流程图根元素满足 `width="680"`、`viewBox="0 0 680 <height>"`、`role="img"`，且
  `<title>` 与 `<desc>` 非空。
- 文本落在所属框内：右侧留 8px，底部按 0.4em 下沿计算（12px 字约 4.8px）。
- 没有框归属的文本不得越出画布（右侧 40px 边距，底部同样保留）。
- 框高不足时报告溢出像素数。修法是加高该框，并把下方元素整体下移，不要缩小字号。
- `README.md` 与 `README_zh-CN.md` 都列出每个技能和每一张根目录图。

### 提交前自检

```bash
python3 scripts/validate_skills.py
```

并人工确认：

1. SVG 能被浏览器直接打开，无语法错误。
2. 自动校验通过（没有报出命名、尺寸、无障碍或文字溢出问题）。
3. `README.md` 与 `README_zh-CN.md` 的流程图清单已列出该图。
4. `CHANGELOG.md` → `[未发布]` 已记录。

## 规则二：skill 必须显式登记到每个分发目标

技能不会自动同步。`config/skill-links.toml` 用 `[profiles.*]` 描述分发集合，`[targets.*]`
只引用 profile。每个目标解析后的 `skills` 与 `excluded` 必须覆盖 `skills/` 下的全部技能；
profile 可用 `extends` 继承父 profile，子 profile 的 `skills` 把父级的排除项提升为安装，
`excluded` 把父级的安装项降为排除。新增技能时，必须在相关 profile 中明确决定安装或排除。

- 至少保留 `[targets.agents]`，它是默认共享目录（默认 `~/.agents/skills`）。
- 共享目录是本仓库的分发终点；不要登记已不再使用的中间分发服务。
- 默认使用 `mode = "symlink"`，共享目录中的条目指向仓库，仓库内容改动即时生效；移动或重命名仓库后需重新 `sync`。
- 改动 `skills/` 或 `config/skill-links.toml` 后必须重新 `sync`，变更才会进入共享目录。
- 改完先 `python3 scripts/manage_skill_links.py sync --dry-run`，确认无误再 `sync`；
  用 `check` 校验受管理链接是否指向本仓库。该脚本需要 Python 3.11+（或安装 `tomli`）。
- 未在配置中出现的条目不会被处理；第三方技能、用户自建条目一律不碰。

## 当前流程图清单

| 技能 | 主流程图 |
| --- | --- |
| agent-gitignore | `assets/agent-gitignore-flow.svg` |
| chinese-text-fixer | `assets/chinese-text-fixer-flow.svg` |
| chrome-bookmarks | `assets/chrome-bookmarks-flow.svg` |
| communication-formulas | `assets/communication-formulas-flow.svg` |
| design-convergence-review | `assets/design-convergence-review-flow.svg` |
| first-principles | `assets/first-principles-flow.svg` |
| five-dimension-analysis | `assets/five-dimension-analysis-flow.svg` |
| git-commit | `assets/git-commit-flow.svg` |
| hermes-context-review | `assets/hermes-context-review-flow.svg` |
| human-readable-codebook | `assets/human-readable-codebook-flow.svg` |
| llm-wiki | `assets/llm-wiki-flow.svg` |
| prompt-optimizer | `assets/prompt-optimizer-flow.svg` |

仓库级说明图：`assets/repository-overview.svg`（不属于任何技能）。
