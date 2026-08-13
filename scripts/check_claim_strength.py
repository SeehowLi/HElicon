#!/usr/bin/env python3
"""Enforce Iron Rule 3: a revision must not strengthen a claim.

Future pass-pipeline contract: run after a proposed edit and before acceptance;
consume the single JSON object. Exit 0 means no mechanically observable upward
move, exit 1 means one or more upward moves, and exit 2 means invalid input.
V1 checks only the global claim-marker multiset; V2 supplies directional
strength checks, while V1's relocation report warns when a marker changes scope.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
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
# fhe_lexicon_freeze.md misuse row: adversary model.
# fhe_lexicon_freeze.md misuse row: selective versus adaptive security.
# fhe_lexicon_freeze.md misuse row: IND-CPA versus IND-CCA/IND-CCA2.
# fhe_lexicon_freeze.md misuse row: static versus adaptive corruption.
# fhe_lexicon_freeze.md misuse row: computational/statistical/perfect privacy.
# fhe_lexicon_freeze.md misuse row: somewhat/leveled/fully homomorphic scope.
# fhe_lexicon_freeze.md misuse row: approximate versus exact semantics.
# fhe_lexicon_freeze.md misuse row: bounded versus no leakage.
CRYPTO_LADDERS: dict[str, tuple[tuple[str, ...], ...]] = {
    "adversary_model": (("semi-honest", "honest-but-curious"), ("malicious",)),
    "security_adaptivity": (("selective",), ("adaptive",)),
    "security_indistinguishability": (("IND-CPA",), ("IND-CCA",), ("IND-CCA2",)),
    "corruption": (("static corruption",), ("adaptive corruption",)),
    "privacy_guarantee": (("computational",), ("statistical",), ("perfect",)),
    "scheme_scope": (
        ("somewhat homomorphic encryption",),
        ("leveled homomorphic encryption",),
        ("fully homomorphic encryption",),
    ),
    "exactness": (("approximate",), ("exact",)),
    "leakage": (("bounded leakage",), ("no leakage",)),
}
CRYPTO_LADDER_COUNT = 8
CRYPTO_LADDER_MANIFEST_SHA256 = "bd698e056038d59be3c38c9479b94721a33d9f6bfd881eee3ef37a7c73957b3e"
# v1 constants above are published and immutable. This parallel v2 contract
# adds noun-phrase anchors for the three ladders whose tiers are bare words.
CRYPTO_LADDER_ANCHORS: dict[str, tuple[str, ...]] = {
    "security_adaptivity": (
        "security", "secure", "adversary", "corruption", "notion",
        "chosen-message", "chosen-ciphertext", "soundness", "simulation",
    ),
    "privacy_guarantee": (
        "privacy", "security", "secrecy", "indistinguishability", "hiding",
        "binding", "zero-knowledge", "soundness", "correctness",
    ),
    "exactness": (
        "arithmetic", "homomorphic", "encryption", "computation", "evaluation",
        "result", "scheme", "HE", "CKKS", "BFV", "BGV", "TFHE",
    ),
}
CRYPTO_LADDER_ANCHOR_COUNT = 3
CRYPTO_LADDER_ANCHORED_MANIFEST_SHA256 = "eef87d52f5b29469d79ea2d69706616458f1b8112106beb244a6ae783d861421"
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
PUNCTUATION_RE = re.compile(r"[^\w\s-]")
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


@dataclass
class CryptoMove:
    kind: str
    ladder: str
    original: str
    revised: str
    original_position: dict[str, int]
    revised_position: dict[str, int]
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


def anchor_matches(observed: str, anchor: str) -> bool:
    return observed == anchor if anchor.isupper() else observed.casefold() == anchor.casefold()


def has_nearby_anchor(text: str, term_match: re.Match[str], anchors: tuple[str, ...]) -> bool:
    words = list(WORD_RE.finditer(text))
    term_index = next(
        (index for index, word in enumerate(words) if word.start() == term_match.start()),
        None,
    )
    if term_index is None:
        return False
    for anchor_index in range(max(0, term_index - 2), min(len(words), term_index + 3)):
        if anchor_index == term_index:
            continue
        anchor_match = words[anchor_index]
        if not any(anchor_matches(anchor_match.group(0), anchor) for anchor in anchors):
            continue
        left, right = sorted((term_match, anchor_match), key=lambda match: match.start())
        if not PUNCTUATION_RE.search(text[left.end():right.start()]):
            return True
    return False


def ladder_occurrences(
    text: str,
    ladder: tuple[tuple[str, ...], ...],
    ladder_name: str | None = None,
) -> list[tuple[int, str, int]]:
    lookup = {word.casefold(): level for level, group in enumerate(ladder) for word in group}
    if not lookup:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, lookup), key=len, reverse=True)) + r")\b", re.IGNORECASE)
    anchors = CRYPTO_LADDER_ANCHORS.get(ladder_name or "")
    return [
        (match.start(), match.group(0), lookup[match.group(0).casefold()])
        for match in pattern.finditer(text)
        if anchors is None or has_nearby_anchor(text, match, anchors)
    ]


def crypto_ladder_manifest(ladders: dict[str, tuple[tuple[str, ...], ...]]) -> bytes:
    return json.dumps(
        ladders, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")


def crypto_ladder_anchored_manifest(
    ladders: dict[str, tuple[tuple[str, ...], ...]],
    anchors: dict[str, tuple[str, ...]],
) -> bytes:
    return json.dumps(
        {"anchors": anchors, "ladders": ladders},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def validate_crypto_ladders(
    ladders: dict[str, tuple[tuple[str, ...], ...]] = CRYPTO_LADDERS,
    expected_count: int = CRYPTO_LADDER_COUNT,
    expected_manifest_sha256: str = CRYPTO_LADDER_MANIFEST_SHA256,
    anchors: dict[str, tuple[str, ...]] = CRYPTO_LADDER_ANCHORS,
    expected_anchor_count: int = CRYPTO_LADDER_ANCHOR_COUNT,
    expected_anchored_manifest_sha256: str = CRYPTO_LADDER_ANCHORED_MANIFEST_SHA256,
) -> None:
    if len(ladders) != expected_count or any(
        len(levels) < 2
        or any(not group or any(not isinstance(term, str) or not term for term in group) for group in levels)
        for levels in ladders.values()
    ):
        raise UserError("cryptographic strength ladder set missing or malformed")
    if hashlib.sha256(crypto_ladder_manifest(ladders)).hexdigest() != expected_manifest_sha256:
        raise UserError("cryptographic strength ladder manifest mismatch")
    if (
        len(anchors) != expected_anchor_count
        or set(anchors) != {"security_adaptivity", "privacy_guarantee", "exactness"}
        or any(not values or any(not isinstance(value, str) or not value for value in values) for values in anchors.values())
    ):
        raise UserError("cryptographic strength ladder anchor set missing or malformed")
    if (
        hashlib.sha256(crypto_ladder_anchored_manifest(ladders, anchors)).hexdigest()
        != expected_anchored_manifest_sha256
    ):
        raise UserError("cryptographic strength ladder anchored manifest mismatch")


def scope_spans(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(0).strip().casefold())
        for match in re.finditer(r"[^.!?;\n]+", text)
        if match.group(0).strip()
    ]


def occurrence_scope(spans: list[tuple[int, int, str]], offset: int) -> int | None:
    return next((index for index, (start, end, _text) in enumerate(spans) if start <= offset < end), None)


def crypto_moves(before: str, after: str) -> tuple[list[CryptoMove], list[CryptoMove], list[CryptoMove]]:
    import latex_guard

    upward: list[CryptoMove] = []
    downward: list[CryptoMove] = []
    relocations: list[CryptoMove] = []
    before_spans = scope_spans(before)
    after_spans = scope_spans(after)
    alignment = latex_guard.align_claim_scopes(
        [scope for _start, _end, scope in before_spans],
        [scope for _start, _end, scope in after_spans],
    )
    old_to_new = {old: new for old, new in alignment if old is not None and new is not None}

    for ladder_name, ladder in CRYPTO_LADDERS.items():
        old = ladder_occurrences(before, ladder, ladder_name)
        new = ladder_occurrences(after, ladder, ladder_name)
        if Counter(level for _offset, _word, level in old) == Counter(
            level for _offset, _word, level in new
        ):
            old_by_level: dict[int, list[tuple[int, str, int]]] = {}
            new_by_level: dict[int, list[tuple[int, str, int]]] = {}
            for item in old:
                old_by_level.setdefault(item[2], []).append(item)
            for item in new:
                new_by_level.setdefault(item[2], []).append(item)
            for level in sorted(set(old_by_level) | set(new_by_level)):
                old_items = old_by_level.get(level, [])
                new_items = new_by_level.get(level, [])
                unmatched_new = list(new_items)
                for old_offset, old_word, _ in old_items:
                    old_scope = occurrence_scope(before_spans, old_offset)
                    expected_scope = old_to_new.get(old_scope) if old_scope is not None else None
                    match_index = next(
                        (
                            index
                            for index, (new_offset, _new_word, _new_level) in enumerate(unmatched_new)
                            if occurrence_scope(after_spans, new_offset) == expected_scope
                        ),
                        None,
                    )
                    if match_index is not None:
                        unmatched_new.pop(match_index)
                        continue
                    if unmatched_new:
                        new_offset, new_word, _ = unmatched_new.pop(0)
                        relocations.append(CryptoMove(
                            "crypto_relocation", ladder_name, old_word, new_word,
                            position(before, old_offset), position(after, new_offset), 0,
                        ))
            continue

        for original, revised in zip(old, new):
            old_offset, old_word, old_level = original
            new_offset, new_word, new_level = revised
            if new_level == old_level:
                continue
            target = upward if new_level > old_level else downward
            target.append(CryptoMove(
                "crypto_upward_move" if new_level > old_level else "crypto_downward_move",
                ladder_name,
                old_word,
                new_word,
                position(before, old_offset),
                position(after, new_offset),
                new_level - old_level,
            ))
    return upward, downward, relocations


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
    validate_crypto_ladders()
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

    crypto_upward, crypto_downward, crypto_relocations = crypto_moves(before, after)
    conservative_no_leakage = sum(
        item.ladder == "leakage" and item.original.casefold() == "no leakage"
        for item in crypto_downward
    )
    filtered_moves: list[UpwardMove] = []
    for item in moves:
        if item.kind == "negation_removed" and item.original.casefold() == "no" and conservative_no_leakage:
            conservative_no_leakage -= 1
            continue
        filtered_moves.append(item)
    moves = filtered_moves
    payload = [asdict(item) for item in sorted(moves, key=lambda item: item.original_position["offset"])]
    return {
        "schema": "helicon-claim-strength-check-v1",
        "before": str(before_path),
        "after": str(after_path),
        "upward_moves": payload,
        "upward_move_count": len(payload),
        "crypto_upward_moves": [asdict(item) for item in crypto_upward],
        "crypto_downward_moves": [asdict(item) for item in crypto_downward],
        "crypto_relocations": [asdict(item) for item in crypto_relocations],
        "passed": not payload and not crypto_upward,
    }


def main() -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    try:
        validate_crypto_ladders()
        args = parser.parse_args()
        result = compare(Path(args.before), Path(args.after))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-claim-strength-check-v1", "passed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
