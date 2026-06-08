# LLM 위키 스키마 — <위키 주제> 위키

본 파일은 본 작업 폴더에서 동작하는 LLM 에이전트가 위키를 **규율 있게** 유지·확장하기 위한 운영 매뉴얼임. Karpathy의 LLM Wiki 패턴(`gist:karpathy/442a6bf555914893e9891c11519de94f`)을 사용자 도메인에 맞춰 인스턴스화한 버전.

> ⓘ 이 템플릿을 작업 폴더 루트의 `CLAUDE.md`로 복사한 뒤 다음 항목을 치환:
> - `<위키 주제>` — 본인 도메인 (예: "개인 학습·에세이 통합")
> - `§9.1` 정션 표 — 마운트한 raw 하위 폴더 경로 명시
> - `§1` 위키 목적 — 본인 사용 맥락에 맞춰 재작성

---

## 1. 위키의 목적과 범위

- **주제**: <위키 주제>
- **사용자 역할**: 소스 큐레이션, 분석 방향 제시, 좋은 질문 던지기, 의미 해석
- **LLM 역할**: 읽기·요약·교차참조·일관성 유지·정합성 점검 등 부기(bookkeeping) 일체
- **상위 글로벌 규칙 우선**: `~/.claude/CLAUDE.md`의 모든 규칙(메모리 동기화, 산출물 본문 결론만 기입, 신뢰도 표기, AI 응답 스타일 등)은 본 위키 운영에도 동일 적용

---

## 2. 디렉터리 구조

```
<작업 폴더>/
├─ CLAUDE.md                # 본 스키마 파일
├─ raw/                     # 원본 자료 (immutable)
│  └─ <subfolder>/  → junction → <원본 절대경로>
├─ wiki/                    # LLM이 작성·유지하는 markdown 페이지
│  ├─ areas/                # 분류 루트(지도)와 축 노드 (선택, category 위키)
│  ├─ concepts/             # 사고·이론·프레임워크
│  ├─ sources/              # 원본 자료별 요약
│  ├─ entities/             # 인물·기관·책·제품
│  ├─ themes/               # 관통 모티프
│  ├─ essays/               # 사용자 본인 글
│  └─ syntheses/            # 종합·해석·비교
└─ working log/             # 세션 로그 (위키와 별개)
```

---

## 3. 페이지 유형별 frontmatter 규약 (YAML 표준 + 부모 1개 원칙)

**중요**:
- `related_*` 필드처럼 위키 link 다수 포함 시 반드시 **block list + 인용 부호** 사용. 인라인 콤마 분리(`[[a]], [[b]]`)는 YAML 표준 위반
- 한 노드의 `related_*` 합계는 **부모 1개** + (부모 노드인 경우 자식 다수)만 허용. 형제·다른 축 cross-link 금지
- raw 자료 슬러그를 `related_sources`에 wikilink 형식으로 두지 말 것 — 그래프 빌더에서 ghost(missing) 노드로 잡힘. raw 메타는 본문 `## 참고 자료` 섹션 plain text로 기록

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

세부 카테고리별 필드는 스킬의 `references/frontmatter-spec.md` 참조.

---

## 4. 파일 명명 규약

- **raw 언어·용어 우선**: 슬러그·title은 가급적 raw 자료의 원어(현재 도메인은 한국어)로 작성. raw 본문에 해당 개념·인물·기관·주제를 가리키는 용어가 이미 있으면 임의 의역·영문 환원 없이 raw의 표현을 최대한 그대로 슬러그·title에 사용. 예외는 원어에 표준 표기가 없거나 영문 약어가 사실상 고유명사인 경우(EMG·MPI·MSDS 등)
- 슬러그: 한국어 기본 (공백은 하이픈으로): `지식의-누적성.md`. 원어가 영문인 자료만 소문자·하이픈 영문 슬러그 (`attention-mechanism.md`)
- 동일 슬러그 중복 금지 — 위키 전체에서 unique
- 위키 링크는 `[[슬러그]]` 형식

---

## 5. 운영 3종

### 5.1 Ingest (인입)
사용자가 raw에 자료 + "인입해줘" 요청 → LLM이:
1. 자료 읽기
2. 핵심 시사점 3~7개 사용자와 토의
3. 신규 노드의 부모(축 노드 또는 다른 카테고리 노드) 1개를 사용자에게 확정 받음
4. source 페이지 작성 (또는 essay 분류 시 essay 페이지)
5. 신규 concept·entity 페이지 생성 / 기존 페이지 갱신 — 부모 1개만 link, 형제·다른 축과 cross-link 금지
6. 부모 노드의 `related_concepts`(또는 동등 자식 필드)에 자식 등재 (양방향 link는 부모-자식 1쌍만 유지)
7. raw 자료 슬러그는 본문 `## 참고 자료` 섹션에 plain text로 기록 (frontmatter `related_sources`에 wikilink 형식으로 두지 말 것)

### 5.2 Query (질의)
1. 축 노드(`areas/`)에서 관련 페이지 식별
2. 읽기 + 필요시 raw 검증
3. 답변 + 인용
4. 가치 있으면 synthesis 파일링 (사용자 동의)

### 5.3 Lint (정합성 점검)
스킬의 `scripts/lint.py` 실행 → 보고서 `wiki/lint-reports/lint-YYYY-MM-DD.md` 저장. 자동 수정은 `scripts/lint_fix.py` 사용자 승인 후 실행.

---

## 6. 트리 구조·index/log 미운영 정책

본 위키는 글로벌 「LLM 위키 트리 구조 원칙」과 「LLM 위키 index.md / log.md 미생성 규칙」을 적용함.

- 트리 계층: 지도(루트) → 축(상위 카테고리) → 카테고리 노드(말단) 3계층
- 신규 노드의 부모 link는 정확히 1개. 형제·다른 축 cross-link 금지
- 한 노드의 `related_*` wikilink 합계는 부모 1개 + (부모 노드인 경우 자식 다수)만 허용
- `wiki/index.md`·`wiki/log.md` 생성·갱신 금지 — 카탈로그는 축 노드 `related_concepts` 자식 리스트가 대체, 이벤트 기록은 `working log/session_log_*.md` 또는 `wiki/worklog/` 활동 노드가 대체
- 기존 위키의 다중 link·index·log 잔존은 사용자 명시 요청 시에만 정리, 자동 마이그레이션 금지

---

## 7. 문체·형식 규칙

본 위키는 외부 공유 산출물이 아닌 사용자 개인 지식베이스이므로 docx 한정 `~음` 체 강제는 적용하지 않음. 단 글로벌 규칙 중 다음은 적용:

- AI 상투어 회피
- 능동태 우선, 동사 다양화
- 산출물 본문에 작성 메타 정보 기입 금지 (그런 메타는 `working log/session_log_*.md`에만)
- 신뢰도 태그는 본문에 노출하지 말 것 — `status` frontmatter 필드로 표시

---

## 8. raw/ 불변 원칙

- 절대 수정·삭제·rename 금지
- 사용자가 직접 추가
- `raw/`만 있으면 `wiki/` 전체 재생성 가능해야 함 (재생성 가능성)
- 외부 URL 자료는 가능한 한 raw에 markdown으로 캐싱

### 8.1 정션 폴더 안전 규칙 ⚠

본 위키는 다음 디렉터리 정션을 사용:

| 정션 경로 | 대상 원본 |
| --- | --- |
| `raw/<name>/` | `<원본 절대경로>` |

공통 규칙:
- 정션 하위 파일을 수정·삭제·rename·이동하면 **원본 폴더 그대로 영향**. 변경 금지
- 원본에 새 파일 추가 시 정션에 자동 반영
- `.gdoc`은 메타 포인터이므로 동반 `_exported.txt`·`.docx`·`.txt` 우선 사용
- 다른 PC로 작업 옮길 때는 정션 재생성 필요 (스킬의 `references/junction-setup.md` 참조)
- 정션 삭제: `rmdir raw\<name>` 또는 `Remove-Item raw\<name>`만. `rm -rf` 금지

---

## 9. 시작 체크리스트

- [ ] 디렉터리 골격 생성 (`areas/`·`concepts/`·`sources/`·`entities/`·`themes/`·`essays/`·`syntheses/`)
- [ ] CLAUDE.md (본 파일) 본인 도메인에 맞춰 수정
- [ ] raw 정션 마운트 (필요 시)
- [ ] 분류 루트(지도)·축 노드 초기 생성 (`index.md`·`log.md`는 만들지 말 것)
- [ ] 첫 시드 자료 인입
