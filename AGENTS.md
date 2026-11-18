# 仓库指令

在本仓库工作时，以下约定必须遵守。详细说明、理由和视觉规范见 [RULES.md](RULES.md)，技能包契约见 [CONTRIBUTING.md](CONTRIBUTING.md)。两者冲突时以 RULES.md 为准。

- 每个 skill 必须有主 SVG 流程图，放在根目录 `assets/`，文件名为 `<skill-name>-flow.svg`；确需多张时额外图用 `<skill-name>-<topic>-flow.svg`。技能包内的 `assets/` 只放输出资源，不放流程图。
- 改动 `skills/`、`assets/` 或 `config/` 后运行 `python3 scripts/validate_skills.py`，通过后才算完成。该校验同时检查每个技能的主图、README 清单、`SKILL.md` 行数与资源引用、SVG 尺寸/无障碍，以及分发配置覆盖。
- 技能目录里可以有 `SKILL.md` 之外的任意文件。`agents/openai.yaml` 是可选的。
- `SKILL.md` 的 frontmatter 字段以官方为准：`name` 与 `description` 必填，可选 `license`、`compatibility`、`allowed-tools`、`metadata`。`name` 1 到 64 字符，只含小写字母、数字和连字符，首尾和连续连字符都不允许，并与目录名一致；`description` 1 到 1024 字符，写清楚做什么和何时使用；`compatibility` 不超过 500 字符。
- `SKILL.md` 保持在 500 行以内，详细内容放进 `references/`；`SKILL.md` 必须直接链接每个 reference，references 之间可以交叉链接但不得形成必须先读的链。
- `config/skill-links.toml` 用 profile 描述安装/排除集合，target 只引用 profile；每个 target 解析后的 `skills` 与 `excluded` 必须覆盖全部技能。新增技能时在相关 profile 中决定安装或排除。
- 改动 `skills/` 或 `config/` 后需要 `sync` 到共享目录。先运行 `python3 scripts/manage_skill_links.py sync --dry-run` 确认，再执行 `sync`，最后用 `check` 校验（`validate_skills.py` 与 `manage_skill_links.py` 都需要 Python 3.11+，或安装 `tomli`）。
