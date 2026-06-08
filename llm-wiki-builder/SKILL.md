---
name: llm-wiki-builder
description: Karpathy LLM Wiki 패턴 기반 개인 지식베이스 구축·운영 스킬. raw 폴더 정션 마운트, CLAUDE.md 위키 스키마 생성, ingest·query·lint 3종 운영 절차, frontmatter YAML 표준화, broken link 자동 점검을 일괄 제공. essay·source·concept·entity·theme·synthesis 6 카테고리 + 양방향 link 그래프 관리. 트리거 — llm 위키 구축, Karpathy 위키 패턴, 개인 지식베이스, /llm-wiki-builder.
---

# llm-wiki-builder

Karpathy의 LLM Wiki 패턴(`gist:karpathy/442a6bf555914893e9891c11519de94f`)을 사용자 도메인에 인스턴스화해 개인 지식베이스를 구축·운영하는 스킬. 본 스킬은 2026-05-23 작업 폴더 `260523 llm 위키`에서 실제 구축한 위키(콘텐츠 페이지 63건)의 운영 절차·도구·규약을 재사용 가능한 형태로 일반화한 것.

## 적용 상황

- 사용자가 외부 자료(독서·기사·영상·강연)와 본인 글(에세이·메모)을 시간에 걸쳐 누적하고 관통하는 주제·개념·인물 간 연결을 가시화하고 싶을 때
- 단순 RAG가 아닌 부피·밀도가 증가하는 영구 위키를 원할 때
- 본 위키 운영 도구(Obsidian + Claude Code) 환경이 갖춰진 경우

## 핵심 아키텍처 — 3 레이어

| 레이어 | 역할 |
| --- | --- |
| **raw/** | 원본 자료 (immutable) — LLM은 읽기만, 수정 금지 |
| **wiki/** | LLM이 작성·유지하는 markdown 페이지 (6 카테고리) |
| **CLAUDE.md** | 위키 운영 매뉴얼 (스키마·규약·절차 정의) |

## 6 페이지 카테고리

- `concepts/` — 사고·이론·프레임워크
- `sources/` — 원본 자료별 요약 (1 source = 1 page)
- `entities/` — 인물·기관·책·제품
- `themes/` — concept보다 큰 관통 모티프
- `essays/` — 사용자 본인 글 (외부 글과 구분)
- `syntheses/` — 다수 소스를 가로지른 종합·해석·비교

## 트리 구조·index/log 미운영 정책

본 스킬은 글로벌 「LLM 위키 트리 구조 원칙」을 따름. 핵심:

- 트리 계층: 지도(루트) → 축(상위 카테고리) → 카테고리 노드(말단) 3계층
- 신규 노드의 부모 link는 정확히 1개 — 축 또는 다른 카테고리 노드. 형제 cross-link 금지
- 한 노드의 frontmatter `related_*` wikilink 합계는 부모 1개 + (부모 노드인 경우 자식 다수)만 허용
- `wiki/index.md`·`wiki/log.md`를 생성·갱신하지 말 것 — 그래프 시각화에서 별 모양 허브로 작용해 트리뷰를 흐림. 카탈로그는 축 노드 `related_concepts` 자식 리스트가 대체, 이벤트는 `working log/session_log_*.md` 또는 `wiki/worklog/` 활동 노드가 대체
- `related_sources` 같은 raw 자료 슬러그 필드도 wiki/ 외 파일을 가리켜 그래프 빌더에서 ghost(missing) 노드로 잡힘 — raw 메타는 본문 `## 참고 자료` 섹션 plain text로 두는 편이 그래프 정합에 유리

## 운영 3종 — Ingest / Query / Lint

### Ingest (인입)
1. raw에 자료 떨어뜨림
2. LLM이 자료 읽고 핵심 시사점 3~7개를 사용자와 토의
3. 신규 노드의 부모(축 또는 다른 카테고리 노드) 1개를 사용자에게 확정 받기
4. `sources/[slug].md` 작성 + 본문에서 추출된 신규 concept·entity는 별도 페이지 생성
5. 부모 노드에만 `related_syntheses` link 연결 — 형제 cross-link 금지. 부모 노드의 `related_concepts`에 자식 등재 (양방향 1쌍)
6. raw 자료 슬러그·인용은 본문 `## 참고 자료` 섹션 plain text로 기록 (frontmatter `related_sources`에 wikilink 형식으로 두지 말 것)

상세 절차: `references/ingest-procedure.md`

### Query (질의)
1. 축 노드(`areas/` 또는 위키 루트의 분류축)에서 관련 페이지 식별
2. 페이지들 읽기, 필요시 raw 원본까지 거슬러 검증
3. 답변 — 인용은 `[[slug]]` 또는 `raw/...` 명시
4. 답변이 가치 있으면 `syntheses/[slug].md`로 파일링 (사용자 동의 후)

### Lint (정합성 점검)
- 깨진 링크 (broken `[[link]]`)
- 고아 페이지 (incoming 참조 0건)
- frontmatter YAML 표준 위반
- 비대칭 백링크 (정보용)

자동화 도구: `scripts/lint.py` + `scripts/lint_fix.py`
상세 절차: `references/lint-procedure.md`

## Quick Start — 새 위키 구축

### 1. 폴더 골격 생성

```bash
mkdir -p raw wiki/{concepts,sources,entities,themes,essays,syntheses} "working log"
```

### 2. raw 폴더 정션 마운트 (Windows)

기존 원본 자료 폴더를 raw 하위로 노출:

```ps1
New-Item -ItemType Junction -Path "raw\<name>" -Target "<원본폴더 절대경로>"
```

상세: `references/junction-setup.md` (정션 안전 규칙·다중 PC 재생성·삭제 시 주의)

### 3. CLAUDE.md 작성

`references/CLAUDE-template.md`를 작업 폴더 루트에 복사한 뒤 위키 주제·정션 경로·도메인에 맞게 수정. 템플릿은 트리 원칙·index/log 미운영 정책 반영 버전.

### 4. 루트 노드(지도)·축 노드 초기 생성

`wiki/areas/<지도>.md`(분류 루트)와 그 자식 축 노드 8~10개를 먼저 생성. 축 노드의 `related_syntheses`는 지도 1개만, 지도의 `related_syntheses`는 축들을 자식으로 listed. `index.md`·`log.md`는 만들지 말 것.

### 5. frontmatter 표준 — 부모 link 1개 원칙

모든 page는 block list 형식 YAML frontmatter 사용. 인라인 `[[link]]` 콤마 분리는 YAML 표준 위반. 부모 link는 정확히 1개(축 또는 다른 카테고리 노드)만 가지며, 형제·다른 축 cross-link는 작성하지 않음.

```yaml
---
title: "페이지 제목"
type: concept | source | entity | theme | essay | synthesis
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-노드]]"   # 정확히 1개
---
```

raw 자료 슬러그를 `related_sources`에 wikilink 형식으로 두지 말 것 — 그래프 빌더가 ghost 노드로 잡음. raw 메타는 본문 `## 참고 자료` 섹션 plain text로 기록.

상세: `references/frontmatter-spec.md`

### 5b. raw 언어·용어 우선 (슬러그·title 명명)

- 슬러그·title은 가급적 raw 자료의 **원어**로 작성 (현재 도메인은 한국어).
- raw 본문에 해당 개념·인물·기관·주제를 가리키는 용어가 이미 있으면 임의 의역·영문 환원 없이 **raw의 표현을 최대한 그대로** 슬러그·title에 사용.
- 영문 학술어로 환원하지 말고 자료가 쓴 한국어 용어를 우선 (「사용자 글의 시그니쳐 보존」과 정합).
- 예외: 원어에 표준 표기가 없거나 영문 약어가 사실상 고유명사인 경우(EMG·MPI·MSDS 등)만 원표기 유지.

### 6. 첫 ingest 시범

사용자가 raw에 자료 하나를 두고 "인입해줘"라고 요청하면 위 Ingest 절차 수행. 첫 인입은 양방향 link 컨벤션 시각 확립이 목적이므로 조금 깊게.

## 운영 노하우 (실전)

### 사용자와의 협업 패턴

- 인입 자료가 사용자 본인 글이면 `essays/`, 외부 자료면 `sources/`
- 외부 LLM(Gemini Deep Research·ChatGPT 등) 생성물도 외부 자료로 분류 (essay 아님)
- 같은 자료가 두 raw 폴더에 있으면 source 페이지의 `raw_path_alt` 필드 활용

### Cross-pollination 탐지

사용자가 같은 주제를 essay·deep research 두 채널로 동시 탐구하는 패턴이 흔함. 인입 시 시점(같은 날·다음 날) 비교가 강력한 발견을 만듦. 그 패턴은 synthesis 후보로 직결.

### Status 단계 운영

- `stub` — 식별 정보만 (entity 기본값)
- `draft` — 본문 있음, 미완 (concept 기본값)
- `mature` — 인입 직후 source·essay (사용자 검토 거치며 단계 상승)

### Theme 형성 신호

여러 essay/source/concept이 같은 모티프로 묶이기 시작하면 theme 페이지 생성. theme는 본 위키의 가장 큰 hub이므로 신중하게 명명. 2026-05-23 작업 폴더 예시: `[[ai-induced-cognitive-atrophy]]` + `[[selves-across-time]]` 2개로 전체 위키가 양분됨.

## 사용자 글의 시그니쳐 보존

본 위키는 외부 자료 누적이 아니라 사용자 사고의 영구화. 그러므로:
- essay 본문에서 사용자 본인 명제만 추출 (LLM 페르소나 응답은 보조 자료로만)
- 사용자가 명시한 명명을 concept으로 승격 (외부 학술 용어로 환원하지 말 것)
- syntheses 작성 시 사용자 관점·해석을 중심에 두기

## 참고 파일

- `references/CLAUDE-template.md` — 위키 운영 매뉴얼 템플릿 (작업 폴더 루트 CLAUDE.md로 복사)
- `references/frontmatter-spec.md` — YAML 표준 규약 + 카테고리별 frontmatter 예시
- `references/ingest-procedure.md` — 인입 7단계 상세
- `references/lint-procedure.md` — 정합성 점검 + 자동화 도구 사용법
- `references/junction-setup.md` — raw 폴더 정션 마운트 가이드
- `references/worklog-ingest.md` — raw 내 todo·세션 로그를 업무 캠페인(worklog) 노드로 편입하는 절차
- `scripts/lint.py` — frontmatter·link·고아·비대칭 점검 도구
- `scripts/lint_fix.py` — frontmatter 표준화 + broken link 자동 수정 도구

## 작업 폴더에서 실제 운영 사례

본 스킬의 일반화 출처는 `C:\Users\rkwka\내 드라이브\90. 김석준 개인\260523 llm 위키`. 2026-05-23 단일 작업 세션으로 다음 도달:
- 콘텐츠 페이지 63건 (concept 24·source 13·entity 9·theme 2·essay 14·synthesis 1)
- 양방향 link 200+
- 두 관통 theme 형성
- 첫 lint·자동 수정·재검증 사이클 1회 완료

본 스킬을 다른 도메인(연구·독서·취미 심화 등)에 적용 시 위 사례의 운영 패턴을 참고.
