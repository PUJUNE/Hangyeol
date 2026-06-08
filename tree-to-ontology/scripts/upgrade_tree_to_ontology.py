from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date
from pathlib import Path

ONTOLOGY_FIELDS = {"ontology_level", "ontology_role", "entrypoint", "typed_relations"}
ROLE_BY_TYPE = {
    "theme": ("0", "entrypoint-theme"),
    "concept": ("1", "core-concept"),
    "synthesis": ("1", "synthesis"),
    "entity": ("1", "entity"),
    "essay": ("2", "evidence-essay"),
    "source": ("2", "evidence-source"),
}
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    match = FM_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end() :]


def remove_fields(fm: str, fields: set[str]) -> str:
    lines = fm.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        match = re.match(r"^([A-Za-z_]+)\s*:", line)
        if match:
            field = match.group(1)
            if field in fields:
                skip = True
                continue
            skip = False
            out.append(line)
            continue
        if skip:
            if line.startswith((" ", "\t")) or line.lstrip().startswith("-"):
                continue
            skip = False
        out.append(line)
    return "\n".join(out).rstrip()


def scalar(fm: str, field: str) -> str | None:
    match = re.search(rf"^{field}\s*:\s*(.+?)\s*$", fm, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def wikilinks_in_field(fm: str, field: str) -> list[str]:
    match = re.search(rf"^{field}\s*:(.*?)(?=^\S|\Z)", fm + "\n", re.MULTILINE | re.DOTALL)
    if not match:
        return []
    return re.findall(r"\[\[([^\]]+)\]\]", match.group(1))


def relation_block(relations: list[tuple[str, str]]) -> str:
    if not relations:
        return "typed_relations: []"
    lines = ["typed_relations:"]
    for rel_type, target in relations:
        lines.append(f'  - type: "{rel_type}"')
        lines.append(f'    target: "[[{target}]]"')
    return "\n".join(lines)


def load_extra_relations(path: Path | None) -> dict[str, list[tuple[str, str]]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[tuple[str, str]]] = {}
    for row in data:
        source = row["source"]
        out.setdefault(source, []).append((row["type"], row["target"]))
    return out


def pages(wiki: Path) -> list[Path]:
    return [
        p
        for p in sorted(wiki.rglob("*.md"))
        if "lint-reports" not in p.parts and not any(part.startswith(".") for part in p.parts)
    ]


def backup_wiki(wiki: Path) -> Path:
    dst = wiki.parent / f"{wiki.name}_backup_{date.today().strftime('%y%m%d')}_pre_ontology"
    if not dst.exists():
        shutil.copytree(wiki, dst)
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Upgrade a tree wiki to an ontology-enhanced wiki.")
    parser.add_argument("--wiki", default="wiki", help="Wiki directory")
    parser.add_argument("--entrypoints", default="", help="Comma-separated entrypoint slugs")
    parser.add_argument("--relations-json", help="Optional JSON list of {source,type,target}")
    parser.add_argument("--no-backup", action="store_true", help="Skip wiki backup")
    args = parser.parse_args()

    wiki = Path(args.wiki)
    entrypoints = {x.strip() for x in args.entrypoints.split(",") if x.strip()}
    extra = load_extra_relations(Path(args.relations_json) if args.relations_json else None)
    page_paths = pages(wiki)
    slugs = {p.stem for p in page_paths}
    warnings: list[str] = []

    backup = None if args.no_backup else backup_wiki(wiki)
    changed = 0
    relation_count = 0
    axes = sorted(p.stem for p in (wiki / "areas").glob("*.md")) if (wiki / "areas").exists() else []
    root_map = next((a for a in axes if "지도" in a or "map" in a.lower()), axes[0] if axes else None)

    for path in page_paths:
        text = path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        if fm is None:
            warnings.append(f"{path.relative_to(wiki)}: frontmatter missing")
            continue
        clean = remove_fields(fm, ONTOLOGY_FIELDS)
        slug = path.stem
        page_type = scalar(clean, "type") or ""
        relations: list[tuple[str, str]] = []

        if path.parent.name == "areas":
            level = "structure"
            if slug == root_map:
                role = "tree-root"
                for axis in axes:
                    if axis != slug:
                        relations.append(("has_axis", axis))
            else:
                role = "tree-axis"
                if root_map:
                    relations.append(("part_of", root_map))
            entrypoint = "false"
        else:
            level, role = ROLE_BY_TYPE.get(page_type, ("2", "content-node"))
            entrypoint = "true" if slug in entrypoints else "false"
            axis_links = wikilinks_in_field(clean, "related_axes")
            if len(axis_links) == 1:
                relations.append(("belongs_to", axis_links[0]))
            else:
                warnings.append(f"{path.relative_to(wiki)}: related_axes count {len(axis_links)}")

        for rel_type, target in extra.get(slug, []):
            if target in slugs:
                relations.append((rel_type, target))
            else:
                warnings.append(f"{slug}: missing relation target {target}")

        block = "\n".join(
            [
                f'ontology_level: "{level}"',
                f'ontology_role: "{role}"',
                f"entrypoint: {entrypoint}",
                relation_block(relations),
            ]
        )
        new_text = f"---\n{clean}\n{block}\n---\n{body}"
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
        relation_count += len(relations)

    print(f"backup: {backup if backup else 'skipped'}")
    print(f"pages: {len(page_paths)}")
    print(f"changed: {changed}")
    print(f"typed_relations: {relation_count}")
    print(f"warnings: {len(warnings)}")
    for warning in warnings:
        print(f"- {warning}")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
