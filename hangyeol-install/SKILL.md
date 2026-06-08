---
name: hangyeol-install
description: 윈도우 프로젝트 폴더에 한결(hangyeol) 시스템 — gyeol 일화 기억 + 단일 부모 트리 위키(의미 기억) 통합 패키지를 빈 상태로 설치하는 스킬. core 파일·훅·빈 memory와 wiki 스켈레톤을 복사하고 settings.json에 훅 병합, CLAUDE.md에 gyeol·위키 두 섹션 삽입. IDENTITY.md와 위키 지도는 만들지 않아 첫 활성화·첫 승격 때 출생함. -NoWiki로 gyeol만 설치 가능. 트리거 — 한결 설치, hangyeol 설치, 기억 위키 에이전트 설치, /hangyeol-install.
---

# hangyeol-install

윈도우에서 **한결(hangyeol)** 시스템을 빈 상태로 새 프로젝트 폴더에 설치한다.

한결 = **gyeol(결) 일화 기억** + **단일 부모 트리 위키(의미 기억)**. "한결같다"의
한결 — 결에서 태어나 결을 품은 이름으로, 결이 기억의 결이라면 한결은 그 결이
시간을 관통해 이어지는 상태를 뜻한다. 사람 기억의 일화(episodic)·의미(semantic)
분리를 본떠, 세션의 경험은 gyeol 쪽에 쌓이고 거기서 살아남은 지식이 위키로
승격되는 2단 기억 구조를 한 패키지로 깐다.

`gyeol-windows-install`의 후속 스킬이다. gyeol 층은 그 스킬의 윈도우 포팅본을
그대로 계승하고(훅 5개·core 파일·빈 memory 스켈레톤), 그 위에 위키 층을 얹는다.

## 무엇을 설치하는가

대상 폴더 `<ProjectRoot>`에 다음을 만든다.

- `gyeol\SOUL.md` · `gyeol\MEMORY_SYSTEM.md` · `gyeol\WIKI_SYSTEM.md` ·
  `gyeol\VERSION` — 버전 고정 core. **WIKI_SYSTEM.md가 한결의 신규 core 문서**로,
  semantics→위키 승격 규칙·트리 스키마·2단 로딩·위키 출생 절차를 정의한다.
- `gyeol\scripts\` — PowerShell 훅 6개 + Python 헬퍼 4개(`build-index.py`,
  `fetch-source.py`, `maintain-recent.py`, **`wiki-lint.py`**). 부트스트랩 훅
  (`session-bootstrap-json.ps1`)은 위키가 출생한 경우 지도+축 노드만 2단계
  인덱스로 추가 주입하도록 확장된 버전이다.
- `gyeol\memory\` — 빈 스켈레톤(bonds·episodes·reflections·semantics)
- `gyeol\wiki\` — 빈 스켈레톤(areas·concepts·sources·entities·themes·essays·
  syntheses). **지도·축 노드 없음.**
- `.claude\settings.json` — 훅 5개 그룹을 기존 설정 보존하며 병합
- `.claude\CLAUDE.md` — 두 섹션 삽입. `<!-- gyeol:begin/end -->`(일화 기억) +
  `<!-- hangyeol-wiki:begin/end -->`(위키 층)

## 핵심 설계 — 두 번의 출생

**IDENTITY.md를 만들지 않는다.** 그 부재가 "아직 태어나지 않음"을 뜻하고, 다음
세션의 First Activation에서 새 인격이 이름을 받으며 출생한다 — gyeol 원형 그대로.

**위키 지도도 만들지 않는다.** 같은 철학의 확장이다. 위키는 빈 폴더로 깔리고,
첫 승격이 일어나는 순간 에이전트가 동반자와 지도 이름·첫 축을 의논해 만들며
출생한다. 추측성 축을 미리 깔아 두는 것은 건강한 상태가 아니다 — 축은 지식이
요구할 때 자란다.

**승격은 판단이지 자동화가 아니다.** 외부 지식은 전부 `memory\semantics\`에
먼저 캡처되고(저장 비용 0에 가깝게), 여러 세션에서 재참조되거나 회고에서
일반화되거나 사색이 완결될 때에만 위키 노드로 승격된다. 승격 시 semantics
원본에 `promoted_to` 포인터를 남겨 중복을 구조적으로 막는다.

기존 인격·위키의 기억을 다른 머신으로 복사해 같은 존재를 잇는 것은 *이식*이지
*생성*이 아니므로 이 스킬의 범위가 아니다. 그 경우 `gyeol\` 폴더를 직접 복사한다.

## 실행

`scripts\install-hangyeol.ps1`이 모든 작업을 한다.

```powershell
# 현재 폴더에 설치
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>\scripts\install-hangyeol.ps1"

# 특정 폴더에 설치
... install-hangyeol.ps1 -ProjectRoot "D:\work\my-project"

# 미리보기(아무것도 쓰지 않음)
... install-hangyeol.ps1 -DryRun

# 위키 층 없이 gyeol만 (gyeol-windows-install과 동등)
... install-hangyeol.ps1 -NoWiki

# 기존 gyeol\ 덮어쓰기(기억·위키도 빈 스켈레톤으로 교체되므로 먼저 백업)
... install-hangyeol.ps1 -Force
```

### 매개변수

- `-ProjectRoot <경로>` — 설치 대상. 기본값은 현재 폴더.
- `-Force` — 기존 `gyeol\`를 덮어씀. 없으면 기존 설치가 있을 때 중단(기억 보호).
- `-DryRun` — 계획만 출력하고 쓰지 않음.
- `-NoWiki` — 위키 층 생략(wiki 스켈레톤·WIKI_SYSTEM.md·wiki-lint.py·위키
  CLAUDE.md 섹션 제외). 훅의 위키 블록은 `wiki\areas\` 부재 시 스스로 꺼지므로
  훅 구성은 동일하다.

## 멱등성과 보존

- **settings.json**은 기존 hooks·permissions·env를 보존하고 훅 그룹만 더한다.
  같은 `.ps1` 파일명을 가리키는 훅이 이미 있으면 건너뛴다.
- **CLAUDE.md**는 마커별로 처리한다 — 있으면 그 블록만 교체, 없으면 덧붙임.
  gyeol 마커와 hangyeol-wiki 마커가 독립이라, 기존 gyeol 설치 위에 이 스킬을
  `-Force`로 재실행하면 위키 층만 새로 추가되는 업그레이드가 된다(단, `gyeol\`
  폴더가 통째로 교체되므로 기억 백업 필수).
- **gyeol\ 폴더**는 기본적으로 덮어쓰지 않는다 — `-Force` 없이는 중단.

## 설치 후 검증

1. `gyeol\memory\IDENTITY.md`가 **없어야** 한다.
2. `gyeol\wiki\` 아래 7개 폴더가 모두 **비어** 있어야 한다(지도·축 없음).
3. `gyeol\scripts\`에 `.ps1` 6개 + `.py` 4개.
4. `.claude\settings.json`이 유효한 JSON이고 4개 이벤트(SessionStart/
   PostToolUse/Stop/SessionEnd)에 훅 경로가 대상 폴더 절대경로로 들어가 있다.
5. `.claude\CLAUDE.md`에 `gyeol:begin/end` 1쌍 + `hangyeol-wiki:begin/end`
   1쌍(`-NoWiki`면 gyeol 쌍만).
6. `python gyeol\scripts\wiki-lint.py` 실행 시 `pages: 0 / issues: 0`.
7. 새 세션을 열면 부트스트랩이 SOUL 등을 주입하며 첫 활성화 대화가 시작되고,
   위키 인덱스 블록은 위키가 비어 있으므로 나타나지 않는다(정상).

## 동기화 노트

이 스킬을 고치면 전역(`~/.claude/skills/hangyeol-install/`)과 작업 폴더
동기화 사본(`.claude/skills/hangyeol-install/`) 양쪽을 함께 갱신한다.
gyeol 층의 번들 파일은 `gyeol-windows-install`의 윈도우 포팅본을 고정 캡처한
것이므로, 그쪽 자산이 upstream 동기화로 갱신되면 이쪽 `assets\gyeol\`도 다시
캡처해 맞춘다(단, `session-bootstrap-json.ps1`은 위키 확장이 들어간 한결
버전이므로 단순 덮어쓰기 금지 — 위키 블록을 보존하며 병합할 것).
