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


def load_glossary(path: Path) -> tuple[list[dict[str, Any]], int]:
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
        if not synonyms and not variants:
            raise UserError(
                f"glossary entry {index} requires a non-empty forbidden_synonyms "
                "or forbidden_variants array"
            )
        normalized.append({
            "term": entry["term"].strip(),
            "abbreviation": abbreviation.strip() if isinstance(abbreviation, str) else None,
            "forbidden_synonyms": [item.strip() for item in synonyms],
            "forbidden_variants": [item.strip() for item in variants],
        })
    active_rule_count = sum(
        len(entry["forbidden_synonyms"]) + len(entry["forbidden_variants"])
        for entry in normalized
    )
    if active_rule_count == 0:
        raise UserError("glossary has no active forbidden synonym or variant rules")
    return normalized, active_rule_count


def matches(text: str, value: str, *, ignore_case: bool = True) -> list[re.Match[str]]:
    flags = re.IGNORECASE if ignore_case else 0
    return list(re.finditer(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", text, flags))


def mask_latex_regions(text: str) -> str:
    """Blank non-prose LaTeX regions without changing offsets or line numbers."""
    spans: list[tuple[int, int]] = []
    patterns = (
        r"\\begin\s*\{\s*(?:equation|align|gather)\*?\s*\}.*?"
        r"\\end\s*\{\s*(?:equation|align|gather)\*?\s*\}",
        r"\\\[.*?\\\]",
        r"(?<!\\)(\${1,2}).*?(?<!\\)\1",
    )
    for pattern in patterns:
        spans.extend(match.span() for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE))

    for match in re.finditer(r"\\([A-Za-z]+)\*?", text):
        spans.append(match.span())
        command = match.group(1).casefold()
        if not (
            command.endswith("ref")
            or command.endswith("label")
            or "cite" in command
        ):
            continue
        cursor = match.end()
        while True:
            whitespace = re.match(r"\s*", text[cursor:])
            cursor += whitespace.end() if whitespace else 0
            optional = re.match(r"\[[^\]]*\]", text[cursor:], re.DOTALL)
            if optional is None:
                break
            spans.append((cursor, cursor + optional.end()))
            cursor += optional.end()
        argument = re.match(r"\{[^{}]*\}", text[cursor:], re.DOTALL)
        if argument is not None:
            spans.append((cursor, cursor + argument.end()))

    masked = list(text)
    for start, end in spans:
        for index in range(start, end):
            if masked[index] != "\n":
                masked[index] = " "
    return "".join(masked)


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


def is_sentence_initial_capitalization(text: str, match: re.Match[str], term: str) -> bool:
    observed = match.group(0)
    if not term or observed != term[0].upper() + term[1:] or observed == term:
        return False
    if match.start() == 0:
        return True
    prefix = text[:match.start()]
    return bool(re.search(r"(?:[.!?:][ \t]+|\n[ \t]*)\Z", prefix))


def added_case_inconsistencies(before: str, after: str, term: str) -> list[re.Match[str]]:
    """Return only newly added noncanonical case forms outside sentence starts."""
    before_counts: dict[str, int] = {}
    for match in matches(before, term):
        observed = match.group(0)
        if observed == term or is_sentence_initial_capitalization(before, match, term):
            continue
        before_counts[observed] = before_counts.get(observed, 0) + 1

    added: list[re.Match[str]] = []
    remaining = before_counts.copy()
    for match in matches(after, term):
        observed = match.group(0)
        if observed == term or is_sentence_initial_capitalization(after, match, term):
            continue
        if remaining.get(observed, 0):
            remaining[observed] -= 1
        else:
            added.append(match)
    return added


def compare(before_path: Path, after_path: Path, glossary_path: Path) -> dict[str, Any]:
    before = read_text(before_path)
    after = read_text(after_path)
    before_prose = mask_latex_regions(before)
    after_prose = mask_latex_regions(after)
    entries, active_rule_count = load_glossary(glossary_path)
    replacements: list[Replacement] = []
    for entry in entries:
        term = entry["term"]
        for synonym in entry["forbidden_synonyms"]:
            replacements.extend(
                Replacement(term, "forbidden_synonym", match.group(0), location(after, match.start()))
                for match in added_matches(before_prose, after_prose, synonym)
            )
        for variant in entry["forbidden_variants"]:
            replacements.extend(
                Replacement(term, "plural_or_hyphen_variant", match.group(0), location(after, match.start()))
                for match in added_matches(before_prose, after_prose, variant)
            )

        replacements.extend(
            Replacement(term, "case_inconsistency", match.group(0), location(after, match.start()))
            for match in added_case_inconsistencies(before_prose, after_prose, term)
        )

        abbreviation = entry["abbreviation"]
        if abbreviation:
            before_full = bool(matches(before_prose, term))
            before_short = bool(matches(before_prose, abbreviation, ignore_case=False))
            after_full = bool(matches(after_prose, term))
            after_short_matches = matches(after_prose, abbreviation, ignore_case=False)
            if before_full and not before_short and after_short_matches:
                replacements.extend(
                    Replacement(term, "abbreviation_full_name_mix", match.group(0), location(after, match.start()))
                    for match in after_short_matches
                )
            elif before_short and not before_full and after_full:
                replacements.extend(
                    Replacement(term, "abbreviation_full_name_mix", match.group(0), location(after, match.start()))
                    for match in matches(after_prose, term)
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
        "active_rule_count": active_rule_count,
        "replacements": payload,
        "replacement_count": len(payload),
        "passed": not payload,
    }


def main() -> int:
    parser = JsonArgumentParser(
        description=__doc__,
        epilog=(
            'Glossary JSON schema:\n'
            '{"entries":[{"term":"required string","abbreviation":"optional string or null",'
            '"forbidden_synonyms":["string",...],"forbidden_variants":["string",...]}]}\n'
            "Each entry must have a non-empty term and at least one non-empty item across "
            "forbidden_synonyms and forbidden_variants. Both fields, when present, must be arrays."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
