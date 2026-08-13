#!/usr/bin/env python3
"""Build a layered terminology glossary for the terminology-freeze check.

Future pass-pipeline contract: load the public L0 core, optionally overlay one
L1 direction and an L2 project Markdown glossary, then pass the emitted JSON to
check_terminology_freeze.py. Configuration errors exit 2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from check_terminology_freeze import UserError as GlossaryUserError
from check_terminology_freeze import load_glossary
from glossary_md_to_json import UserError as MarkdownUserError
from glossary_md_to_json import convert_markdown, write_json


SCHEMA = "helicon-glossary-build-v1"
LEXICON_SCHEMA = "helicon-lexicon-v1"


class UserError(Exception):
    """An invalid layer, direction, or output path."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


def source_label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_layer(path: Path, layer: str, direction: str | None) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UserError(f"lexicon not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"lexicon is not UTF-8: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise UserError(f"invalid lexicon JSON: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != LEXICON_SCHEMA:
        raise UserError(f"invalid lexicon schema: {path}")
    if payload.get("layer") != layer or payload.get("direction") != direction:
        raise UserError(f"lexicon layer metadata mismatch: {path}")
    entries, _ = load_glossary(path)
    return entries


def active_rules(entries: list[dict[str, Any]]) -> int:
    return sum(
        len(entry["forbidden_synonyms"]) + len(entry["forbidden_variants"])
        for entry in entries
    )


def build(root: Path, direction: str | None, project: Path | None) -> dict[str, Any]:
    root = root.resolve()
    core_path = root / "references" / "fhe_lexicon.json"
    core = load_layer(core_path, "L0", None)
    layers: list[tuple[str, Path, list[dict[str, Any]]]] = [("L0", core_path, core)]

    direction_entries: list[dict[str, Any]] = []
    if direction is not None:
        if not re.fullmatch(r"[a-z0-9_]+", direction):
            raise UserError("direction must contain only lowercase letters, digits, and underscores")
        direction_path = root / "references" / "direction_packs" / direction / "glossary.json"
        direction_entries = load_layer(direction_path, "L1", direction)
        layers.append(("L1", direction_path, direction_entries))

    project_entries: list[dict[str, Any]] = []
    if project is not None:
        project_payload = convert_markdown(project, direction)
        project_entries = project_payload["entries"]
        layers.append(("L2", project, project_entries))

    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    origins: dict[str, tuple[str, str]] = {}
    conflicts: list[dict[str, Any]] = []
    fields = ("abbreviation", "forbidden_synonyms", "forbidden_variants")
    for layer, source, entries in layers:
        label = source_label(source, root)
        for entry in entries:
            key = entry["term"].casefold()
            if key in merged:
                previous_layer, previous_file = origins[key]
                conflicts.append({
                    "term": entry["term"],
                    "overridden_layer": previous_layer,
                    "overridden_file": previous_file,
                    "overriding_layer": layer,
                    "overriding_file": label,
                    "overridden_fields": [name for name in fields if merged[key][name] != entry[name]],
                })
            else:
                order.append(key)
            merged[key] = entry
            origins[key] = (layer, label)

    entries = [merged[key] for key in order]
    return {
        "schema": SCHEMA,
        "direction": direction,
        "core_layer_entry_count": len(core),
        "direction_layer_entry_count": len(direction_entries),
        "project_layer": "present" if project is not None else "absent",
        "project_layer_entry_count": len(project_entries),
        "merged_entry_count": len(entries),
        "active_rule_count": active_rules(entries),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "entries": entries,
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--direction")
    parser.add_argument("--project", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help=argparse.SUPPRESS)
    try:
        args = parser.parse_args()
        payload = build(args.root, args.direction, args.project)
        write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except (
        UserError,
        GlossaryUserError,
        MarkdownUserError,
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(json.dumps({"schema": SCHEMA, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
