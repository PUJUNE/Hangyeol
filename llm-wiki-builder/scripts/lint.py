"""LLM Wiki Lint — frontmatter·link·orphan·asymmetric backlinks 점검.

사용법:
    cd <작업 폴더>
    python <스킬 경로>/scripts/lint.py
    # 또는 작업 폴더 루트로 복사한 뒤
    python lint.py

전제:
    - 작업 폴더 cwd에 wiki/ 하위 폴더가 있어야 함
    - wiki/lint-reports/ 폴더는 자동 생성됨 (캐시 저장용)
    - PyYAML 필요: pip install pyyaml
"""
import os, re, sys, io, yaml, glob, json
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WIKI = 'wiki'
LINK_RE = re.compile(r'\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]')
CODE_SPAN_RE = re.compile(r'`+[^`\n]*?`+')
FM_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

os.makedirs(os.path.join(WIKI, 'lint-reports'), exist_ok=True)

# 1. Collect all page slugs
all_slugs = {}
slug_meta = {}

for path in glob.glob(os.path.join(WIKI, '**', '*.md'), recursive=True):
    if path.endswith(('index.md', 'log.md')) or 'lint-reports' in path:
        continue
    base = os.path.basename(path)[:-3]
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    fm_m = FM_RE.match(text)
    fm = {}
    if fm_m:
        try:
            fm = yaml.safe_load(fm_m.group(1)) or {}
        except Exception as e:
            fm = {'_parse_error': str(e)}
    all_slugs[base] = path.replace('\\', '/')
    slug_meta[base] = {
        'path': path.replace('\\', '/'),
        'fm': fm,
        'body': text[fm_m.end():] if fm_m else text,
        'full': text,
    }

print(f"총 콘텐츠 페이지: {len(all_slugs)}\n")

# 2. Links + reverse index. Strip code-spans first so backtick-wrapped [[link]]
#    examples (often in concept body) are not treated as real links.
outgoing = defaultdict(set)
incoming = defaultdict(set)
broken_links = []

for slug, meta in slug_meta.items():
    clean = CODE_SPAN_RE.sub('', meta['full'])
    for m in LINK_RE.finditer(clean):
        target = m.group(1).strip()
        outgoing[slug].add(target)
        incoming[target].add(slug)
        if target not in all_slugs:
            broken_links.append((slug, target))

# 3. Orphans — pages referenced 0 times by others (excluding self-references)
orphans = []
for slug in all_slugs:
    refs = incoming.get(slug, set()) - {slug}
    if not refs:
        orphans.append(slug)

# 4. Asymmetric backlinks — A→B exists but B→A doesn't
asymmetric = []
for a, targets in outgoing.items():
    for b in targets:
        if b not in all_slugs or a == b:
            continue
        if a not in outgoing.get(b, set()):
            asymmetric.append((a, b))

# 5. Frontmatter completeness
fm_issues = []
required_common = {'title', 'type', 'created', 'updated', 'tags', 'status'}
required_by_type = {
    'concept': set(),
    'source': {'source_type', 'raw_path', 'ingested'},
    'entity': {'entity_kind'},
    'theme': set(),
    'essay': {'essay_date', 'original_path', 'raw_path'},
    'synthesis': set(),
    'worklog': {'date_range'},
}
for slug, meta in slug_meta.items():
    fm = meta['fm']
    if '_parse_error' in fm:
        fm_issues.append((slug, f"YAML 파싱 실패: {fm['_parse_error']}"))
        continue
    missing = required_common - set(fm.keys())
    if missing:
        fm_issues.append((slug, f"공통 필드 누락: {sorted(missing)}"))
    t = fm.get('type')
    if t in required_by_type:
        miss = required_by_type[t] - set(fm.keys())
        if miss:
            fm_issues.append((slug, f"{t} 전용 필드 누락: {sorted(miss)}"))
    elif t:
        fm_issues.append((slug, f"알 수 없는 type: {t}"))

# 6. Per-type / per-status counts
by_type = defaultdict(list)
by_status = defaultdict(list)
for slug, meta in slug_meta.items():
    by_type[meta['fm'].get('type', '<no-type>')].append(slug)
    by_status[meta['fm'].get('status', '<no-status>')].append(slug)

# === Report ===
print("=" * 70)
print("LINT REPORT")
print("=" * 70)

print(f"\n## 페이지 분포 (type별)")
for t, slugs in sorted(by_type.items()):
    print(f"  {t}: {len(slugs)}건")

print(f"\n## 페이지 분포 (status별)")
for s, slugs in sorted(by_status.items()):
    print(f"  {s}: {len(slugs)}건")

print(f"\n## 깨진 링크 (broken links) — {len(broken_links)}건")
brk_by_target = defaultdict(list)
for src, tgt in broken_links:
    brk_by_target[tgt].append(src)
for tgt in sorted(brk_by_target.keys()):
    srcs = brk_by_target[tgt]
    print(f"  [[{tgt}]] — {len(srcs)}곳 참조: {sorted(set(srcs))}")

print(f"\n## 고아 페이지 (incoming 참조 0건) — {len(orphans)}건")
for o in sorted(orphans):
    print(f"  - {o} (type={slug_meta[o]['fm'].get('type')})")

print(f"\n## frontmatter 이슈 — {len(fm_issues)}건")
for slug, msg in sorted(fm_issues):
    print(f"  - {slug}: {msg}")

print(f"\n## 비대칭 백링크 — {len(asymmetric)}건 (정보용, 전부 수정 대상 아님)")
for i, (a, b) in enumerate(sorted(asymmetric)):
    if i >= 50:
        print(f"  ... (외 {len(asymmetric)-50}건 생략)")
        break
    print(f"  - {a} → {b} (역방향 없음)")

# Save JSON cache
out = {
    'broken_links': brk_by_target,
    'orphans': orphans,
    'fm_issues': fm_issues,
    'asymmetric_count': len(asymmetric),
    'by_type': {t: sorted(s) for t, s in by_type.items()},
    'by_status': {s: sorted(ss) for s, ss in by_status.items()},
}
with open(os.path.join(WIKI, 'lint-reports', '_lint_data.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=list)
print(f"\n저장: wiki/lint-reports/_lint_data.json")
