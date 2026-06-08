# Worklog 편입 절차 — raw 로그를 업무 캠페인 노드로

raw 폴더 안에 흩어진 `todo log.md`·세션 로그(`session_log_*.md`)·`claude log`/`working log` 폴더를 위키 그래프에 편입하는 절차. source(자료)와 구분되는 **활동 기록**을 다룬다. frontmatter 규약은 `frontmatter-spec.md`의 Worklog 절 참조.

## 핵심 원칙

1. **입자 = 업무 캠페인**: 개별 todo 1개를 1노드로 만들면 그래프가 노이즈로 폭증한다(`16. recent`만 todo 100+). 같은 주제의 todo·세션을 묶어 **하나의 캠페인 노드**로 만든다.
2. **관계축 = 인과**: source의 `related_*`(단순 관련)와 달리 활동은 인과를 가진다.
   - `produces` — 활동이 낳은 source·concept (결과물)
   - `applies` — 활동이 적용·검증한 기존 concept (지식)
   - `advances` — 진척시킨 theme·entity (주제·과제)
   - `precedes`/`follows` — 활동 간 시간 인과
   - `source_logs` — 근거 raw 경로 (인용, `[[link]]` 아님)
3. **결론만**: 세션 로그의 요청 표현·작성 과정·도구 흐름 등 메타는 본문에 옮기지 않는다. **무슨 업무·산출·결정**만 요약(글로벌 규칙 "산출물 본문 결론만" 정합).
4. **재생성 원칙 유지**: raw 안의 로그를 출처로 하므로 §9 재생성 가능성을 깨지 않는다. 단 프로젝트 `working log/`(raw 밖)는 편입 대상이 아니다.

## 절차

1. **스캔**: `find <대상> -iname "todo*log*.md"`, `-iname "session_log*"`, `-type d -iname "*log"`로 로그 인벤토리 작성.
2. **등급 필터**: `16. recent`는 폴더명에 등급(A/B/C/D)이 있다. **A(R&D 핵심)·핵심 B(연구 지원)만** 편입. C(주간보고·비용·회의비)·D(설문·고용·홈페이지)·도구 메타작업(스킬 개발·디자인·video-html)은 제외.
3. **주제 클러스터링**: 폴더명으로 주제별 캠페인 안을 만든다(예: AgAgCl 전하량 / 하이드로젤 pH·DSC / PEDOT 생기원 / EMG 설계 / 외부분석 / AED·이미용). 캠페인 경계는 임의 확정하지 말고 표로 제시해 **사용자 확정**(업무 플랜 사전확인 규칙).
4. **노드 작성**: `wiki/worklog/<날짜>-<주제>-캠페인.md`. produces/applies/advances를 기존 위키 슬러그에 정확히 매핑. source_logs에 raw 경로(휘발성 폴더는 인입 시점 스냅샷). 본문은 "무엇을 했나(결론)" + "관계" 두 절.
5. **incoming 확보(orphan 방지)**: 두 경로 중 택일/병용.
   - produces 대상 source 본문에 `> 이 자료는 [[<캠페인>]] 활동에서 산출됨` 한 줄 역링크
   - 관련 theme frontmatter에 `related_worklog:`로 캠페인을 모음(주제↔활동 양방향, 허브 역할에 적합)
   - 캠페인 간 `precedes`/`follows` 체인도 상호 incoming을 만든다
6. **index 갱신**: `## Worklog (N)` 섹션에 한 줄 요약 추가.
7. **log·lint**: `wiki/log.md`에 `## [날짜] worklog | ...` 기록, `python lint.py wiki`로 깨진 링크 0·고아 0·frontmatter 0 확인.

## 검증 포인트

- lint `required_by_type`에 `worklog`(필수 `date_range`)가 등록돼 있어야 "알 수 없는 type" 경고가 안 난다.
- worklog status는 `진행`/`완료`/`보류`를 쓴다(stub/draft/mature 아님). lint는 status 값을 검사하지 않으므로 무방.
- todo log 다수는 짧은 등록 메모라 폴더명이 핵심 정보다. 본문 결론은 폴더명 + 기존 위키 지식으로 작성하고, 새 주제만 todo 본문을 읽어 보강.
