# Failure Taxonomy

Classify every failing case exactly once, by its **primary** cause. Count by class and stratum, then rank by `frequency × cost`. A class with fewer than three observed failures is a hypothesis, not a pattern.

## Classes

### F1 — Objective ambiguity

**Looks like:** outputs are well-formed but not what the user needed; two reviewers disagree on whether a case passed; the model produces a generic answer to a specific need.
**Cause:** the prompt states a topic, not an observable outcome, audience, and definition of done.
**First move:** rewrite the objective as "given X, produce Y for audience Z, judged by W". Add the done criterion, not more style rules.
**Avoid:** piling on adjectives ("professional, high-quality, comprehensive").

### F2 — Missing input or context

**Looks like:** the model invents a value; output says "assuming…"; accuracy jumps when one extra field is supplied; empty or partial input is handled inconsistently.
**Cause:** the prompt never says which inputs arrive, what shape they have, or what to do when one is missing.
**First move:** write an input contract (fields, types, required/optional, max length) and an explicit missing-data behavior (`ask`, `output null`, `stop with reason`). Delimit each input block.
**Avoid:** telling the model to "use the context" without saying where the context starts and ends.

### F3 — Output contract drift

**Looks like:** extra prose around JSON, markdown fences when raw JSON was required, wrong keys, free-text labels, truncated lists, inconsistent ordering.
**Cause:** the output format is described in prose rather than specified as a schema with allowed values and an invalid-output rule.
**First move:** add a schema block, one minimal example, and a rule for invalid or empty results. Use the provider's structured-output or tool schema when available.
**Avoid:** repeating "please follow the format exactly"; it does not create a contract.

### F4 — Decision boundary confusion

**Looks like:** a confusion matrix with one dominant off-diagonal cell; the model labels by keyword rather than by the underlying condition; boundary cases flip between runs.
**Cause:** categories are named but not defined; no inclusion/exclusion criteria, no precedence, no tie-breaker.
**First move:** define each class by its **observable condition**, add ordered decision rules with a default, and state the tie-breaker. Add two hard negatives per confused pair.
**Avoid:** adding labels or examples before the boundary rule exists; that usually increases confusion.

### F5 — Example coverage or bias

**Looks like:** the model copies surface features of the examples; rare classes get worse after examples are added; near-duplicate examples crowd out coverage; performance drops on inputs unlike the examples.
**Cause:** examples are unbalanced, too similar, mislabeled, or leak the test distribution.
**First move:** keep 2–5 examples, one per confused boundary, balanced across labels, with hard negatives. Remove examples that duplicate test cases.
**Avoid:** adding examples until the eval set passes. That is leakage.

### F6 — Multi-step or decomposition failure

**Looks like:** steps are skipped, arithmetic or aggregation is wrong, a later constraint contradicts an earlier step, the model answers before gathering what it needs.
**Cause:** the task needs intermediate state but the prompt asks for a single leap.
**First move:** specify the intermediate artifacts (extract → check → decide), with a checkpoint where the model can self-correct. Keep the steps observable in the output.
**Avoid:** adding "think step by step" to a reasoning model that already plans; specify the required intermediate result instead.

### F7 — Grounding and evidence failure

**Looks like:** claims without support, invented citations or IDs, answers that ignore supplied documents, confident answers when the source is silent.
**Cause:** no evidence requirement, no abstain path, no instruction to quote or cite.
**First move:** require a quote or span ID per claim, define an explicit "insufficient evidence" output, and put the source before the question. Verify citations mechanically where possible.
**Avoid:** "do not hallucinate"; it states the goal without a procedure.

### F8 — Tool or agent policy failure

**Looks like:** wrong tool, redundant calls, loops, early stop, side effects without confirmation, permission escalation, ignored tool errors.
**Cause:** the prompt does not define when to use which tool, when to stop, what needs approval, or how to recover.
**First move:** add a tool table (use when / do not use when), stop conditions, retry and escalation limits, and an explicit confirmation rule for irreversible actions.
**Avoid:** describing tools in narrative prose that competes with the actual tool descriptions.

### F9 — Refusal and safety calibration

**Looks like:** refuses a benign request, complies with a harmful one, gives a partial answer with no safe alternative, or applies policy inconsistently across paraphrases.
**Cause:** scope and refusal conditions are implicit; no examples of the boundary.
**First move:** state the allowed scope, the refusal condition, and the safe-alternative path. Add one benign-boundary and one harmful case. Test paraphrases.
**Avoid:** blanket "be safe" language; it produces both over- and under-refusal.

### F10 — Verbosity, tone, or length

**Looks like:** answers exceed the cap, bury the result, switch register, or pad with restatements.
**Cause:** the length or tone constraint is far from the output instruction, or is stated as a preference rather than a limit.
**First move:** put a hard cap and one short exemplar next to the output contract. Cut duplicate instructions.
**Avoid:** stacking "concise, brief, to the point" in three places.

### F11 — Model or harness mismatch

**Looks like:** the prompt worked on another model; output truncates at the context limit; tools or structured output behave differently; latency or cost jumped.
**Cause:** prompts are model- and harness-specific; settings and context budgets changed.
**First move:** re-baseline on the actual target, check context budget and tool availability, and adapt format conventions to the provider. Treat cross-model transfer as a hypothesis to test.
**Avoid:** assuming a gain transfers across models or versions.

### F12 — Instruction conflict or precedence

**Looks like:** the model satisfies rule A and violates rule B; emphasis changes which rule wins; the same instruction appears twice with different wording.
**Cause:** contradictory or duplicated instructions with no precedence order.
**First move:** remove duplicates, order the rules, and state which one wins on conflict. Put the non-negotiable rule last and make it specific.
**Avoid:** adding "IMPORTANT" to both sides of a conflict.

## Classify in one pass

For each failing case, record:

| Field | Content |
|---|---|
| Case ID | Stable ID from the eval set |
| Input | The exact input (redacted) |
| Actual | The model output |
| Expected | Label or pass rule |
| First divergence | The first token or field where it went wrong |
| Class | One F-code |
| Severity | `blocking` (wrong or unsafe), `quality` (partial), `cost` (too slow/long) |
| Evidence | Quote that supports the classification |

Then aggregate:

```markdown
| Class | Typical | Boundary | Adversarial | Regression | Total | Cost weight | Priority |
|---|---|---|---|---|---|---|---|
| F4 | 2 | 6 | 0 | 1 | 9 | high | 1 |
| F3 | 0 | 1 | 4 | 0 | 5 | high | 2 |
```

`Priority = frequency × cost`, not frequency alone.

## From taxonomy to hypothesis

Write one sentence per selected class:

> Because the prompt defines "feature request" only by its name, the model labels any message containing "can you add…" as a feature request even when the user is reporting a broken export (F4, 9/50 cases, 6 boundary).

A hypothesis names the missing element, the observed behavior, and the case shape. If you cannot fill all three, you are guessing.

## When the taxonomy does not fit

If more than 20% of failures land in "other", the taxonomy is wrong for this task or the labels are inconsistent. Stop optimizing and fix the measurement first. A prompt cannot fix a label definition that two humans read differently.
