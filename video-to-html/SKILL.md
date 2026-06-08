---
name: video-to-html
description: 유튜브 URL·자막·전사 txt를 받아 타임코드가 표기된 상세 md 보고서와 정적 인터랙티브 HTML을 생성한다. 검색, 주제 필터, 논지 흐름, 비교 탭, Q&A 아코디언 포함. 트리거 — video to HTML, 유튜브 HTML 보고서, 영상 인터랙티브 리포트, /video-to-html.
---

# Video to HTML

## Purpose

Turn a YouTube URL or transcript into two outputs:

1. `*_상세보고서.md` — structured Korean report for review.
2. `YYMMDD_영상명.html` — self-contained static HTML with fixed workshop-report styling.

Use the fixed format from this skill instead of inventing a new landing page or generic dashboard.

## Workflow

1. Check source type.
   - YouTube URL: run `scripts/fetch_youtube_subs.py`. Use both `*_스크립트.txt` and `*_segments.json`.
   - Existing `.txt` or `.srt`: use it as the transcript source. Prefer inputs that include `[MM:SS]` or `HH:MM:SS` timestamps.
   - Existing summary `.md`: use it as the source of truth and skip transcript extraction only when it already contains timestamps, or clearly state in chat that timestamp coverage cannot be complete.
2. Read `references/content_schema.md` before preparing the structured data.
3. Read `references/workshop_design_tone.md` before editing HTML design.
4. Create a report in Korean with noun-phrase headings and concise business-report structure. Include source timecodes for each major claim or section.
5. Create `content.json` that follows the schema. Every HTML content block must include `timecode`, `timecodes`, or `start_sec` so the rendered HTML shows where the related video content appears.
6. Run `scripts/build_video_html.py content.json`. The default HTML filename must be `YYMMDD_영상명.html`, for example `260515_AI 잘 쓰는 회사의 공식은 따로 있습니다.html`.
7. Verify:
   - `node -e` can parse the embedded script in the HTML.
   - The HTML has no external image dependency unless the user asked for it.
   - Search, filters, flow buttons, comparison tabs, and Q&A toggles are present.
   - Timecode badges appear on sections, topic cards, flow details, tabs, Q&A items, table rows, and final summary items whenever those blocks exist.
   - When `metadata.url` is a YouTube link, timecode badges become links to `watch?v=ID&t=<seconds>s`; flow selector buttons keep plain text and the flow detail panel carries the link.
   - Q&A open/close toggling keeps the timecode badge visible and only changes the trailing `+` / `−` icon.
   - Output files do not include authoring-process metadata or confidence tags.

## Report Structure

Use these sections unless the source requires minor renaming:

- 영상 개요
- 중심 논지
- 문제 구조
- 논지 전개
- 회사 AI와 개인 AI의 차이
- 회사 맥락의 구성 요소
- 제안된 운영 구조
- 시청자가 가져갈 판단 기준
- 결론

Keep the report focused on final content. Do not add unrequested risk, decision-request, or next-action sections.

## HTML Format

The HTML must be a static single file that opens directly in a browser. It must include:

- First viewport with title, summary, metadata, and thumbnail or visual panel.
- Sticky search and topic filter controls.
- Left section navigation on desktop and stacked navigation on mobile.
- Topic cards with category tags.
- Timecode badges on all content blocks.
- Interactive 논지 흐름 selector.
- Comparison tabs.
- Q&A accordion.
- A short final summary section.

Use `references/html_format.md` for the fixed component map.

## Scripts

### Fetch YouTube subtitles

```powershell
python "<skill>/scripts/fetch_youtube_subs.py" "https://www.youtube.com/watch?v=VIDEO_ID" --out .
```

Outputs:

- `<safe-title>_스크립트.txt`
- `<safe-title>_segments.json`
- `<safe-title>_meta.json`

### Build HTML

```powershell
python "<skill>/scripts/build_video_html.py" content.json
```

The builder writes `YYMMDD_<content.title>.html` next to `content.json` by default. It accepts optional `--out <path-or-directory>` when the user explicitly wants a different location, and optional `--thumbnail-file` to embed a local thumbnail as a data URI. If no thumbnail is supplied, it uses the `thumbnail_data_uri` or `thumbnail_url` field from JSON.

## References

- `references/content_schema.md` — JSON contract for `build_video_html.py`.
- `references/workshop_design_tone.md` — fixed color, typography, and layout tone.
- `references/html_format.md` — required HTML component structure and validation checklist.
