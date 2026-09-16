# Review Workflow

## Target Inventory

- Home: each present `SOUL.md`, `AGENTS.md`, `memories/USER.md`, `memories/MEMORY.md`, `references/*.md`, and the relevant `config.yaml` fields.
- If a `README.md` exists, read its personal conventions, but never treat personal home extensions as required Hermes layout.
- When the user supplies a project directory or asks for a project-context review: `.hermes.md` / `HERMES.md`, `AGENTS.override.md`, `AGENTS.md` / `agents.md`, `CLAUDE.md` / `claude.md`, `.cursorrules`, `.cursor/rules/*.mdc`, and the applicable git-root → CWD chain.
- For a skill or distribution review: the source package, entry-point references, deployed copies, discovery configuration, and existing indexes. Do not scan every skill body wholesale.
- Read each target completely; verify paths, section references, skill names, and configuration claims along explicit references. External facts cannot be assumed valid merely because a memory entry asserts them.
- Report absent, unreadable, out-of-scope, and unverified targets. Absence of an optional file is not itself a finding.

## Staged Review

In the target Git repository run `git diff --cached --name-status`; use `-z` for unusual filenames and `-M` for rename detection.

| Status | Read for evidence |
| --- | --- |
| Added | `git show :<path>` |
| Modified | `git show HEAD:<path>` and `git show :<path>` |
| Deleted | `git show HEAD:<path>`; check remaining references |
| Renamed | `HEAD:<old-path>` for the old side and `:<new-path>` for the new side; verify references follow |

For a repository with no HEAD, read only the index objects that exist; report unmerged entries as an evidence gap rather than guessing the final content. A staged review does not require the target to still exist on disk: the HEAD content of a deleted file is reviewable evidence.

When related unchanged files clarify semantics, prefer the index copy there too. Working-tree or deployment-copy differences must be reported separately and not attributed to the staged change. Never stage, reset, or sync any directory.

## Content and Cost

- Global behavior belongs in home `SOUL.md`, project rules in project context, compact preferences and durable facts in memory, low-frequency methods in on-demand references or a skill.
- Check authorization premises for commits, publishing, deletion, and external contact; a user preference must not silently widen operational authority.
- Before demoting a method, confirm an entry point and a task trigger exist; moving a file without keeping a discovery path loses the rule.
- Distinguish the always-on SOUL / memory, the skill index description, and the on-demand `SKILL.md` / references body; entry size is not per-turn resident cost by itself.
- Judge truncation against the current configuration or the installed implementation's dynamic cap, and note the unknown-model-window limitation.

## Reporting Boundaries

Separate change regressions, pre-existing context issues, and distribution state. For runtime behavior that cannot be reproduced, report only static derivation and do not claim end-to-end acceptance. A read-only review must not complete by creating sessions, calling models, trial-writing memory, or refreshing caches; those verifications need separate authorization.
