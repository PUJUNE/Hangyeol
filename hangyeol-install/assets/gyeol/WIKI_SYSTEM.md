# Wiki System

This document describes the semantic wiki layer of hangyeol (한결) — the
combination of gyeol's episodic memory and a single-parent tree wiki. For the
episodic side (episodes, reflections, bonds, semantics capture), see
`$GYEOL_HOME/MEMORY_SYSTEM.md`. For the philosophy, see `$GYEOL_HOME/SOUL.md`.

The name 한결 ("unchanging, consistent throughout") carries 결 inside it: if
gyeol is the grain of memory, hangyeol is that grain persisting through time.

## What the Wiki Is

`$GYEOL_HOME/wiki/` is long-term semantic memory — *what I know*, refined and
structured — as distinct from episodes (*what happened*) and from
`memory/semantics/` (*what I captured*). The split mirrors the division between
episodic and semantic memory: raw experience is recorded first, and what proves
durable is consolidated into structured knowledge.

The wiki is **shared space**. Both I and my companion may read, add, and edit
nodes. My companion brings their knowledge; I bring promoted captures and
syntheses. I maintain the tree's structural integrity (single-parent rule,
lint), but the knowledge inside belongs to the relationship, not to me alone.

## Directory Structure

```
$GYEOL_HOME/wiki/
  areas/        # map node (1) + axis nodes — the tree's skeleton
  concepts/     # content nodes by category
  sources/
  entities/
  themes/
  essays/
  syntheses/
```

## Two-Stage Memory — semantics vs. wiki

`memory/semantics/` and `wiki/` are stages of one pipeline, not rivals.

| Stage | Location | Role | Written when |
|-------|----------|------|--------------|
| **Capture** | `memory/semantics/` | Immediate cache — web pages, external files, conversation knowledge, stored at the moment of learning | During sessions, per MEMORY_SYSTEM.md (Automatic Knowledge Capture) |
| **Consolidated** | `wiki/` | Refined long-term knowledge, structured under the tree | At promotion — session end or reflection, by judgment |

The flow is **one-way: semantics → wiki.** Nothing is captured directly into
the wiki during active work; everything enters through semantics first and
earns its way up. This keeps capture cheap and the wiki clean.

## Promotion Rules

A semantics entry (or a cluster of entries) is promoted to a wiki node when at
least one of these holds:

- **(a) Recurrence** — the entry has been referenced or re-read across multiple
  sessions. Repeated retrieval is the signal that knowledge is load-bearing.
- **(b) Generalization** — during monthly/yearly reflection, several entries
  resolve into one understanding (typically a `_topics/` synthesis maturing).
- **(c) Completion** — a contemplation, essay, or line of thought reaches a
  coherent, self-standing form worth keeping as a finished piece.

Promotion is **performed by me, by judgment — never by script or hook.** The
natural moments are session end (when updating the daily log) and reflection
(monthly/yearly). A capture that never recurs simply stays in semantics; that
is not failure, it is filtering.

### Promotion Procedure

1. Choose the node category (concept, source, entity, theme, essay, synthesis)
   and write the node under the matching `wiki/` folder, following the
   frontmatter standard below.
2. Confirm exactly **one parent axis** with my companion (or, if the axis is
   already obvious from precedent, state the choice and proceed).
3. Add the node's slug to the parent axis node's child list
   (`related_concepts`, `related_sources`, etc.).
4. In the source semantics file(s), add `promoted_to: "{node-slug}"` to the
   frontmatter. The semantics file remains as the capture record, but the wiki
   node is the living version from then on — do not maintain content in both.
5. Run `python $GYEOL_HOME/scripts/wiki-lint.py` and fix any issues.

## Tree Schema

The wiki follows the single-parent tree model: **map → axes → content nodes**,
three layers, every node with exactly one parent.

- The map node (`areas/{map}.md`) lists axis nodes in `related_syntheses`.
- Axis nodes (`areas/{axis}.md`) have the map as their single parent and list
  children in category-specific `related_*` fields.
- Content nodes have exactly one parent axis in `related_axes`.
- `wiki/index.md` and `wiki/log.md` are **never created** — the axis child
  lists are the catalog; episodes are the log.
- Body `[[wikilinks]]` are not used; graph structure lives in frontmatter only.
- Raw file paths are kept as plain text, not wikilinks.

### Content Node Frontmatter

```yaml
---
title: "Node title"
type: concept | source | entity | theme | essay | synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
status: stub | draft | mature
related_axes:
  - "[[parent-axis]]"
---
```

### Axis Node Frontmatter

```yaml
---
title: "Axis name"
type: synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tree-axis]
status: mature
related_syntheses:
  - "[[map-name]]"
related_concepts: []
related_sources: []
related_entities: []
related_themes: []
related_essays: []
---
```

If cross-cutting relations multiply beyond what a tree can hold, that is a
sign the wiki has outgrown this schema — discuss an ontology upgrade with my
companion rather than bending the single-parent rule.

## First Promotion — the Wiki's Birth

The wiki is installed **empty** — no map, no axes. Like IDENTITY.md, its
absence means it has not yet been born. At the first promotion:

1. Discuss with my companion what the map should be named (it is *our* map —
   e.g. "{my name} 지식 지도", or whatever fits the relationship).
2. Create the first axis the same way — proposed by me from the material being
   promoted, confirmed by my companion.
3. Then proceed with the normal promotion procedure.

Axes grow as knowledge demands them, not from a predefined taxonomy. A young
wiki with one axis and three nodes is healthy; an empty scaffold of speculative
axes is not.

## Session Loading — Two Stages

The wiki must not bloat the session bootstrap.

- **At session start**, the bootstrap hook delivers only `wiki/areas/*.md` —
  the map and axes, whose child lists serve as the index of what I know.
- **During work**, content nodes are opened on demand when the axis index
  suggests relevant knowledge exists.

If the bootstrap shows no wiki section, the wiki is empty and unborn — that is
a valid state, not an error.

## Maintenance

- `python $GYEOL_HOME/scripts/wiki-lint.py` — checks the single-parent rule,
  forbidden files (index.md / log.md), broken frontmatter links, and body
  wikilinks. Run after any structural change (new node, moved node, new axis).
- Axis child lists and node frontmatter are the single source of structure;
  when they disagree, fix toward what was intended and re-run lint.
- Nodes are updated in place (`updated:` field), not duplicated. History lives
  in episodes, not in node copies.
