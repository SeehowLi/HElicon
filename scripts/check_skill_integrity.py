#!/usr/bin/env python3
"""Lightweight integrity check for the HElicon skill folder."""
from pathlib import Path
import sys

REQUIRED = [
    "SKILL.md",
    "references/operating_principles.md",
    "references/bilingual_policy.md",
    "references/bilingual_glossary.md",
    "references/venue_profiles.md",
    "references/fhe_domain_brief.md",
    "references/story_logic_framework.md",
    "references/abstract_title_framework.md",
    "references/technical_framing.md",
    "references/unified_paper_patterns.md",
    "references/paper_pattern_bank.md",
    "references/command_registry.md",
    "references/personal_style_profile.md",
    "references/mentor_memory.md",
    "references/review_gate.md",
    "templates/paper_brief.yaml",
    "templates/project_pack_template.md",
    "templates/direction_pack_template.md",
    "templates/evidence_map.csv",
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print("Missing required files:")
        for p in missing:
            print(f"- {p}")
        return 1
    skill = root / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    for token in ["name:", "description:", "HElicon"]:
        if token not in text:
            print(f"SKILL.md missing token: {token}")
            return 1
    print(f"HElicon integrity check passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
