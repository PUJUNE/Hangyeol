from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")
CONTENT_DIRS = {"concepts", "sources", "entities", "themes", "essays", "syntheses"}


def load(path: Path) -> tuple[dict, str, str | None]:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        return {}, text, "frontmatter missing"
    try:
        return yaml.safe_load(match.group(1)) or {}, text[match.end():], None
    except Exception as exc:
        return {}, text, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a single-parent tree wiki.")
    parser.add_argument("--wiki", default="wiki", help="Wiki directory")
    args = parser.parse_args()
    wiki = Path(args.wiki)
    pages = [p for p in wiki.rglob("*.md") if "lint-reports" not in p.parts and not any(part.startswith(".") for part in p.parts)]
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
        if parent_dir == "areas" and path.name not in {"index.md", "log.md"}:
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
