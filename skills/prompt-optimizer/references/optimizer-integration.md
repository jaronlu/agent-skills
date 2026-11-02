# Programmatic Optimizer Integration

Use this reference only when the user asks to use an open-source optimizer or when manual candidate generation is too limited for the measured task. The optimizer is a candidate-search method inside the measured workflow; the skill still owns the contract, data split, independent evaluation, and ship decision.

## Pick a search shape

Start with the smallest search that matches the observed failure:

| Search shape | Consider when | Example from DSPy |
|---|---|---|
| Add/select demonstrations | The task is clear, but representative examples may improve behavior | `BootstrapFewShot` |
| Search instructions and demonstrations | The instruction itself is underspecified and there is enough labeled development data | `MIPROv2` |
| Reflect on execution traces and propose edits | Failures need natural-language diagnosis and the task has a reliable feedback metric | `GEPA` |

Related open-source approaches include **PromptWizard**, which iteratively refines instructions and demonstrations, and **TextGrad**, which uses textual feedback to update prompt-like components. Treat these as algorithm examples, not product endorsements; inspect current repository maintenance, license, API compatibility, and dependency requirements before adopting one.

These are options, not universal rankings. Prefer a targeted instruction edit for one clear failure class. Do not introduce a framework or convert a static prompt into a multi-module program unless that change is in scope and useful to the user.

## Define the optimizer interface

Before running search, make these items explicit:

- **Program/task:** the prompt or module being optimized, with its input and output contract.
- **Metric:** a deterministic check or anchored rubric that scores the behavior the user needs. Keep required format and safety constraints as hard checks, not soft preferences that can be traded away for a higher aggregate score.
- **Development data:** only the development split may be supplied to the optimizer. Few-shot examples must be drawn from this split and must not duplicate or paraphrase evaluation cases.
- **Feedback:** provide failure labels or concise, redacted explanations where the optimizer supports reflective feedback. Do not expose holdout failures as feedback.
- **Budget:** set a finite limit for candidate trials, model calls, tokens, and wall time before search. Record what was actually spent.
- **Reproducibility:** record framework and optimizer version, metric version, seed or randomness settings, target model/settings, candidate configuration, and development-set hash.

If there is no reliable metric or labeled development set, do not run automated search and present its output as evidence. Offer a provisional synthetic development set, or use Quick mode for a one-off request.

## Run and select

1. Run the baseline using the same task implementation and metric intended for the optimizer.
2. Run the optimizer only on development data, respecting the predefined budget. Save its configuration, candidate outputs, scores, and failures.
3. Select one candidate using development results and the contract's hard constraints. Do not select by a single scalar score if it hides format, safety, or per-stratum regressions.
4. Freeze the selected candidate before revealing holdout data. Compare the baseline and frozen candidate on the holdout using the evaluation protocol in `evaluation.md`.
5. If the holdout gate fails, report that honestly. Do not feed holdout errors back into another search and continue calling the same data a holdout; rotate or collect a new sealed set before another confirmatory claim.

The optimizer's own development score is a search signal, not an unbiased estimate of production performance. More search trials increase the chance of overfitting the development set; disclose the search budget and treat the sealed holdout as the final check.

## Framework notes

- **DSPy** is a code-first framework: define a task/module and metric, then use an optimizer to compile or tune it against examples. Its result may be a DSPy program or module configuration rather than a portable standalone prompt. Explain this integration cost before recommending it as a drop-in prompt editor.
- **PromptWizard** and **TextGrad** use different search and feedback designs from DSPy. Map their behavior to the same contract, metric, data-split, budget, and holdout requirements instead of assuming they share DSPy's semantics.
- Do not add an optimizer dependency to this skill's required runtime. Use the framework only in the user's project or an isolated experiment when requested and available.

## Sources

- DSPy optimization guide: https://dspy.ai/learn/optimization/overview/
- DSPy project: https://github.com/stanfordnlp/dspy
- PromptWizard project: https://github.com/microsoft/PromptWizard
- TextGrad project: https://github.com/zou-group/textgrad
