# Attention Is All You Need — distilled notes

Source: arXiv:1706.03762; version/date: v7, 2023-08-02 (v1 2017-06-12).
Coverage: full text (HTML v7); key numbers verified against Tables 2–4.

## Problem and contribution
Dominant sequence-transduction models were RNN/CNN encoder-decoders joined by
attention. The paper's claim: recurrence and convolution can be removed
entirely — a pure-attention architecture (the Transformer) reaches better
quality while training faster and more parallelizably (Abstract, §1, §3).
The contribution matters because this architecture became the substrate for
subsequent large language models. (Paper claim.)

## Core ideas
- **Self-attention replaces recurrence**: every position attends to all
  positions in one step, removing the serial dependency on sequence length
  (§3.2.1, Eq. 1); per-layer cost is O(n²·d) (Table 1).
- **Multi-head attention**: h=8 parallel attention heads, each d_k=d_v=64 on
  d_model=512, so different relation types are modeled simultaneously (§3.2.2).
- **Positional encoding**: sinusoidal signals inject order information that the
  removed recurrence used to provide; learned and sinusoidal embeddings perform
  nearly identically (§3.5).
- **Stacked encoder-decoder**: 6 layers each with residual connections and
  layer normalization (§3.1).

## Evidence and results
Setup: WMT 2014 translation (newstest2014), BLEU (the paper states no
tokenization/casing detail). Transformer (big)
reaches 28.4 EN-DE / 41.8 EN-FR; Transformer (base) 27.3 / 38.1 (Table 2,
§6.1); the abstract claims >2 BLEU over the best prior results including
ensembles. Baselines in the same table: ByteNet 23.75, GNMT+RL 24.6, ConvS2S
25.16, MoE 26.03 (EN-DE, Table 2). Cost: big model trained 300,000 steps —
3.5 days on one 8-GPU P100 machine (§5.2); parameters 65M base / 213M big
(Table 3). Ablations (Table 3, §6.2): single-head attention is 0.9 BLEU worse
than h=8 and quality drops again at h=32; shrinking the attention key size
d_k hurts. Generalization: English constituency parsing F1 91.3 (WSJ-only) /
92.7 (semi-supervised) (Table 4, §6.3).

## Limitations and open questions
Author-stated: no explicit limitations section; the O(n²·d) per-layer cost in
sequence length is stated in Table 1. Inference: results are single runs with
no significance tests, so base-vs-big and head-count deltas (≈0.5–0.9 BLEU)
carry no error bars; evaluation is limited to translation and parsing. A reader
cannot retrain from the paper alone without the released code (external:
tensor2tensor); the tables let one verify reported numbers at face value only.
Speculation: the O(n²) cost motivated the later sparse/linear attention line of
work (beyond the paper).

## Demo (optional)
no demo — the mechanism is fully specified by Eq. 1–4 and §3.2; a re-derivation
would illustrate the equation, not test any paper claim.
