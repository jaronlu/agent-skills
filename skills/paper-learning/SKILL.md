---
name: paper-learning
description: "Distills and explains research papers into reusable per-paper notes. Use when the user shares a paper (arXiv id, URL, or PDF) or asks to learn, summarize, or critically read one."
---

# Paper Learning

Turn a paper into reusable notes, then answer the user's question from the evidence.

## Workflow

1. Identify the paper and check for existing notes at the user-specified path or
   workspace `papers/<slug>.md` (arXiv id or short name). Keep notes and demos
   outside the skill package; update existing notes in place.
2. Reuse notes only when they cover the question and the same paper version.
   Match the notes' source id and version/date to the request: for arXiv, the id
   plus `vN` from the abs/pdf URL, the user, or the notes' Source line. A URL or
   id without `vN` is the version current at fetch time — record that `vN` and
   date. If notes omit version/date, or id/`vN`/date differ, read the source and
   update. Otherwise read the relevant source: abstract, method, evidence, and
   limitations. If unavailable or only partly accessible, state the gap rather
   than inventing content.
3. Create or update notes using [the template](references/paper-template.md).
   Follow the shape in the filled examples — [argument-style paper](references/example-notes.md)
   and [experimental paper](references/example-notes-experimental.md); do not
   copy their paper-specific claims. Lead with conclusions, explain technical
   terms on first use, distinguish paper claims from your inferences, and attach
   source locations to key claims and numbers (section, page, table, or figure).
   Keep notes understandable on their own.
4. Answer the question using the relevant ideas, evidence, and limitations; link
   the notes. Verify missing evidence as needed. Fetch other papers or newer
   results when requested, keeping each paper's notes separate; otherwise state
   the scope boundary and stop.

## Optional demo

Use a demo only when it clarifies the mechanism. Choose a language or form suited
to the paper, and place files beside the notes as `<slug>_demo.<ext>`. Keep runnable
demos offline and deterministic; inspect code before running it, map outputs to
paper concepts, and distinguish illustration from reproduction of reported results.
If no meaningful demo exists, record "no demo".
