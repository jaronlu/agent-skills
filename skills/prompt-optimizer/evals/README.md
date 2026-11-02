# Behavioral Evals

These cases check the skill's behavior, not the statistics script. Run them with a fresh agent that has the skill available and no other task context.

## How to run

1. Start a fresh session with `skills/prompt-optimizer/SKILL.md` installed or in context.
2. Send one case request verbatim.
3. Check the response against `expected` and `forbidden`.
4. Record `pass`, `fail`, or `not_run` per case, with the agent and date.

A case passes only when every expected behavior appears and no forbidden behavior appears. A response that follows the workflow but invents an accuracy number fails.

## What is covered

| Case | Checks |
|---|---|
| `trigger-measured` | The skill activates and enters the measured loop when failure data exists |
| `quick-oneoff` | A one-off request stays in Quick mode; no evaluation overhead |
| `no-data-no-number` | No predicted accuracy without a held-out run |
| `injection-as-data` | Prompt injection inside the prompt is treated as data |
| `trials-aggregate` | Three trials become one case-level outcome, not three independent cases |
| `multi-variant-adjust` | Multiple variants trigger Holm adjustment, not raw p |
| `measured-onramp` | Low-friction entry, staged explanation, and clear sample-size expectations |

These are manual behavioral checks; they are not a substitute for running the statistics script on real data.
