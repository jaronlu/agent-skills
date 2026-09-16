# Memory Format and Capacity Checks

## Effective Limits

Parse `memory.memory_char_limit` and `memory.user_char_limit` from the relevant configuration. A missing key uses the reviewed installation's default and is not a configuration error. The verified implementation defaults are 2200 (MEMORY) and 1375 (USER) characters; if the version cannot be confirmed, state that the documented baseline is used and do not claim the effective limit is verified.

Distinguish missing from invalid values: report unparseable, null, non-positive, boolean, or type-incompatible values; never mask an invalid value through coercion. Configuration, environment overrides, and call sites can affect the effective value; when they conflict, check the current implementation rather than picking arbitrarily.

## Format and Runtime Count

In the verified implementation the delimiter is the full `\n§\n`, i.e. an entry boundary is a line containing only `§`; entries need no leading or trailing delimiters and may be multiline.

1. Read the text as UTF-8, allowing a BOM; read or decode failure is an evidence gap, not an empty file.
2. Split on the full delimiter, `.strip()` each entry, drop empty entries, then remove exact duplicates preserving order.
3. The runtime char count is `len("\n§\n".join(entries))` — it includes inter-entry delimiters and excludes trailing whitespace; it is not the UTF-8 byte length or a token count.
4. Report duplicates, anomalous empty entries, and non-canonical boundaries separately; do not let runtime cleaning or dedup hide disk-level problems. A `§` inside entry text is not automatically a boundary and is not itself a format violation.
5. Check whether `raw.strip()` round-trips against the deduplicated canonical join, and whether any single entry exceeds the whole-store limit, as drift signals. Do not invoke drift-detection methods that write backups.

For each store, report the actual character count, the effective limit and its source, the usage ratio, and `max(0, actual - limit)` overage. If raw file characters are also reported, keep them distinct from the runtime count.

## Capacity Severity

- At or over the limit: P1. External oversized files can remain loaded with a warning while further additions are blocked; this is not automatic truncation or data loss.
- Exactly at the limit: P1 capacity warning, not an invalid format; replacements or deletions that do not grow content may still succeed.
- At 90% of the limit but under it: P2 headroom note. 90% is this skill's review threshold, not a Hermes runtime limit.
- Below the threshold: do not delete meaningful constraints merely to compress.

## Semantics and Safety

Check whether memory duplicates SOUL or project rules, widens authority, stores low-frequency templates, references stale projects, or holds outdated environment facts. You may recommend demoting methods to a project document or skill reference with a clear entry point, but never migrate them during the review.

Memory loading is affected by switches, security scanning, and session snapshots. Scanning may replace an entry in the prompt while leaving the disk text intact; reading files alone does not prove full injection. Without authorization, do not trial-write, create backups, or restart sessions.
