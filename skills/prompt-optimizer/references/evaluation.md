# Evaluation Protocol

The point of this file is to make "better" falsifiable. Read it when you are designing the case set, choosing a judge, or writing the decision record.

## 1. What to measure

| Layer | Metric | Why |
|---|---|---|
| Primary | Task pass rate (binary per case) | The only number that supports a ship decision |
| Contract | Format compliance, schema validity, allowed values | A prompt that fails format is unusable regardless of content |
| Safety | Correct refusal / correct compliance on negative cases | Catches over- and under-refusal |
| Cost | Prompt-template tokens, output tokens, latency | A 3× prompt for +2pp is usually a bad trade |
| Secondary | Human preference, rubric score | Tie-breaker and qualitative diagnosis, not the ship gate |

Report per stratum as well as overall. An aggregate gain that hides a 20-point drop on boundary cases is a regression, not an improvement.

Count cost from the prompt template, not the test inputs: use the target tokenizer on the system prompt plus fixed instructions, exclude per-case input text, and record output tokens and latency separately. If the tokenizer is unavailable, label the character-count estimate as an estimate. This is the denominator for the 25% growth budget.

Do not collapse everything into one weighted score. Weights hide which dimension moved.

## 2. Building the case set

### Sources, in order of value

1. Real production inputs, stratified by frequency and by known failure.
2. Past incidents and support tickets, one case per distinct failure mode.
3. Synthetic cases derived from the contract: empty input, missing fields, maximum length, mixed language, contradictory instructions, prompt-injection text, out-of-scope requests.
4. Regression cases: every failure that has ever reached production.

Redact names, account IDs, emails, and secrets before a case touches disk. Keep the raw mapping out of the repository.

### Composition

| Stratum | Share | Purpose |
|---|---|---|
| Typical | 50% | Detect regressions on the common path |
| Boundary / ambiguous | 25% | The cases where labels or rules collide |
| Adversarial / negative | 15% | Injection, empty input, out-of-scope, malformed |
| Known regressions | 10% | Prevent backsliding |

Minimum 20 development cases to iterate. Seal 30% as a holdout and do not inspect its inputs, labels, or outputs during diagnosis or variant generation. A ship decision requires at least 50 paired holdout cases; with a 30% holdout this means at least 167 total cases. Use 100+ paired holdout cases when you expect a gain under 5 percentage points. With p ≈ 0.5, the 95% Wilson half-width is roughly:

| n | Half-width |
|---|---|
| 20 | ±20 pp |
| 50 | ±14 pp |
| 100 | ±10 pp |
| 200 | ±7 pp |

That table is the reason a 5-point "win" on 20 cases is noise. Gate the 5pp stratum rule only on strata with at least 10 cases; smaller strata are reported as warnings, not ship blockers.

### Labels and pass rules

Write the pass rule before looking at any output. Prefer mechanical rules; for semantic cases use a 3–5 criterion rubric with binary criteria and one anchored example per criterion.

Double-label at least 20% of cases, blind, and report agreement. If the two labellers disagree on a case, the case is ambiguous: either fix the label definition or move it to the boundary stratum. Do not let a prompt be blamed for an unlabelable case.

### Holdout and contamination

- Seal 30% as a holdout. Use only the development split to diagnose failures and compare variants. Freeze and record the selected candidate before opening the holdout; compare it with baseline once. If multiple candidates are tested on the holdout, adjust across all of them and do not revise prompts from those results. Once you tune against holdout results, it is no longer a holdout.
- Never copy test inputs into few-shot examples, and remove near-duplicates between the example set and the test set.
- Version the set: hash of case IDs plus label version. Store it next to the prompt version. A score without the set hash is not reproducible.

## 3. Running the comparison

Same model, same settings, same tools, same order-independent conditions. Record them:

```
model: <id and version>
temperature: <value>
max_tokens: <value>
tools: <none or list>
harness: <name and version>
date: <ISO date>
case_set: <sha256 of sorted case ids + label version>
```

Run each case once per variant when the target is deterministic. If the target is non-deterministic (temperature > 0, sampling, tool variability), run 3 trials per case, aggregate to one case-level outcome by majority (ties fail), and report the per-trial spread. Never treat trials as independent cases and never compare a single run of A with a single run of B.

Store one JSONL record per case per variant per trial:

```json
{"case_id":"c017","variant":"baseline","trial":1,"stratum":"boundary","passed":false,"score":0.4,"format_ok":true,"tokens":812,"latency_ms":1430,"failure_class":"decision_boundary"}
```

`passed` is required and accepts `true/false`, `0/1`, or `pass/fail`. `trial` is optional; rows with distinct trials are aggregated by majority (ties fail). `stratum` may be omitted or `null` (treated as `unset`) but must be identical for a case across all variants. `score` is optional partial credit in `[0, 1]`; `format_ok` is an optional boolean used for format compliance. The report must show format coverage as checked cases / total cases; incomplete coverage cannot satisfy the 100% format gate. `failure_class` should use the taxonomy so the diagnosis and the numbers agree.

`compare.py` accepts multiple rows per case/variant when they carry distinct `trial` values and aggregates them by majority. Duplicate `case_id`/`variant`/`trial` rows are rejected. Mixed trial and non-trial rows for the same case are rejected.

Defaults: `--min-n 50` (minimum paired cases for a significance result), `--min-stratum-n 10`, `--adjust holm`. If paired n is below `--min-n`, the script reports p-values descriptively but does not mark the comparison significant. Use `--skip-invalid` only to triage a dirty file; inspect the reported rows before a ship decision.

## 4. Judging

### Deterministic first

Schema validation, enum checks, regex, required literals, length caps, exact-match fields. These are cheap, reproducible, and should never be delegated to a judge.

### LLM judge, if needed

1. Write the rubric as binary criteria, not a 1–10 vibe scale.
2. Label 20 cases yourself from a dev split, never the holdout, then measure judge agreement (Cohen's κ). Below 0.6, fix the rubric or the anchors; do not use the judge. If calibration cases overlap the comparison set, disclose the overlap and treat agreement as optimistic.
3. Judge pairwise (A vs B) rather than absolute scores when possible.
4. Randomize order and run both orders; count a win only when the verdict is stable across the swap.
5. Hide variant names and any metadata that leaks which one is new.
6. Use a different model family from the candidate where feasible. A model judging its own output is weak evidence.
7. Temperature 0, fixed judge version, and log judge prompts.

Known biases to control: position, verbosity (longer looks better), self-preference, and agreement with the most recent instruction. Swapping positions and using concise rubrics covers most of it.

### Human spot-check

At least 10% of cases (minimum 5), blind, sampled across strata. Disagreements with the judge are adjudicated by a third read, and the adjudication is recorded. The spot-check is not decoration; it is the calibration signal for the judge.

## 5. Statistics

### Pass rate interval (Wilson)

```
center = (p + z²/(2n)) / (1 + z²/n)
half   = z * sqrt(p(1-p)/n + z²/(4n²)) / (1 + z²/n)
```

Use Wilson, not the normal approximation, at n < 100 and p near 0 or 1.

### Paired comparison (McNemar exact)

Only cases present in both variants are paired. Let:

- `b` = baseline pass, candidate fail
- `c` = baseline fail, candidate pass

```
p = 2 * Σ_{k=0}^{min(b,c)} C(b+c, k) / 2^(b+c)   (capped at 1)
```

This tests whether the direction of change is symmetric. It says nothing about effect size; report the delta and its interval alongside it.

### Delta interval (paired bootstrap)

Resample case IDs with replacement 5,000 times, compute `rate(candidate) - rate(baseline)` each time, take the α/2 and 1−α/2 percentiles (2.5th and 97.5th at α = 0.05). Seed the RNG so the interval is reproducible. For small n the interval is wide, which is the honest result.

### Adjusted p-values and multiple variants

Three variants against one baseline at α = 0.05 gives roughly a 14% chance of at least one false positive. The script defaults to Holm adjustment across candidate variants and reports both raw `p` and `p_adj`; `--adjust bonferroni` is available, and `--adjust none` is for exploratory analysis only. Either apply Holm (or Bonferroni) or designate one primary variant in advance and say so before looking at results.

Ship only when `p_adj < α` **and** the delta CI excludes zero. A result with a positive CI but `p_adj ≥ α` is directional or canary-only, not a ship.

### What not to say

- "No significant difference" is not "equivalent".
- A p-value is not an effect size.
- A 2-point gain on 20 cases is not a finding.
- "The judge preferred it" is not a task-success result.

## 6. Worked example

50 cases, baseline 35/50 (70%), candidate 42/50 (84%). Discordant: b = 2, c = 9 (n = 11).

- McNemar exact: `2 × (C(11,0)+C(11,1)+C(11,2)) / 2^11 = 2 × 67 / 2048 ≈ 0.065`.
- Delta: +14 pp; paired bootstrap 95% CI is roughly +2 to +26 pp.

Read: directionally positive, not significant at 50 cases. With one comparison, Holm-adjusted `p_adj` equals raw `p = 0.065`, so the ship rule fails; treat it as directional or canary-only. If the decision matters, collect more cases. Do not report "accuracy improved to 84%" as if it were established.

The same data with b = 2, c = 12 gives p ≈ 0.013: a similar rate but a more consistent direction. Consistency of change matters more than the raw delta.

## 7. Reporting

```markdown
| Variant | n | Pass | Rate | 95% CI | Δ vs baseline | p | p_adj | Tokens | Latency |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 50 | 35 | 70% | 56–81% | — | — | — | 210 | 0.9s |
| A | 50 | 42 | 84% | 71–92% | +14 pp | 0.065 | 0.065 | 470 | 1.4s |

Also report trial count, trial spread, score, and format compliance when those fields were collected.
```

Then a per-stratum table, the decision, the limitations, and the artifact paths. State whether the result is conclusive or directional.

## 8. Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Test leakage | Score keeps climbing as examples are added | Freeze the set; add new cases instead |
| Tuning on the holdout | Final number drops in production | One look only; rotate sets |
| Single run | Results flip between runs | 3 trials, report spread |
| Trials treated as independent cases | n inflates and p-values look stronger | Aggregate to one case-level outcome by majority |
| Unadjusted multiple comparisons | One of several variants looks significant by chance | Holm or Bonferroni (`--adjust holm`) |
| Judge drift | Same output, different verdicts over time | Pin judge version; re-calibrate |
| Metric gaming | Format improves, task success does not | Keep task success primary |
| Cost blindness | +3pp for 4× tokens | Report token delta; set a budget before testing |
| Ambiguous labels | Prompt blamed for label noise | Adjudicate; move to boundary stratum |
| Ignoring strata | Overall gain hides a boundary collapse | Always break down by stratum |
