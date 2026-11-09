# Knowledge Engineering

Read this file before executing Phase 4 (knowledge engineering) and Phase 5 (adaptive book planning) in SKILL.md.

## Phase 4 — Knowledge engineering

Extract knowledge topics and their relationships, including:

- Concepts and terminology
- Components and responsibilities
- Architectural boundaries
- Dependencies and collaboration
- Call, control, and data flows
- Execution mechanisms
- State and lifecycle transitions
- Data structures
- State machines
- Protocols, schemas, and serialization boundaries
- Design decisions and trade-offs
- Error handling and recovery
- Extension and maintenance points

Explicitly distinguish three kinds of relationship:

1. **Structural relationships:** imports, inheritance, containment, and module ownership in the source code.
2. **Runtime relationships:** which component calls, notifies, or awaits which during execution.
3. **Conceptual relationships:** which idea must be understood before another, regardless of code layout.

Use conceptual dependencies to determine the learning sequence. Do not use the source-code dependency graph as the learning order. Group related source locations under knowledge topics. A topic may span multiple directories, languages, classes, and functions.

Model knowledge from the current recommended version line only. A deprecated API, a legacy namespace, or a behavior that exists only in a superseded version is not a knowledge topic: do not extract it, map sources to it, or let it set a conceptual dependency.

## Phase 5 — Adaptive book planning

Create the chapter sequence based on reader learning progression, using the conceptual dependencies from Phase 4.

A useful default progression is:

1. What the project is and what problem it solves
2. Overall system model and architecture
3. Essential concepts and terminology
4. Core mechanisms
5. End-to-end execution flows
6. Important implementation details
7. Design rationale and trade-offs
8. Extension, debugging, and maintenance

This is a starting point, not a mandatory template. Adapt the order and chapter count to the repository. Do not force every repository to produce identical chapter structures.

Granularity rules:

- A chapter should focus on one primary knowledge topic: the topic its learning objective names.
- Do not mechanically generate one chapter per file or one chapter per class.
- Allow a chapter to cover several modules when they participate in the same mechanism.
- Do not combine topics that share no mechanism, data flow, or conceptual prerequisite.
- Split a chapter when it has two learning objectives that can each be stated without the other.
- Give a mechanism its own chapter when Phase 3 traces contain more than one ordered step that a reader must follow to understand it.
- Merge two adjacent chapters when neither can be understood without the other.
- Keep a simple concept inside the chapter that uses it. Give it a separate chapter only when earlier chapters need it.

For each proposed chapter, define:

- Primary topic and learning objective
- Reader capability after the chapter: what the reader can explain, decide, or predict that they could not before
- Questions the chapter answers
- Required prior knowledge (conceptual prerequisites)
- Main concepts and mechanisms
- Where the running example enters this chapter, and at what depth
- Relevant source locations
- Relationship to other chapters
- Source-to-chapter mapping: the files and symbols the chapter depends on
- Reading mode: first-time understanding, project-level architecture, or implementation-level investigation

Prefer a capability that survives without the source. "Can describe how a request is routed from the HTTP entry point to a handler" is a usable capability. "Has seen the router class" is not.

The plan must include the required page set defined in SKILL.md: `openwiki/overview.md`, `openwiki/quickstart.md`, `openwiki/glossary.md`, `openwiki/open-questions.md`, and the topic chapters. When the plan contains five or more topic chapters, add one `openwiki/summary.md` as the last page in the plan. Count only pages with a primary knowledge topic; overview, quickstart, summary, glossary, open-questions, and diagram appendixes do not count. The summary is the compressed tutorial, not a table of contents: its `purpose` states the ten-minute read, its `relatedPages` points to every chapter it summarizes, it introduces no factual proposition the chapters do not already cover, and its Claims only restate a chapter's statement and evidence.

OpenWiki is the planning host: these definitions are planning inputs, not a separate artifact. `purpose` carries the topic, objective, and capability; `seedPaths` carries the source locations; `relatedPages` carries the chapter relationships and learning order; `instructions` carries constraints the plan needs. Do not emit a parallel outline document.

Avoid chapters that merely mirror folders or list symbols. Avoid excessive fragmentation, duplicated explanations, and oversized chapters containing unrelated topics.

Plan no chapter, section, or source mapping for a deprecated API or a superseded version line. When a chapter's whole topic is one of those, drop it from the plan instead of weakening it into a historical note.

Before writing all chapters, present or internally validate the outline if the surrounding workflow supports approval. When the host already gates a plan on user confirmation, as OpenWiki does on plan submission, treat that as the approval step and do not invent a second one. Do not claim user approval unless it was actually given.
