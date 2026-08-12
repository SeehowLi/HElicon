#!/usr/bin/env python3
"""Report H-* command coverage across public routing contracts and eval cases.

This is a read-only command-surface verifier. Future pass-pipeline integration
may consume its JSON matrix as a release report; by default gaps are reported
without blocking, while --fail-on-gap makes them exit 1. Invalid inputs exit 2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


COMMAND_RE = re.compile(r"\bH-[A-Z][A-Z0-9-]*\b")
DOCUMENTS = {
    "skill": "SKILL.md",
    "command_registry": "references/command_registry.md",
    "intent_router": "references/intent_router.md",
}


class UserError(Exception):
    """An invalid or unreadable repository root."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UserError(f"required file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def analyze(root: Path) -> dict[str, Any]:
    root = root.resolve()
    texts = {name: read_utf8(root / relative) for name, relative in DOCUMENTS.items()}
    case_paths = sorted((root / "evals" / "cases").glob("*.json"))
    if not case_paths:
        raise UserError("evals/cases contains no JSON cases")
    eval_texts = {path.relative_to(root).as_posix(): read_utf8(path) for path in case_paths}
    commands = sorted(set().union(*(set(COMMAND_RE.findall(text)) for text in texts.values())))
    matrix = []
    gaps = []
    for command in commands:
        row = {
            "command": command,
            "SKILL.md": command in texts["skill"],
            "command_registry.md": command in texts["command_registry"],
            "intent_router.md": command in texts["intent_router"],
            "eval_case": any(command in text for text in eval_texts.values()),
        }
        missing = [key for key in ("SKILL.md", "command_registry.md", "intent_router.md", "eval_case") if not row[key]]
        matrix.append(row)
        if missing:
            gaps.append({"command": command, "missing": missing})
    return {
        "schema": "helicon-command-coverage-v1",
        "columns": ["SKILL.md", "command_registry.md", "intent_router.md", "eval_case"],
        "matrix": matrix,
        "command_count": len(matrix),
        "gap_count": len(gaps),
        "gaps": gaps,
        "eval_case_files": sorted(eval_texts),
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--fail-on-gap", action="store_true")
    try:
        args = parser.parse_args()
        result = analyze(Path(args.root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.fail_on_gap and result["gap_count"] else 0
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-command-coverage-v1", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
