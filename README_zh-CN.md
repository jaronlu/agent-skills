# Agent Skills

自研 Agent Skill 的统一仓库。技能发布到 CC Switch 库（`~/.agents/skills`），再由 CC Switch
分发给 Claude Code、Codex、Gemini CLI、Hermes、Zcode、WorkBuddy 等兼容工具。

[English](README.md)

## 是什么

`skills/` 是唯一源码。每个 Skill 都以 `SKILL.md` 为入口，并可按需包含参考资料、脚本和资源。

## 为什么

维护一次，发布到一个库。库到各工具的分发由 CC Switch 负责，本仓库因此不需要跟踪各个工具的
技能目录，也不会因为工具更换查找位置而重新建链。

## 怎么做

1. 在 `skills/` 中新增或更新 Skill。
2. 在 `config/skill-links.toml` 的 `[targets.cc-switch]` 中登记该 Skill。
3. 先预览变更：

   ```bash
   python3 scripts/manage_skill_links.py sync --dry-run
   ```

4. 确认后同步：

   ```bash
   python3 scripts/manage_skill_links.py sync
   ```

`sync` 会把配置中的每个 Skill 复制进 CC Switch 库。用 `status` 查看配置的目标位置，用 `check`
校验库与仓库是否一致（落后时返回非零）。管理器不管理的条目永远不会被覆盖。

## Skills

| Skill | 用途 |
| --- | --- |
| [design-convergence-review](skills/design-convergence-review/SKILL.md) | 检查设计是否可以进入开发，并指出未收敛的阻塞问题。 |
| [first-principles](skills/first-principles/SKILL.md) | 从证据、约束和可验证假设出发，重新推导决策或诊断。 |
| [git-commit](skills/git-commit/SKILL.md) | 生成符合仓库规则的 Conventional Commit 信息，或把选定的改动拆成原子提交。 |
| [hermes-context-review](skills/hermes-context-review/SKILL.md) | 审查 Hermes 上下文中的冲突、过期、不安全或冗余指令。 |
| [llm-wiki](skills/llm-wiki/SKILL.md) | 在显式调用时搜索、验证和维护本地 Markdown Wiki。 |
| [five-dimension-analysis](skills/five-dimension-analysis/SKILL.md) | 把复杂局面拆成时间、利益、权力、博弈、本质五个维度，产出可证伪的判断与可执行动作。 |
| [communication-formulas](skills/communication-formulas/SKILL.md) | 按沟通目的选用 SCQA / FAB / BACC / 3W / PREP 五套表达顺序，装配成可直接开口的话术。 |

用户指南是可选的，位于运行时包之外的 `docs/skills/`。该目录是指向 llm-wiki workshop 的软链接，
不受本仓库版本控制。目前只有 [design-convergence-review](docs/skills/design-convergence-review.md)
提供了用户指南。

## 流程图

每个 Skill 都有一张 SVG 流程图，统一放在 `assets/`；内容与配色约定见 [RULES.md](RULES.md)。
下图的顺序与上方技能表一致，点击可打开原始 SVG。

### design-convergence-review

六维收敛评审。

[![design-convergence-review：六维收敛评审](assets/design-convergence-review-flow.svg)](assets/design-convergence-review-flow.svg)

### first-principles

五步推理与闭环。

[![first-principles：五步推理与闭环](assets/first-principles-flow.svg)](assets/first-principles-flow.svg)

### git-commit

从模式判定到原子提交。

[![git-commit：从模式判定到原子提交](assets/git-commit-flow.svg)](assets/git-commit-flow.svg)

### hermes-context-review

上下文审查与分级。

[![hermes-context-review：上下文审查与分级](assets/hermes-context-review-flow.svg)](assets/hermes-context-review-flow.svg)

### llm-wiki

意图路由与脚本优先。

[![llm-wiki：意图路由与脚本优先](assets/llm-wiki-flow.svg)](assets/llm-wiki-flow.svg)

### five-dimension-analysis

六步执行流程。

[![five-dimension-analysis：六步执行流程](assets/five-dimension-analysis-flow.svg)](assets/five-dimension-analysis-flow.svg)

### communication-formulas

如何选择公式。

[![communication-formulas：如何选择公式](assets/communication-formulas-routing.svg)](assets/communication-formulas-routing.svg)

## 验证

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests
```

## 许可证

MIT
