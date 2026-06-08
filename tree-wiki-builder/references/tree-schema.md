# Tree Wiki Schema

## Directory Layout

```text
raw/
wiki/
  areas/
  concepts/
  sources/
  entities/
  themes/
  essays/
  syntheses/
working log/
```

## Parent Rules

- Content pages have exactly one parent in `related_axes`.
- Axis pages have exactly one parent map in `related_syntheses`.
- The map page lists axis pages in `related_syntheses`.
- Axis pages list children in category-specific `related_*` fields.
- Do not use `wiki/index.md` or `wiki/log.md`.
- Keep raw file paths as plain text fields or body text, not wikilinks.

## Ingest Checklist

1. Identify whether the new material is a source, essay, concept, entity, theme, or synthesis.
2. Ask the user to confirm one parent axis.
3. Create the content page with `related_axes` containing exactly one wikilink.
4. Add the content slug to the parent axis child list.
5. Keep body wikilinks out unless the user explicitly wants graph edges in body text.
6. Run `scripts/tree_lint.py --wiki wiki`.
