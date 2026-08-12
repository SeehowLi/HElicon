#!/usr/bin/env python3
"""Compare the repository install payload with an explicitly named installed skill."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_EXCLUSIONS = {".git", ".agents", ".helicon", "__pycache__", "evals", "handoff"}


def canonical_bytes(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def inventory(root: Path, source_payload: bool) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if source_payload and relative.parts[0] in SOURCE_EXCLUSIONS:
            continue
        if "__pycache__" in relative.parts or path.suffix.lower() == ".pyc":
            continue
        result[relative.as_posix()] = hashlib.sha256(canonical_bytes(path)).hexdigest()
    return result


def manifest(files: dict[str, str]) -> str:
    payload = "".join(f"{digest}  {relative}\n" for relative, digest in sorted(files.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compare(source: Path, installed: Path) -> dict:
    source_files = inventory(source, source_payload=True)
    installed_files = inventory(installed, source_payload=False)
    return {
        "source_manifest_sha256": manifest(source_files),
        "installed_manifest_sha256": manifest(installed_files),
        "source_file_count": len(source_files),
        "installed_file_count": len(installed_files),
        "source_only": sorted(set(source_files) - set(installed_files)),
        "installed_only": sorted(set(installed_files) - set(source_files)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installed_skill", nargs="?", type=Path)
    args = parser.parse_args()
    if args.installed_skill is None:
        print(json.dumps({"status": "not-executed"}, sort_keys=True))
        return 0
    installed = args.installed_skill.resolve()
    if not installed.is_dir():
        print(json.dumps({"status": "error"}, sort_keys=True))
        return 2
    source = Path(__file__).resolve().parents[1]
    try:
        result = compare(source, installed)
    except (OSError, UnicodeError):
        print(json.dumps({"status": "error"}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if (
        result["source_manifest_sha256"] == result["installed_manifest_sha256"]
        and not result["source_only"]
        and not result["installed_only"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
