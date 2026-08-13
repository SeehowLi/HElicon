#!/usr/bin/env python3
"""Convert an L2 Markdown glossary table to helicon-lexicon-v1 JSON.

This is the project-layer adapter for the terminology-freeze contract. Future
pass-pipeline integration may call ``convert_markdown`` before glossary_build;
empty Avoid rows are reported and skipped, while malformed input exits 2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA = "helicon-lexicon-v1"
LAYOUT_TERM = ("term", "preferred english", "avoid", "notes")
LAYOUT_BILINGUAL = (
    "chinese", "recommended english", "acceptable alternatives", "avoid", "notes"
)


class UserError(Exception):
    """An invalid Markdown glossary or output path."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


def split_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise UserError("glossary table rows must start and end with a pipe")
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def variants(term: str) -> list[str]:
    derived: list[str] = []
    if "-" in term:
        derived.append(re.sub(r"\s+", " ", term.replace("-", " ")).strip())
    if " " in term:
        derived.append(re.sub(r"\s+", "-", term.strip()))
    return unique([item for item in derived if item != term])


def convert_markdown(path: Path, direction: str | None = None) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"Markdown glossary not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"Markdown glossary is not UTF-8: {path}") from exc
    except OSError as exc:
        raise UserError(f"cannot read Markdown glossary: {path}") from exc

    lines = text.splitlines()
    header_index = -1
    layout: tuple[str, ...] | None = None
    for index, line in enumerate(lines[:-1]):
        if not line.strip().startswith("|"):
            continue
        cells = tuple(cell.casefold() for cell in split_row(line))
        if cells not in (LAYOUT_TERM, LAYOUT_BILINGUAL):
            continue
        separator = split_row(lines[index + 1])
        if len(separator) != len(cells) or not is_separator(separator):
            raise UserError(f"invalid Markdown table separator at line {index + 2}")
        header_index = index
        layout = cells
        break
    if layout is None:
        raise UserError("no supported glossary table header found")

    term_index = 0 if layout == LAYOUT_TERM else layout.index("recommended english")
    avoid_index = layout.index("avoid")
    entries: list[dict[str, Any]] = []
    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.strip().startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != len(layout):
            raise UserError(f"wrong column count at line {index + 1}")
        term = cells[term_index].strip()
        if not term:
            raise UserError(f"empty term at line {index + 1}")
        avoid = cells[avoid_index].strip()
        if not avoid:
            print(f"skipped line {index + 1}: empty Avoid for {term}", file=sys.stderr)
            continue
        synonyms = unique(
            [item.strip() for item in re.split(r"[;,；，]", avoid) if item.strip()]
        )
        entries.append({
            "term": term,
            "abbreviation": None,
            "forbidden_synonyms": synonyms,
            "forbidden_variants": variants(term),
        })
    if not entries:
        raise UserError("glossary table produced no active entries")
    return {"schema": SCHEMA, "layer": "L2", "direction": direction, "entries": entries}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except OSError as exc:
        raise UserError(f"cannot write JSON output: {path}") from exc


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    try:
        args = parser.parse_args()
        payload = convert_markdown(args.markdown)
        write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": SCHEMA, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
