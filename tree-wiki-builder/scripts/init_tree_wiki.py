from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

CATEGORIES = ["concepts", "sources", "entities", "themes", "essays", "syntheses"]
CHILD_FIELDS = ["related_concepts", "related_sources", "related_entities", "related_themes", "related_essays", "related_syntheses"]


def slug(text: str) -> str:
    return text.strip().replace("/", "／").replace("\\", "＼").replace(":", " -")


def fm(title: str, page_type: str, tags: list[str], extra: str = "") -> str:
    today = date.today().isoformat()
    tag_text = "[" + ", ".join(tags) + "]"
    parts = [
        "---",
        f'title: "{title}"',
        f"type: {page_type}",
        f"created: {today}",
        f"updated: {today}",
        f"tags: {tag_text}",
        "status: mature",
    ]
    if extra:
        parts.append(extra.rstrip())
    parts.append("---")
    return "\n".join(parts) + "\n\n"


def write_new(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a single-parent tree wiki.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--map", required=True, help="Top map node title")
    parser.add_argument("--axes", required=True, help="Comma-separated axis titles")
    args = parser.parse_args()

    root = Path(args.root)
    wiki = root / "wiki"
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "working log").mkdir(parents=True, exist_ok=True)
    (wiki / "areas").mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        (wiki / cat).mkdir(parents=True, exist_ok=True)

    axes = [slug(a) for a in args.axes.split(",") if a.strip()]
    map_slug = slug(args.map)
    map_extra = "related_syntheses:\n" + "\n".join(f'  - "[[{axis}]]"' for axis in axes)
    map_body = f"# {args.map}\n\n이 문서는 트리 위키의 루트 지도임.\n"
    created = write_new(wiki / "areas" / f"{map_slug}.md", fm(args.map, "synthesis", ["tree-map"], map_extra) + map_body)
    print(f"map: {'created' if created else 'exists'} {map_slug}")

    child_blocks = "\n".join(f"{field}: []" for field in CHILD_FIELDS)
    for axis in axes:
        extra = f'related_syntheses:\n  - "[[{map_slug}]]"\n{child_blocks}'
        body = f"# {axis}\n\n이 축에 속한 콘텐츠 노드를 관리함.\n"
        created = write_new(wiki / "areas" / f"{axis}.md", fm(axis, "synthesis", ["tree-axis"], extra) + body)
        print(f"axis: {'created' if created else 'exists'} {axis}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
