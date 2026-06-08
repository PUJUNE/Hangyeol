# Lint 절차 — 정합성 점검

위키가 ~30 page 이상 자라면 모순·고아·broken link·frontmatter 오류가 누적될 수 있음. 주기적 lint로 건강 유지.

## 점검 항목 7가지

1. **페이지 간 모순·충돌** — 한 page가 A라고 한 것을 다른 page가 ~A라고 한 경우
2. **stale claim** — 새 source가 들어와 무효화한 옛 주장
3. **고아 페이지** — 다른 page에서 `[[link]]`로 0회 참조
4. **본문에 등장하지만 자체 page가 없는 개념·엔티티** — broken link
5. **누락된 양방향 링크** — A→B는 있는데 B→A 없음 (의도된 비대칭은 정상)
6. **frontmatter 누락·오류** — 필수 필드 누락, YAML 표준 위반
7. **데이터 공백** — "별도 인입 후보"·"미확인"·"출처 미확인"으로 남긴 항목

## 자동화 도구 — scripts/lint.py

스킬의 `scripts/lint.py`를 작업 폴더 루트로 복사 후 실행:

```bash
cd <작업 폴더>
python scripts/lint.py
```

출력:
- 페이지 분포 (type별·status별)
- 깨진 링크 + 참조 출처
- 고아 페이지
- frontmatter 이슈 (YAML 파싱 실패·필수 필드 누락·잘못된 type 등)
- 비대칭 백링크 (정보용)

캐시: `wiki/lint-reports/_lint_data.json`에 모든 결과 저장 (다음 lint와 비교용)

## 자동 수정 — scripts/lint_fix.py

사용자 승인 후 실행:

```bash
python scripts/lint_fix.py
```

자동 수정 대상:
- **P0 frontmatter YAML 표준화**: `related_*: [[a]], [[b]]` → block list
- **P1 broken link**: 본문 내 옛 슬러그 잔존을 새 슬러그로 치환 (수동 매핑 정의 필요)
- **P1 `[[link]]` 오인식**: 본문에서 위키 link를 설명하는 텍스트를 백틱 escape

스크립트 상단의 `BODY_REPLACEMENTS` 매핑을 본 작업 폴더 상황에 맞춰 수정한 뒤 실행.

## Lint 보고서 작성

`wiki/lint-reports/lint-YYYY-MM-DD.md` 파일로 저장. 구조:

```markdown
---
title: "Lint Report — YYYY-MM-DD"
type: lint-report
created: YYYY-MM-DD
scope: "wiki/ 전체 (페이지 N건)"
status: actionable | resolved
---

# Lint Report — YYYY-MM-DD

## 요약 (표)
## 1. 구조적 결함 (있을 시)
## 2. 깨진 링크
## 3. 고아 페이지
## 4. 비대칭 백링크
## 5. 데이터 공백
## 6. 조치 우선순위 (P0~P3)
## 7. 후속
## 8. 조치 결과 (자동 수정 후 추가)
## 메타
```

## log.md 기록

```markdown
## [YYYY-MM-DD] lint
- 보고서: wiki/lint-reports/lint-YYYY-MM-DD.md
- 발견: broken N건, 고아 N건, frontmatter 이슈 N건
- 자동 수정: scripts/lint_fix.py (사용자 승인 후)
- 재검증: 모든 항목 0건 ✓
```

## Lint의 메타 의미

본 동작은 단순 정리가 아니라 본 위키의 [[provocations]] 메커니즘 — 사용자에게 "이 page들 사이에 모순이 있는데 어떻게 해석할 거냐"고 묻는 마찰. 보고서가 사용자 메타인지 자극.

## 다음 lint 주기

- 새 인입 ~5건 누적 시
- 또는 사용자 요청 시
- 주제 큰 변화·새 theme 형성 후

## 코드 변경 후 검증

`lint.py` 자체를 수정한 경우 (예: 정규식 개선) 재실행해서 0건 달성 확인. 코드-span 내부 `[[link]]`를 무시하는 정규식 등은 작업 폴더 상황에 따라 조정 필요.
