# Cleanup rules

Apply after classification. These are principles with tunable defaults; anything the user sets in the current conversation overrides them. Prefer deleting in the fallback folder rather than in the folders the user works from.

## Always drop

- Exact URL duplicates, and the same URL after stripping tracking query keys (`utm_*`, `gclid`, `fbclid`, `ref`, `spm`, `plantype`, …).
- The same repository (`org/repo`) or the same product host when an equivalent entry is already kept outside the fallback folder: extra marketing, pricing, download, tag, or docs-subtree pages.
- `chrome://`, `chrome-extension://`, `about:`.
- Session and account-state URLs: chat threads (`/c/`, `/chat/<id>`, `/app/<id>`, `threadId=`), shared documents carrying tokens, and login or checkout steps.
- Console, billing, API-key, signup, and trial pages, unless the product itself is a service the user keeps.
- Content farms and course dumps (aggregators, reposted tutorials, interview dumps, video-course mirrors) when the official source exists.
- Unofficial mirrors of a tool whose official repository is already kept.

## Keep

- Official sites, documentation, and repository roots.
- Work documents, official or government service pages, and anything the user names.

## Defaults you may tune

- One URL per host or product outside the fallback folder. When a host genuinely needs more, keep the smallest number that still covers the need — two is a reasonable default, and official documentation sites may need more.
- Prefer the home page or `/docs` when choosing which URL to keep.
- Cap repeats inside the fallback folder per host, and ask which page the user actually uses when the choice is not obvious.
- Keep a repository because it is the official source or widely used, not because it matches an arbitrary star count. Apply the user's own threshold when they state one.

A per-host limit is a judgment call, not a target: record the numbers you used in the session report so the user can correct them.

## Do not add a navigation catalog

Organize the bookmarks that exist. Add a missing official home page only when the user already saved a random subpage of that product and the home page is the better keep. Never bulk-insert “should have” sites.
