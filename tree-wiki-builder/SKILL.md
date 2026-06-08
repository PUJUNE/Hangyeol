---
name: tree-wiki-builder
description: 단일 부모 원칙의 markdown tree wiki를 구축·운영하는 스킬. 지도→축→콘텐츠 노드 3계층, related_axes 1개 규칙, index.md·log.md 미생성, raw 불변 보존, ingest·query·lint 절차와 초기화 스크립트를 제공. 트리거 — 트리 위키 구축, tree wiki, 단일 부모 위키, /tree-wiki-builder.
---

# tree-wiki-builder

`llm-wiki-builder`에서 위키의 트리 골격만 분리한 범용 스킬. 의미 관계를 먼저 늘리지 않고, 파일 위치와 부모 관계를 안정화해 Obsidian 그래프가 지도→축→콘텐츠 노드로 읽히게 만든다.

## 기본 모델

- 트리 골격은 `wiki/areas/<지도>.md` → `wiki/areas/<축>.md` → `wiki/{concepts,sources,entities,themes,essays,syntheses}/<노드>.md` 3계층으로 둔다.
- 콘텐츠 노드는 frontmatter의 `related_axes`에 부모 축 1개만 가진다.
- 축 노드는 지도 1개를 부모로 가지고, 자식 목록을 `related_concepts`, `related_sources`, `related_entities`, `related_themes`, `related_essays`, `related_syntheses`에 보유한다.
- 본문 `[[wikilink]]`는 원칙적으로 쓰지 않는다. 그래프 관계는 frontmatter의 부모·자식 목록으로만 관리한다.
- `wiki/index.md`와 `wiki/log.md`는 만들지 않는다. 카탈로그는 축 노드 자식 목록이 맡고, 작업 이력은 `working log/session_log_*.md`가 맡는다.

## 착수 절차

1. 사용자가 원하는 위키 주제, 지도명, 축 후보를 확인한다. 축 후보가 없으면 4~8개 이하의 초안을 제시하고 확정받는다.
2. `scripts/init_tree_wiki.py`로 폴더와 지도·축 노드를 생성한다.
3. raw 원본이 있으면 `raw/` 아래에 보관하거나 정션으로 연결하되, LLM이 raw를 수정하지 않는다고 명시한다.
4. 신규 자료 인입 시 자료를 읽고 핵심 시사점 3~7개를 사용자와 확인한 뒤, 부모 축 1개를 확정받는다.
5. 콘텐츠 노드를 만들고 부모 축의 자식 목록에도 같은 슬러그를 추가한다.
6. 작업 후 `scripts/tree_lint.py`로 깨진 링크, 부모 1개 규칙, 금지 파일 존재 여부를 확인한다.

## Frontmatter 표준

콘텐츠 노드:

```yaml
---
title: "노드 제목"
type: concept | source | entity | theme | essay | synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
status: stub | draft | mature
related_axes:
  - "[[부모-축]]"
---
```

축 노드:

```yaml
---
title: "축 이름"
type: synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tree-axis]
status: mature
related_syntheses:
  - "[[지도-이름]]"
related_concepts: []
related_sources: []
related_entities: []
related_themes: []
related_essays: []
---
```

## 리소스

- `scripts/init_tree_wiki.py` — 새 트리 위키 골격과 지도·축 노드 생성.
- `scripts/tree_lint.py` — 단일 부모 규칙, 금지 파일, 깨진 링크, 고아 구조 점검.
- `references/tree-schema.md` — 트리 frontmatter와 인입 규칙 상세.

## 판단 기준

- 여러 부모가 필요해 보이면 트리 분류를 바꾸지 말고, 먼저 하나의 주 부모를 고른다.
- 횡단 관계가 많아지면 이 스킬 범위를 넘어 `tree-to-ontology`로 전환한다.
- 기존 위키에 다중 link나 본문 wikilink가 있어도 사용자가 정리를 요청하지 않으면 자동 마이그레이션하지 않는다.
