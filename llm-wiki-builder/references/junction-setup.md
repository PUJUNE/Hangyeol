# raw 폴더 정션 마운트 가이드 (Windows)

raw 폴더에 외부 원본 자료를 노출시키는 가장 안전한 방법 = Windows 디렉터리 정션. 복사하지 않고 가리키기만 함 → 원본 갱신 자동 반영 + 용량 부담 없음.

## 명령

PowerShell (관리자 권한 불필요):

```ps1
New-Item -ItemType Junction -Path "raw\<name>" -Target "<원본 절대경로>"
```

cmd 대안:

```cmd
mklink /J "raw\<name>" "<원본 절대경로>"
```

### 예시

```ps1
# 에세이 폴더 마운트
New-Item -ItemType Junction -Path "raw\essays" -Target "C:\Users\rkwka\내 드라이브\92. 에세이"

# 딥리서치 폴더 마운트
New-Item -ItemType Junction -Path "raw\deep-research" -Target "C:\Users\rkwka\내 드라이브\02. 딥리서치"
```

## 안전 규칙 ⚠

### 절대 금지
- 정션 하위 파일을 수정·삭제·rename·이동 → **원본 폴더 그대로 영향**
- `rm -rf raw/<name>/` 또는 `Remove-Item -Recurse raw\<name>` → **원본을 함께 지움**

### 허용
- 읽기 (LLM이 본문 read)
- 정션 자체 삭제: `rmdir raw\<name>` 또는 `Remove-Item raw\<name>` (정션만 제거, 원본 보존)

## 다중 PC 동기화

정션은 자동 따라오지 않음 (Google Drive·OneDrive 동기화 시도 동일). 새 PC에서 작업 시:

1. 작업 폴더 동기화 완료 후
2. PowerShell에서 raw 하위 정션 재생성:

```ps1
cd "<작업 폴더 경로>"
New-Item -ItemType Junction -Path "raw\essays" -Target "<원본 절대경로 1>"
New-Item -ItemType Junction -Path "raw\deep-research" -Target "<원본 절대경로 2>"
```

## 검증

정션 정상 작동 확인:

```bash
ls raw/<name>/ | head -5
# 정상 시 원본 폴더 내용 출력
```

## 다중 raw 정션 운영

본 작업 폴더(260523 llm 위키) 예시:

| 정션 | 원본 | 자료 성격 |
| --- | --- | --- |
| `raw/essays/` | `92. 에세이` | 사용자 본인 글 |
| `raw/deep-research/` | `02. 딥리서치` | 외부 LLM 보고서 + 논문 PDF |

각 정션은 인입 시 다른 카테고리(`essays/` vs `sources/`)로 분류됨.

## `.gdoc` 파일 처리

Google Drive `.gdoc`은 메타 포인터일 뿐 본문 없음. 읽기 전에:

1. 동반 `_exported.txt`·`.docx`·`.txt` 우선 사용
2. 없으면 `gdoc-batch-exporter` 스킬로 export (Apps Script 1회 실행)

본 위키 운영 시 사용자에게 이 사실을 안내하고 대안 자료 사용 또는 export 진행 권유.

## CLAUDE.md §9.1 갱신

새 정션 추가 시 작업 폴더 루트의 `CLAUDE.md` §9.1 정션 안전 규칙 표에 항목 추가. 다중 PC에서 재생성 명령도 같이 기록해 두면 다른 PC에서 참조 편함.
