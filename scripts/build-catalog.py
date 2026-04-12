#!/usr/bin/env python3
"""
Build catalog.json from the repo's bundled skills.

Scans for SKILL.md files under skills/, extracts frontmatter metadata,
and writes catalog.json.

Usage:
    python scripts/build-catalog.py
    python scripts/build-catalog.py --output catalog.json
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "catalog.json"
SKILLS_DIR = REPO_ROOT / "skills"


def parse_frontmatter(skill_md_path: Path) -> dict:
    """Extract YAML-like frontmatter from a SKILL.md file."""
    text = skill_md_path.read_text(encoding="utf-8")

    # Match frontmatter between --- delimiters (also supports ```skill blocks)
    # Pattern 1: standard YAML frontmatter
    fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        # Pattern 2: ```skill block frontmatter
        fm_match = re.search(r"```skill\s*\n---\s*\n(.*?)\n---", text, re.DOTALL)

    if not fm_match:
        return {}

    frontmatter = {}
    for line in fm_match.group(1).strip().splitlines():
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip("'\"")
            if value:
                frontmatter[key] = value

    return frontmatter


def find_skills_in_dir(base_dir: Path) -> list[tuple[Path, Path]]:
    """Find all SKILL.md files under a directory. Returns (skill_md_path, skill_dir)."""
    results = []
    if not base_dir.exists():
        return results
    for skill_md in sorted(base_dir.rglob("SKILL.md")):
        results.append((skill_md, skill_md.parent))
    return results


def has_assets(skill_dir: Path) -> bool:
    """Check if a skill directory has non-SKILL.md files (assets, templates, scripts)."""
    for item in skill_dir.iterdir():
        if item.name != "SKILL.md" and item.name != "LICENSE.txt":
            return True
    return False


def build_catalog(output_path: Path = DEFAULT_OUTPUT) -> dict:
    """Scan the repo skills directory and build the catalog."""
    skills = []
    seen_names = {}

    for skill_md, skill_dir in find_skills_in_dir(SKILLS_DIR):
        fm = parse_frontmatter(skill_md)
        name = fm.get("name", skill_dir.name)
        description = fm.get("description", "")
        license_info = fm.get("license", "")

        rel_path = str(skill_dir.relative_to(REPO_ROOT))

        skill_entry = {
            "name": name,
            "description": description,
            "source": "agent-skills-hub",
            "source_type": "repo",
            "path": rel_path,
            "has_assets": has_assets(skill_dir),
        }
        if license_info:
            skill_entry["license"] = license_info

        if name in seen_names:
            seen_names[name].append(rel_path)
            skill_entry["duplicate_of"] = seen_names[name][0]
        else:
            seen_names[name] = [rel_path]

        skills.append(skill_entry)

    skills.sort(key=lambda s: s["name"])

    catalog = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": len(skills),
        "sources": {"repo": len(skills)},
        "duplicates": [
            {"name": name, "found_in": sources}
            for name, sources in seen_names.items()
            if len(sources) > 1
        ],
        "skills": skills,
    }

    output_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return catalog


def print_summary(catalog: dict) -> None:
    """Print a human-readable summary."""
    print(f"✅ Catalog built: {catalog['total_skills']} skills total")
    print(f"   Repo:        {catalog['sources']['repo']}")
    if catalog["duplicates"]:
        print(f"\n⚠️  Duplicates detected ({len(catalog['duplicates'])}):")
        for dup in catalog["duplicates"]:
            print(f"   - '{dup['name']}' found in: {', '.join(dup['found_in'])}")
    print(f"\n📄 Written to: {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    catalog = build_catalog(output)
    print_summary(catalog)
