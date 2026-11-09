# Documentation Standards

Read this file before executing Phase 6 (human-readable documentation) in SKILL.md. The writing requirements and chapter ending rules below apply to every chapter produced in any phase.

## Phase 6 — Human-readable documentation

Select and combine the patterns below according to the topic. Do not force every section into every pattern.

**Concept**
- What is it?
- Why does it exist?
- What problem does it solve?
- Where does it sit in the system?
- Which nearby concepts are easy to confuse with it?
- Give a concrete, repository-consistent example.

**Mechanism or principle**
- Problem and constraints
- Core idea
- Step-by-step operation
- Relevant implementation
- Design trade-offs and limitations

**Execution flow**
- Trigger and entry point
- Preconditions
- Call chain and component handoffs, shown as a key call chain block
- Important data and state changes
- Output or side effect
- Error, retry, cancellation, and boundary behavior where relevant

**Architecture**
- Overall structure
- Component responsibilities
- Dependencies and collaboration
- Control and data flows
- Reasons for boundaries and design trade-offs

**Comparison**
- Compared alternatives
- Shared goal
- Material differences
- Advantages, costs, and constraints
- Why this repository uses its current approach, if evidence supports that conclusion

**Practice**
- Goal and prerequisites
- Steps and key code
- Expected result
- Verification method
- Common failure modes

Use only the patterns that add explanatory value.

### Summary page

One planned page compresses the book into a ten-minute read. Do not confuse it with the overview: the overview fixes purpose and boundaries, while this page explains how the system works at a level just above the chapters.

- Open with one paragraph that names the problem and what the system does about it, then the system model in two to four sentences.
- When the book has a top-level architecture diagram, link the same `openwiki/assets/` file the architecture page uses. Do not draw a new diagram for this page; if the book has no top-level diagram, the summary carries none.
- Summarize three to eight core mechanisms, each in at most five sentences with one single-line call chain and no code excerpts. Carry the problem, the idea, and what breaks without it.
- Compress the running example into eight to twelve numbered steps that name the component handoffs.
- List what the book does not cover and which areas remain unverified.
- Introduce no new factual proposition. Every statement must trace to a chapter; any Claim submitted for this page restates that chapter's statement and evidence rather than adding new evidence.
- Target 2000-3000 characters in the run language, but never exceed one tenth of the book's total characters. When the two conflict, the one-tenth cap wins and the summary stays shorter than 2000.
- Rewrite the chapter takeaways as one connected explanation instead of pasting them together.

The chapter-ending sections do not apply to this page.

### Overview page

The overview fixes purpose and boundaries. It is not the summary and does not explain mechanisms.

- One paragraph: what the project is, who it serves, and what problem it solves at the highest level.
- Boundaries: what the project owns and does not own, with external systems named.
- A short map of major components and their responsibilities, without call chains or implementation detail.
- Links to `quickstart.md` and, when present, `summary.md`.
- No code excerpts and no mechanism walkthrough.

### Quickstart page

The quickstart is the book's entry point and reading router.

- One-paragraph orientation, anchored in at least one verified fact about the project.
- Short route: the summary page when present, then the core chapters, sized for a ten-minute pass.
- Full route: the overview, then the chapters in learning order.
- Task routing: short "if you want to X, read Y" entries that link only to pages that exist in the plan.
- No mechanism explanation of its own; route to the chapter that owns it.

### Glossary page

- One entry per project-specific term that a chapter defines.
- One or two sentences per entry, using the exact term the chapters use, plus a link to the chapter where it first appears.
- Do not explain mechanisms or repeat chapter prose; do not expand an abbreviation without verified evidence.
- Keep a stable order, alphabetical or first-use, and update the entry when a chapter redefines the term.

### Open-questions page

- One entry per unresolved area: what is unverified, why it could not be verified, what evidence or check would resolve it, and which chapter is affected.
- Never turn a guess into a Claim; an unsupported hypothesis belongs here, not in a chapter.
- Remove an entry when it is resolved, and update the chapter that depended on it.
- Keep the list short and specific; do not use it as a backlog of unread files.

Every factual page, including overview, quickstart, glossary, and open-questions, must establish at least one repository-grounded Claim. A routing-only page still anchors its orientation in a verified fact.

### Narrative shape

For any mechanism worth a chapter, prefer this arc over a feature list:

1. The problem the reader can already feel
2. Why the obvious approach fails here
3. The key insight
4. The mechanism, step by step, on the running example
5. Where it breaks, and what the code does about that
6. What the reader can now do or predict

Return to the running example from Phase 3 rather than introducing a new example per section.

### Code in prose

- Place each block after the reader already knows what to look for.
- Quote only the lines that carry the mechanism.
- Caption every block with what to notice.
- Explain non-obvious lines only; do not narrate syntax.
- Prefer prose or clearly labeled pseudocode when the exact text is not the point. Never present pseudocode as a code excerpt.
- Treat a code block as replaceable: the surrounding prose must still explain the mechanism if the block is deleted.

### Key call chains

Every mechanism and execution-flow section carries the verified path from trigger to effect as one compact call-chain block.

- One hop per line, entry first, joined by `→`. Name each hop with its real symbol, not a paraphrase.
- Annotate a hop only when its responsibility is not obvious from the name, for example `→ TextNode（页码/偏移）`. Keep the annotation short.
- Include the hops the explanation depends on: dispatch, registration, callback, event, dependency-injection resolution, or persistence. Do not skip a hop that would otherwise look like magic.
- Use the repository's actual identifiers. Keep file paths and line numbers optional and strippable.
- Mark an unverified hop as `?` or omit it and say so; never fill a gap with a plausible symbol.
- One chain per scenario. Do not repeat an identical chain in several sections.

A chain may be a single line for a shallow path or indented lines when hops carry annotations:

```text
handle_request → AuthGuard.verify → Router.dispatch → Handler.serve
  → Repository.find（事务边界）→ Cache.set → response
```

The block is evidence, not decoration: the prose must already explain why each hop exists.

### Key code excerpts

For each mechanism, quote the code that carries it. Every mechanism that describes implementation quotes at least one excerpt; concept-only sections are exempt.

- Select 1–3 excerpts per mechanism; the smallest block that shows the signature plus the branch, loop, handoff, or registration that matters.
- Keep the original language, indentation, and identifiers, including Objective-C method declarations or C signatures. Never translate code into pseudocode while calling it code.
- Prefer the excerpt that proves the claim over the excerpt that summarizes the file. Configuration keys, type declarations, dispatch tables, and test assertions can be the key code.
- Caption each excerpt with what to notice, before or after it, and explain only the non-obvious lines.
- Keep the excerpt small enough to read in one sitting; trim unrelated lines and mark omissions rather than pasting whole functions.
- Apply the strip test: if the excerpt is deleted, the prose still explains the mechanism.

### SVG assets

Flowcharts and sequence diagrams are SVG artifacts, not Mermaid or PlantUML source and not screenshots. Architecture, state, and data-flow diagrams, icons, and logos follow the same rule: every SVG a page uses is a separate file.

- Author every flowchart and sequence diagram as SVG.
- Save each SVG as its own file under `openwiki/assets/`, named in ASCII kebab-case for what it shows (for example `openwiki/assets/request-lifecycle.svg`). The page holds only the reference, never the SVG source.
- Reference the file with a relative image link written from the page's own directory that resolves to `openwiki/assets/<name>.svg`, at any nesting depth. From `openwiki/architecture/request.md`, that is `../assets/request-lifecycle.svg`; from a top-level page it is `assets/request-lifecycle.svg`. Give the image descriptive alt text naming the asset, so the prose still reads if the image fails to load.
- Do not inline `<svg>` markup in the page, do not base64-encode an image into the page, and do not place SVG files outside `openwiki/assets/`.
- Validate every asset before linking it: parse the file with an XML parser and require a single `<svg>` root. A parse error fails the page check; do not rely on the renderer to reveal malformed SVG.
- If the `fireworks-tech-graph` skill is available, use it: generate or edit the diagram through its `flowchart` or `sequence` mode, writing the SVG straight to `openwiki/assets/`, run its `validate`, `render`, and `check` gates, and fix reported geometry or label problems before referencing it.
- Without that skill, hand-author valid SVG: one root `<svg>` with an explicit `viewBox`, text in real `<text>` elements, arrowheads declared as `<marker>`, and no external fonts, images, stylesheets, or scripts.
- Never substitute a Mermaid block, a text description, or a raster screenshot for a required flowchart or sequence diagram. If the page renderer cannot load a referenced SVG, disclose that limitation instead of silently inlining the markup or changing the format.
- Label every participant, lifeline, decision, handoff, and edge so the diagram explains itself at reading size. Check for clipped text, overlapping labels, and unlabeled arrows.
- At most one diagram per mechanism or scenario, and only when the prose and call chain cannot carry the relationship on their own. State the question it answers before the link, and explain the diagram after it, so deleting the reference leaves the prose coherent.
- Reuse one visual style and palette across the book so diagrams read as one system.
- Reuse one asset for one diagram: when two pages need the same diagram, link to the same file instead of copying it. If only one page's diagram must change, create a new asset, retarget that page, and delete the old file when no other page links it.
- Do not leave an asset that no page links.

### Explain implementation with evidence

When explaining actual repository behavior:

- Name the source path and the relevant symbol (class, function, type, configuration key, or registration) so the claim can be checked.
- Include line numbers or a small code excerpt only when the available tools support reliable locations and the reader benefits from them. Keep location references separable from the sentence carrying the explanation, so they can be stripped without breaking it.
- Explain what the code contributes to the larger mechanism.
- Trace cross-file behavior through verified call sites, registrations, dispatch, dependency injection, events, or configuration.
- Cite tests and examples when they demonstrate intended behavior.
- Avoid dumping large source blocks. Quote only the code needed to support the explanation.
- Never publish a credential, token, connection string, private key, internal host, or `.env` value: redact it in place, keep the surrounding line, and do not hint at the removed value's length or format. The same rule applies to diagrams and to Claim statements.

Never invent a call chain based only on naming similarity or architectural convention. Dynamic dispatch, reflection, callbacks, event buses, dependency injection, async tasks, and generated registries require special care.

Keep the page body and the Claim set aligned: the body carries the proposition, the Claim carries the evidence and the confidence qualifier, and every Claim cites a `repo://` resource. Never print a confidence label in the prose.

### Handle generated code and schemas correctly

When the repository contains generated code, identify the generation boundary.

Explain, when applicable:

1. The source definition or schema
2. The generator, compiler, or parser
3. The generated artifacts
4. How handwritten code consumes those artifacts
5. Which files should or should not be edited manually
6. How and when regeneration occurs

Keep generated code distinct from handwritten business logic. Do not treat generated files as independent design sources when their schema or generator is the real source of truth.

## Writing requirements

- Use the output language the surrounding workflow supplies, such as the `language` returned by an OpenWiki run. Default to clear Simplified Chinese only when the host or project context specifies none.
- Preserve canonical English technical terms. On first use, write a clear explanation in the run language followed by the English term where useful.
- When the run language is Chinese, pair Chinese quotation marks correctly in prose: open with `“` (U+201C) and close with `”` (U+201D), and use `‘’` for a quote nested inside one. The common slip is closing a quote with another `“`, which silently reverses the pair. Before submitting a page, scan the prose outside code spans and code blocks for unbalanced `“`/`”` counts and for a `“` that sits immediately before `。`, `，`, `、`, or the end of a sentence.
- Expand project-specific abbreviations on first use when their meaning can be verified.
- State the chapter's reading mode in its opening paragraph; do not add a frontmatter field for it.
- Lead with the conclusion or question being answered.
- Use short, focused paragraphs and descriptive headings.
- Explain jargon; do not explain one unknown term with several other unknown terms.
- Use concrete examples grounded in repository behavior.
- Give each mechanism a verified key call chain and the short code excerpts that carry it, not merely prose about the code.
- Draw diagrams as SVG files under `openwiki/assets/`, linked from the page; icons and logos follow the same asset rule. `fireworks-tech-graph` is an optional dependency outside this skill package: use it for flowcharts and sequence diagrams when it is installed, and fall back to the hand-authored SVG route in **SVG assets** when it is not. Add diagrams only for meaningful architecture, sequence, flow, state, or data relationships; do not add them decoratively.
- Avoid repeated definitions, generic filler, and claims such as "highly scalable" unless evidence and constraints are explained.
- Do not speculate about author intent. Distinguish explicit design rationale from rationale inferred from implementation.
- Do not force every chapter to contain the same headings.

## Chapter ending

For substantial chapters, finish with:

### Key takeaways
A concise summary of the mechanisms and conclusions the reader should retain.

### What you can now do
Concrete tasks the reader can perform, or predictions they can make, with this chapter's knowledge.

### Important relationships
The essential relationships among concepts or components.

### Check your understanding
Two to five questions that test reasoning, causality, and execution, not just memorization of symbol names. Every question must be answerable from the chapter alone, without opening the source.

### Where to look next
Optional. A short list of source locations or follow-up chapters for readers who want to dig deeper.

Omit a subsection if it would add no value.
