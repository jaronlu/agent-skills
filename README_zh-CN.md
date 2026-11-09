# Agent Skills

自研 Agent Skill 的统一仓库。技能直接链接到 `~/.agents/skills`，供兼容的 Agent 工具发现。

[English](README.md)

## 是什么

`skills/` 是唯一源码。每个 Skill 都以 `SKILL.md` 为入口，并可按需包含参考资料、脚本和资源。

## 为什么

在本仓库维护技能，并将登记的技能直接同步到 `~/.agents/skills`。目标路径可在
`config/skill-links.toml` 中显式配置；如果本机使用其他共享技能目录，可在该处调整。

## 怎么做

1. 在 `skills/` 中新增或更新 Skill。
2. 在 `config/skill-links.toml` 的 `[targets.agents]` 中登记该 Skill。
3. 先预览变更：

   ```bash
   python3 scripts/manage_skill_links.py sync --dry-run
   ```

4. 确认后同步：

   ```bash
   python3 scripts/manage_skill_links.py sync
   ```

`sync` 会把配置中的每个 Skill 链接到 `~/.agents/skills`。用 `status` 查看配置的目标位置，用
`check` 校验受管理的链接是否指向本仓库（缺失或错误时返回非零）。执行同步前先用
`sync --dry-run` 检查变更；未登记的条目不会被处理。

## Skills

| Skill | 用途 |
| --- | --- |
| [chrome-bookmarks](skills/chrome-bookmarks/SKILL.md) | 分类整理 Chrome 书签、去掉冗余和低价值项，并在浏览器完全退出后写回。 |
| [design-convergence-review](skills/design-convergence-review/SKILL.md) | 检查设计是否可以进入开发，并指出未收敛的阻塞问题。 |
| [first-principles](skills/first-principles/SKILL.md) | 质疑惯例命题，推导成本或性能边界，明确仍需验证的部分。 |
| [git-commit](skills/git-commit/SKILL.md) | 生成符合仓库规则的 Conventional Commit 信息，或把选定的改动拆成原子提交。 |
| [hermes-context-review](skills/hermes-context-review/SKILL.md) | 审查 Hermes 上下文中的冲突、过期、不安全或冗余指令。 |
| [llm-wiki](skills/llm-wiki/SKILL.md) | 在显式调用时搜索、验证和维护本地 Markdown Wiki。 |
| [paper-learning](skills/paper-learning/SKILL.md) | 通用论文学习：把论文蒸馏成可复用笔记（存到工作区 papers/ 目录），demo 可选、语言随论文。 |
| [five-dimension-analysis](skills/five-dimension-analysis/SKILL.md) | 把复杂局面拆成时间、利益、权力、博弈、本质五个维度，产出可证伪的判断与可执行动作。 |
| [communication-formulas](skills/communication-formulas/SKILL.md) | 按沟通目的选用 SCQA / FAB / BACC / 3W / PREP 五套表达顺序，装配成可直接开口的话术。 |
| [prompt-optimizer](skills/prompt-optimizer/SKILL.md) | 以最小改动诊断和优化提示词，并区分快速改写与有证据支持的评估。 |
| [human-readable-codebook](skills/human-readable-codebook/SKILL.md) | 把仓库讲成不翻源码也能读懂的书：OpenWiki 硬闸门、按 Phase 挂载参考、证据分级维护。 |
| [chinese-text-fixer](skills/chinese-text-fixer/SKILL.md) | 修复中文标点与排版：引号方向、全角半角、标点旁空格、零宽字符与实体；乱码只识别不还原。 |

用户指南是可选的，位于运行时包之外的 `docs/skills/`。该目录是指向 llm-wiki workshop 的软链接，
不受本仓库版本控制。目前只有 [design-convergence-review](docs/skills/design-convergence-review.md)
提供了用户指南。

## 流程图

每个 Skill 都有一张 SVG 流程图。均放在 `assets/`。内容与配色约定见 [RULES.md](RULES.md)。
下图的顺序与上方技能表一致。

### chrome-bookmarks

Chrome 开着也可整理；完全退出后才写回。

[![chrome-bookmarks：分类去冗余并写回](assets/chrome-bookmarks-flow.svg)](assets/chrome-bookmarks-flow.svg)

### design-convergence-review

六维收敛评审。

[![design-convergence-review：六维收敛评审](assets/design-convergence-review-flow.svg)](assets/design-convergence-review-flow.svg)

### first-principles

四步分析，包含证据门禁与现实验证。

[![first-principles：四步分析与现实验证](assets/first-principles-flow.svg)](assets/first-principles-flow.svg)

### git-commit

从模式判定到原子提交。

[![git-commit：从模式判定到原子提交](assets/git-commit-flow.svg)](assets/git-commit-flow.svg)

### hermes-context-review

上下文审查与分级。

[![hermes-context-review：上下文审查与分级](assets/hermes-context-review-flow.svg)](assets/hermes-context-review-flow.svg)

### llm-wiki

意图路由与脚本优先。

[![llm-wiki：意图路由与脚本优先](assets/llm-wiki-flow.svg)](assets/llm-wiki-flow.svg)

### paper-learning

从论文入口到蒸馏笔记与回答路由的通用流程。

[![paper-learning：从论文入口到蒸馏笔记与回答路由](assets/paper-learning-flow.svg)](assets/paper-learning-flow.svg)

### five-dimension-analysis

六步执行流程。

[![five-dimension-analysis：六步执行流程](assets/five-dimension-analysis-flow.svg)](assets/five-dimension-analysis-flow.svg)

### communication-formulas

如何选择公式。

[![communication-formulas：如何选择公式](assets/communication-formulas-routing.svg)](assets/communication-formulas-routing.svg)

### prompt-optimizer

从模式选择到有证据支持的提示词决策。

[![prompt-optimizer：从模式选择到有证据支持的提示词决策](assets/prompt-optimizer-flow.svg)](assets/prompt-optimizer-flow.svg)

### human-readable-codebook

OpenWiki 闸门、八个阶段、证据分级的页面。

[![human-readable-codebook：闸门、八阶段、证据分级](assets/human-readable-codebook-flow.svg)](assets/human-readable-codebook-flow.svg)

### chinese-text-fixer

扫描、分级复核，确认后才写回。

[![chinese-text-fixer：扫描、复核与确认写回](assets/chinese-text-fixer-flow.svg)](assets/chinese-text-fixer-flow.svg)

## 验证

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests
```

## 许可证

MIT
