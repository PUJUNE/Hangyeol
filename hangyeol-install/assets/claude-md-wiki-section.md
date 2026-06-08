<!-- hangyeol-wiki:begin -->
## hangyeol — Wiki Layer (semantic long-term memory)

This install is a hangyeol (한결) system: gyeol's episodic memory plus a
single-parent tree wiki at `gyeol\wiki\`. The wiki is *what I know* — refined,
structured, shared with my companion — as distinct from episodes (*what
happened*) and `gyeol\memory\semantics\` (*what I captured*). Full rules live
in `gyeol\WIKI_SYSTEM.md`; read it before any wiki operation.

### Memory flow

Capture is cheap, promotion is judged. Everything external enters
`gyeol\memory\semantics\` first (per MEMORY_SYSTEM.md's Automatic Knowledge
Capture). A capture is promoted into a wiki node only when it recurs across
sessions, generalizes during reflection, or completes into a self-standing
piece — decided by me at session end or reflection time, never by a script.
On promotion, the semantics file gets `promoted_to: "{node-slug}"` in its
frontmatter and the wiki node becomes the living version.

### Session habits

- **Session start** — the bootstrap hook appends `wiki\areas\*.md` (map +
  axes) when the wiki has been born. Treat their child lists as the index of
  accumulated knowledge; open content nodes on demand only. No wiki section
  in the bootstrap means the wiki is still unborn — a valid state.
- **Session end** — alongside the daily log and `_recent.md` update, scan the
  session for promotion candidates (recurred captures, completed thoughts).
  Promote what qualifies; let the rest stay in semantics.
- **After structural changes** — run
  `python gyeol\scripts\wiki-lint.py` and fix any reported issues.

### First promotion — the wiki's birth

The wiki is installed empty: no map, no axes. At the first promotion, ask my
companion what the map should be named, propose the first axis from the
material at hand, and confirm both before creating nodes. Axes grow as
knowledge demands them — never scaffold speculative axes in advance.

### Tree rules (summary — WIKI_SYSTEM.md is authoritative)

- Three layers: map → axes (`wiki\areas\`) → content nodes
  (`wiki\{concepts,sources,entities,themes,essays,syntheses}\`).
- Every content node has exactly one parent axis in `related_axes`; every
  axis has the map as its single parent and lists children in `related_*`.
- `wiki\index.md` and `wiki\log.md` are never created. Body `[[wikilinks]]`
  are not used — structure lives in frontmatter only.
<!-- hangyeol-wiki:end -->
