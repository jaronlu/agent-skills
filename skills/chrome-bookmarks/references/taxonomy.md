# Default taxonomy

Derive the tree from the bookmarks in front of you. When the user names a scheme — in this conversation, in a file, or in an earlier plan — that scheme always wins, including its folder names and language.

Otherwise use the pattern below as a starting point and adapt it to what the bookmarks actually contain. A folder with one or two items, or a category the user has nothing for, is not worth creating.

## Invariants

- The bookmark bar holds folders, not loose URLs, and no wrapper folder repeats the bar's own name.
- Top-level folders stay few (3–7), named in the user's language and vocabulary.
- Group by purpose first, then by platform, vendor, or topic inside a group.
- Folders nest at most three levels deep (top-level folder → subfolder → sub-subfolder); leaves sit inside the deepest folder and do not count as a level, so `AI / Agent / 官方文档 / leaf` is legal while a fourth folder level is not. Promote anything deeper instead of adding a fourth level.
- Each item lives in exactly one folder.
- A second level is normally a category, not a domain. Open a domain folder only when that one domain keeps four or more bookmarks; leaves inside it drop the `company` prefix.
- When the tree the user has already contains a fallback bucket (`归档`, `Archive`, `Misc`, …), keep it for everything that does not fit and never delete it for being empty; cleanup rules delete inside it first. When the tree has none, do not invent one — place every item by purpose and say where the old bucket's items went. Either way, moving items out of a content folder such as `归档/工作` needs the user's word.
- Delete empty folders except the top-level ones the user wants to keep and the fallback bucket above.

## Default pattern

```
work/     the user's job: internal services, work documents, collaboration tools
study/    courses, textbooks, papers, drills
dev/      long-term development reference: languages, frameworks, toolchains, repos
ai/       AI ecosystem
  agent/  model labs, agent frameworks, coding agents, MCP — official sites, docs, repos
  relay/  API relay and coding-plan aggregators, shared-account services
tools/    occasional online tools, dashboards, consoles, subscriptions
chore/    life administration: government, bills, health, housing, shopping
misc/     fallback; cleanup rules delete here first
```

Rename, merge, or drop any of these to match the user's own scheme: a user who works in Chinese keeps `工作/`, `学习/`, … instead. Top-level folders stay lowercase and few; the third level is the deepest and holds leaves, or a domain folder when a domain qualifies.

## Decision order

Take the first folder that matches, so the same bookmark always lands in the same place:

`work → study → ai → dev → tools → chore → misc`

- Work wins over everything: a bookmark the user needs for their job goes to `work`, even when it is a language, a tool, or a model vendor.
- `study` is what the user is currently learning; `dev` is standing reference. A course moves out of `study` when the user stops following it.
- `ai` covers the AI ecosystem before generic `dev`, so vendor docs, agent frameworks, and relays stay together. `agent` and `relay` never mix: relays are third-party resale services, and an outage or a policy change there must not take the vendor entries with it.
- Other AI products (chat, image, writing, transcription) go to `tools`; open `ai/apps/` only once at least four of them justify it.

## Placement

- **work**: anything the user needs for their job, including self-hosted services and internal documents. Never treat these as low value.
- **study**: courses, books, papers, drills. Keep the current edition or the canonical page only.
- **dev**: one subfolder per platform or stack the user actually uses, added only when several bookmarks justify it. Official docs and repository roots belong here.
- **ai/agent**: model labs, agent frameworks, coding agents, MCP, and the repositories behind them, one leaf per `company·slug`.
- **ai/relay**: third-party API relays, coding-plan aggregators, shared-account services, kept separate from `ai/agent`. Prefer one leaf per relay platform.
- **tools**: occasional online tools, consoles, dashboards, paid services. Prefer the product's home page or docs over dashboard and console URLs.
- **chore**: banks, government, health, housing, shopping, transport. Keep the current page per service and drop superseded ones.
- **misc**: the fallback, split by topic only when a topic earns a folder.

## Bookmark names

Name every saved URL `<company>·<slug>`: the site, vendor, or organization, a middle dot, then a short slug for the product or page (lowercase, hyphens instead of spaces).

Examples: `OpenAI·api`, `Anthropic·claude-code`, `Vercel·docs`, `Reuters·markets`. When a page belongs to no company, use the site or the organization as `company` (a personal blog uses the author's handle, a government page uses the agency).

The pattern targets product, site, and repository leaves. Personal documents, government pages, internal systems, and anything the user named keep their own title — a labour-claim document stays recognisable as `劳动维权·赔偿估算` rather than being flattened into `Google·document`.

- The same `company·slug` appears once per folder: replace the older URL instead of keeping a second one, and prefer the official documentation URL or the repository root over pricing, tag, dashboard, and session URLs.
- A renamed leaf keeps the pattern even when the user's own folder names are in another language; leave identifiers and product names untranslated.

## Open-source repositories

Keep a repository when it is the official source for the product or a widely used project, and drop forks, demos, and tutorial clones. Apply the user's own bar when they state one instead of inventing a threshold.

## Overrides

When the user names a different top-level set, rebuild the tree to match and move displaced items into the closest surviving folder or the fallback folder rather than leaving loose URLs on the bar.
