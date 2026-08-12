#!/usr/bin/env python3
"""Verify Iron Rule 1 before a revision may enter P3-P7.

Future pass-pipeline contract: call this read-only checker with BEFORE, AFTER,
and --glossary; consume its single JSON object; continue only on exit 0.
Exit 1 means at least one immutable category changed, and exit 2 means the
input or glossary could not be validated.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Callable

import latex_guard


SUPPORTED = {".md", ".tex", ".txt"}
SI_RE = re.compile(r"\\SI\s*\{(?P<value>[^{}]+)\}\s*\{(?P<unit>[^{}]+)\}")
UNIT_RE = re.compile(
    r"(?<![A-Za-z0-9_.])(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>%|×|[xX](?![A-Za-z])|ns|us|µs|ms|s|sec(?:onds?)?|"
    r"min(?:utes?)?|h(?:ours?)?|B|KB|MB|GB|TB|bits?|bytes?|KiB|MiB|GiB)"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)
CAPTION_LITERAL_REF_RE = re.compile(
    r"\b(?:Figure|Fig\.|Table|Equation|Eq\.|Section|Sec\.)\s*~?\s*\d+(?:\.\d+)*",
    re.IGNORECASE,
)
CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str], bool], ...] = (
    ("negation", latex_guard.NEGATION_RE, False),
    ("modality", latex_guard.MODALITY_RE, False),
    ("quantifier", latex_guard.QUANTIFIER_SCOPE_RE, False),
    ("comparison", latex_guard.COMPARISON_RE, False),
    ("claim_strength", latex_guard.CLAIM_STRENGTH_RE, True),
)


class UserError(Exception):
    """A deterministic configuration or input error."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


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


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_unit_numbers(text: str) -> Counter[str]:
    values: list[str] = []
    masked = list(text)
    for match in SI_RE.finditer(text):
        values.append(f"SI:{normalize(match.group('value'))}:{normalize(match.group('unit'))}")
        masked[match.start():match.end()] = " " * (match.end() - match.start())
    remainder = "".join(masked)
    values.extend(
        f"{match.group('value')} {normalize(match.group('unit'))}"
        for match in UNIT_RE.finditer(remainder)
    )
    return Counter(values)


def extract_latex_keys(text: str) -> Counter[str]:
    allowed = {"cite", "ref", "label", "eqref", "autoref"}
    values: list[str] = []
    for match in latex_guard.REFERENCE_RE.finditer(text):
        command = match.group("command").casefold()
        family = "cite" if command.startswith("cite") else command
        if family not in allowed:
            continue
        values.extend(f"{family}:{key.strip()}" for key in match.group("keys").split(",") if key.strip())
    return Counter(values)


def extract_figure_table_contract(text: str) -> Counter[str]:
    values: list[str] = []
    for match in latex_guard.FIGURE_ENV_RE.finditer(text):
        environment = "figure" if match.group("name").startswith("figure") else "table"
        body = match.group("body")
        values.extend(
            f"{environment}:label:{value.strip()}"
            for value in re.findall(r"\\label\s*\{([^{}]+)\}", body)
        )
        for caption in latex_guard.balanced_arguments(body, "caption"):
            for reference in extract_latex_keys(caption):
                values.append(f"{environment}:caption:{reference}")
            values.extend(
                f"{environment}:caption-literal:{normalize(item.group(0))}"
                for item in CAPTION_LITERAL_REF_RE.finditer(caption)
            )
    return Counter(values)


def extract_math_canonical(text: str) -> Counter[str]:
    """Ignore all formatting whitespace inside extracted math regions."""
    values: Counter[str] = Counter()
    for value, count in latex_guard.extract_math(text).items():
        values[re.sub(r"\s+", "", value)] += count
    return values


def load_glossary(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UserError(f"glossary not found: {path}") from exc
    except (UnicodeDecodeError, OSError) as exc:
        raise UserError(f"cannot read UTF-8 glossary {path}: {exc}") from exc
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise UserError(f"invalid glossary JSON: {path}") from exc
        entries = payload.get("entries") if isinstance(payload, dict) else None
        if not isinstance(entries, list):
            raise UserError("glossary JSON requires an entries array")
        terms = [entry.get("term") for entry in entries if isinstance(entry, dict)]
        if not terms or any(not isinstance(term, str) or not term.strip() for term in terms):
            raise UserError("every glossary entry requires a non-empty term")
        return sorted({term.strip() for term in terms}, key=lambda item: (-len(item), item.casefold()))
    terms = latex_guard.glossary_terms(path)
    if not terms:
        raise UserError("glossary contains no terms")
    return terms


def term_counter(text: str, terms: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for term in terms:
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
        counts[term] = len(pattern.findall(text))
    return +counts


def claim_counter(text: str) -> Counter[str]:
    """Count normalized marker classes without binding them to sentence order."""
    prose = latex_guard.prose_for_claim_scope(text)
    values: Counter[str] = Counter()
    for name, pattern, _collapse in CLAIM_PATTERNS:
        markers = latex_guard.scope_markers(prose, pattern, collapse_per_scope=False)
        values.update({f"{name}:{marker}": count for marker, count in markers.items()})
    return values


def expanded(counter: Counter[str]) -> list[str]:
    return [value for value in sorted(counter) for _ in range(counter[value])]


def category_report(before: Counter[str], after: Counter[str]) -> dict[str, Any]:
    removed = before - after
    added = after - before
    removed_items = expanded(removed)
    added_items = expanded(added)
    changed = [
        {"before": old, "after": new}
        for old, new in zip(removed_items, added_items)
    ]
    return {
        "added": added_items,
        "removed": removed_items,
        "changed": changed,
        "violation_count": max(len(added_items), len(removed_items)),
    }


def compare(before_path: Path, after_path: Path, glossary_path: Path) -> dict[str, Any]:
    before = read_text(before_path)
    after = read_text(after_path)
    glossary = load_glossary(glossary_path)
    extractors: dict[str, Callable[[str], Counter[str]]] = {
        "numbers_with_units": extract_unit_numbers,
        "latex_keys": extract_latex_keys,
        "math": extract_math_canonical,
        "figure_table": extract_figure_table_contract,
        "glossary_terms": lambda value: term_counter(value, glossary),
    }
    categories = {
        name: category_report(extractor(before), extractor(after))
        for name, extractor in extractors.items()
    }
    categories["claim_scope"] = category_report(claim_counter(before), claim_counter(after))
    total = sum(item["violation_count"] for item in categories.values())
    return {
        "schema": "helicon-immutable-set-check-v1",
        "before": str(before_path),
        "after": str(after_path),
        "glossary": str(glossary_path),
        "categories": categories,
        "total_violations": total,
        "passed": total == 0,
    }


def parser() -> argparse.ArgumentParser:
    value = JsonArgumentParser(description=__doc__)
    value.add_argument("before")
    value.add_argument("after")
    value.add_argument("--glossary", required=True)
    return value


def main() -> int:
    try:
        args = parser().parse_args()
        result = compare(Path(args.before), Path(args.after), Path(args.glossary))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-immutable-set-check-v1", "passed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
