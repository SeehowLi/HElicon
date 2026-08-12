#!/usr/bin/env python3
"""Compare immutable sets before and after a research-prose revision."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import sys
from typing import Any

ALLOW_CHOICES = (
    "numbers",
    "references",
    "math",
    "figures",
    "terms",
    "negation",
    "modality",
    "quantifier_scope",
    "comparison",
    "claim_strength",
)
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
NEGATION_RE = re.compile(
    r"\b(?:(?P<not>not|cannot|can['’]t|won['’]t|shan['’]t|"
    r"(?:is|are|was|were|do|does|did|has|have|had|would|should|could|might|must|need)n['’]t)"
    r"|(?P<no>no)|(?P<never>never)|(?P<without>without)|(?P<neither>neither)|"
    r"(?P<nor>nor)|(?P<none>none))\b",
    re.IGNORECASE,
)
MODALITY_RE = re.compile(
    r"\b(?:(?P<may>may)|(?P<might>might(?:n['’]t)?)|"
    r"(?P<can>can|cannot|can['’]t)|(?P<could>could(?:n['’]t)?)|"
    r"(?P<should>should(?:n['’]t)?)|(?P<would>would(?:n['’]t)?)|"
    r"(?P<must>must(?:n['’]t)?)|(?P<will>will|won['’]t))\b",
    re.IGNORECASE,
)
QUANTIFIER_SCOPE_RE = re.compile(
    r"\b(?:(?P<at_least>at\s+least)|(?P<at_most>at\s+most)|"
    r"(?P<more_than>more\s+than)|(?P<less_than>less\s+than)|"
    r"(?P<all>all)|(?P<any>any)|(?P<each>each)|(?P<every>every)|"
    r"(?P<both>both)|(?P<either>either)|(?P<neither>neither)|"
    r"(?P<none>none)|(?P<some>some)|(?P<several>several)|"
    r"(?P<many>many)|(?P<most>most)|(?P<few>few)|(?P<only>only)|(?P<no>no))\b",
    re.IGNORECASE,
)
COMPARISON_RE = re.compile(
    r"\b(?:(?P<up>higher|greater|larger|exceed(?:s|ed|ing)?)|"
    r"(?P<down>lower|smaller|less|fewer)|"
    r"(?P<better>better|faster|superior|outperform(?:s|ed|ing)?)|"
    r"(?P<worse>worse|slower|inferior)|"
    r"(?P<relation>than|compared\s+(?:with|to)|relative\s+to))\b",
    re.IGNORECASE,
)
CLAIM_STRENGTH_RE = re.compile(
    r"\b(?:(?P<possibility>may|might|could|possibly|perhaps|potentially)|"
    r"(?P<probability>likely|probably|presumably)|(?P<improbability>unlikely|improbably)|"
    r"(?P<appearance>appear(?:s|ed|ing)?|seem(?:s|ed|ing)?)|"
    r"(?P<tentative>suggest(?:s|ed|ing)?|indicat(?:e|es|ed|ing)|"
    r"conjectur(?:e|es|ed|ing)|consistent\s+with)|"
    r"(?P<assertive>show(?:s|ed|ing)?|demonstrat(?:e|es|ed|ing)|establish(?:es|ed|ing)?)|"
    r"(?P<absolute>prov(?:e|es|ed|en|ing)|guarantee(?:s|d|ing)?|ensur(?:e|es|ed|ing))|"
    r"(?P<universal>always|never|necessarily)|"
    r"(?P<maximal>impossible|perfect|optimal))\b",
    re.IGNORECASE,
)
CLAIM_PATTERNS = (
    NEGATION_RE,
    MODALITY_RE,
    QUANTIFIER_SCOPE_RE,
    COMPARISON_RE,
    CLAIM_STRENGTH_RE,
)
WORD_RE = re.compile(r"[a-z0-9_]+")
HEDGE_MARKERS = frozenset(
    {"possibility", "probability", "improbability", "appearance", "tentative"}
)
SCOPE_STOPWORDS = frozenset(
    "the is are was were be been being do does did have has had to of in on for from "
    "with by as at under during this that these those it its we our they their and or but".split()
)
MIN_SCOPE_SIMILARITY = 0.60
SCOPE_AMBIGUITY_MARGIN = 0.05


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


def prose_for_claim_scope(text: str) -> str:
    """Remove non-prose regions before scanning claim-scope markers."""
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = MATH_ENV_RE.sub(" ", text)
    text = FIGURE_ENV_RE.sub(" ", text)
    text = re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)", " ", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$", " ", text, flags=re.DOTALL)
    text = REFERENCE_RE.sub(" ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
    text = text.replace("’", "'").casefold()
    contractions = {
        r"\bcannot\b|\bcan['’]t\b": "can not",
        r"\bwon['’]t\b": "will not",
        r"\bshan['’]t\b": "shall not",
        r"\bisn['’]t\b": "is not",
        r"\baren['’]t\b": "are not",
        r"\bwasn['’]t\b": "was not",
        r"\bweren['’]t\b": "were not",
        r"\bdoesn['’]t\b": "does not",
        r"\bdon['’]t\b": "do not",
        r"\bdidn['’]t\b": "did not",
        r"\bhasn['’]t\b": "has not",
        r"\bhaven['’]t\b": "have not",
        r"\bhadn['’]t\b": "had not",
        r"\bwouldn['’]t\b": "would not",
        r"\bshouldn['’]t\b": "should not",
        r"\bcouldn['’]t\b": "could not",
        r"\bmightn['’]t\b": "might not",
        r"\bmustn['’]t\b": "must not",
        r"\bneedn['’]t\b": "need not",
    }
    for pattern, replacement in contractions.items():
        text = re.sub(pattern, replacement, text)
    # Rule 12 treats this correlative as rhetoric rather than semantic negation.
    return re.sub(r"\bnot\s+only\b", "not_only", text)


def claim_scopes(text: str) -> list[str]:
    prose = prose_for_claim_scope(text)
    return [part.strip() for part in re.split(r"(?:[.!?;]+|\n+)\s*", prose) if part.strip()]


def normalize_scope_word(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(("xes", "zes", "ches", "shes", "sses")):
        return word[:-2]
    if len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def marker_stripped_words(scope: str) -> tuple[str, ...]:
    spans = [
        match.span()
        for claim_pattern in CLAIM_PATTERNS
        for match in claim_pattern.finditer(scope)
    ]
    return tuple(
        normalize_scope_word(token.group(0))
        for token in WORD_RE.finditer(scope)
        if token.group(0) not in SCOPE_STOPWORDS
        and not any(token.start() < end and start < token.end() for start, end in spans)
    )


def scope_similarity(old: tuple[str, ...], new: tuple[str, ...]) -> float:
    ordered = SequenceMatcher(None, old, new, autojunk=False).ratio()
    bag = SequenceMatcher(None, sorted(old), sorted(new), autojunk=False).ratio()
    return max(ordered, bag)


def has_claim_marker(scope: str) -> bool:
    return any(pattern.search(scope) for pattern in CLAIM_PATTERNS)


def align_claim_scopes(before: list[str], after: list[str]) -> list[tuple[int | None, int | None]]:
    """Greedily align the most similar marker-free scopes one-to-one."""
    old_words = [marker_stripped_words(scope) for scope in before]
    new_words = [marker_stripped_words(scope) for scope in after]
    # ponytail: O(n^2) keeps alignment dependency-free and is bounded by paper-sized inputs.
    candidates = sorted(
        (
            (scope_similarity(old, new), old_index, new_index)
            for old_index, old in enumerate(old_words)
            for new_index, new in enumerate(new_words)
        ),
        key=lambda item: (-item[0], abs(item[1] - item[2]), item[1], item[2]),
    )
    eligible = [candidate for candidate in candidates if candidate[0] >= MIN_SCOPE_SIMILARITY]
    ambiguous_old = {
        old_index
        for old_index, scope in enumerate(before)
        if has_claim_marker(scope)
        and len(scores := [score for score, candidate_old, _ in eligible if candidate_old == old_index]) > 1
        and scores[0] - scores[1] < SCOPE_AMBIGUITY_MARGIN
    }
    ambiguous_new = {
        new_index
        for new_index, scope in enumerate(after)
        if has_claim_marker(scope)
        and len(scores := [score for score, _, candidate_new in eligible if candidate_new == new_index]) > 1
        and scores[0] - scores[1] < SCOPE_AMBIGUITY_MARGIN
    }
    old_used: set[int] = set()
    new_used: set[int] = set()
    aligned: list[tuple[int | None, int | None]] = []
    for _, old_index, new_index in eligible:
        if (
            old_index not in ambiguous_old
            and new_index not in ambiguous_new
            and old_index not in old_used
            and new_index not in new_used
        ):
            aligned.append((old_index, new_index))
            old_used.add(old_index)
            new_used.add(new_index)
    aligned.extend((index, None) for index in range(len(before)) if index not in old_used)
    aligned.extend((None, index) for index in range(len(after)) if index not in new_used)
    return aligned


def scope_markers(
    scope: str, pattern: re.Pattern[str], *, collapse_per_scope: bool = False
) -> Counter[str]:
    markers = [match.lastgroup for match in pattern.finditer(scope) if match.lastgroup]
    if pattern is CLAIM_STRENGTH_RE:
        markers = ["hedged" if marker in HEDGE_MARKERS else marker for marker in markers]
    return Counter(set(markers) if collapse_per_scope else markers)


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


def marker_diff(
    before: list[str],
    after: list[str],
    alignment: list[tuple[int | None, int | None]],
    pattern: re.Pattern[str],
    *,
    collapse_per_scope: bool = False,
) -> dict[str, dict[str, int]]:
    """Compare markers within aligned scopes and expose no manuscript-derived anchors."""
    removed: Counter[str] = Counter()
    added: Counter[str] = Counter()
    for old_index, new_index in alignment:
        old = (
            scope_markers(before[old_index], pattern, collapse_per_scope=collapse_per_scope)
            if old_index is not None
            else Counter()
        )
        new = (
            scope_markers(after[new_index], pattern, collapse_per_scope=collapse_per_scope)
            if new_index is not None
            else Counter()
        )
        removed.update(old - new)
        added.update(new - old)
    return {
        "removed": dict(sorted(removed.items())),
        "added": dict(sorted(added.items())),
    }


def compare(before_path: Path, after_path: Path, glossary: Path | None, allowed: set[str]) -> dict[str, Any]:
    before = read_utf8(before_path)
    after = read_utf8(after_path)
    old_scopes = claim_scopes(before)
    new_scopes = claim_scopes(after)
    scope_alignment = align_claim_scopes(old_scopes, new_scopes)
    categories = {
        "numbers": (extract_numbers(before), extract_numbers(after)),
        "references": (extract_references(before), extract_references(after)),
        "math": (extract_math(before), extract_math(after)),
        "figures": (extract_figures(before), extract_figures(after)),
    }
    claim_categories = {
        "negation": (NEGATION_RE, False),
        "modality": (MODALITY_RE, False),
        "quantifier_scope": (QUANTIFIER_SCOPE_RE, False),
        "comparison": (COMPARISON_RE, False),
        "claim_strength": (CLAIM_STRENGTH_RE, True),
    }
    differences: dict[str, Any] = {}
    failures: list[str] = []
    for name, (old, new) in categories.items():
        delta = counter_diff(old, new)
        changed = bool(delta["removed"] or delta["added"])
        differences[name] = {"changed": changed, "allowed": name in allowed, **delta}
        if changed and name not in allowed:
            failures.append(name)
    for name, (pattern, collapse_per_scope) in claim_categories.items():
        delta = marker_diff(
            old_scopes,
            new_scopes,
            scope_alignment,
            pattern,
            collapse_per_scope=collapse_per_scope,
        )
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
    parser.add_argument("before", help="original .tex, .md, or .txt file")
    parser.add_argument("after", help="revised .tex, .md, or .txt file")
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
    print("Immutable-set check passed." if result["passed"] else "Immutable-set check failed.")


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        before = Path(args.before)
        after = Path(args.after)
        for path in (before, after):
            if path.suffix.lower() not in {".tex", ".md", ".txt"}:
                raise UserError(f"expected a .tex, .md, or .txt file: {path}")
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
