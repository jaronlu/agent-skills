# Repository Analysis

Read this file before executing Phase 1 (repository discovery), Phase 2 (repository understanding), and Phase 3 (scenario-driven analysis) in SKILL.md.

## Phase 1 — Repository discovery

Inspect the repository before planning the book.

Identify, where applicable:

- Project purpose and problem domain
- Languages, frameworks, dependencies, build and test systems
- Runtime entry points and execution modes
- Major packages, modules, services, and boundaries
- Core data structures and abstractions
- External systems and integration points
- Configuration and extension mechanisms
- Tests, examples, generated files, and code-generation inputs
- Important runtime flows and lifecycle boundaries

Do not infer architecture from directory names alone. Verify important boundaries through imports, call sites, registrations, configuration, tests, and runtime entry points.

A project may belong to multiple categories. Do not force it into one label.

Directory discovery is only a starting map. It is not repository understanding; Phase 2 is still required.

## Phase 2 — Repository understanding

Establish how the code runs, not only where it lives. Cover, where applicable:

- Application and execution entry points: main functions, server bootstraps, CLI commands, job runners, event handlers, exported library APIs
- Component responsibilities and boundaries: what each component owns, and what it must not do
- Cross-file call chains: calls traced from entry point to the component doing the work, through verified call sites
- Dependency injection: where objects are constructed and which implementation is bound
- Callbacks and event-driven execution: who registers a handler, who emits the event, and in what order
- Asynchronous execution and concurrency: tasks, threads, queues, locks, cancellation, and ordering guarantees
- Data creation, transformation, transfer, and consumption: where data originates, how its shape changes, and where it ends
- State transitions: state fields, enumerations, guards, and the code that moves between states
- Object and resource lifecycles: creation, initialization, reuse, release, and shutdown
- Error handling and recovery: exception boundaries, retries, fallbacks, timeouts, and cleanup

Rules:

- Do not infer runtime behavior solely from class names, filenames, or directory structure. Read the implementation and its call sites before stating what it does.
- When dynamic dispatch, reflection, or framework wiring hides a link, record it as Unverified until a registration, configuration entry, or test confirms it.

## Phase 3 — Scenario-driven analysis

Select representative execution scenarios from the evidence gathered in Phases 1 and 2. Consider:

- Typical normal execution
- Cross-component collaboration
- Complex execution mechanisms, such as async work, callbacks, retries, and lifecycle hooks
- Important state transitions
- Error handling and recovery

For each important scenario, trace:

1. Trigger
2. Entry point
3. Initial state
4. Execution sequence
5. Component interactions
6. Data transformations
7. State changes
8. External dependencies
9. Output and side effects
10. Termination and error handling

Rules:

- Name the evidence for each scenario, such as the entry point file and key symbols.
- If a step cannot be traced, mark that step Unverified. Do not fill the gap with a plausible guess.
- Do not invent scenarios unsupported by source code.

Finally, promote one traced scenario to the book's running example, as described in Phase 3 of SKILL.md. It must be a path the source fully supports, because every chapter will lean on it.
