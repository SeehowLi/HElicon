#!/usr/bin/env python3
"""Validate the HElicon skill package and progressive-disclosure routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

MAX_BODY_LINES = 500
MAX_DESCRIPTION_CHARS = 1024
REQUIRED = (
    "SKILL.md",
    "README.md",
    "VERSION.md",
    "CHANGELOG.md",
    "INSTALL_AND_WORKFLOW.md",
    "agents/openai.yaml",
    "references/operating_principles.md",
    "references/bilingual_policy.md",
    "references/bilingual_glossary.md",
    "references/venue_profiles.md",
    "references/fhe_domain_brief.md",
    "references/story_logic_framework.md",
    "references/abstract_title_framework.md",
    "references/technical_framing.md",
    "references/contribution_patterns.md",
    "references/unified_paper_patterns.md",
    "references/paper_pattern_bank.md",
    "references/direction_knowledge_map.md",
    "references/command_registry.md",
    "references/personal_style_profile.md",
    "references/mentor_memory.md",
    "references/review_gate.md",
    "references/pass_pipeline.md",
    "references/draft_intake.md",
    "references/language_polish.md",
    "references/fhe_lexicon_freeze.md",
    "references/citation_discipline.md",
    "references/deadline_compression.md",
    "references/style_baseline_policy.md",
    "references/rebuttal_playbook.md",
    "references/intent_router.md",
    "references/project_memory.md",
    "references/external_advisor_protocol.md",
    "templates/paper_brief.yaml",
    "templates/project_pack_template.md",
    "templates/direction_pack_template.md",
    "templates/project_first_use_prompt.md",
    "templates/evidence_map.csv",
    "templates/claim_ledger.md",
    "templates/evidence_matrix.csv",
    "templates/revision_queue.csv",
    "templates/reviewer_risk_log.md",
    "templates/draft_map.md",
    "templates/pass_log.md",
    "templates/polish_ledger.csv",
    "templates/rebuttal_response.md",
    "templates/style_baseline_readme.md",
    "templates/advisor_brief.md",
    "templates/submission_gate_checklist.md",
    "scripts/check_skill_integrity.py",
    "scripts/check_core_contamination.py",
    "scripts/selftest_checks.py",
    "scripts/style_fingerprint.py",
    "scripts/latex_guard.py",
    "scripts/check_ai_tells.py",
    "scripts/export_dossier.py",
    "scripts/bootstrap_project_pack.py",
    "scripts/install.sh",
    "scripts/install.ps1",
    "scripts/extract_pdf_text.py",
    "scripts/collect_fhe_papers.py",
    "scripts/generate_distilled_bibtex.py",
    "provenance/distilled_sources.bib",
    "provenance/external_influences.md",
)
REFERENCE_RE = re.compile(r"(?:references|templates)/[A-Za-z0-9_./-]+\.(?:md|csv|ya?ml)")


class UserError(Exception):
    """A concise command-line error."""


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path} ({exc})") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def skill_limits(text: str) -> tuple[int, int]:
    lines = text.splitlines()
    delimiters = [index for index, line in enumerate(lines) if line == "---"]
    if len(delimiters) < 2 or delimiters[0] != 0:
        raise UserError("SKILL.md has invalid YAML frontmatter delimiters")
    frontmatter = lines[1:delimiters[1]]
    description_lines = [line for line in frontmatter if line.startswith("description:")]
    if len(description_lines) != 1:
        raise UserError("SKILL.md must contain exactly one single-line description")
    description = description_lines[0].split(":", 1)[1].strip()
    if not any(line.startswith("name:") for line in frontmatter):
        raise UserError("SKILL.md frontmatter is missing name")
    body_lines = len(lines) - delimiters[1] - 1
    return len(description), body_lines


def validate(root: Path) -> dict[str, Any]:
    if not root.exists() or not root.is_dir():
        raise UserError(f"skill root does not exist: {root}")
    errors: list[str] = []
    missing = [relative for relative in REQUIRED if not (root / relative).is_file()]
    errors.extend(f"missing required file: {relative}" for relative in missing)
    if missing and "SKILL.md" in missing:
        return {"root": str(root), "passed": False, "errors": errors}

    skill_text = read_utf8(root / "SKILL.md")
    description_chars, body_lines = skill_limits(skill_text)
    if description_chars > MAX_DESCRIPTION_CHARS:
        errors.append(f"SKILL.md description has {description_chars} characters; limit is {MAX_DESCRIPTION_CHARS}")
    if body_lines > MAX_BODY_LINES:
        errors.append(f"SKILL.md body has {body_lines} lines; limit is {MAX_BODY_LINES}")

    registry_path = root / "references/command_registry.md"
    registry_text = read_utf8(registry_path) if registry_path.exists() else ""
    routing_text = skill_text + "\n" + registry_text

    referenced_missing: list[str] = []
    for match in sorted(set(REFERENCE_RE.findall(routing_text))):
        if not (root / match).is_file():
            referenced_missing.append(match)
            errors.append(f"routed file does not exist: {match}")

    orphans: list[str] = []
    direction_indexed = "references/direction_knowledge_map.md" in routing_text or "direction_knowledge_map.md" in routing_text
    for path in sorted((root / "references").rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("references/direction_packs/") and direction_indexed:
            continue
        if relative not in routing_text and path.name not in routing_text:
            orphans.append(relative)
            errors.append(f"orphan reference not routed by SKILL.md or command_registry.md: {relative}")

    return {
        "root": str(root),
        "passed": not errors,
        "description_chars": description_chars,
        "body_lines": body_lines,
        "limits": {"description_chars": MAX_DESCRIPTION_CHARS, "body_lines": MAX_BODY_LINES},
        "missing_required": missing,
        "referenced_missing": referenced_missing,
        "orphan_references": orphans,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="skill repository root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        result = validate(Path(args.root))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["passed"]:
            print(
                f"HElicon integrity check passed: {args.root} "
                f"(body={result['body_lines']}/{MAX_BODY_LINES}, "
                f"description={result['description_chars']}/{MAX_DESCRIPTION_CHARS})"
            )
        else:
            print("HElicon integrity check failed:")
            for error in result["errors"]:
                print(f"- {error}")
        return 0 if result["passed"] else 1
    except UserError as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
