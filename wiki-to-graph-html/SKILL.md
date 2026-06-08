---
name: wiki-to-graph-html
description: Karpathy 패턴 LLM 위키 폴더(concepts·entities·sources·themes·syntheses·essays·worklog·areas 카테고리, frontmatter related_*·applies·advances + 본문 wikilink)를 단일 HTML 지식그래프 파일로 변환하는 스킬. 옵시디언식 force-directed 그래프 + 본문 뷰어 + 검색·타입 필터 + 노드 크기·장력·엣지 거리 슬라이더를 포함하며, 모든 md 본문을 임베드하므로 위키 폴더 없이도 단독 동작. 트리거 — 위키 그래프 HTML, 지식그래프 html, 위키 시각화, 옵시디언 그래프 뷰 html, /wiki-to-graph-html.
---

# wiki-to-graph-html

LLM 위키 폴더(`llm-wiki-builder` 스킬이 만드는 Karpathy 패턴 구조)를 단일 HTML 파일로 변환함. 산출물은 외부 의존성·CDN·서버 없이 더블클릭만으로 동작하며, 원본 위키 폴더가 삭제되어도 본문이 모두 임베드되어 있어 독립적으로 열람 가능.

## 기대 입력

### 위키 디렉터리 구조

```
<wiki_dir>/
├─ areas/        # 분류 루트(지도)·축 노드 (category 위키, type: synthesis로 매핑)
├─ concepts/     # type: concept
├─ entities/     # type: entity
├─ sources/      # type: source
├─ themes/       # type: theme
├─ syntheses/    # type: synthesis
├─ essays/       # type: essay
├─ worklog/      # type: worklog (일일·캠페인 활동 노드)
└─ lint-reports/ # (폴더째 제외)
```

위 폴더에 해당하지 않는 위치(예 — wiki 루트에 직접 둔 md)의 `.md`는 frontmatter의 `type:` 값을 보고 분류함. 표준 7종(concept/entity/source/theme/synthesis/essay/worklog)이면 해당 타입, 외이면 `type: other`.

글로벌 「LLM 위키 index.md / log.md 미생성 규칙」에 따라 `wiki/index.md`·`wiki/log.md`는 본 스킬의 입력 위키에도 존재하지 않는 것을 가정함(스캐너가 발견하면 제외 처리). 잔존 시 그래프에서 별 모양 허브로 잡혀 트리 시각화를 흐림.

### frontmatter 표준

```yaml
---
title: "표시 제목"
type: concept | entity | source | theme | synthesis | essay
tags: [태그1, 태그2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-노드]]"   # 정확히 1개 (트리 부모 link)
related_concepts:           # 부모 노드(축·허브)일 때만 자식 listed
  - "[[자식-slug]]"
---
```

- `related_*` 필드의 값은 block list + `"[[slug]]"` 인용 형식. 인라인 콤마 나열은 파싱하지 않음.
- 본문에 등장하는 `[[slug]]` 위키링크도 모두 엣지로 수집함 (frontmatter와 합집합).
- `[[slug|alias]]` 별칭 표기 지원.
- raw 자료 슬러그를 wikilink 형식으로 두지 말 것 — 실제 위키 노드가 없으면 ghost(missing) 노드로 표시됨. raw 메타는 본문 `## 참고 자료` 섹션의 plain text 슬러그로 기록.

## 호출 방식

스킬 폴더의 `scripts/build_wiki_html.py`를 직접 실행함.

```bash
# 기본: ./wiki → ./wiki_graph.html
python scripts/build_wiki_html.py

# 위키 폴더 지정 (출력은 자동으로 <wiki_dir>의 부모 폴더에)
python scripts/build_wiki_html.py /path/to/wiki

# 출력 경로 명시
python scripts/build_wiki_html.py /path/to/wiki /path/to/out.html

# 제목 지정 (HTML <title>·placeholder 헤더에 반영)
python scripts/build_wiki_html.py wiki wiki_graph.html --title "내 게임이론 위키"
```

표준 라이브러리만 사용함 (pathlib, json, re, argparse). 추가 설치 불필요.

## 산출물 HTML 기능

- **좌측 그래프 뷰** — 자체 force-directed simulation(SVG). 노드 색은 타입별 (개념·인물·소스·테마·종합·에세이·미생성). 노드 크기는 슬라이더 베이스 × 연결도 가중치. 드래그·휠 줌·팬 지원. 미생성 wikilink 대상은 `missing` 타입의 ghost 노드로 표시.
- **우측 본문 뷰어** — 클릭한 노드의 마크다운 본문을 인라인 렌더링(헤딩·리스트·인용·코드·강조·외부 링크·`[[wikilink]]`). 위키링크 클릭 시 그래프 노드 선택과 본문 전환이 동시 발생. 하단에 자동 backlink 목록.
- **검색** — 좌상단 입력창에서 제목·태그 substring 매칭. 일치하지 않는 노드·엣지는 숨김 처리.
- **타입 필터** — 좌하단 범례의 체크박스로 타입별 on/off.
- **인터랙션 슬라이더** — 좌상단 툴바에 3종:
  - 노드 크기 (2~14, 기본 5) — 즉시 반지름·라벨 위치 갱신
  - 장력(반발) (200~6000, 기본 1800) — repulsion. 조작 시 시뮬레이션 자동 재가열
  - 엣지 거리 (20~280, 기본 90) — linkDist. 동일하게 reheat
- **HUD** — 우상단에 현재 보이는 노드/엣지 개수.
- 초기 렌더 시 연결도 1위 노드가 자동 선택됨. 8초 후 시뮬레이션 정지(성능). 슬라이더 조작·드래그로 언제든 재가동.

## 작업 단계

1. 사용자가 위키 폴더 경로를 명시하지 않은 경우, 현재 작업 폴더의 `wiki/` 존재 여부를 확인하고 그것을 사용할지 사용자에게 확인.
2. 위 디렉터리 구조와 frontmatter 표준을 따르는지 sample 1~2개 파일을 Read로 확인. 표준에서 크게 벗어나면 변환 결과의 한계(엣지 누락 등)를 사용자에게 사전 안내.
3. `python scripts/build_wiki_html.py <wiki_dir> <out_path> --title "..."` 실행.
4. 출력 로그의 `nodes: N / edges: M`를 사용자에게 보고. 노드 수가 실제 .md 수와 일치하는지(`index.md`/`log.md`/`lint-reports/` 제외) 자체 검증.
5. 산출물 파일 절대 경로 안내.

## 자주 묻는 변형

- **wiki 폴더 구조가 다름** — `TYPE_BY_DIR` 매핑은 6 카테고리에 고정. 다른 구조를 쓰는 사용자가 있으면 스크립트의 해당 상수를 한 번만 수정하는 것이 가장 깔끔. 임시 변경이라면 사용자 폴더 이름을 표준 6개 중 하나로 매핑(예 `figures` → `entities`)하는 옵션을 별도로 제안.
- **본문 wikilink만 있고 frontmatter related_* 비어 있음** — 본문 wikilink도 엣지로 수집하므로 정상 동작. 그래프가 sparse하다면 frontmatter 보강을 권장.
- **외부 폰트·CDN 차단 환경** — 본 산출물은 시스템 폰트 폴백(맑은 고딕·Apple SD Gothic Neo·Segoe UI)만 사용. CDN 의존성 없음.
- **노드 라벨이 잘림** — 라벨은 SVG `<text>`로 노드 위에 그려지며 잘림 처리 없음. 라벨이 겹쳐 보이면 장력을 키워 노드 간격을 벌리거나 노드 크기를 줄여 시각적 밀도 조정.

## 출력하지 않는 것

- 본 스킬은 위키 폴더 자체를 만들지 않음. 위키 디렉터리 초기 구축은 `llm-wiki-builder` 스킬을 먼저 사용.
- 위키 본문 내용 수정·정렬·중복 제거를 하지 않음. 입력 그대로 임베드.
- 외부 정적 사이트(GitHub Pages 등) 배포 자동화를 포함하지 않음. 산출물은 단일 HTML 파일이므로 임의 위치에 복사하여 사용.

## 검증 체크리스트

- [ ] 출력 로그의 nodes 수 = 실제 .md 개수(`index.md`/`log.md`/`lint-reports/` 제외)
- [ ] missing 타입 노드가 비정상적으로 많지 않음 (40% 이상이면 wikilink 슬러그 오타 가능성)
- [ ] 브라우저에서 더블클릭 → 그래프 정상 표시 + 검색·슬라이더·노드 클릭 동작
- [ ] 위키 폴더를 임시로 다른 경로로 옮긴 뒤에도 HTML 단독 동작
