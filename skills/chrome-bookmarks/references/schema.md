# Bookmarks document schema

Read this before writing or editing a Bookmarks document, so the file Chrome loads stays valid.

## Document

The file is JSON at `<user-data>/<Profile>/Bookmarks`. Replace only `roots.bookmark_bar`; copy every other top-level key and both other roots from the file you read.

```json
{
  "checksum": "…",
  "roots": { "bookmark_bar": {…}, "other": {…}, "synced": {…} },
  "version": 1
}
```

`checksum`, `version`, and `sync_metadata` belong to Chrome. Keep whatever the file already carries and never compute or invent a value; do not assume `sync_metadata` exists — Chrome adds it while sync metadata is present and drops it again.

## Nodes

```json
{"children": [], "date_added": "13410500000000000", "date_modified": "13410500000000000",
 "guid": "1f0c6a2f9c4b4c1e8a7d5f3b2c9e0a11", "id": "12", "name": "归档", "type": "folder"}

{"date_added": "13410500000000000", "guid": "a94f7c1d2b8e4a6f9c3d5e7b1a2f4c60", "id": "13",
 "name": "OpenAI·api", "type": "url", "url": "https://platform.openai.com/docs/quickstart"}
```

- `type` is `folder` or `url`; folder nodes need `children` (possibly empty), url nodes need `url`.
- `id` is a unique decimal string inside the document and `guid` is 32 hex characters. Let the script assign both; never reuse an `id`.
- Copy an existing node to keep its `date_added` and override only `name`/`url`; give a new folder `date_added` and `date_modified` the same value.
- Times are microseconds since 1601-01-01 UTC, written as strings: `(unix_seconds + 11644473600) * 1_000_000`.
- Bookmarks on the bar are folders by convention; loose url children are valid JSON but show up as a `warning:` line on writeback.

## After a write

- Re-read the file and compare structure and counts. Chrome rewrites `id`s, `checksum`, and ordering the next time it saves, so hashes matching the prepared copy is not the goal.
- If the tree looks wrong after Chrome opens it, restore `Bookmarks.bak` instead of patching the live file by hand.
