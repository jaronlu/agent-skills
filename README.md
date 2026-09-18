# Agent Skills

One repository for the agent skills you maintain. Skills are published to the CC Switch library
at `~/.agents/skills`, and CC Switch distributes them to Claude Code, Codex, Gemini CLI, Hermes,
Zcode, WorkBuddy, and other compatible tools.

[简体中文](README_zh-CN.md)

## What

`skills/` is the source of truth. Each skill is a self-contained package with a `SKILL.md` entry point and optional references, scripts, and assets.

## Why

Maintain a skill once and publish it to one library. CC Switch owns every agent-facing
distribution step, so this repository never tracks individual tool directories and never has to be
re-linked when a tool changes where it looks for skills.

## How

1. Add or update a skill in `skills/`.
2. Register it in `config/skill-links.toml` under `[targets.cc-switch]`.
3. Review the proposed changes:

   ```bash
   python3 scripts/manage_skill_links.py sync --dry-run
   ```

4. Apply them:

   ```bash
   python3 scripts/manage_skill_links.py sync
   ```

`sync` copies each configured skill into the CC Switch library. Use `status` to see the configured
destinations and `check` to verify the library matches this repository; `check` exits non-zero when
the library is behind. Entries the manager does not own are never overwritten.

## Skills

| Skill | What it does |
| --- | --- |
| [chrome-bookmarks](skills/chrome-bookmarks/SKILL.md) | Classifies Chrome bookmarks, removes duplicates and low-value items, and writes back only after Chrome quits. |
| [design-convergence-review](skills/design-convergence-review/SKILL.md) | Checks whether a design is ready for implementation and identifies unresolved blockers. |
| [first-principles](skills/first-principles/SKILL.md) | Rebuilds a decision or diagnosis from evidence, constraints, and testable assumptions. |
| [git-commit](skills/git-commit/SKILL.md) | Drafts repository-aware Conventional Commit messages, or turns the selected changes into atomic commits. |
| [hermes-context-review](skills/hermes-context-review/SKILL.md) | Audits Hermes context for conflicting, stale, unsafe, or wasteful instructions. |
| [llm-wiki](skills/llm-wiki/SKILL.md) | Searches, verifies, and maintains a local Markdown wiki when explicitly invoked. |
| [paper-learning](skills/paper-learning/SKILL.md) | Distills any research paper into reusable notes in the user's papers directory, with an optional language-agnostic demo. |
| [five-dimension-analysis](skills/five-dimension-analysis/SKILL.md) | Splits a messy situation across time, interests, power, bargaining, and essence, then outputs falsifiable judgments and actionable moves. |
| [communication-formulas](skills/communication-formulas/SKILL.md) | Picks one of five speaking formulas (SCQA, FAB, BACC, 3W, PREP) by communication goal and assembles ready-to-say wording. |

User guides are optional and live outside the runtime packages, in `docs/skills/`. That directory is
a symlink into the llm-wiki workshop, so it is not version-controlled here. Only
[design-convergence-review](docs/skills/design-convergence-review.md) ships a guide today.

## Diagrams

Every skill ships one SVG flow diagram, all kept in `assets/`; [RULES.md](RULES.md) defines the
required content and styling. Each diagram below follows the order of the skill table above, and
links to its raw SVG.

### chrome-bookmarks

Classify, dedupe, and write Chrome bookmarks after a full quit.

[![chrome-bookmarks: classify, dedupe, write back](assets/chrome-bookmarks-flow.svg)](assets/chrome-bookmarks-flow.svg)

### design-convergence-review

Six-dimension convergence review.

[![design-convergence-review: six-dimension convergence review](assets/design-convergence-review-flow.svg)](assets/design-convergence-review-flow.svg)

### first-principles

Five-step reasoning and closure.

[![first-principles: five-step reasoning and closure](assets/first-principles-flow.svg)](assets/first-principles-flow.svg)

### git-commit

From mode selection to atomic commits.

[![git-commit: from mode selection to atomic commits](assets/git-commit-flow.svg)](assets/git-commit-flow.svg)

### hermes-context-review

Context audit and severity.

[![hermes-context-review: context audit and severity](assets/hermes-context-review-flow.svg)](assets/hermes-context-review-flow.svg)

### llm-wiki

Intent routing and script-first retrieval.

[![llm-wiki: intent routing and script-first retrieval](assets/llm-wiki-flow.svg)](assets/llm-wiki-flow.svg)

### paper-learning

From paper intake to distilled notes and routed answers.

[![paper-learning: from paper intake to distilled notes and routed answers](assets/paper-learning-flow.svg)](assets/paper-learning-flow.svg)

### five-dimension-analysis

Six-step workflow.

[![five-dimension-analysis: six-step workflow](assets/five-dimension-analysis-flow.svg)](assets/five-dimension-analysis-flow.svg)

### communication-formulas

Choosing a formula.

[![communication-formulas: choosing a formula](assets/communication-formulas-routing.svg)](assets/communication-formulas-routing.svg)

## Verify

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests
```

## License

MIT
