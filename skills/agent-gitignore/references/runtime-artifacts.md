# Agent 运行时产物清单与判定依据

本文件是 `agent-gitignore` 的取证记录和维护依据。脚本只处理这里认定为「一次性运行时状态」的路径；
用户编写、通常有意提交的 Agent 配置不在此列。

## 判定标准

同时满足以下三条才算运行时产物：

1. **机器生成**：由 Agent/插件在会话、扫描或构建过程中写入，不是用户手写的规则或提示词。
2. **可随时重建**：删除后不影响项目功能、协作和 Agent 配置，最多丢失本地会话历史。
3. **项目级**：产生在当前仓库工作区内，会被 `git status` 看见。只落在 `~/` 全局目录的不需要写进项目 `.gitignore`。

混合目录（同一目录既有用户配置又有临时状态）只忽略具体临时子路径，**绝不整目录忽略**。

## 自动忽略白名单

与 `scripts/add-entries.sh` 的 `CATALOG` 保持同步。

| 条目 | 归属 Agent | 实测内容 |
|---|---|---|
| `.zcode/plans/`、`.zcode/workflow-runs/`、`.zcode/workflow-drafts/` | ZCode | 会话计划（`plan-<sessionId>.md`）、动态工作流运行脚本与草稿；会话数据库在全局 `~/.zcode/cli/db`，不落在项目内 |
| `.workbuddy/` | WorkBuddy | `memory/`、`reviews/`、`artifacts/` |
| `.mimosa/` | mimosa 安全扫描插件 | `hook-state/`、`history/`、`finding-ledger/`、`reports/`、`hook-status/` |
| `.v2c/` | video2code 插件 | `plugin_root` 指针 |
| `.claude/settings.local.json` | Claude Code | 本机权限缓存（`permissions.allow` 列表） |
| `.aider.chat.history.md` | Aider | 对话历史 |
| `.aider.input.history` | Aider | 输入历史 |
| `.aider.llm.history` | Aider | LLM 交互历史 |
| `.aider.tags.cache.v*/` | Aider | tags 缓存目录（版本号随 Aider 升级变化） |

脚本只在对应路径**真实存在**时写入；已存在等价忽略规则（含父目录规则、glob）时用
`git check-ignore` 判定为已覆盖，不重复追加。

## 永不自动忽略

以下路径常被用户有意提交，整目录忽略会隐藏真正的配置变更：

- Claude Code：`.claude/settings.json`、`.claude/commands/`、`.claude/agents/`、`.claude/skills/`、`.claude/hooks/`
- ZCode：`.zcode/config.json`、`.zcode/agents/`、`.zcode/workflows/`（用户主动保存的工作流定义）
- Cursor：`.cursor/rules/`、`.cursor/mcp.json`、`.cursorignore`
- Gemini CLI：`.gemini/`、`GEMINI.md`（实测已被跟踪）
- OpenCode：`.opencode/`、`opencode.json`
- Codex：`.codex/`
- Continue：`.continue/`、`.continueignore`
- 其他：`.windsurf/rules`、`.windsurfrules`、`.clinerules`、`.roo/rules/`、`.kiro/steering/`、
  `.junie/guidelines*`、`.trae/rules/`、`.qoder/rules/`、`.github/copilot-instructions.md`、
  `AGENTS.md`、`AGENTS.local.md`

GitHub Copilot CLI 的全局状态在 `~/.copilot`；仓库内的 instructions 文件属用户配置。

## 扩展流程

1. 在目标仓库确认该路径由 Agent 自动生成、删除后可再生，且未被 git 跟踪。
2. 若目录混合了用户配置，只登记具体临时子路径（例如 `.claude/settings.local.json`），不登记父目录。
3. 修改 `CATALOG`，在临时仓库跑 `--dry-run` 和重复运行，确认幂等且不会命中已跟踪文件。
4. 同步更新本文件的白名单表、`CHANGELOG.md`，再运行 `python3 scripts/validate_skills.py`。
