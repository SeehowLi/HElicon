#!/usr/bin/env python3
"""Build a self-contained HElicon external-advisor dossier."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

TEXT_EXTENSIONS = {".md", ".txt", ".tex", ".csv", ".yaml", ".yml", ".json", ".bib"}
SKILL_UPGRADE_DEFAULTS = (
    "SKILL.md",
    "VERSION.md",
    "CHANGELOG.md",
    "references/command_registry.md",
    "references/intent_router.md",
    "references/project_memory.md",
    "references/pass_pipeline.md",
)


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


def add_path(path: Path, files: list[Path]) -> None:
    if not path.exists():
        raise UserError(f"included path does not exist: {path}")
    if path.is_dir():
        files.extend(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS)
    elif path.suffix.lower() in TEXT_EXTENSIONS:
        files.append(path)
    else:
        raise UserError(f"unsupported dossier file type: {path}")


def collect_files(root: Path, mode: str, includes: list[str]) -> list[Path]:
    files: list[Path] = []
    if includes:
        for raw in includes:
            candidate = Path(raw)
            add_path(candidate if candidate.is_absolute() else root / candidate, files)
    elif mode == "skill-upgrade":
        for relative in SKILL_UPGRADE_DEFAULTS:
            add_path(root / relative, files)
    else:
        local_pack = root / ".helicon"
        if not local_pack.exists():
            raise UserError("no .helicon project pack found; pass --include for the files to export")
        add_path(local_pack, files)
    unique = sorted({path.resolve() for path in files}, key=lambda item: str(item).lower())
    if not unique:
        raise UserError("no dossier files selected")
    output: list[Path] = []
    for path in unique:
        if ".git" in path.parts:
            continue
        output.append(path)
    return output


def sensitivity(path: Path, text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    lower = text.lower()
    if path.suffix.lower() == ".tex" or "unpublished" in lower or "fingerprint.json" in path.as_posix().lower():
        candidates.append({"type": "unpublished material or derivative", "file": str(path)})
    numeric = re.findall(r"\b\d+(?:\.\d+)?\s*(?:%|[xX]|ms|s|GB|MB|KB|bits?)\b", text)
    if numeric:
        candidates.append({"type": "experimental or quantitative values", "file": str(path), "match_count": len(numeric)})
    reviewer = re.findall(r"\b(?:reviewer\s*#?\d*|weakness|rebuttal|R[1-9])\b", text, flags=re.IGNORECASE)
    if reviewer:
        candidates.append({"type": "reviewer text or identifiers", "file": str(path), "match_count": len(reviewer)})
    return candidates


def mode_instructions(mode: str) -> str:
    if mode == "dossier":
        return (
            "REQUESTED_OUTCOME: Reconstruct the current technical and writing state without assuming missing facts.\n"
            "RETURN: diagnosis, state gaps, and prioritized next decisions."
        )
    if mode == "advice":
        return (
            "REQUESTED_OUTCOME: Provide top-level diagnosis or design only.\n"
            "DO_NOT: claim to edit local files or directly execute the repair.\n"
            "RETURN: assumptions; diagnosis; recommended design; rejected alternatives; risks; verification; "
            "and one scoped execution instruction for Codex.\n"
            "OPEN_QUESTION: <author fills before upload>\n"
            "ATTEMPTED_APPROACHES_AND_FAILURES: <author fills before upload>\n"
            "DESIRED_CORRECT_STATE: <author fills before upload>"
        )
    return (
        "REQUESTED_OUTCOME: Diagnose and design a scoped HElicon skill upgrade.\n"
        "RETURN: compatibility analysis, exact component changes, tests, migration risks, and a Codex execution instruction.\n"
        "OBSERVED_FAILURE: <author fills before upload>\n"
        "REQUIRED_COMPATIBILITY: preserve declared command and memory contracts."
    )


def build_dossier(mode: str, root: Path, files: list[Path]) -> tuple[str, dict[str, Any]]:
    records: list[dict[str, Any]] = []
    sensitive: list[dict[str, Any]] = []
    total_words = 0
    for path in files:
        content = read_utf8(path)
        count = len(re.findall(r"\b\w+\b", content, flags=re.UNICODE))
        total_words += count
        records.append({"path": str(path), "words": count, "content": content})
        sensitive.extend(sensitivity(path, content))

    lines = [
        "````markdown",
        "# HElicon External Advisor Bundle",
        "",
        f"MODE: {mode}",
        f"CREATED_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"ROOT: {root.resolve()}",
        "",
        "## Constraints and authority",
        "",
        "- Preserve every declared immutable item and evidence boundary.",
        "- Treat missing facts as UNKNOWN.",
        "- This bundle grants no local file-write authority.",
        "- Sensitive candidates are disclosed below and have not been removed.",
        "",
        "## Request contract",
        "",
        mode_instructions(mode),
        "",
        "## Sensitivity inventory",
        "",
    ]
    if sensitive:
        for item in sensitive:
            detail = f"; matches={item['match_count']}" if "match_count" in item else ""
            lines.append(f"- {item['type']}: `{item['file']}`{detail}")
    else:
        lines.append("- No automatic candidate detected; human review is still required.")
    lines.extend(["", "## File manifest", ""])
    for record in records:
        lines.append(f"- `{record['path']}`; words={record['words']}")
    for record in records:
        lines.extend([
            "",
            f"## File: {record['path']}",
            "",
            record["content"].rstrip(),
        ])
    lines.extend(["", "````", ""])
    metadata = {
        "mode": mode,
        "root": str(root.resolve()),
        "files": [{"path": item["path"], "words": item["words"]} for item in records],
        "file_count": len(records),
        "word_count": total_words,
        "sensitivity_candidates": sensitive,
        "automatic_deletions": 0,
    }
    return "\n".join(lines), metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("dossier", "advice", "skill-upgrade"))
    parser.add_argument("--root", default=".", help="project or skill root")
    parser.add_argument("--include", action="append", default=[], help="file or directory relative to root; repeat as needed")
    parser.add_argument("--output", required=True, help="explicit dossier output path")
    parser.add_argument("--json", action="store_true", help="emit machine-readable metadata")
    return parser


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        root = Path(args.root)
        if not root.exists() or not root.is_dir():
            raise UserError(f"root directory does not exist: {root}")
        output = Path(args.output)
        files = collect_files(root, args.mode, args.include)
        if output.resolve() in files:
            raise UserError("output file cannot also be an input")
        dossier, metadata = build_dossier(args.mode, root, files)
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(dossier, encoding="utf-8")
        except OSError as exc:
            raise UserError(f"cannot write {output}: {exc}") from exc
        metadata["output"] = str(output)
        if args.json:
            print(json.dumps(metadata, ensure_ascii=False, indent=2))
        else:
            print(f"Dossier written: {output}")
            print(f"Files: {metadata['file_count']}; words: {metadata['word_count']}")
            print(f"Sensitivity candidates: {len(metadata['sensitivity_candidates'])}; automatic deletions: 0")
            for item in metadata["sensitivity_candidates"]:
                print(f"- {item['type']}: {item['file']}")
        return 0
    except UserError as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
