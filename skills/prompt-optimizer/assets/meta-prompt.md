# Meta-Prompt: Generate Prompt Variants

Copy this into a strong model after filling the bracketed fields. It replaces the common "you are a prompt engineer, improve this" template: it feeds failure evidence, forbids invented gains, and forces one change per variant.

```text
You are a senior prompt engineer. Improve the baseline prompt below using only the evidence supplied.

## Task contract
[Paste the contract: objective, inputs, output contract, audience, tools, target model, success metric, failure cost]

## Invariants (must survive byte-for-byte)
[List literals, placeholders, terminology, locale, caps, policy text]

## Baseline prompt
"""
[Paste the exact baseline]
"""

## Failure evidence
Case set: [n cases, strata, synthetic or real]
Baseline result: [pass rate, per-stratum rates]
Failure classes and counts: [F-code: count, with 2-3 redacted examples each]

## Constraints
- Target: [model, harness, temperature, tools, context limit]
- Token budget: no more than [125%] of the baseline unless you justify the increase
- Do not add facts, requirements, tools, or examples that are not supported by the evidence
- Do not claim an accuracy gain; you have not run the evaluation

## What to produce
1. Diagnosis: for each of the top two failure classes, one sentence in the form
   "Because the prompt <missing element>, the model <observed behavior> on <case shape>."
2. Up to three variants; include only distinct useful interventions. Use one or two when there is only one diagnosed failure class, and do not invent a third to fill the template. Each variant:
   - changes exactly one thing (or two tightly coupled things) tied to one failure class;
   - preserves every invariant;
   - includes the complete revised prompt in a fenced block;
   - states the hypothesis, the exact diff, the expected failure reduction, the risk, and the token delta.
3. A recommendation: which variant to test first and why.
4. Open questions: only those that block a correct rewrite.

Variant plan (omit any slot that does not have a distinct hypothesis):
- A: fix the highest-frequency failure class.
- B: fix a distinct highest-cost failure class.
- C: a distinct output-contract/boundary fix or conservative minimal edit.

If the evidence is insufficient to support a change, say so and propose the smallest test that would settle it. Do not invent case counts, examples, or results.

Before returning, check:
- Every invariant still appears verbatim.
- No variant adds a requirement that was not in the contract.
- Each variant's diff matches its stated hypothesis.
- No accuracy number appears anywhere in your answer.
```

## Notes for the operator

- Redact case content before pasting. Keep the holdout out of the prompt entirely.
- If the model returns three variants that all rewrite everything, send it back with: "Each variant must change one thing; show the diff."
- Treat the recommendation as a candidate ordering, not a decision. The eval loop decides.
- If the model asks for the eval set, give it only the design split, never the holdout.
