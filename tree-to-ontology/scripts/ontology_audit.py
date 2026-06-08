from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import yaml

ALLOWED_RELATIONS = {
    "belongs_to",
    "part_of",
    "has_axis",
    "has_mechanism",
    "causes",
    "contradicts",
    "addresses",
    "pairs_with",
    "extends",
    "instantiates",
    "grounds",
    "supports",
    "evidenced_by",
    "draws_from",
    "applies_to",
    "shares_structure_with",
}
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def pages(wiki: Path) -> list[Path]:
    return [
        p
        for p in sorted(wiki.rglob("*.md"))
        if "lint-reports" not in p.parts and not any(part.startswith(".") for part in p.parts)
    ]


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        return {"_error": "frontmatter missing"}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except Exception as exc:
        return {"_error": str(exc)}


def target_slug(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = LINK_RE.search(value)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit ontology metadata in a tree wiki.")
    parser.add_argument("--wiki", default="wiki", help="Wiki directory")
    parser.add_argument("--entrypoints", default="", help="Optional comma-separated expected entrypoints")
    parser.add_argument("--edges-json", default="", help="Optional output JSON path")
    args = parser.parse_args()

    wiki = Path(args.wiki)
    page_paths = pages(wiki)
    slugs = {p.stem for p in page_paths}
    expected_entrypoints = {x.strip() for x in args.entrypoints.split(",") if x.strip()}
    issues: list[str] = []
    edges: list[dict] = []
    level_counts = Counter()
    relation_counts = Counter()
    entrypoints: list[str] = []

    for path in page_paths:
        rel = path.relative_to(wiki).as_posix()
        slug = path.stem
        fm = load(path)
        if "_error" in fm:
            issues.append(f"{rel}: {fm['_error']}")
            continue
        for field in ["ontology_level", "ontology_role", "entrypoint", "typed_relations"]:
            if field not in fm:
                issues.append(f"{rel}: missing {field}")
        level_counts[str(fm.get("ontology_level"))] += 1
        if fm.get("entrypoint"):
            entrypoints.append(slug)
        relations = fm.get("typed_relations")
        if not isinstance(relations, list):
            issues.append(f"{rel}: typed_relations must be a list")
            continue
        if path.parent.name != "areas":
            belongs = [r for r in relations if isinstance(r, dict) and r.get("type") == "belongs_to"]
            if len(belongs) != 1:
                issues.append(f"{rel}: must have exactly one belongs_to relation")
        for row in relations:
            if not isinstance(row, dict):
                issues.append(f"{rel}: relation row must be a mapping")
                continue
            rel_type = row.get("type")
            target = target_slug(row.get("target"))
            if rel_type not in ALLOWED_RELATIONS:
                issues.append(f"{rel}: disallowed relation type {rel_type}")
            if not target or target not in slugs:
                issues.append(f"{rel}: broken relation target {row.get('target')}")
                continue
            relation_counts[rel_type] += 1
            edges.append({"source": slug, "source_path": rel, "type": rel_type, "target": target})

    if expected_entrypoints and set(entrypoints) != expected_entrypoints:
        issues.append(f"entrypoints mismatch: expected {sorted(expected_entrypoints)}, got {sorted(entrypoints)}")
    for forbidden in [wiki / "index.md", wiki / "log.md"]:
        if forbidden.exists():
            issues.append(f"forbidden file exists: {forbidden.relative_to(wiki)}")

    if args.edges_json:
        Path(args.edges_json).write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"pages: {len(page_paths)}")
    print(f"typed_relations: {len(edges)}")
    print(f"entrypoints: {', '.join(sorted(entrypoints))}")
    print("levels:")
    for key, count in sorted(level_counts.items()):
        print(f"  {key}: {count}")
    print("relations:")
    for key, count in sorted(relation_counts.items()):
        print(f"  {key}: {count}")
    print(f"issues: {len(issues)}")
    for issue in issues:
        print(f"- {issue}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
