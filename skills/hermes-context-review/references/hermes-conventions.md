# Hermes Conventions

Documentation baseline: official Hermes Agent docs checked on 2026-08-20. Memory parsing, configurable defaults, context loading and skill discovery were also checked against local source commit `bf1c28b480` on 2026-09-16 (`tools/memory_tool_store.py`, `agent/agent_init.py`, `agent/prompt_builder.py`, `agent/skill_utils.py`). This is a versioned baseline, not a guarantee about every installation.

Use the target installation's source or matching documentation when judging runtime behavior. Re-check defaults, loading precedence and truncation rules whenever the target version differs or evidence conflicts; do not wait for an arbitrary age threshold. Mark unavailable runtime evidence as unverified.

Sources:

- Prompt assembly: https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- Persistent memory: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Context files: https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files
- Context references: https://hermes-agent.nousresearch.com/docs/user-guide/features/context-references
- Personality & SOUL.md: https://hermes-agent.nousresearch.com/docs/user-guide/features/personality
- LLM-friendly docs index: https://hermes-agent.nousresearch.com/docs/llms.txt

## Home layout (HERMES_HOME, default ~/.hermes)

- `SOUL.md` — global persona and standing behavior. Loaded only from the Hermes home, never from project directories. Seeded with a default if missing; injected verbatim after security scan and truncation.
- `memories/MEMORY.md` — agent's personal notes; default configurable write limit 2,200 characters.
- `memories/USER.md` — user profile; default configurable write limit 1,375 characters.
- `config.yaml` — model, providers, memory/skill write gates, platform hints, truncation caps.
- `skills/` — agent skills (SKILL.md packages; a skill may carry its own `references/`).
- `state.db` — FTS5 session storage backing `session_search`.
- `pending/` — staged memory and skill writes awaiting approval.

Neither a home-level `references/` directory nor a home-level `AGENTS.md` is a required global context slot. A home `AGENTS.md` has no special global loading rule; it can still load through ordinary project discovery when the home lies on the applicable working-directory / git-root chain. "Context references" in Hermes means the CLI `@file:` / `@folder:` / `@url:` inline-injection feature, not a directory of markdown files.

### Personal home extensions (observed, not part of the Hermes contract)

This section describes personal conventions observed on individual machines, not documented
Hermes behavior. Apply an item only when the target home actually contains the file it describes,
usually explained in that home's own `README.md`. Never report the absence of anything in this
section as a finding, and never treat these paths as required by Hermes.

- Home-level `AGENTS.md` — personal cross-project defaults. Effective only through explicit inclusion or applicable project discovery, not merely because it is in the home. Review it when present; flag assumptions of unconditional global effect.
- Home-level `references/*.md` — on-demand methods and templates, read per task type.
- The home may itself be a git repository tracking only its managed files, with runtime state (logs, sessions, caches, databases) gitignored. Only when it is, the staged-change review path (`git diff --cached`) applies there.

## Memory format

- Entries are separated by a `§` (U+00A7) delimiter on its own line; entries may be multiline.
- Enabled stores are loaded as a frozen snapshot; ordinary mid-session writes do not update that snapshot. Confirm refresh behavior in the target version before claiming a running prompt changed.
- An add/replace that would exceed the configured limit fails; at-limit content is not itself invalid. External oversized files can remain loaded with a warning. Consolidation is agent-driven, not automatic storage compaction.
- Exact duplicates are not added again; loading deduplicates while preserving order. Content is security-scanned on writes and load; unsafe entries may remain on disk but be replaced in the prompt snapshot.
- Replace/remove operations guard against non-round-tripping external edits and may save a backup before refusing a write. Append skips that drift guard in the checked version. A read-only audit must not invoke mutation or backup-producing methods.

## Project context files

- First non-empty project context type wins: `.hermes.md` / `HERMES.md` (walk to git root) → AGENTS directory chain → `CLAUDE.md` / `claude.md` → `.cursorrules` plus `.cursor/rules/*.mdc` (latter types CWD only).
- The AGENTS chain merges git root down to CWD. Within each directory, the first non-empty `AGENTS.override.md`, `AGENTS.md` or `agents.md` wins. Outside a git repo only CWD is checked; arbitrary parent files are not inherited.
- All context files are security-scanned (prompt injection) and head/tail-truncated at 70% head / 20% tail when over the cap (`context_file_max_chars` if set, otherwise dynamic with a 20,000-char floor).
- `SOUL.md` is loaded independently as the identity slot, always from the Hermes home.

## config.yaml keys worth cross-checking

- `memory.memory_enabled`, `memory.user_profile_enabled`, `memory.memory_char_limit` (default 2200), `memory.user_char_limit` (default 1375), `memory.write_approval`
- `skills.write_approval`, `skills.create_dir`, `skills.external_dirs`, `skills.trusted_project_dirs`, `skills.project_discovery` (availability depends on version)
- `context_file_max_chars`
- `platform_hints`
