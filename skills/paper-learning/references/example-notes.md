# The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement — distilled notes

Source: arXiv:2609.11873; version/date: unknown (record abs `vN` and date when fetched).
Coverage: distilled from accessible text; page-level locations not recorded.

## Problem and contribution
Survey plus position paper on recursive self-improvement (RSI): systems that
turn experience into persistent state changes that improve both current
capability and the process of future improvement. The contribution is an
autonomy-centered ruler, not a new model. (Paper claim.)

## Core ideas
- **HCI (Eq. 2)**: `H = 100 * (s - F0) / (100 - F0)`, where `F0` is the
  90th-percentile score of the benchmark's entry year. `H=0` is that frontier;
  `H=100` is perfect.
- **Improvement loop**: experience → propose a modification → evaluate under an
  acceptance rule → retain accepted change → successor inherits and loops.
- **B0–L5 ladder**: what the AI autonomizes versus what humans retain, from
  in-task only (B0) to rewriting the improver itself (L5).

## Evidence and results
Paper's 2026 finding (as stated): bounded tasks near-closed (grad science
~85.8, math ~86.4); interactive tasks lag (software engineering 52.6,
terminal/search 56.8, tool agents 39.9). Argument paper: no new ablation table.

## Limitations and open questions
Author-stated: higher autonomy is not a better improvement process; L2+ hazards
include benchmark overfitting, extra search compute mistaken for algorithm
gains, and heritable errors. Inference: novelty is a unifying ruler more than a
new method; the 2026 numbers are not reproducible from the paper alone without
the owner tables. Speculation: L3–L5 extensions such as rewriting `propose_*`.

## Demo (optional)
`papers/rsi-2609-11873_demo.py` — `python3 papers/rsi-2609-11873_demo.py`.
Illustrates HCI and an L1 vs L2 loop with a no-regression gate. Does not
reproduce the reported domain scores (`F0` in Part A is synthetic).
