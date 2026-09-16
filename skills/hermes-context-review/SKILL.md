---
name: hermes-context-review
description: Review durable Hermes Agent context for conflicting rules, stale references, memory-format violations, unsafe instructions, and wasted context. Use when the user asks to review, audit, simplify, or validate SOUL.md, AGENTS.md, memories, references, or config.yaml for a Hermes agent.
---

# Hermes Context Review

Review Hermes's durable operating context. Focus on behavior, authority, maintainability, and context cost—not prose polish.

## Core Contract

- Read-only review: never edit, back up, stage, commit, change configuration, or create schedules. A suggested fix is not an authorization to execute it.
- Never expose secrets, and do not replicate configuration content into context documents; report only the minimal non-sensitive evidence.
- Use an explicit Hermes home when supplied, otherwise `$HERMES_HOME` or `~/.hermes`. If no reviewable target resolves, state why and stop without a verdict.
- For staged reviews the index is authoritative; report disk deployment state separately and never mix it into staged-change evidence.
- Read each target completely. Distinguish on-disk facts, load behavior derived from the installed implementation, and runtime-session evidence. Mark unavailable or unverified evidence explicitly.

## Review Flow

1. **Scope the review.** Read [references/review-workflow.md](references/review-workflow.md) to resolve the home, project, or staged scope and to list what is and is not checked.
2. **Verify the effective loading path.** Read [references/runtime-checks.md](references/runtime-checks.md) to check version, home, CWD, load switches, shadowing, skill provenance, and session snapshots. A file existing is not the same as it being loaded.
3. **Check ownership and consistency.** Read [references/hermes-conventions.md](references/hermes-conventions.md) before judging paths, ownership, format, or limits. Check for conflicts, stale or broken references, duplication, over-broad or unsafe rules, and rules filed in the wrong layer: global behavior in home `SOUL.md`, project rules in project context, compact preferences and durable facts in memory, on-demand methods in references.
4. **Check memory and context cost.** Read [references/memory-checks.md](references/memory-checks.md) when memory is in scope. Resolve defaults and limits against the runtime implementation; a missing config key is not itself an error. Flag truncation risk; when recommending demotion of low-frequency detail, keep the constraint and its discoverable entry point.

## Report Contract

Start with the overall conclusion, then list evidence-backed findings by severity. Each finding gives file and precise location, evidence, impact, and the smallest correction; separate newly introduced problems from pre-existing gaps. Report in the language of the user's request, and state "Checked, no findings" for dimensions reviewed without findings. An evidence gap is not a pass.

- **P0**: broken authority, security risk, critical invalid reference, or memory-format violation that can change behavior.
- **P1**: conflicting, stale, duplicated, misplaced, load-gap, or capacity issues with meaningful impact.
- **P2**: bounded clarity or compression improvements that do not change behavior; do not report cosmetic wording preferences.

Unless the review stopped because no target exists, end with exactly one line: `VERDICT: BLOCK` with any P0; otherwise `VERDICT: WARN` with any P1 or a critical verification gap; otherwise `VERDICT: PASS` (P2 suggestions may follow). PASS covers only the declared scope and is not an end-to-end runtime acceptance.
