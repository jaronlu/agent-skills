# Loading and Distribution Checks

A file existing, being expected to load, and being loaded in the current session are three different kinds of evidence.

## Installation and Context Chain

1. Identify the actual install path, version or commit, and the home under review. The current shell's environment does not prove a running gateway uses the same profile; mark its effective settings unknown when they cannot be read.
2. Cross-check relevant non-sensitive configuration: memory load switches, context-file char caps, terminal CWD, skill source directories, and disabled state. When parsing configuration, emit only allow-listed fields; never print full configs or environments.
3. When the user asks for a project review, determine the session CWD and git root, then label loaded, shadowed, missing, and unreadable files according to the installed version's precedence. Never treat the reviewing process's CWD as the Hermes session CWD.
4. Confirm the SOUL source is an effective home. A home-level `AGENTS.md` has no standalone global loading privilege, but the home itself may enter ordinary project discovery when it lies on the applicable chain.
5. Memory loading is gated separately by `memory.memory_enabled` and `memory.user_profile_enabled`. A disabled state is a configuration fact; report it only when it conflicts with user expectation or documented intent.
6. Check frozen-snapshot and refresh semantics against the implementation; a disk update does not prove the running prompt updated. Do not import runtime modules that create directories, refresh indexes, or write caches to complete a read-only review.

## Skill Distribution Chain

Only when the review covers skills, reference availability, or an end-to-end diagnostic:

- Locate the source package, the publishing library, and tool deployment directories; follow symlink targets and compare package file content, not just mtimes.
- Check the installed version's `skills.create_dir`, `skills.external_dirs`, project skill directories plus trust configuration, disabled items, and platform gates. A directory existing does not put it in discovery scope.
- Newer implementations can discover home skills, `create_dir`, `external_dirs`, and trusted-project `.hermes/skills` / `.agents/skills`. Actual precedence comes from the reviewed version's source; do not assume `~/.agents/skills` is auto-loaded globally.
- If a skill index or cache exists, read the relevant entries and version info; a missing cache entry alone does not prove current invisibility—combine it with directories and configuration.
- Report "source not yet published", "deployed copy outdated", "outside discovery scope", and "current session unverified" separately. Uncommitted source changes are not automatically a deployment fault; judge against the publishing expectation.
- Give only the minimal correction; do not sync files, mutate distribution databases, refresh caches, or restart processes. Do not bypass a distribution manager's ownership by installing directly to its targets.

## Verification Output

Report separately:

- **On-disk facts**: paths, versions, relevant configuration, content comparisons.
- **Static derivation**: what these inputs should load under the installed implementation, and which inputs are unknown.
- **Runtime evidence**: what existing session diagnostics prove; without them, state "no new session started; actual prompt unverified".

Never require reading secrets, full logs, or private session content. If the needed evidence is unavailable, keep the critical verification gap instead of filling it by guesswork.
