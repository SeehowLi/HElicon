#!/usr/bin/env python3
"""Compare LaTeX immutable sets before and after a revision."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any

ALLOW_CHOICES = ("numbers", "references", "math", "figures", "terms")
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:\s*(?:%|[xX]|ms|s|GB|MB|KB|bits?))?(?![\w.])")
REFERENCE_RE = re.compile(
    r"\\(?P<command>cite\w*|ref|autoref|eqref|cref|label)\s*"
    r"(?:\[[^\]]*\]\s*)*\{(?P<keys>[^{}]*)\}"
)
MATH_ENV_RE = re.compile(
    r"\\begin\{(?P<name>equation\*?|align\*?|gather\*?|multline\*?|displaymath|math)\}"
    r"(?P<body>.*?)\\end\{(?P=name)\}",
    re.DOTALL,
)
FIGURE_ENV_RE = re.compile(
    r"\\begin\{(?P<name>figure\*?|table\*?)\}(?P<body>.*?)\\end\{(?P=name)\}",
    re.DOTALL,
)


class UserError(Exception):
    """A concise command-line error."""


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path} ({exc})") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def balanced_arguments(text: str, command: str) -> list[str]:
    results: list[str] = []
    start_re = re.compile(rf"\\{command}\*?\s*(?:\[[^\]]*\]\s*)*\{{")
    for match in start_re.finditer(text):
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{" and (index == 0 or text[index - 1] != "\\"):
                depth += 1
            elif text[index] == "}" and (index == 0 or text[index - 1] != "\\"):
                depth -= 1
            index += 1
        if depth == 0:
            results.append(normalized(text[match.end():index - 1]))
    return results


def extract_math(text: str) -> Counter[str]:
    values: list[str] = []
    spans: list[tuple[int, int]] = []
    for match in MATH_ENV_RE.finditer(text):
        values.append(f"{match.group('name')}:{normalized(match.group('body'))}")
        spans.append(match.span())
    masked = list(text)
    for start, end in spans:
        masked[start:end] = " " * (end - start)
    remainder = "".join(masked)
    patterns = (
        re.compile(r"\$\$(.*?)\$\$", re.DOTALL),
        re.compile(r"\\\[(.*?)\\\]", re.DOTALL),
        re.compile(r"\\\((.*?)\\\)", re.DOTALL),
        re.compile(r"(?<!\\)\$(?!\$)((?:\\.|[^$])*?)(?<!\\)\$(?!\$)", re.DOTALL),
    )
    for pattern in patterns:
        for match in pattern.finditer(remainder):
            values.append(normalized(match.group(1)))
    return Counter(values)


def extract_references(text: str) -> Counter[str]:
    values: list[str] = []
    for match in REFERENCE_RE.finditer(text):
        command = match.group("command")
        for key in match.group("keys").split(","):
            if key.strip():
                values.append(f"{command}:{key.strip()}")
    return Counter(values)


def extract_figures(text: str) -> Counter[str]:
    values: list[str] = []
    for match in FIGURE_ENV_RE.finditer(text):
        name = match.group("name")
        body = match.group("body")
        for label in re.findall(r"\\label\s*\{([^{}]+)\}", body):
            values.append(f"{name}:label:{label.strip()}")
        for caption in balanced_arguments(body, "caption"):
            values.append(f"{name}:caption:{caption}")
    return Counter(values)


def extract_numbers(text: str) -> Counter[str]:
    return Counter(normalized(match.group(0)) for match in NUMBER_RE.finditer(text))


def glossary_terms(path: Path | None) -> list[str]:
    if path is None:
        return []
    text = read_utf8(path)
    terms: set[str] = set()
    if path.suffix.lower() == ".csv":
        try:
            rows = list(csv.reader(text.splitlines()))
        except csv.Error as exc:
            raise UserError(f"invalid glossary CSV: {path} ({exc})") from exc
        for row in rows[1:]:
            for cell in row[:2]:
                if cell.strip():
                    terms.add(cell.strip())
    else:
        for line in text.splitlines():
            if line.strip().startswith("|") and "---" not in line:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if cells and cells[0].lower() not in {"term", "chinese"}:
                    for cell in cells[:2]:
                        for value in re.split(r"\s*;\s*|\s*,\s*", cell):
                            clean = re.sub(r"[`*_]", "", value).strip()
                            if clean:
                                terms.add(clean)
        terms.update(re.findall(r"`([^`]+)`", text))
    return sorted(terms, key=lambda item: (-len(item), item.lower()))


def term_counts(text: str, terms: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in terms:
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
        count = len(pattern.findall(text))
        if count:
            counts[term] = count
    return counts


def counter_diff(before: Counter[str], after: Counter[str]) -> dict[str, dict[str, int]]:
    removed = before - after
    added = after - before
    return {
        "removed": dict(sorted(removed.items())),
        "added": dict(sorted(added.items())),
    }


def compare(before_path: Path, after_path: Path, glossary: Path | None, allowed: set[str]) -> dict[str, Any]:
    before = read_utf8(before_path)
    after = read_utf8(after_path)
    categories = {
        "numbers": (extract_numbers(before), extract_numbers(after)),
        "references": (extract_references(before), extract_references(after)),
        "math": (extract_math(before), extract_math(after)),
        "figures": (extract_figures(before), extract_figures(after)),
    }
    differences: dict[str, Any] = {}
    failures: list[str] = []
    for name, (old, new) in categories.items():
        delta = counter_diff(old, new)
        changed = bool(delta["removed"] or delta["added"])
        differences[name] = {"changed": changed, "allowed": name in allowed, **delta}
        if changed and name not in allowed:
            failures.append(name)

    terms = glossary_terms(glossary)
    old_terms = term_counts(before, terms)
    new_terms = term_counts(after, terms)
    term_changes = {
        term: {"before": old_terms.get(term, 0), "after": new_terms.get(term, 0)}
        for term in sorted(set(old_terms) | set(new_terms))
        if old_terms.get(term, 0) != new_terms.get(term, 0)
    }
    differences["terms"] = {
        "changed": bool(term_changes),
        "allowed": "terms" in allowed,
        "count_changes": term_changes,
        "note": "Glossary occurrence-count changes are reported but do not fail the guard.",
    }
    return {
        "before": str(before_path),
        "after": str(after_path),
        "glossary": str(glossary) if glossary else None,
        "allowed": sorted(allowed),
        "passed": not failures,
        "failed_categories": failures,
        "differences": differences,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="original .tex file")
    parser.add_argument("after", help="revised .tex file")
    parser.add_argument("--glossary", help="Markdown or CSV glossary")
    parser.add_argument("--allow", action="append", default=[], choices=ALLOW_CHOICES, help="explicitly allow one changed category; repeat as needed")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def print_human(result: dict[str, Any]) -> None:
    for name, delta in result["differences"].items():
        if not delta["changed"]:
            continue
        if name == "terms":
            for term, counts in delta["count_changes"].items():
                print(f"terms: {term!r}: {counts['before']} -> {counts['after']} (reported only)")
            continue
        status = "ALLOWED" if delta["allowed"] else "FAIL"
        print(f"{status}: {name}")
        for kind in ("removed", "added"):
            for value, count in delta[kind].items():
                print(f"  {kind}: {value!r} x{count}")
    print("LaTeX immutable-set check passed." if result["passed"] else "LaTeX immutable-set check failed.")


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        before = Path(args.before)
        after = Path(args.after)
        for path in (before, after):
            if path.suffix.lower() != ".tex":
                raise UserError(f"expected a .tex file: {path}")
        result = compare(before, after, Path(args.glossary) if args.glossary else None, set(args.allow))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_human(result)
        return 0 if result["passed"] else 1
    except UserError as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
