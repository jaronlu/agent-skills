---
name: agent-gitignore
description: Adds disposable AI-agent runtime artifacts to the current git repo's .gitignore and commits only that file. Ignores ZCode plan/workflow-run paths, .workbuddy/, .mimosa/, .v2c/, .claude/settings.local.json and Aider caches, skipping absent paths, tracked files and user-authored config. Use when asked to ignore agent-generated or runtime files, clean git status noise from AI agents/plugins, or when the user mentions ZCode, WorkBuddy, Claude Code, mimosa, video2code, Aider, 忽略 Agent 运行时产物, or gitignore 太乱.
---

# agent-gitignore

把 AI Agent 在项目内生成的**一次性运行时产物**写进当前仓库 `.gitignore`，并自动做一次**只包含 `.gitignore`** 的原子提交。固定白名单 + 存在性检测：不存在的跳过，已被忽略的跳过，**已被 git 跟踪的一律不碰**，用户手写的 Agent 配置一律不忽略。

## 自动忽略清单

| 条目 | Agent | 运行时性质 |
|---|---|---|
| `.zcode/plans/`、`.zcode/workflow-runs/`、`.zcode/workflow-drafts/` | ZCode | 会话计划文件、动态工作流运行脚本与草稿；同目录 `.zcode/config.json`、`.zcode/agents/`、`.zcode/workflows/` 是用户配置，不忽略 |
| `.workbuddy/` | WorkBuddy | `memory/`、`reviews/`、`artifacts/` |
| `.mimosa/` | mimosa 插件 | `hook-state/`、`history/`、`reports/` |
| `.v2c/` | video2code 插件 | `plugin_root` 指针 |
| `.claude/settings.local.json` | Claude Code | 本机权限缓存；同目录 `settings.json`、`commands/` 不忽略 |
| `.aider.*` | Aider | chat/input/llm 历史与 tags 缓存 |

清单维护在 `scripts/add-entries.sh` 顶部的 `CATALOG` 变量里。完整证据、本机安装清单和「永不自动忽略」名单见
[references/runtime-artifacts.md](references/runtime-artifacts.md)。

## 执行步骤

1. 运行本 skill 自带脚本：

   ```sh
   sh <skill_dir>/scripts/add-entries.sh
   ```

   `<skill_dir>` 是本 `SKILL.md` 所在目录。脚本用 `git rev-parse --show-toplevel` 定位仓库根，从子目录调用也能写到正确的 `.gitignore`。有新增条目时自动提交，并用 pathspec 限定只提交 `.gitignore`。

   可用参数：
   - `--dry-run`：只预览，不写文件、不提交。用户说「先看看」时使用。
   - `--no-commit`：只写 `.gitignore`，不提交。
   - `--only zcode,workbuddy`：只处理指定 Agent，逗号分隔。
2. 按脚本输出向用户转述：新增了哪些条目（附 Agent）、提交 hash（如有）、哪些本来已覆盖、哪些已被跟踪、哪些当前不存在。
3. 特殊输出按以下方式处理：
   - `tracked, unaffected: ...` — 该路径已在 git 索引里，`.gitignore` 对它无效，脚本不会自动改索引，并报告跟踪路径。目录条目仍可添加规则以忽略该目录下未跟踪的运行时产物。向用户确认是否要 `git rm -r --cached <path>` 将已跟踪路径移出索引；未确认前不执行。
   - `commit skipped: .gitignore already had pending changes` — 追加前 `.gitignore` 就有未提交改动。向用户确认：把 `.gitignore` 连同他们的改动整体提交，还是由用户自己处理。不要替用户合并。
   - `commit failed: ...` — 原样展示错误（常见原因：pre-commit hook 失败、缺少 `user.name` / `user.email`）。先诊断再行动，不盲目重试。
   - 没有 `added` — 不产生提交，只汇报。

## 边界情况

- **不在 git 仓库内**：脚本退回当前目录并写 `.gitignore`，跳过 Git 检查和提交；输出明确提示该目录不是 git 仓库、请用户判断是否保留该文件。不要自行删除文件。
- **Agent 配置不是运行时产物**：`.claude/settings.json`、`.claude/commands/`、`.cursor/rules/`、`.gemini/`、`.opencode/`、`.codex/`、`.continue/`、`AGENTS.md`、`GEMINI.md`、`opencode.json`、`.github/copilot-instructions.md` 等通常由用户编写并有意提交，**禁止整目录忽略**。ZCode 同理：只处理 `.zcode/plans/` 等一次性子路径，`.zcode/config.json`、`.zcode/agents/`、`.zcode/workflows/` 属用户配置。白名单只接受经过确认的一次性状态。
- **白名单之外的可疑目录**：先向用户确认它是否是一次性产物，再决定是否扩展 `CATALOG`；不擅自扩大写入范围。
- **已提交的运行时产物**：先报告，再由用户决定是否移出跟踪；不自动 `git rm --cached`。
- **重复唤起**：幂等。已有条目不会再写，也不会产生空提交。
