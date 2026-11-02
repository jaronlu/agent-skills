# Evidence and Claim Limits

Use this file to justify a method, or to check a claimed gain before repeating it. The rule is simple: **a published result supports a mechanism, not your number.**

## What the research supports

### Meta Prompting (Zhang, Yuan & Yao, 2023)

A Qwen-72B base model guided by example-free meta-prompts reached **46.3% pass@1 on MATH** and **83.5% on GSM8K**. The paper's later revision formalizes meta-prompting as typed prompt transformations and separates it from recursive meta-prompting; it explicitly notes that the formalism does not guarantee improved accuracy, and that the Game-of-24 agent's 100% result has token-accounting caveats.

What it supports: a strong model can write or improve prompts without task-specific worked examples.
What it does not support: the same gain on your task, your model, or your data.

### PE2 (Ye, Axmed, Pryzant & Khani, 2023; ACL 2024 Findings)

Adding three components to a meta-prompt — **detailed task description, context specification, and a step-by-step reasoning template** — produced prompts that beat "let's think step by step" by **6.3% on MultiArith**, **3.1% on GSM8K**, and **6.9% on counterfactual tasks**. PE2 also made targeted edits to existing prompts.

What it supports: the quality of the meta-prompt itself matters; vague "make it better" instructions underperform structured critique.
What it does not support: that PE2 works on production tasks without an eval set, or that its gains transfer across models.

### Google DeepMind's Veo example (2025-12-08)

A Google DeepMind UX engineer describes asking Gemini to write detailed video prompts for Veo — often 5–10 at a time, sometimes multiple pages — instead of writing them by hand. This is an **anecdotal practitioner report with no controlled comparison**.

What it supports: for generative models sensitive to detail, delegating prompt authorship to a strong language model can produce richer prompts.
What it does not support: any quantitative improvement, or the claim that longer prompts are better in general.

### Claude prompt improver (2024-10-14)

Anthropic's Console feature rewrites prompts with chain-of-thought sections, standardized and enriched examples, clarification, and assistant prefill. Anthropic reported **+30% accuracy on a multilabel classification test** and **100% word-count adherence on a summarization task**.

What it supports: structured rewriting can produce large gains on some tasks.
What it does not support: that the gain is typical. These are vendor-selected tasks, and the techniques are model-specific.

### Programmatic optimizers

DSPy (MIPROv2, GEPA, SIMBA), PromptWizard, TextGrad, and OPRO optimize prompts against a metric and a dataset. They are the right tool when you need to search a large space or optimize many prompts.

What they support: optimization is an empirical search problem, not a writing problem.
What they do not support: skipping the metric, the dataset, or the held-out evaluation.

## What the evidence does not support

| Claim | Status |
|---|---|
| "Meta-prompting typically improves prompts by 20–40%" | No controlled source; treat as marketing |
| "An LLM's judgment that version B is better is sufficient" | Self-preference and position bias are well documented; use blind, calibrated judging |
| "Longer, more detailed prompts are always better" | Detail helps when it removes ambiguity; it hurts when it adds tokens, conflicts, or overfitting |
| "A prompt tuned on GPT transfers to Claude/Gemini" | Cross-model transfer is a hypothesis; re-baseline |
| "One lucky run at n=20 proves the gain" | The interval is roughly ±20 points; see the evaluation protocol |
| "Prompt engineering is obsolete now that models are better" | Better models raise the baseline; they do not remove task-specific contracts, boundaries, or evaluation |

## How this skill uses the evidence

- The **meta-prompt asset** follows PE2: detailed task description, context, failure evidence, and an explicit reasoning template, plus invariants that PE2-style rewriting tends to drop.
- The **workflow** follows the empirical framing of DSPy-style optimization: baseline, metric, candidate search, held-out decision.
- The **claim rules** follow from the limits above: no percentage without a case set, a CI, and a recorded model/settings snapshot.
- The **quick mode** exists because the research gains are conditional on reuse and measurement; a one-off request does not justify the overhead.

## Sources

- Zhang, Y., Yuan, Y., & Yao, A. C.-C. (2023). *Meta Prompting for AI Systems.* arXiv:2311.11482. https://arxiv.org/abs/2311.11482
- Ye, Q., Axmed, M., Pryzant, R., & Khani, F. (2023). *Prompt Engineering a Prompt Engineer.* arXiv:2311.05661; ACL 2024 Findings. https://arxiv.org/abs/2311.05661
- Google. *A Googler explains how to "meta prompt" for incredible Veo videos.* 2025-12-08. https://blog.google/products-and-platforms/products/gemini/meta-prompting-veo-gemini-tips/
- Anthropic. *Improve your prompts in the developer console.* 2024-10-14. https://claude.com/resources/articles/prompt-improver
- DSPy. https://dspy.ai/
- PromptWizard. https://github.com/microsoft/PromptWizard
- TextGrad. https://github.com/zou-group/textgrad
- Suzgun, M. *Meta-prompting* repository (Game of 24). https://github.com/suzgunmirac/meta-prompting
- MR.PEA. https://openreview.net/forum?id=YSkby14i2v — cited by secondary sources; the primary page could not be independently verified at the time of writing.
