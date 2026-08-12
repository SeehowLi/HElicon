#!/usr/bin/env python3
"""Enforce Iron Rule 2 and P3 terminology freeze on a proposed revision.

Future pass-pipeline contract: call with BEFORE, AFTER, and a JSON glossary;
accept only exit 0. Exit 1 reports mechanically observed substitutions or form
drift, while exit 2 reports an invalid input or glossary.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any


SUPPORTED = {".md", ".tex", ".txt"}


class UserError(Exception):
    """A deterministic input or glossary error."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


@dataclass
class Replacement:
    term: str
    kind: str
    observed: str
    position: dict[str, int]


def read_text(path: Path) -> str:
    if path.suffix.lower() not in SUPPORTED:
        raise UserError(f"unsupported text file: {path}")
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def load_glossary(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UserError(f"glossary not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"glossary is not UTF-8: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise UserError(f"invalid glossary JSON: {path}") from exc
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not entries:
        raise UserError("glossary requires a non-empty entries array")
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("term"), str) or not entry["term"].strip():
            raise UserError(f"glossary entry {index} requires a non-empty term")
        abbreviation = entry.get("abbreviation")
        if abbreviation is not None and (not isinstance(abbreviation, str) or not abbreviation.strip()):
            raise UserError(f"glossary entry {index} has an invalid abbreviation")
        synonyms = entry.get("forbidden_synonyms", [])
        variants = entry.get("forbidden_variants", [])
        if not isinstance(synonyms, list) or not all(isinstance(item, str) and item.strip() for item in synonyms):
            raise UserError(f"glossary entry {index} has invalid forbidden_synonyms")
        if not isinstance(variants, list) or not all(isinstance(item, str) and item.strip() for item in variants):
            raise UserError(f"glossary entry {index} has invalid forbidden_variants")
        normalized.append({
            "term": entry["term"].strip(),
            "abbreviation": abbreviation.strip() if isinstance(abbreviation, str) else None,
            "forbidden_synonyms": [item.strip() for item in synonyms],
            "forbidden_variants": [item.strip() for item in variants],
        })
    return normalized


def matches(text: str, value: str, *, ignore_case: bool = True) -> list[re.Match[str]]:
    flags = re.IGNORECASE if ignore_case else 0
    return list(re.finditer(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", text, flags))


def location(text: str, offset: int) -> dict[str, int]:
    prior = text.rfind("\n", 0, offset)
    return {
        "offset": offset,
        "line": text.count("\n", 0, offset) + 1,
        "column": offset + 1 if prior < 0 else offset - prior,
    }


def added_matches(before: str, after: str, value: str) -> list[re.Match[str]]:
    before_count = len(matches(before, value))
    return matches(after, value)[before_count:]


def compare(before_path: Path, after_path: Path, glossary_path: Path) -> dict[str, Any]:
    before = read_text(before_path)
    after = read_text(after_path)
    entries = load_glossary(glossary_path)
    replacements: list[Replacement] = []
    for entry in entries:
        term = entry["term"]
        for synonym in entry["forbidden_synonyms"]:
            replacements.extend(
                Replacement(term, "forbidden_synonym", match.group(0), location(after, match.start()))
                for match in added_matches(before, after, synonym)
            )
        for variant in entry["forbidden_variants"]:
            replacements.extend(
                Replacement(term, "plural_or_hyphen_variant", match.group(0), location(after, match.start()))
                for match in added_matches(before, after, variant)
            )

        for match in matches(after, term):
            if match.group(0) != term:
                replacements.append(Replacement(term, "case_inconsistency", match.group(0), location(after, match.start())))

        abbreviation = entry["abbreviation"]
        if abbreviation:
            before_full = bool(matches(before, term))
            before_short = bool(matches(before, abbreviation, ignore_case=False))
            after_full = bool(matches(after, term))
            after_short_matches = matches(after, abbreviation, ignore_case=False)
            if before_full and not before_short and after_short_matches:
                replacements.extend(
                    Replacement(term, "abbreviation_full_name_mix", match.group(0), location(after, match.start()))
                    for match in after_short_matches
                )
            elif before_short and not before_full and after_full:
                replacements.extend(
                    Replacement(term, "abbreviation_full_name_mix", match.group(0), location(after, match.start()))
                    for match in matches(after, term)
                )

    unique = {
        (item.term, item.kind, item.observed, item.position["offset"]): item
        for item in replacements
    }
    payload = [asdict(unique[key]) for key in sorted(unique, key=lambda item: item[3])]
    return {
        "schema": "helicon-terminology-freeze-check-v1",
        "before": str(before_path),
        "after": str(after_path),
        "glossary": str(glossary_path),
        "replacements": payload,
        "replacement_count": len(payload),
        "passed": not payload,
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--glossary", required=True)
    try:
        args = parser.parse_args()
        result = compare(Path(args.before), Path(args.after), Path(args.glossary))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-terminology-freeze-check-v1", "passed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
