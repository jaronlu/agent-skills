# Evidence Verification

Read this file before executing Phase 7 (evidence and quality verification) in SKILL.md. Run the parts of the checklist below that apply to each page while writing, and run the full checklist once across the page set before `openwiki_finish`. On `update`, skip the sections that only apply to a new book.

## Phase 7 — Evidence and quality verification

Label every important claim with one of three confidence levels:

- **Verified:** directly supported by source, tests, or authoritative project documentation.
- **Inferred:** reasoned from multiple verified locations; explain the reasoning.
- **Unverified:** plausible but not established by available evidence.

Never silently present an inference as a verified fact.

After drafting, verify the documentation independently of the author's own assessment. Use search and read tools to check:

- Referenced source files exist.
- Referenced symbols exist.
- Important call relationships have source evidence.
- Every stated key call chain is verified hop by hop, including dispatch, registration, callback, and dependency-injection hops.
- Execution sequences match the implementation.
- Data-flow descriptions match the actual transformations.
- State transitions are supported by the implementation.
- Diagrams reflect real components and relationships.
- Flowcharts and sequence diagrams exist as SVG files under `openwiki/assets/` and are valid SVG that render without external assets. Parse each file with an XML parser and require a single `<svg>` root.
- Every image link in a page resolves from that page's own directory to an existing file under `openwiki/assets/`, and no page contains inline SVG markup. Check by listing `openwiki/assets/` and matching each page's image targets against the listing; a missing target fails the check.
- No asset exists without a page that links it.
- Diagram files survive the run: after `openwiki_finish`, re-list `openwiki/assets/` and confirm every referenced asset is still present.
- Every stale or unresolved Claim in the page job has an explicit decision: confirmed with `confirmedClaimIds`, revised under the same `id` in `claims`, or retracted with `retractedClaimIds`. The final page body and the reconciled Claim set agree.
- Every submitted Claim cites a `repo://` resource; no bare path is accepted.
- Code examples match actual APIs and signatures.
- Generated code is distinguished from handwritten code.

If the available tools cannot verify a claim, label it Unverified and disclose the limitation. Do not report a check as performed if it was not.

## Where confidence lives

The three confidence levels are a writing and verification device, not reader-facing prose.

- OpenWiki Claims have no confidence field. Record the judgement in the Claim statement: state Verified claims plainly, and prefix Inferred and Unverified claims with `Inferred:` or `Unverified:`. Do not duplicate it inline, and do not keep a parallel section-level note.
- An unsupported hypothesis belongs on the open-questions page, not in a Claim.
- The reader must be able to understand and trust the chapter without parsing confidence markers.

## Review checklist

Apply the sections that fit each page while writing it; run the full checklist once across the page set before `openwiki_finish`.

### Reader understanding
- [ ] The reader knows what problem the topic solves.
- [ ] New project-specific terms are explained before use.
- [ ] The explanation moves from context to mechanism to implementation.
- [ ] Cross-module relationships are explained rather than merely listed.
- [ ] The chapter has a clear learning objective.
- [ ] The chapter is understandable without opening any source file.
- [ ] Removing every source reference leaves a coherent, self-contained explanation.
- [ ] Code blocks carry their own explanation and can be replaced by prose without losing the mechanism.

### Source grounding
- [ ] Important implementation claims point to real source locations.
- [ ] Cross-file call chains have been verified.
- [ ] Every key call chain shown to the reader is verified hop by hop, including dispatch, callback, event, and DI hops.
- [ ] Dynamic dispatch, callbacks, events, reflection, and dependency injection are not guessed.
- [ ] Facts, inferences, and unknowns are distinguishable in the Claim record; the prose does not present an inference as a verified fact.
- [ ] Generated code is traced back to its schema or generator where applicable.

### Writing and structure
- [ ] The outline follows reader learning progression, not directory order.
- [ ] Each paragraph has one main point.
- [ ] Symbol names and file paths do not overwhelm the explanation.
- [ ] Examples match actual repository behavior.
- [ ] Each mechanism carries a key call chain and focused code excerpts; excerpts keep the original language and are trimmed to what carries the mechanism.
- [ ] Diagrams represent verified relationships.
- [ ] Flowcharts and sequence diagrams are SVG asset files under `openwiki/assets/`, not Mermaid, raster screenshots, or inline markup in the page.
- [ ] Every SVG parses as XML with a single `<svg>` root before it is linked.
- [ ] Every image link resolves from that page's directory to an existing file in `openwiki/assets/`, verified against a directory listing rather than by assuming the write succeeded.
- [ ] No asset exists without a page that links it.
- [ ] When the run language is Chinese, quotation marks in prose outside code spans are paired and oriented correctly: `“` opens, `”` closes, nested quotes use `‘’`, and no closing position is written as a second `“`.
- [ ] Repetition, filler, and unnecessary detail have been removed.

### Completeness
- [ ] The project purpose and overall architecture are understandable.
- [ ] Important mechanisms and end-to-end flows are covered.
- [ ] Design trade-offs are explained when evidence permits.
- [ ] The chapter ends with useful takeaways and understanding questions.
- [ ] The summary page traces every statement to a chapter, introduces no new factual proposition, submits only Claims that restate a chapter's statement and evidence, and respects the 2000-3000 character target and the one-tenth cap.
- [ ] A reader can reconstruct the system model and the role of the core mechanisms from the summary page alone when the book has one, or from the overview and first chapter when it does not.
- [ ] Limitations and unverified areas are disclosed.

### Repository understanding
- [ ] Entry points are identified and verified through source, not only directory names.
- [ ] Cross-file call chains are traced through verified call sites.
- [ ] Component responsibilities and boundaries are verified against the implementation.
- [ ] Data creation, transformation, transfer, and consumption are described from the code.
- [ ] State transitions are supported by guards, assignments, or transition code.
- [ ] Lifecycle and asynchronous or concurrent execution are described from the code.

### Scenario coverage
- [ ] Typical normal execution is covered.
- [ ] Cross-component collaboration is covered.
- [ ] Complex mechanisms (async, callbacks, retries, lifecycle hooks) are covered where present.
- [ ] Relevant error and recovery paths are covered.
- [ ] Each scenario traces trigger, entry point, initial state, sequence, output, and termination.
- [ ] Every scenario is supported by named source evidence; none is invented.

### Knowledge engineering
- [ ] Core concepts are identified and explained before they are used.
- [ ] Structural, runtime, and conceptual relationships are labeled as distinct kinds.
- [ ] The learning sequence follows conceptual dependencies, not the source-code dependency graph.
- [ ] Chapter prerequisites are consistent with the learning sequence.

### Chapter granularity
- [ ] Each chapter focuses on one primary knowledge topic.
- [ ] Chapters are not generated mechanically from files or classes.
- [ ] Cross-module mechanisms are explained together where they participate in one mechanism.
- [ ] Simple concepts are not split unnecessarily, and complex mechanisms are decomposed when it helps.

### Evidence verification
- [ ] Every referenced source file exists.
- [ ] Every referenced symbol exists.
- [ ] Important call relationships have source evidence.
- [ ] Data-flow descriptions match the actual transformations.
- [ ] State transition descriptions match the implementation.
- [ ] Diagrams match the verified components and relationships.
- [ ] Flowcharts and sequence diagrams are well-formed SVG asset files under `openwiki/assets/` with readable labels and no clipped or overlapping text; each SVG parses as XML; each page link resolves to an existing file; when `fireworks-tech-graph` was used, its `check` gate passed.
- [ ] Code examples match actual APIs and signatures.
- [ ] Quoted code is copied from the verified implementation, not reconstructed from memory.
- [ ] Generated code is distinguished from handwritten code.
- [ ] Every important claim's confidence is in its Claim statement (plain for Verified, `Inferred:` or `Unverified:` prefix otherwise), not in the prose.
- [ ] Every submitted Claim cites a `repo://` resource, and no Claim rests on an unsupported hypothesis that belongs on the open-questions page.
- [ ] Every stale or unresolved Claim in the page job is confirmed, revised, or retracted, and the final body matches the Claim set.
- [ ] Checks that the available tools could not perform are disclosed, not reported as passed.

### Knowledge maintenance
- [ ] Impact analysis uses the claim states OpenWiki reports (`stale`, `unresolved`) instead of a hand-written source-to-chapter map.
- [ ] Conceptual dependencies are recorded and used for impact analysis.
- [ ] Changed files and symbols are identified before updating.
- [ ] Affected items are classified as Unaffected, Needs review, Requires update, or Invalidated.
- [ ] Conclusions that depend on changed code are rechecked, not assumed still valid.
- [ ] Incremental consistency is claimed only for dependencies that were checked.

### Reader adaptation
- [ ] Each topic chapter declares its reading mode: first-time understanding, project-level architecture, or implementation-level investigation.
- [ ] First-time chapters give purpose, boundaries, and one end-to-end path before implementation detail.
- [ ] Architecture chapters explain component responsibilities and collaboration without reading as a file list.
- [ ] Implementation chapters give call chains, data transformations, and source locations.
- [ ] Project-specific concepts are explained, and general programming concepts are not taught.

Revise weak sections rather than publishing them as they stand. Do not mark a section as verified if it was not checked.
