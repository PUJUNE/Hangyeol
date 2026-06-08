"""LLM Wiki Lint Auto-fix
P0 — frontmatter YAML standardization (related_* fields → block list)
P1 — broken links (custom BODY_REPLACEMENTS 매핑 정의 필요)

사용법:
    cd <작업 폴더>
    # BODY_REPLACEMENTS를 본 작업 폴더 lint 결과에 맞춰 수정한 뒤
    python <스킬 경로>/scripts/lint_fix.py

전제:
    - 작업 폴더 cwd에 wiki/ 하위 폴더가 있어야 함
    - 표준 입력으로 사용자 승인 받는 대화는 호출자(LLM)가 별도 처리
"""
import os, re, sys, io, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WIKI = 'wiki'
FM_RE = re.compile(r'^(---\s*\n)(.*?)(\n---\s*\n)', re.DOTALL)

# Fields that may contain comma-separated [[link]] sequences and must be
# converted to block lists with quoted links.
LIST_FIELDS = {
    'tags', 'related_concepts', 'related_sources', 'related_entities',
    'related_essays', 'related_syntheses', 'related_themes', 'related_papers',
    'themes',
}

# `field: [[a]], [[b]], [[c]]` style lines
LINE_LIST_LINK_RE = re.compile(
    r'^(\s*)(\w+)\s*:\s*(\[\[[^\]]+\]\](?:\s*,\s*\[\[[^\]]+\]\])*)\s*$'
)


def fix_frontmatter(text):
    """Return (new_text, changes_list)."""
    changes = []
    m = FM_RE.match(text)
    if not m:
        return text, changes
    start, fm_body, end = m.group(1), m.group(2), m.group(3)
    new_lines = []
    for ln in fm_body.split('\n'):
        lm = LINE_LIST_LINK_RE.match(ln)
        if lm and lm.group(2) in LIST_FIELDS:
            indent, field, body = lm.group(1), lm.group(2), lm.group(3)
            links = re.findall(r'\[\[([^\]]+)\]\]', body)
            new_lines.append(f"{indent}{field}:")
            for lk in links:
                new_lines.append(f'{indent}  - "[[{lk}]]"')
            changes.append(f"{field}: {len(links)}개 link → block list")
            continue
        new_lines.append(ln)
    new_fm = '\n'.join(new_lines)
    new_text = start + new_fm + end + text[m.end():]
    return new_text, changes


# P1·P2 — body link fixes. 본 작업 폴더의 lint 결과에 따라 수정 필요.
# 예시 (2026-05-23 작업 폴더의 실제 사용):
#
# BODY_REPLACEMENTS = {
#     'wiki/syntheses/ai-acceleration-shumer-vs-self.md': [
#         ('[[260214 1640 개방성의 도구]]', '[[260214-ai-as-openness-tool]]'),
#     ],
#     'wiki/sources/heo-junyi-graduation-speech-2007.md': [
#         ('[[260203 1105]]', '`260203 1105`'),
#         ('[[260206 0257]]', '`260206 0257`'),
#         ('[[260218 0523 옛날 글]]', '`260218 0523 옛날 글`'),
#     ],
#     'wiki/entities/nonaka-ikujiro.md': [
#         ('[[link]]', '`[[link]]`'),
#     ],
#     'wiki/concepts/unix-philosophy.md': [
#         ('[[link]]', '`[[link]]`'),
#     ],
# }
BODY_REPLACEMENTS = {}


def apply_body_fixes(path, text):
    changes = []
    norm = path.replace('\\', '/')
    repls = BODY_REPLACEMENTS.get(norm, [])
    for old, new in repls:
        if old in text:
            text = text.replace(old, new)
            changes.append(f"본문: {old} → {new}")
    return text, changes


def main():
    total_fm_changes = 0
    total_body_changes = 0
    fm_files = 0
    body_files = 0
    for path in glob.glob(os.path.join(WIKI, '**', '*.md'), recursive=True):
        if 'lint-reports' in path or path.endswith(('log.md',)):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        new_text, fm_ch = fix_frontmatter(text)
        new_text, body_ch = apply_body_fixes(path, new_text)
        all_ch = fm_ch + body_ch
        if all_ch:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_text)
            rel = path.replace('\\', '/')
            print(f"\n[{rel}]")
            for c in all_ch:
                print(f"  - {c}")
            if fm_ch:
                fm_files += 1
                total_fm_changes += len(fm_ch)
            if body_ch:
                body_files += 1
                total_body_changes += len(body_ch)
    print(f"\n=== 요약 ===")
    print(f"frontmatter 수정: {fm_files} 파일 / {total_fm_changes} 필드")
    print(f"body 수정: {body_files} 파일 / {total_body_changes} 항목")


if __name__ == '__main__':
    main()
