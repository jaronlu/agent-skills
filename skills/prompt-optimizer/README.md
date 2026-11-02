# prompt-optimizer

An eval-driven skill for improving prompts. It separates a one-off rewrite from a measured optimization loop, so a prompt is only called "better" after it passes cases the rewrite did not see.

Read [SKILL.md](SKILL.md) first; it is the entry point and the only file an agent needs to load up front.

## Requirements

- Python 3.8+ (the statistics script uses `math.comb` and `statistics.NormalDist`)
- No third-party packages
- An agent that can load `SKILL.md` as a skill (Claude Code, DSH, or a compatible harness)

## Install

From the repository root:

```bash
ln -s "$(git rev-parse --show-toplevel)/skills/prompt-optimizer" ~/.claude/skills/prompt-optimizer
```

Or copy the directory into your harness's skills directory. Keep the directory name `prompt-optimizer`.

## Use

Ask for prompt work in the normal way: "optimize this prompt", "why does this prompt fail", "A/B test these variants", or the Chinese equivalents. The skill chooses Quick, Audit, or Measured mode.

At the start, share the prompt and what you want to improve. For a diagnosis, include one example of a bad result if you have it; for a measured run, include the target model and any existing test cases. If you have no cases yet, the skill can draft a small synthetic development set with you. It will explain the next step first and introduce statistical details only when they affect the decision. A single failure pattern may need only one or two candidate prompts; three are not mandatory.

For a measured run, write one JSONL row per case per variant per trial:

```json
{"case_id":"c001","variant":"baseline","trial":1,"stratum":"typical","passed":false,"score":0.4,"format_ok":true,"tokens":210,"latency_ms":900}
```

Then run, from this directory:

```bash
python3 scripts/compare.py results.jsonl --baseline baseline --markdown --adjust holm --min-n 50
```

Useful flags: `--min-n` (directional threshold, default 50), `--min-stratum-n` (default 10), `--adjust holm|bonferroni|none`, `--skip-invalid`, `--json`.

`--min-n` gates significance using paired case count shared by the baseline and candidate. The report also shows format-check coverage; incomplete coverage cannot satisfy a 100% format-compliance gate. Keep development and sealed-holdout results in separate files: tune on development data, freeze the selected candidate, then run the final baseline comparison on the holdout.

## Layout

```
SKILL.md                 workflow, modes, ship rule, guardrails
references/              evaluation protocol, failure taxonomy, rewrite patterns, evidence
assets/                  meta-prompt and eval-report templates
scripts/compare.py       zero-dependency statistics and trial aggregation
scripts/test_compare.py  unit tests
references/evals/       manual behavioral scenarios
```

## Tests

From the repository root:

```bash
python3 -m unittest discover -s skills/prompt-optimizer/scripts -p 'test_*.py'
```

## License

No license file is present in this repository. Add one before redistributing this skill outside the repository.
