---
type: note
project: "references"
source: codex
tags:
  - note
status: reference
---
# Content JSON Schema

Create a UTF-8 JSON file and pass it to `scripts/build_video_html.py`.

## Timecode Rule

Every visible HTML content block must include a video location. Use one of these fields:

- `timecode`: one timestamp such as `"03:42"`.
- `timecodes`: multiple timestamps such as `["03:42", "05:18"]`.
- `start_sec`: numeric seconds such as `222`; the builder renders it as `03:42`.

Apply this to sections, section paragraphs, diagram items, fact cards, topic cards, flow items, comparison tabs, tab list items, Q&A items, table rows, and takeaways. If the source lacks timestamps, do not invent them; state the limitation in chat and omit only the blocks that cannot be grounded.

When `metadata.url` is a YouTube link, the builder turns every timecode badge into a clickable link that opens the video at that moment (`watch?v=ID&t=<seconds>s`). For non-YouTube or missing URLs it keeps a plain text badge. The flow selector buttons keep their time as text and link from the detail panel instead, to avoid nesting a link inside a button.

## Required Top-Level Fields

```json
{
  "title": "영상 제목",
  "summary": "첫 화면에 표시할 1~2문장 요약",
  "metadata": {
    "channel": "채널명",
    "upload_date": "YYYY-MM-DD",
    "duration": "15분 40초",
    "subtitle": "한국어 자동 자막",
    "url": "https://www.youtube.com/watch?v=..."
  },
  "sections": [],
  "categories": [],
  "topics": [],
  "flows": [],
  "tabs": [],
  "questions": [],
  "takeaways": []
}
```

## Sections

Use 2~4 sections before the interactive blocks. Keep them concise.

```json
{
  "id": "overview",
  "title": "개요",
  "timecode": "00:18",
  "paragraphs": [
    { "timecode": "00:18", "text": "문단 1" },
    { "timecode": "01:04", "text": "문단 2" }
  ],
  "diagram": [
    { "timecode": "02:11", "title": "AI 도입", "body": "도구와 교육은 늘지만 업무 방식은 그대로 남음." }
  ],
  "facts": [
    { "timecode": "03:20", "title": "마케팅", "body": "초안은 나오지만 톤과 타깃을 사람이 다시 맞춤." }
  ]
}
```

`diagram` and `facts` are optional. Use them when the source naturally has steps or repeated cases.

## Categories and Topics

Categories drive the filter buttons. Use 4~6 categories.

```json
"categories": [
  { "id": "problem", "label": "문제" },
  { "id": "case", "label": "사례" },
  { "id": "structure", "label": "구조" },
  { "id": "conclusion", "label": "결론" }
]
```

Each topic card must include a category id.

```json
{
  "category": "case",
  "timecode": "04:12",
  "title": "회의록 정리",
  "body": "요약은 가능하지만 결정 배경과 반대 의견이 빠짐.",
  "detail": "다음 사람이 회의 맥락을 다시 물어야 하므로 조직 지식으로 남지 않음."
}
```

## Flow

Use 5~7 items for the 논지 흐름 selector.

```json
{
  "timecode": "01:40",
  "stage": "1. 도입 현상",
  "title": "AI 도입 활동의 증가",
  "text": "회사는 교육과 도구를 도입하지만 실제 업무 절차는 줄지 않음.",
  "point": "도입 활동과 업무 성과를 분리해서 보게 함."
}
```

## Tabs

Use 2~4 comparison tabs.

```json
{
  "id": "personal",
  "label": "개인 AI",
  "timecode": "05:22",
  "title": "개인 업무 보조",
  "body": "개인이 배경을 설명하고 초안을 얻는 방식임.",
  "list": [
    { "timecode": "05:22", "text": "사용자가 배경을 직접 입력함" },
    { "timecode": "05:41", "text": "결과 검토가 개인에게 남음" }
  ]
}
```

## Q&A

Use 5~8 questions. Answers should be short enough to scan.

```json
{ "timecode": "12:04", "q": "영상의 결론은 무엇임?", "a": "AI는 잘 쌓아둔 회사에서 잘 작동한다는 결론임." }
```

## Table

Optional. Use when the video contains repeated comparison axes.

```json
{
  "table": {
    "title": "회사 맥락의 구성",
    "headers": ["맥락 유형", "예시", "역할"],
    "rows": [
      {
        "timecode": "06:18",
        "cells": ["업무 기준", "매뉴얼, 내부 규정", "결과물의 판단 기준을 맞춤"]
      }
    ]
  }
}
```

## Takeaways

Use timestamped objects for final summary items.

```json
"takeaways": [
  { "timecode": "13:10", "text": "최종 정리 문장" }
]
```

## Thumbnail

Prefer a local thumbnail file with `--thumbnail-file` so the output HTML embeds it. If that is not available, set `thumbnail_data_uri` or `thumbnail_url`.
