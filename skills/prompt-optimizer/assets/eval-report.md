# Eval Report: <prompt name> v<n>

- **Decision:** ship / iterate / reject / quick-unvalidated
- **Date:** <YYYY-MM-DD>
- **Owner:** <name>
- **Target:** <model + version, harness, temperature, tools, context limit>
- **Tokenizer:** <tokenizer name/version, or "character estimate">
- **Judge calibration:** <n cases, dev split, Cohen's κ, overlap none/disclosed>
- **Case set:** <n cases, strata, real/synthetic, hash>
- **Split:** <development n; sealed holdout n; holdout opened after candidate freeze>
- **Run record:** <path to JSONL> · <1 or 3 trials per case; majority aggregation, ties fail>

## 1. Contract

| Field | Value |
|---|---|
| Objective | |
| Inputs | |
| Output contract | |
| Invariants | |
| Audience | |
| Tools / permissions | |
| Success metric | |
| Failure cost | |

## 2. Baseline and diagnosis

Baseline prompt:

```text
<paste verbatim>
```

| Failure class | Typical | Boundary | Adversarial | Regression | Total | Priority |
|---|---|---|---|---|---|---|
| | | | | | | |

Hypotheses:

1. Because …, the model … on …
2. …

## 3. Variants

| Variant | Single change | Hypothesis | Tokens vs baseline | Risk |
|---|---|---|---|---|
| A | | | | |
| B | | | | |
| C | | | | |

Diffs:

```diff
--- baseline
+++ variant A
@@
```

## 4. Results

`n` counts cases after trial aggregation (not trial rows).

| Variant | n | Pass | Rate | 95% CI | Δ vs baseline | p | p_adj | Sig | Prompt tokens | Latency |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | | | | | — | — | — | — | | |
| A | | | | | | | | | | |
| B | | | | | | | | | | |
| C | | | | | | | | | | |

Quality and trials:

| Variant | Score | Format | Trials | Trial spread |
|---|---|---|---|---|
| baseline | | | | |
| A | | | | |
| B | | | | |
| C | | | | |

Per stratum:

| Variant | Typical | Boundary | Adversarial | Regression |
|---|---|---|---|---|
| baseline | | | | |
| A | | | | |

Format compliance: <value and checked/total coverage>. Invariant violations: <none / list>. Judge agreement (κ): <value>. Human spot-check: <n cases, disagreements>. Prompt-token growth vs baseline: <value>.

## 5. Decision

<Ship / iterate / reject, with the rule that fired. State whether the result is conclusive or directional. Check all of: `p_adj < 0.05`, delta CI lower bound > 0, at least 50 paired holdout cases, no stratum with n ≥ 10 drops > 5pp, format compliance 100% with complete coverage, token budget respected, invariants intact.>

## 6. Recommended prompt

```text
<complete prompt>
```

## 7. Residual risks and next test

- <risk, likelihood, mitigation>
- <next experiment, success criterion>

## 8. Reproducibility

```
git commit: <hash>
case set hash: <hash>
development / holdout: <case counts; holdout freeze date>
model: <id and version>
temperature: <value>
judge: <model and version>
date: <ISO date>
command: python3 scripts/compare.py results.jsonl --baseline baseline --markdown --adjust holm --min-n 50
```
