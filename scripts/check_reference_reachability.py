#!/usr/bin/env python3
"""Measure reference/template reachability and the public context budget.

This is the read-only verifier for context-cost governance. Future pipeline
integration may consume the JSON report as a reporting pass; only an explicit
--fail-on-orphan policy may turn orphaned files into exit 1. Input errors exit 2.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import json
from pathlib import Path
import re
from typing import Any


ROOT_FILES = (
    "SKILL.md",
    "references/command_registry.md",
    "references/intent_router.md",
    "references/pass_pipeline.md",
)
LINK_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:references|templates)/[A-Za-z0-9_./-]+|"
    r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)\.(md|json|ya?ml|csv|txt)",
    re.IGNORECASE,
)


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


def inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def referenced_paths(source: Path, root: Path, known: set[Path]) -> set[Path]:
    text = read_utf8(source)
    by_name: dict[str, list[Path]] = defaultdict(list)
    for path in known:
        by_name[path.name.casefold()].append(path)
    results: set[Path] = set()
    for match in LINK_RE.finditer(text):
        raw = (match.group(1) + "." + match.group(2)).replace("\\", "/")
        if raw.startswith(("references/", "templates/")):
            candidate = (root / raw).resolve()
            if candidate in known:
                results.add(candidate)
            continue
        sibling = (source.parent / raw).resolve()
        if sibling in known:
            results.add(sibling)
            continue
        matches = by_name.get(Path(raw).name.casefold(), [])
        if len(matches) == 1:
            results.add(matches[0])
    return results


def analyze(root: Path) -> dict[str, Any]:
    root = root.resolve()
    starts = [(root / value).resolve() for value in ROOT_FILES]
    for path in starts:
        if not path.is_file():
            raise UserError(f"required graph root is missing: {path.relative_to(root)}")
    targets = {
        path.resolve()
        for directory in (root / "references", root / "templates")
        if directory.is_dir()
        for path in directory.rglob("*")
        if path.is_file()
    }
    if not targets:
        raise UserError("references/ and templates/ contain no files")

    reachable: set[Path] = {path for path in starts if path in targets}
    parents: dict[Path, set[Path]] = defaultdict(set)
    queue: deque[Path] = deque(starts)
    scanned: set[Path] = set()
    while queue:
        source = queue.popleft()
        if source in scanned:
            continue
        scanned.add(source)
        for target in referenced_paths(source, root, targets):
            parents[target].add(source)
            if target not in reachable:
                reachable.add(target)
                queue.append(target)

    rows = []
    for path in sorted(targets, key=lambda item: item.relative_to(root).as_posix()):
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "reachable": path in reachable,
            "referenced_by": sorted(
                parent.relative_to(root).as_posix() for parent in parents.get(path, set())
            ),
        })
    orphaned = [row for row in rows if not row["reachable"]]
    total_bytes = sum(row["bytes"] for row in rows)
    orphan_bytes = sum(row["bytes"] for row in orphaned)
    return {
        "schema": "helicon-reference-reachability-v1",
        "roots": list(ROOT_FILES),
        "files": rows,
        "orphan_files": [{"path": row["path"], "bytes": row["bytes"]} for row in orphaned],
        "file_count": len(rows),
        "reachable_file_count": len(rows) - len(orphaned),
        "orphan_file_count": len(orphaned),
        "total_bytes": total_bytes,
        "orphan_bytes": orphan_bytes,
        "orphan_ratio_percent": round(100.0 * orphan_bytes / total_bytes, 4) if total_bytes else 0.0,
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--fail-on-orphan", action="store_true")
    try:
        args = parser.parse_args()
        result = analyze(Path(args.root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.fail_on_orphan and result["orphan_file_count"] else 0
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-reference-reachability-v1", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
