# 贡献指南

本仓库遵循当前 Codex 技能包模型。保持运行时包小巧、可预测，且不包含重复的用户文档。

仓库级强制规则（每个技能必须配 SVG 流程图、分发目标必须显式登记）见 [RULES.md](RULES.md)。
本文件描述技能包契约，两者冲突时以 `RULES.md` 为准。

## 仓库契约

每个技能位于 `skills/<skill-name>/` 下。

```text
skills/<skill-name>/
├── SKILL.md              # 必需：唯一的执行指令来源
├── agents/
│   └── openai.yaml       # 本仓库要求：UI 元数据
├── references/           # 可选：代理按需阅读的资料
├── scripts/              # 可选：确定性可执行辅助工具
└── assets/               # 可选：模板或复制到输出中的文件
```

技能包内允许的顶级条目仅有：

- `SKILL.md`
- `README.md`（可选，只给人看）
- `agents/`
- `references/`
- `scripts/`
- `assets/`

请勿在运行时技能包内添加 `README.zh-CN.md`、`SKILL.zh-CN.md`、`templates/`、`examples/`、`config/`、更新日志、安装指南或快速参考文件。可选 `README.md` 不得写入与 `SKILL.md` 冲突的执行规则。

## 文件职责

### `SKILL.md`

- 使用 YAML 前置元数据；`name` 和 `description` 为必需字段，可选字段仅允许当前官方校验器支持的 `license`、`allowed-tools` 和 `metadata`。
- `name` 必须与技能目录名称完全一致。
- 仅使用小写字母、数字和连字符。
- 将所有触发条件放入 `description` 中，因为它控制技能激活。
- 正文专注于另一个代理执行任务所需的指令。
- 优先使用祈使句和渐进式披露。
- 将详细的领域知识放入 `references/`，避免重复。

### `agents/openai.yaml`

提供以下内容：

```yaml
interface:
  display_name: "面向用户的名称"
  short_description: "25-64 个字符的 UI 描述"
  default_prompt: "使用 $skill-name 来完成一项具体任务。"
```

所有字符串都必须用引号包裹。默认提示必须显式提及 `$skill-name`。
明确需要 UI 品牌资源时，可增加 `icon_small`、`icon_large` 和 `brand_color`；未知字段仍视为契约错误。

### `references/`

存储代理在执行过程中可能需要阅读的内容：

- 领域规则
- API 或架构说明
- 校准示例
- 详细检查清单
- 可复用的响应结构

从 `SKILL.md` 直接链接每个引用。避免嵌套引用链。

### `scripts/`

存储确定性辅助工具，防止重复编写相同代码。脚本必须：

- 避免硬编码凭据
- 对敏感数据使用脱敏输出
- 在暴露 CLI 时提供有用的 `--help`
- 在可行时于验证阶段执行

### `assets/`

存储用于输出而非代理上下文的内容，例如文档模板、起始文件或媒体。人读流程图也可以放在这里，由可选的 `README.md` 引用（见 `git-commit`）。如果代理必须读取 Markdown 文件来做决策，则该文件属于 `references/`，而非 `assets/`。

## 用户文档

面向用户的指南位于运行时包之外：

```text
docs/skills/<skill-name>.md
```

用户指南是可选的。它们可以解释安装、示例或动机，但不得定义与 `SKILL.md` 不同的执行规则。

根目录的 `README.md` 和 `README_zh-CN.md` 是技能目录。将运行时定义直接链接到 `skills/<skill-name>/SKILL.md`，将可选指南链接到 `docs/skills/`。

## 添加技能

1. 使用官方技能创建器初始化包：

   ```bash
   python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/init_skill.py" \
     <skill-name> \
     --path skills \
     --interface 'display_name=...' \
     --interface 'short_description=...' \
     --interface 'default_prompt=Use $<skill-name> to ...'
   ```

2. 替换 `SKILL.md` 中的每个占位符。
3. 仅创建技能实际需要的资源目录。
4. 在 `docs/skills/` 下（而非技能内部）添加可选的用户指南。
5. 绘制流程图 `assets/<skill-name>-flow.svg`，规范见 [RULES.md](RULES.md)。
6. 将技能添加到两个根目录目录文件的技能表和流程图清单中。
7. 在 `config/skill-links.toml` 的 `[targets.cc-switch]` 中登记该技能，并执行 `sync`
   发布到 CC Switch 库；库到各工具的分发由 CC Switch 负责。
8. 在 `CHANGELOG.md` → `Unreleased` 下添加条目。
9. 运行验证。

## 验证

```bash
python3 scripts/validate_skills.py
```

当官方验证器在本地可用时，还应运行：

```bash
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" \
  skills/<skill-name>
```

## 质量标准

- 技能具有窄而可复用的职责。
- 触发条件足够具体，以避免意外激活。
- 指令在没有充分理由的情况下不重复通用模型知识。
- 输入、证据边界、输出契约和停止条件是明确的。
- 除非该路径是技能的有意领域契约，否则不提交任何机密、专有配置、生成工件或本地机器路径。
- 按风险比例测试脚本和示例。
- 仓库验证通过，无警告或被忽略的失败。

## Git

除非仓库工具建立了更严格的规则，否则使用 Conventional Commits：

```text
feat(skill-name): 添加功能
fix(skill-name): 修正行为
docs: 更新技能目录
chore: 维护仓库工具
```
