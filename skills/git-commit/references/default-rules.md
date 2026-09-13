# Default Commit Rules

Read only for decisions the message contract, compatible repository rules, and explicit user instructions leave open. The mandatory subject shape and the language rules stay in `SKILL.md`; this file does not restate them.

## Type Selection

Choose the smallest accurate type:

- `feat`: new capability or user-visible behavior
- `fix`: bug, regression, or incorrect behavior
- `perf`: performance improvement without intended behavior change
- `refactor`: structural change without intended behavior change
- `docs`: documentation only
- `style`: formatting or lint only, with no logic change
- `test`: tests only
- `chore`: tooling, dependencies, configuration, maintenance, or generated housekeeping

If no intent dominates, recommend splitting the commit.

## Scope Selection

1. In a multi-module repository, prefer the affected app, package, or module.
2. In a single-module repository, use a stable feature area.
3. When one intent spans several modules, join those real scopes with `&`.
4. Use the scope-less form only when the change is repository-wide and no module owns it.
5. Do not invent a scope merely to satisfy the default shape.

## Wording Defaults

- Keep the subject specific. Do not report implementation trivia unless it is the system-relevant change.
- Use the body for why, impact, migration, or trade-off, not for a line-by-line account of the diff.
- Prefer the same vocabulary the repository already uses for its modules.

## Edge Cases

- Breaking change: prefer `!` for a visible subject signal, and add the footer when the migration impact needs explanation. `BREAKING-CHANGE:` is a valid synonym, but default to `BREAKING CHANGE:`.
- Binary-only diff: describe the asset or artifact that changed.
- Generated files: focus on the visible source change; otherwise use `chore`.
- Pure move or rename: use `refactor` when the structure changed, otherwise `chore`.
- Formatting mixed with logic: ignore the formatting noise and classify the logic change.

## Examples

```text
feat(auth): add WeChat QR login
fix(api): handle null user response
refactor(db): migrate queries to async API
docs: update authentication guide
chore(deps): update axios security patch
test(auth): cover login regression
feat(api)!: remove legacy authentication

BREAKING CHANGE: clients must migrate to the session API
```

One intent across three modules — joined scope, one body line per scope:

```text
feat(common&share&tool): add shared retry policy

- common: add the retry helper
- share: route share calls through it
- tool: drop the local retry loop
```

Avoid vague subjects, mixed intents, past tense, trailing periods, invented scopes, mixed languages, and claims not supported by the diff.
