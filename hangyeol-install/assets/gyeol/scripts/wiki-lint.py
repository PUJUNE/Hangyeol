# hangyeol wiki lint — single-parent tree integrity checker.
#
# Adapted from tree-wiki-builder's tree_lint.py. GYEOL_HOME is derived from
# this script's location (parent of scripts dir), so the default wiki path is
# $GYEOL_HOME/wiki with no arguments needed. PyYAML is used when available;
# otherwise a minimal frontmatter parser (sufficient for the wiki schema's
# flat keys and simple lists) takes over, so the lint has no hard dependency.
from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")
CONTENT_DIRS = {"concepts", "sources", "entities", "themes", "essays", "syntheses"}


def parse_frontmatter_naive(text: str) -> dict:
    """Minimal YAML subset parser: flat 'key: value', inline lists, and
    block lists of scalar items. Enough for the hangyeol wiki schema."""
    data: dict = {}
    key = None
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value == "":
                data[key] = []  # assume block list follows (or empty)
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()] if inner else []
            else:
                data[key] = value.strip("'\"")
        elif re.match(r"^\s+-\s+", line) and key is not None and isinstance(data.get(key), list):
            data[key].append(line.split("-", 1)[1].strip().strip("'\""))
    return data


def load(path: Path) -> tuple[dict, str, str | None]:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        return {}, text, "frontmatter missing"
    raw = match.group(1)
    if yaml is not None:
        try:
            return yaml.safe_load(raw) or {}, text[match.end():], None
        except Exception as exc:
            return {}, text, str(exc)
    return parse_frontmatter_naive(raw), text[match.end():], None


def main() -> int:
    gyeol_home = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Lint the hangyeol single-parent tree wiki.")
    parser.add_argument("--wiki", default=str(gyeol_home / "wiki"), help="Wiki directory (default: $GYEOL_HOME/wiki)")
    args = parser.parse_args()
    wiki = Path(args.wiki)
    if not wiki.is_dir():
        print(f"wiki directory not found: {wiki}")
        return 1
    pages = [p for p in wiki.rglob("*.md") if not any(part.startswith(".") for part in p.parts)]
    slugs = {p.stem for p in pages}
    issues: list[str] = []

    for forbidden in [wiki / "index.md", wiki / "log.md"]:
        if forbidden.exists():
            issues.append(f"forbidden file exists: {forbidden.relative_to(wiki)}")

    for path in pages:
        rel = path.relative_to(wiki).as_posix()
        fm, body, error = load(path)
        if error:
            issues.append(f"{rel}: {error}")
            continue
        parent_dir = path.parent.name
        if parent_dir in CONTENT_DIRS:
            axes = fm.get("related_axes") or []
            if not isinstance(axes, list) or len(axes) != 1:
                issues.append(f"{rel}: related_axes must contain exactly one parent")
        if parent_dir == "areas":
            parents = fm.get("related_syntheses") or []
            if not isinstance(parents, list):
                issues.append(f"{rel}: related_syntheses must be a list")
        clean = re.sub(r"`+[^`\n]*?`+", "", path.read_text(encoding="utf-8"))
        for target in LINK_RE.findall(clean):
            if target not in slugs:
                issues.append(f"{rel}: broken link [[{target}]]")
        if LINK_RE.search(body):
            issues.append(f"{rel}: body wikilink present")

    print(f"pages: {len(pages)}")
    print(f"issues: {len(issues)}")
    for issue in issues:
        print(f"- {issue}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
