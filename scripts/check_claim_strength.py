#!/usr/bin/env python3
"""Enforce Iron Rule 3: a revision must not strengthen a claim.

Future pass-pipeline contract: run after a proposed edit and before acceptance;
consume the single JSON object. Exit 0 means no mechanically observable upward
move, exit 1 means one or more upward moves, and exit 2 means invalid input.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any


SUPPORTED = {".md", ".tex", ".txt"}
STRENGTH_LADDERS: dict[str, tuple[tuple[str, ...], ...]] = {
    "claim": (
        ("may", "might"),
        ("suggests", "suggest", "suggested", "indicates", "indicate", "indicated"),
        ("shows", "show", "showed", "shown"),
        ("demonstrates", "demonstrate", "demonstrated"),
        ("establishes", "establish", "established"),
        ("proves", "prove", "proved", "proven"),
    ),
    "quantity": (("some",), ("many",), ("most",), ("all",)),
    "frequency": (("often",), ("usually",), ("always",)),
}
NEGATION_RE = re.compile(
    r"\b(?:not|no|never|without|neither|nor|none|cannot|can['’]t|"
    r"(?:is|are|was|were|do|does|did|has|have|had|would|should|could|might|must|need)n['’]t)\b",
    re.IGNORECASE,
)
MODAL_RE = re.compile(r"\b(?:may|might|could|can|should|would)\b", re.IGNORECASE)
QUALIFIER_RE = re.compile(
    r"\b(?:under\s+(?:the\s+)?[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}\s+assumption|"
    r"in\s+(?:the\s+)?[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}\s+setting)\b",
    re.IGNORECASE,
)
COMPARISON_GROUPS: dict[str, tuple[set[str], set[str]]] = {
    "performance": ({"outperforms", "outperform", "outperformed"}, {"underperforms", "underperform", "underperformed"}),
    "magnitude": ({"higher", "greater", "larger"}, {"lower", "less", "smaller"}),
    "speed": ({"faster"}, {"slower"}),
    "quality": ({"better", "superior"}, {"worse", "inferior"}),
}


class UserError(Exception):
    """A deterministic input error."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


@dataclass
class UpwardMove:
    kind: str
    original: str
    revised: str | None
    original_position: dict[str, int]
    revised_position: dict[str, int] | None
    ladder_span: int


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


def position(text: str, offset: int) -> dict[str, int]:
    prior = text.rfind("\n", 0, offset)
    return {
        "offset": offset,
        "line": text.count("\n", 0, offset) + 1,
        "column": offset + 1 if prior < 0 else offset - prior,
    }


def ladder_occurrences(text: str, ladder: tuple[tuple[str, ...], ...]) -> list[tuple[int, str, int]]:
    lookup = {word: level for level, group in enumerate(ladder) for word in group}
    if not lookup:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, lookup), key=len, reverse=True)) + r")\b", re.IGNORECASE)
    return [(match.start(), match.group(0), lookup[match.group(0).casefold()]) for match in pattern.finditer(text)]


def removed_occurrences(before: str, after: str, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    old = list(pattern.finditer(before))
    remaining = Counter(match.group(0).casefold() for match in pattern.finditer(after))
    removed: list[tuple[int, str]] = []
    for match in old:
        token = match.group(0).casefold()
        if remaining[token]:
            remaining[token] -= 1
        else:
            removed.append((match.start(), match.group(0)))
    return removed


def removed_by_total_count(before: str, after: str, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    """Treat same-class lexical substitutions as retained rather than deleted."""
    old = list(pattern.finditer(before))
    missing = max(0, len(old) - len(list(pattern.finditer(after))))
    return [(match.start(), match.group(0)) for match in old[-missing:]] if missing else []


def comparison_occurrences(text: str, positive: set[str], negative: set[str]) -> list[tuple[int, str, int]]:
    words = sorted(positive | negative, key=len, reverse=True)
    pattern = re.compile(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", re.IGNORECASE)
    return [
        (match.start(), match.group(0), 1 if match.group(0).casefold() in positive else -1)
        for match in pattern.finditer(text)
    ]


def compare(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = read_text(before_path)
    after = read_text(after_path)
    moves: list[UpwardMove] = []

    for ladder_name, ladder in STRENGTH_LADDERS.items():
        old = ladder_occurrences(before, ladder)
        new = ladder_occurrences(after, ladder)
        for original, revised in zip(old, new):
            old_offset, old_word, old_level = original
            new_offset, new_word, new_level = revised
            if new_level > old_level:
                moves.append(UpwardMove(
                    kind=f"strength:{ladder_name}",
                    original=old_word,
                    revised=new_word,
                    original_position=position(before, old_offset),
                    revised_position=position(after, new_offset),
                    ladder_span=new_level - old_level,
                ))

    for kind, pattern in (("negation_removed", NEGATION_RE), ("modal_removed", MODAL_RE)):
        for offset, word in removed_by_total_count(before, after, pattern):
            moves.append(UpwardMove(kind, word, None, position(before, offset), None, 1))

    for name, (positive, negative) in COMPARISON_GROUPS.items():
        old = comparison_occurrences(before, positive, negative)
        new = comparison_occurrences(after, positive, negative)
        for original, revised in zip(old, new):
            old_offset, old_word, old_direction = original
            new_offset, new_word, new_direction = revised
            if old_direction != new_direction:
                moves.append(UpwardMove(
                    f"comparison_flip:{name}", old_word, new_word,
                    position(before, old_offset), position(after, new_offset), 2,
                ))

    for offset, phrase in removed_occurrences(before, after, QUALIFIER_RE):
        moves.append(UpwardMove("scope_qualifier_removed", phrase, None, position(before, offset), None, 1))

    payload = [asdict(item) for item in sorted(moves, key=lambda item: item.original_position["offset"])]
    return {
        "schema": "helicon-claim-strength-check-v1",
        "before": str(before_path),
        "after": str(after_path),
        "upward_moves": payload,
        "upward_move_count": len(payload),
        "passed": not payload,
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    try:
        args = parser.parse_args()
        result = compare(Path(args.before), Path(args.after))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-claim-strength-check-v1", "passed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
