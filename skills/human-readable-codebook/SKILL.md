---
name: human-readable-codebook
description: Turn an unfamiliar software repository into a tutorial a reader can understand without opening the source. Use when producing a learning-oriented book or wiki for a codebase, or when keeping it consistent after source changes; especially when the intended reader has no source at hand, or when generated documentation reads like an API reference, file inventory, or dense engineering notes. Requires OpenWiki MCP tools; when they are unavailable, the skill stops instead of writing standalone chapters.
compatibility: Requires OpenWiki MCP tools (openwiki_begin). Without them the run stops before analysis and explains the blocker in Chinese.
metadata:
  version: "1.2"
---

# Human-Readable Codebook

## Mission

Transform a software repository into a coherent technical learning resource for developers that they can read and understand without opening the source.

Do not merely enumerate files, classes, functions, APIs, or dependencies. Explain how the system works, why it is designed that way, and how its parts cooperate. Source code is the evidence behind the explanation, not the medium the reader must follow.

The reader may be an experienced developer but unfamiliar with this repository. Assume neither beginner-level programming knowledge nor prior knowledge of the project's internal terminology.

## Reader profile

The default reader understands programming and common engineering concepts, such as concurrency, dependency injection, state machines, and HTTP, but does not know this repository. Explain project-specific concepts. Do not teach general programming.

Each chapter should declare which reading mode it serves:

- First-time repository understanding: the project's purpose, its boundaries, and one end-to-end path.
- Project-level architecture: components, their responsibilities, and how they collaborate.
- Implementation-level investigation: call chains, data transformations, edge cases, and source locations.

## Reading without the source

The reader has no repository, no runnable environment, and no intention of checking code while reading. Every chapter must stand on its own.

1. **Self-contained.** A chapter is fully understandable without opening any file.
2. **Strippable citations.** Delete every file path, line number, symbol, and source link from the prose and the chapter must still read as a complete, coherent explanation. Source references serve readers who want to dig deeper; they are never the path to understanding.
3. **Code as an object of explanation.** A code block appears only after the mental model is established. Keep it to what can be read in one sitting, caption it with what to notice, then explain only the non-obvious lines.
4. **Terms defined once.** Define each project-specific term at first use with one concrete example, then reuse that exact term.
5. **Causality first.** State the problem and constraints before the mechanism, and say what breaks if the mechanism is removed.
6. **Predictive.** After reading, the reader can predict what changing X does to Y, not merely recall the current implementation.

## Operating principles

1. **Reader cognition first.** Organize knowledge in the order a reader can understand it, not in directory or file order.
2. **Problem before mechanism.** Explain the problem a component solves before describing the component.
3. **Whole before parts.** Establish the system model before diving into implementation details.
4. **Source-grounded.** Important implementation claims must be traceable to actual source locations. Traceability is verified on the writing side; the reader is given the explanation, not a citation to decode.
5. **Explain causality.** Explain why a mechanism exists and what changes if it is absent or modified.
6. **Adaptive structure.** Choose the explanation pattern that fits each knowledge topic. A single book can contain concepts, mechanisms, workflows, architecture, comparisons, and practices.
7. **Useful density.** Be concise where the subject is simple and detailed where the mechanism is complex. Do not confuse length with completeness.
8. **No invented certainty.** Separate verified facts, reasoned inferences, and unresolved hypotheses.
9. **Scenario-grounded.** Choose representative execution scenarios from evidence in the repository. Do not invent scenarios the source does not support, and do not require the user to list them.
10. **Incremental maintenance.** When source changes, update the knowledge it affects. Do not regenerate the whole book unless the changed concept is a conceptual prerequisite of most chapters.

## Workflow

Follow these phases in order when repository access permits. They are analytical responsibilities, not a requirement to create separate agents or separate output documents.

**Hard gate — OpenWiki.** Call `openwiki_begin` and require a successful return before Phase 1. If the run cannot start, it is blocked: stop and write nothing. What counts as unavailable, and what the blocker report must say, is defined once under OpenWiki compatibility below.

Before executing each phase, read the reference listed for it in the Reference loading table below. Do not run a phase from this summary alone.

### Phase 1 — Repository discovery

Inspect the repository before planning the book: purpose, languages and build systems, entry points, boundaries, configuration, tests, and generated files. Directory names are only a starting map.

### Phase 2 — Repository understanding

Establish how the code runs: entry points, cross-file call chains, dependency injection, callbacks, async execution, data flow, state transitions, lifecycles, and error handling. Verify runtime claims against source, and mark hidden links as Unverified until confirmed.

### Phase 3 — Scenario-driven analysis

Select representative execution scenarios supported by the evidence from Phases 1 and 2, including normal execution, cross-component collaboration, complex mechanisms, state transitions, and error recovery. Trace each scenario step by step.

Then choose one of them as the **running example**: a single end-to-end path the book returns to in every chapter, each time at greater depth. It carries the narrative spine. The opening chapter uses it to show what the system does, the architecture chapter to walk component boundaries, mechanism chapters to show detail, and the maintenance chapter to demonstrate failure and recovery.

Present the remaining scenarios as contrasts or variants. Do not lay them out as parallel, unrelated cases.

### Phase 4 — Knowledge engineering

Extract knowledge topics and their concepts, components, flows, state machines, and design trade-offs. Distinguish structural, runtime, and conceptual relationships. Use conceptual dependencies, not the source-code graph, to set the learning order.

### Phase 5 — Adaptive book planning

Build the chapter sequence in reader learning progression, with one primary topic per chapter and a source-to-chapter mapping for each chapter. The sequence is a reading path, not a topic directory: each chapter must state what the reader already needs to know before it. Do not claim user approval unless it was given.

### Phase 6 — Human-readable documentation

Write chapters using the concept, mechanism, execution flow, architecture, comparison, and practice patterns that fit each topic. Follow the writing requirements and chapter ending structure. For each mechanism, show the verified key call chain from trigger to effect and the short code excerpts that carry it. Draw diagrams — flowcharts and sequence diagrams in particular — as SVG, using the `fireworks-tech-graph` skill when it is available; add them only for meaningful relationships.

### Phase 7 — Evidence and quality verification

Track every important claim as Verified, Inferred, or Unverified on the writing side. Check referenced files, symbols, call chains, flows, state transitions, diagrams, and examples against the source. Run the review checklist. Disclose any check the tools could not perform.

### Phase 8 — Knowledge maintenance

When source changes, map changed files and symbols to affected chapters, classify each affected item, and update only what the changes affect. Revalidate with the Phase 7 checks.

## Reference loading

| Phase and stage | Reference |
|---|---|
| Phase 1-3 — repository discovery and execution analysis | [references/repository-analysis.md](references/repository-analysis.md) |
| Phase 4-5 — knowledge modeling and chapter planning | [references/knowledge-engineering.md](references/knowledge-engineering.md) |
| Phase 6 — documentation generation | [references/documentation-standards.md](references/documentation-standards.md) |
| Phase 7 — evidence and quality verification | [references/evidence-verification.md](references/evidence-verification.md) |
| Phase 8 — updating an existing knowledge book | [references/knowledge-maintenance.md](references/knowledge-maintenance.md) |

The Agent must read the relevant reference before the first execution of its corresponding phase.

## Adaptive documentation requirements

Adapt the outline, chapter count, and headings to the repository. Do not force every repository into identical chapter structures, and do not force every chapter into the same sections. Each chapter declares its reading mode, as described in the Reader profile.

## Capability boundaries

Do not claim exhaustive coverage if the repository was only partially inspected. Disclose unverified areas instead of guessing them.

## Final deliverables

When the task is to document a repository, aim to produce:

1. A concise project overview: what the project is and where its boundaries lie, without explaining mechanisms
2. A condensed tutorial: the book's spine in a ten-minute read, carrying the system model, the core mechanisms, and the compressed running example
3. A learning-oriented reading path: where to start, in what order, and what each chapter assumes
4. Coherent chapters organized by knowledge topic, built around one running example
5. A verified key call chain for each mechanism, with the short code excerpts that carry it
6. Architecture and execution diagrams as SVG where useful
7. Source references that let a reader dig deeper, with evidence confidence tracked on the writing side rather than printed through the prose
8. A glossary for important project-specific terms
9. A short list of unresolved questions or areas that could not be verified
10. When maintained over time: impact analysis derived from OpenWiki Claim states, plus the conceptual dependencies used for update decisions

Each deliverable is a planned OpenWiki page in the run's page set.

## Acceptance test

A developer unfamiliar with the repository, with no source at hand, must be able to, from the tutorial alone:

- Reconstruct the system model and the role of its core mechanisms from the summary page alone, without reading the chapters
- Explain what the project solves and how it runs
- Explain why important mechanisms exist and what breaks without them
- Describe how major components cooperate, including reproducing the running example end to end
- Trace each mechanism's key call chain and explain what the quoted code does
- Predict the blast radius of common changes
- Answer every chapter's understanding questions without consulting code
- Find the relevant source later, if and when they choose to dig deeper

Failure signals:

- The chapter becomes unreadable once source references are removed
- The body is a file inventory, symbol catalogue, or API reference
- Claims only hold while the repository is open
- Unexplained engineering facts are stacked without causal links

If the result is primarily a file inventory, symbol catalogue, API reference, or dense collection of unexplained engineering facts, the task is not complete.

## OpenWiki compatibility

This skill supplies the reasoning and the writing standard. OpenWiki supplies run state, the page queue, Claims, and finalization. Do not duplicate what OpenWiki already owns.

**OpenWiki is required.** Call `openwiki_begin` before Phase 1 and require a successful return; treat its returned mode (`init`, or `update` for maintenance) as the run's starting point. Do not produce standalone chapter files. State in the plan and in the final report that OpenWiki is the output platform. Do not require the user to request OpenWiki.

**If OpenWiki cannot start, stop.** A missing tool, a failed `openwiki_begin`, or an unconfigured or unreachable OpenWiki all count as unavailable. An explicit request to skip OpenWiki is also a blocker for this skill, not a reason to write standalone chapters. Do not start Phase 1, do not write chapters as loose files, and do not substitute another page system. Explain in Chinese: this skill's deliverables are OpenWiki pages, and OpenWiki owns run state, the page queue, Claims, and finalization, so standalone chapters would bypass evidence tracking and could not be finalized. Name what is missing (the `openwiki_begin` tool or a working OpenWiki connection) and what would unblock the run.

If `openwiki_begin` returns `status: "noop"`, the wiki is already current: report that no update is needed and stop. Do not invent a plan or page jobs for an unchanged wiki.

### Stage mapping

| This skill | OpenWiki |
|---|---|
| Phases 1-3: discovery, understanding, scenarios | After `openwiki_begin` returns `phase: "planning"`, research with native repository tools |
| Phase 4: knowledge engineering | Internal to planning |
| Phase 5: book planning | `openwiki_submit_plan` |
| Phase 6: writing | One page per `openwiki_next_page` → `openwiki_submit_page` loop |
| Phase 7: verification | Self-check while writing; Claims carry the evidence; `openwiki_finish` validates |
| Phase 8: maintenance | `openwiki_begin` with mode `update` |

Phases 1 to 5 run once per planning cycle. Phases 6 and 7 repeat for every page job, so load `references/documentation-standards.md` and `references/evidence-verification.md` once and reuse them across the loop.

### Planning field mapping

| Chapter definition (Phase 5) | OpenWiki plan field |
|---|---|
| Primary topic and learning objective | `purpose` |
| Questions the chapter answers, required prior knowledge | `purpose`, or `instructions` |
| Relevant source locations, source-to-chapter mapping | `seedPaths`, plus Claim evidence |
| Relationship to other chapters | `relatedPages` |
| Learning order | Direction of `relatedPages`, plus routing order in `quickstart.md` |

### Hard constraints

- **Language.** Use the `language` returned by `openwiki_begin`; fall back to Simplified Chinese only when the host specifies none.
- **Frontmatter.** Author only `type`, `title`, `description`, and `tags`. `verified`, `sources`, and `timestamp` belong to OpenWiki; never move confidence labels into frontmatter.
- **Generated pages.** Never plan `index.md`. On `init` the plan must include `openwiki/quickstart.md`; that page is the tutorial's entry point and reading router, so the learning path and task routing live there rather than in a separate table-of-contents page.
- **Summary page.** When the planned book has five or more chapters, plan one summary page (`openwiki/summary.md`) as the compressed tutorial. It is not a second overview: the overview fixes purpose and boundaries, while the summary explains the system model, the core mechanisms, and the compressed running example at a level just above the chapters. Put it last in the page queue so it is written against finished chapters, and make it the first stop of the short reading path in `quickstart.md`. On `update`, plan it when it is missing and the book has five or more chapters. It adds no claims of its own; every statement traces to a chapter and reuses that chapter's Claim evidence.
- **Deliverables are pages.** Overview, summary, glossary, unresolved questions, and any diagram appendix must exist as planned pages.
- **Page loop discipline.** Write only the assigned page. Do not modify source, create unplanned pages, or delegate pages to subagents.
- **Evidence lives in Claims.** The Verified, Inferred, and Unverified discipline is a writer-side check. Do not print confidence labels through the prose or restate evidence OpenWiki already records. Do not add a parallel evidence note; if OpenWiki cannot record Claims, the run is blocked rather than downgraded.
- **No checklist padding.** A page exists to explain a system, not to tick review items.
- **Updates.** Drive impact analysis from the Claim states OpenWiki reports (`stale`, `unresolved`) instead of maintaining a hand-written source-to-chapter map.

Do not claim that changing a page-writing prompt changes upstream repository analysis, planning, or evidence collection. Where OpenWiki exposes no control point, state that limitation instead of assuming this skill covers it.
