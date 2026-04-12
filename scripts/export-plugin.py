#!/usr/bin/env python3
"""
Generate the repo-local plugin manifest and marketplace entry.

This keeps the plugin metadata in sync with the current repo structure while
continuing to use skills/ as the single source of truth.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "z2h-custom"
PLUGIN_DIR = REPO_ROOT / "plugins" / PLUGIN_NAME
PLUGIN_MANIFEST = PLUGIN_DIR / ".codex-plugin" / "plugin.json"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

PLUGIN_JSON = {
    "name": PLUGIN_NAME,
    "version": "0.1.0",
    "description": "Custom installable skills from z2h.",
    "author": {
        "name": "z2h",
        "url": "https://github.com/yiliu30/z2h",
    },
    "homepage": "https://github.com/yiliu30/z2h",
    "repository": "https://github.com/yiliu30/z2h",
    "license": "MIT",
    "keywords": ["skills", "agents", "codex", "claude-code"],
    "skills": "./../../../skills",
    "interface": {
        "displayName": "z2h (Zero to Hero)",
        "shortDescription": "Custom skills bundled from this repo.",
        "longDescription": "Installs the custom skills published in z2h.",
        "developerName": "z2h",
        "category": "Productivity",
        "capabilities": ["Write"],
        "websiteURL": "https://github.com/yiliu30/z2h",
        "brandColor": "#2563EB",
        "defaultPrompt": [
            "Install the custom skills from this repo.",
            "List the skills bundled in this plugin.",
            "Add one of these skills to my local setup.",
        ],
    },
}

MARKETPLACE_JSON = {
    "name": "z2h",
    "interface": {"displayName": "z2h (Zero to Hero)"},
    "plugins": [
        {
            "name": PLUGIN_NAME,
            "source": {
                "source": "local",
                "path": f"../../plugins/{PLUGIN_NAME}",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
    ],
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    write_json(PLUGIN_MANIFEST, PLUGIN_JSON)
    write_json(MARKETPLACE_PATH, MARKETPLACE_JSON)
    print(f"✅ Wrote {PLUGIN_MANIFEST.relative_to(REPO_ROOT)}")
    print(f"✅ Wrote {MARKETPLACE_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
