#!/usr/bin/env python3
"""Set the direction field in one existing HElicon project.yaml.

Only project.yaml is read or written. A non-null direction requires --force
before replacement; all other bytes and fields are preserved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from bootstrap_project_pack import available_directions


class UserError(Exception):
    """A concise command-line error."""


def direction_value(line: str) -> str | None:
    raw = line.split(":", 1)[1].strip()
    if raw in {"", "null", "~"}:
        return None
    if re.fullmatch(r"[a-z0-9_]+", raw):
        return raw
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UserError("project.yaml has an invalid top-level direction value") from exc
    if not isinstance(value, str):
        raise UserError("project.yaml direction must be a string or null")
    return value


def update_project_yaml(path: Path, direction: str, force: bool) -> str | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise UserError(f"project.yaml not found: {path}") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise UserError("project.yaml must be UTF-8 without BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UserError(f"project.yaml is not valid UTF-8: {path}") from exc

    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if re.match(r"^direction\s*:", line)]
    if len(matches) > 1:
        raise UserError("project.yaml contains multiple top-level direction fields")
    old = direction_value(lines[matches[0]]) if matches else None
    print(f"Previous direction: {json.dumps(old, ensure_ascii=False)}")
    if old is not None and not force:
        raise UserError("refusing to overwrite a non-null direction without --force")

    if matches:
        index = matches[0]
        ending_match = re.search(r"(\r\n|\r|\n)$", lines[index])
        ending = ending_match.group(1) if ending_match else ""
        lines[index] = f"direction: {json.dumps(direction, ensure_ascii=False)}{ending}"
    else:
        fingerprint = [index for index, line in enumerate(lines) if re.match(r"^fingerprint\s*:\s*(?:#.*)?(?:\r\n|\r|\n)?$", line)]
        if len(fingerprint) != 1:
            raise UserError("project.yaml must contain one top-level fingerprint field")
        index = fingerprint[0]
        ending_match = re.search(r"(\r\n|\r|\n)$", lines[index])
        ending = ending_match.group(1) if ending_match else "\n"
        lines.insert(index, f"direction: {json.dumps(direction, ensure_ascii=False)}{ending}")

    try:
        path.write_bytes("".join(lines).encode("utf-8"))
    except OSError as exc:
        raise UserError(f"cannot write {path}: {exc}") from exc
    return old


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_pack", help="project pack directory containing project.yaml")
    parser.add_argument("--direction", required=True, choices=available_directions())
    parser.add_argument("--force", action="store_true", help="replace an existing non-null direction")
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        project_yaml = Path(args.project_pack) / "project.yaml"
        update_project_yaml(project_yaml, args.direction, args.force)
        print(f"Direction set to: {args.direction}")
        return 0
    except UserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
