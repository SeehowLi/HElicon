#!/usr/bin/env python3
"""Compare the repository install payload with an explicitly named installed skill."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil


SOURCE_EXCLUSIONS = {".git", ".agents", ".helicon", "__pycache__", "evals", "handoff"}


def parse_python_exclusions(text: str) -> frozenset[str]:
    """Statically read SOURCE_EXCLUSIONS without executing its module."""
    tree = ast.parse(text)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "SOURCE_EXCLUSIONS" for target in targets):
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, (set, frozenset)) or not all(isinstance(item, str) for item in value):
            break
        return frozenset(value)
    raise ValueError("cannot parse Python SOURCE_EXCLUSIONS")


def parse_powershell_exclusions(text: str) -> frozenset[str]:
    """Statically read the top-level exclusion list used by install.ps1."""
    match = re.search(
        r'Where-Object\s*\{[^\r\n]*-notin\s+@\((?P<items>[^)]*)\)',
        text,
    )
    if match is None:
        raise ValueError("cannot parse install.ps1 exclusion list")
    items = re.findall(r'"([^"\r\n]+)"', match.group("items"))
    if not items:
        raise ValueError("install.ps1 exclusion list is empty")
    return frozenset(items)


def parse_shell_exclusions(text: str) -> frozenset[str]:
    """Statically read the top-level exclusion list used by install.sh."""
    match = re.search(
        r"(?m)^\s*(?P<items>[._A-Za-z0-9-]+(?:\|[._A-Za-z0-9-]+)+)\)\s+continue\s+;;\s*$",
        text,
    )
    if match is None:
        raise ValueError("cannot parse install.sh exclusion list")
    return frozenset(match.group("items").split("|"))


def validate_installer_exclusions(
    powershell_text: str,
    shell_text: str,
    source_exclusions: frozenset[str] | set[str] = SOURCE_EXCLUSIONS,
) -> dict[str, frozenset[str]]:
    """Fail closed unless both installers match the shared payload exclusions."""
    observed = {
        "source": frozenset(source_exclusions),
        "powershell": parse_powershell_exclusions(powershell_text),
        "shell": parse_shell_exclusions(shell_text),
    }
    if observed["powershell"] != observed["source"]:
        raise ValueError("install.ps1 exclusions differ from SOURCE_EXCLUSIONS")
    if observed["shell"] != observed["source"]:
        raise ValueError("install.sh exclusions differ from SOURCE_EXCLUSIONS")
    return observed


def copy_source_payload(source: Path, destination: Path) -> None:
    """Copy exactly the repository payload shape used by both installers."""
    source = source.resolve()
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")

    def ignored(directory: str, names: list[str]) -> set[str]:
        directory_path = Path(directory).resolve()
        excluded = {
            name
            for name in names
            if name == "__pycache__" or name.lower().endswith(".pyc")
        }
        if directory_path == source:
            excluded.update(name for name in names if name in SOURCE_EXCLUSIONS)
        return excluded

    shutil.copytree(source, destination, ignore=ignored)


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
