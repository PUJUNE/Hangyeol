# Frontmatter 표준 규약

본 문서는 LLM 위키의 모든 페이지가 따라야 할 YAML frontmatter 규약. 2026-05-23 첫 lint에서 비표준 형식(인라인 link 콤마 분리)이 30건 일괄 발견된 사건의 회복 정의. 글로벌 「LLM 위키 트리 구조 원칙」에 따라 부모 link 1개 원칙도 함께 적용함.

## 핵심 원칙 — 트리 구조와 YAML 표준

- **부모 link는 정확히 1개**: 노드의 `related_*` 필드에 다른 위키 노드를 가리키는 wikilink는 부모(축 또는 다른 카테고리 노드) 1개만 — 형제·다른 축 cross-link 금지. 단 부모 노드(축·허브)는 자기 자식 다수를 listed 할 수 있음(부모→자식 트리 엣지).
- **raw 자료 슬러그는 frontmatter에 두지 말 것**: `related_sources`에 raw 파일 슬러그를 wikilink 형식으로 두면 그래프 빌더가 ghost(missing) 노드로 잡음. raw 메타는 본문 `## 참고 자료` 섹션에 plain text로 기재. `raw_path`처럼 파일 경로 문자열은 무관 (link 형식 아니므로 graph 영향 없음).
- **YAML 표준 준수**: 아래 항목 참조.

## YAML 표준 준수

`tags: [a, b, c]` 같은 단순 문자열 인라인 시퀀스는 유효함. 그러나 위키 link(`[[slug]]`)를 다수 포함하는 필드는 **반드시 block list + 인용 부호**.

### 잘못된 예 (YAML 파서가 frontmatter 전체 무시)

```yaml
related_concepts: [[a]], [[b]], [[c]]
```

### 올바른 예

```yaml
related_concepts:
  - "[[a]]"
  - "[[b]]"
  - "[[c]]"
```

이유: `[[a]]`는 YAML에선 중첩 배열 `[[a]]` = `[ [a] ]`로 해석되며, 콤마 + 또 다른 인라인 시퀀스가 뒤따르면 표준 파서가 mapping error로 frontmatter 전체를 무시함. 그 결과 `type`·`status`·`tags` 등 모든 메타데이터를 잃음 → Dataview 쿼리·LLM 파싱 모두 실패.

## 카테고리별 표준 frontmatter

각 노드는 `related_syntheses`(또는 동등 부모 필드)에 부모 1개만 등재. 다른 `related_*` 필드는 부모 노드(축·허브)일 때만 자식 listed로 채우고, 일반 카테고리 노드에서는 비움.

### Concept (개념·이론·프레임워크)

```yaml
---
title: "개념 이름"
type: concept
created: 2026-05-23
updated: 2026-05-23
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-노드]]"   # 정확히 1개
---
```

본문에 "## 참고 자료" 섹션을 두어 raw 자료·인용을 plain text로 기록.

### Source (원본 자료 요약)

```yaml
---
title: "자료 제목"
type: source
source_type: book | paper | article | video | podcast | conversation | speech
author: "저자 또는 entity 슬러그 plain text"
url: "원문 URL (있을 시)"
raw_path: "raw/<폴더>/<파일>"
raw_path_alt: "raw/<다른 폴더>/<파일>"  # 동일 자료가 두 곳에 있을 시 (선택)
ingested: 2026-05-23
created: 2026-05-23
updated: 2026-05-23
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-노드]]"   # 정확히 1개
---
```

`raw_path`·`url` 등은 파일 경로·URL 문자열이라 wikilink가 아님(그래프 영향 없음). entity·concept·theme를 가리키는 wikilink는 frontmatter에 두지 말고 본문에서 plain text 슬러그로 언급.

### Entity (인물·기관·책·제품)

```yaml
---
title: "고유명사"
type: entity
entity_kind: person | org | book | product | place
created: 2026-05-23
updated: 2026-05-23
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-노드]]"   # 정확히 1개 (보통 기관축·업체축·인물축)
---
```

### Theme (관통 모티프 — 부모 노드 역할 가능)

theme는 다수 source·essay를 묶는 부모 노드 역할을 함. 자식 link는 theme 자신의 `related_concepts`·`related_essays`·`related_sources`에 listed 가능 (부모→자식 트리 엣지). 단 자기 부모는 정확히 1개(`related_syntheses`).

```yaml
---
title: "주제명"
type: theme
created: 2026-05-23
updated: 2026-05-23
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-지도]]"   # 정확히 1개
related_concepts:           # theme의 자식 listed (선택)
  - "[[concept-slug]]"
related_essays:
  - "[[essay-slug]]"
related_sources:
  - "[[source-slug]]"
---
```

### Essay (사용자 본인 글)

```yaml
---
title: "글 제목"
type: essay
essay_date: YYYY-MM-DD  # 원본 작성일
created: 2026-05-23
updated: 2026-05-23
original_path: "92. 에세이/..."  # 원본 폴더 내 경로
raw_path: "raw/essays/..._exported.txt"
tags: [tag1, tag2]
status: stub | draft | mature
related_syntheses:
  - "[[부모-축-또는-theme]]"   # 정확히 1개
---
```

theme·concept·다른 essay와의 관계는 본문 `## 참고 자료`·`## 분류 기준` 섹션에서 plain text 슬러그로 언급.

### Synthesis (종합·해석·비교 — 축·허브 노드)

synthesis는 축 노드·일일 허브처럼 자식 다수를 묶는 부모 역할을 함. 자식 link는 synthesis 자신의 `related_concepts`·`related_*`에 listed (부모→자식 트리 엣지). 자기 부모는 1개(`related_syntheses`).

```yaml
---
title: "종합 주제"
type: synthesis
created: 2026-05-23
updated: 2026-05-23
tags: [tag1, tag2]
status: draft | mature
related_syntheses:
  - "[[부모-지도-또는-축]]"   # 정확히 1개 (축 노드면 지도, 일반 synthesis면 축)
related_concepts:           # 자식 listed (선택)
  - "[[concept-slug]]"
---
```

### Worklog (업무 캠페인 — 활동 노드)

raw 폴더 안의 todo log·세션 로그 등 "활동 기록"을 위키 그래프에 편입하는 노드. 개별 todo 1개가 아니라 **같은 주제의 todo·세션을 묶은 업무 캠페인 단위**로 잡아 노드 폭증을 막는다. source·concept와 같은 link 문법을 쓰되, 관계축은 "관련"이 아니라 **인과**(produces/applies/advances/follows)로 표현해 활동↔지식 관계를 논의 가능하게 한다.

```yaml
---
title: "업무 캠페인 이름"
type: worklog
date_range: "YYYY-MM-DD ~ YYYY-MM-DD"  # 단일 날짜면 한쪽만, 필수
created: 2026-05-24
updated: 2026-05-24
tags: [tag1, tag2]
status: 진행 | 완료 | 보류
produces:          # 이 활동이 낳은 자료·개념 (결과물)
  - "[[source-slug]]"
  - "[[concept-slug]]"
applies:           # 활동이 적용·검증한 기존 지식
  - "[[concept-slug]]"
advances:          # 활동이 진척시킨 주제·과제
  - "[[theme-slug]]"
  - "[[entity-slug]]"
follows:           # 선행 활동 (precedes는 그 역방향)
  - "[[worklog-slug]]"
precedes:
  - "[[worklog-slug]]"
source_logs:       # 근거가 된 raw 로그 경로 (인용, link 아님)
  - "raw/work/16. recent/260331 A .../todo log.md"
---
```

- **메타 배제**: 세션 로그의 "요청 표현·작성 과정·도구 흐름" 같은 메타는 본문에 옮기지 말 것. **무슨 업무를 했고 어떤 산출·결정이 나왔는지(결론)**만 요약 (글로벌 규칙 "산출물 본문 결론만" 정합).
- **휘발성 대응**: `16. recent`·`15. 2026` 등 수시 갱신 폴더가 출처면 `source_logs`에 인입 시점 경로를 스냅샷으로 기록. 경로가 끊겨도 노드는 활동의 결론을 보존.
- **양방향**: produces 대상 source/concept에는 본문에 "이 자료는 [[worklog]] 활동에서 산출됨" 한 줄로 역링크.

## Status 단계

| 단계 | 의미 | 적합한 카테고리 |
| --- | --- | --- |
| `stub` | 식별 정보만 (본문 거의 없음) | entity 기본값 |
| `draft` | 본문 있음, 미완·발전 중 | concept 기본값 |
| `mature` | 사용자 검토 거쳐 안정화 | source·essay 인입 직후 |

## 슬러그 명명 규약

- **raw 언어·용어 우선**: 슬러그·title은 raw 자료의 원어(현재 도메인은 한국어)로 작성하는 것을 기본으로 함. raw 본문에 개념·인물·기관·주제를 가리키는 용어가 이미 있으면 임의 의역·영문 환원 없이 raw의 표현을 최대한 그대로 사용
- 한국어 기본 (공백은 하이픈): `지식의-누적성`
- 원어가 영문인 자료만 소문자·하이픈 영문 슬러그: `attention-mechanism`
- 영문 약어가 사실상 고유명사인 경우(EMG·MPI·MSDS 등)는 원표기 유지
- 동일 슬러그 중복 금지 (전체 위키에서 unique)
- 위키 링크 형식: `[[slug]]` (확장자 생략)
- 날짜 prefix 사용 시: `260218-과거-글모음` (YYMMDD)

## 검증

`scripts/lint.py` 실행으로 frontmatter 표준 위반 자동 점검. 비표준 발견 시 `scripts/lint_fix.py`로 일괄 변환.
