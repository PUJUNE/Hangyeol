---
type: note
project: "references"
source: codex
tags:
  - note
status: reference
---
# HTML Format

The output is a single static HTML file. It must open directly in a browser without a dev server.

## Required Blocks

1. Sticky control bar
   - Search input.
   - Category filter buttons.

2. First viewport
   - Eyebrow label.
   - Video title.
   - One or two sentence summary.
   - Four metadata cells.
   - Thumbnail or visual source panel.
   - Source URL box.

3. Layout
   - Left navigation on desktop.
   - Main content column.
   - Stack navigation above content on mobile.

4. Report sections
   - Overview or context section.
   - Problem or case section.
   - Optional diagram and fact cards.
   - Timecode badge on each section and each nested paragraph, diagram item, or fact card.

5. Interactive blocks
   - Topic cards with search and category filtering.
   - 논지 흐름 selector.
   - Comparison tabs.
   - Optional table.
   - Q&A accordion.
   - Final summary.
   - Timecode badges on each card, flow stage, tab panel, Q&A item, table row, and summary item.

## Interaction Requirements

- Search must filter topic cards by title, body, and detail.
- Filter buttons must combine with search.
- Flow buttons must update a detail panel.
- Tabs must update a comparison panel.
- Q&A buttons must toggle `aria-expanded`.
- Q&A buttons must preserve the nested timecode badge when opened and closed; only the trailing `+` / `−` icon should change.
- Timecode badges must render as `영상 MM:SS` or `영상 HH:MM:SS`.
- JavaScript must be inline and syntactically valid.

## Validation

Run this after generation:

```powershell
node -e "const fs=require('fs'); const html=fs.readFileSync('FILE.html','utf8'); const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1]||''; new Function(script); console.log('JS syntax OK');"
```

Search for project-specific disallowed phrases before final response. Use the current workspace instructions as the phrase list and keep this check outside the final artifact body.

If a thumbnail is used, prefer embedded `data:image/...;base64,` or a local relative image. Do not stretch images.

Check that all rendered content blocks have visible timecode badges unless the user supplied a timestamp-free source and accepted incomplete timestamp coverage.

For Q&A regression testing, open and close at least one Q&A item and confirm the `영상 MM:SS` badge remains visible after both state changes.

## Output Naming

Use the current execution date and the safe video title for the HTML file:

- `<영상제목>_상세보고서.md`
- `YYMMDD_<영상제목>.html`
- Optional intermediate: `<영상제목>_content.json`

Example: `260515_AI 잘 쓰는 회사의 공식은 따로 있습니다.html`

`scripts/build_video_html.py` applies this HTML name automatically when `--out` is omitted. If `--out` is a directory, the script writes the same filename inside that directory.
