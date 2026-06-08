# Ingest 절차 — 인입 6단계

사용자가 raw에 자료를 두고 "인입해줘"라고 요청하면 LLM이 본 절차로 수행. 글로벌 「LLM 위키 트리 구조 원칙」과 「LLM 위키 index.md / log.md 미생성 규칙」 정합.

## 6단계

### 1. 자료 분류 (사용자 글 vs 외부 자료)

- 사용자 본인 글 → `essays/`
- 외부 자료(논문·기사·강연·외부 LLM 생성물) → `sources/`
- 외부 LLM(Gemini Deep Research·ChatGPT 등)이 만든 자료도 외부 자료로 분류 (essay 아님)

### 2. 자료 본문 읽기

- `.txt`·`.md` 우선
- `.docx`는 그대로 가능
- `.gdoc`은 동반 `_exported.txt`·`.docx`·`.txt` 사용. 없으면 `gdoc-batch-exporter` 스킬로 export
- PDF는 첫 ~10페이지 우선, 필요시 전체

### 3. 핵심 시사점 3~7개 사용자와 토의

LLM은 자체 판단으로 page를 작성하지 말고 먼저 사용자에게:
- 추출한 시사점 목록 제시
- 강조 지점·기각·통합 의견 수렴
- 의문점·맥락 질문

이 토의가 [[provocations]] 메커니즘 — 사용자 메타인지를 활성화.

### 3-b. 부모 노드 확정

신규 노드의 부모(축 또는 다른 카테고리 노드) 1개를 사용자에게 후보 제시 후 확정 받기. 형제·다른 축 cross-link는 작성하지 않음. raw 자료 슬러그·인용은 frontmatter `related_sources`에 wikilink 형식으로 두지 말고 본문 `## 참고 자료` 섹션 plain text로 기재.

### 4. source 또는 essay 페이지 작성

frontmatter 표준 형식(block list) 따름. `related_syntheses`에 부모 1개 link, 그 외 `related_*` 필드는 비움. 본문 구조:

```markdown
# <제목>

## 한 줄 요약
(1~2문장)

## 핵심 명제 3~7개
1. ...
2. ...

## 분류 기준
- 이 노드가 어떤 자료·관찰을 묶는지 한두 줄로 명시

## 참고 자료
- raw 자료 슬러그·제목 plain text 목록 (wikilink 형식 사용 금지)

## 추가 탐구
- 후속 질문 후보
- 미해결 영역
```

본문에 `[[other-node]]` wikilink는 사용하지 않음 — 부모 노드(축)는 frontmatter `related_syntheses`로만 표현하고, 다른 카테고리 노드는 plain text 슬러그로만 언급함.

### 5. 신규 concept·entity 페이지 생성 / 기존 갱신

본문에서 추출된 명제를 concept으로 승격할 가치가 있으면 별도 page. 기준:
- 사용자가 명시적으로 명명한 개념
- 여러 다른 page에서 참조될 가능성
- 단일 사례 너머의 일반성

기존 page에 영향이 있으면 그 page의 `related_*` 필드 + 본문 동시 갱신.

### 6. 부모-자식 link 한 쌍만 양방향 유지

신규 노드 A의 부모(축 또는 다른 노드) B에 대해서만 양방향 link:
- A의 `related_syntheses`에 `[[B]]`
- B의 `related_concepts`(또는 동등 자식 필드)에 `[[A]]` 추가

형제 노드·다른 축과의 cross-link는 작성하지 않음. `wiki/index.md`·`wiki/log.md`는 생성·갱신하지 않음 (글로벌 「LLM 위키 index.md / log.md 미생성 규칙」). 이벤트 기록이 필요하면 `working log/session_log_*.md`에 기록.

## 인입 작업 단위

- 1 자료당 보통 10~15 page를 건드림 (생성 + 갱신)
- 본문 압축 권장 — 깊이는 사용자 검토를 통해 점진적으로
- 외부 LLM 생성물 인입 시 사용자 본인 명제만 추출, LLM 페르소나 응답은 보조 자료로만 다룸

## 사용자 협업 패턴

**Cross-pollination 탐지**: 사용자가 같은 주제를 essay·deep research 두 채널로 동시 탐구하는 패턴이 흔함. 인입 시 시점 비교(같은 날·다음 날·한 달 전)가 강력한 발견. 두 자료를 함께 두면 자연스럽게 synthesis 후보 도출.

**Theme 형성 신호**: 여러 essay/source/concept이 같은 모티프로 묶이기 시작하면 theme 페이지 생성. 신중하게 명명 — theme는 본 위키의 가장 큰 hub.

**시그니쳐 보존**: 사용자 본인 명명을 외부 학술 용어로 환원하지 말 것. 두 명칭이 같은 메커니즘을 가리키면 page에 명시적으로 평행 관계 기술 (예: 사용자의 [[ai-lock-in-effect]] vs MS Research의 [[cognitive-offloading]] = 같은 구조의 두 명명).

## 일괄 인입 (4건 이상)

여러 자료를 한 번에 인입할 때 — 다음 사용자 결정 트리:

1. **C 모드 (추천)**: 1건 깊게 + 나머지 동일 패턴 일괄 — 시범 1건으로 컨벤션 시각 확립 후 양산
2. **B 모드**: 일괄 토론 → 일괄 생성 — 모두 먼저 읽고 핵심 시사점 보고 후 양산
3. **A 모드**: 5건 일괄 자동 — 사용자 토론 없이 LLM 판단 (시그니쳐 보존 어려움)
