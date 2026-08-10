#!/usr/bin/env python3
"""Extract private revision-direction signals from ordered paper stages."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path
import re
import sys
from typing import Any

import check_ai_tells
import style_fingerprint

CLAIM_SCOPE_RE = re.compile(r"\b(?:may|might|could|suggests?|shows?|proves?|guarantees?|always|never)\b", re.IGNORECASE)
TECHNICAL_TERM_RE = re.compile(r"\b(?:FHE|CKKS|ciphertexts?|bootstrapping|key switching|threat model|security model|latency|throughput)\b", re.IGNORECASE)


class UserError(Exception):
    """A concise command-line error."""


def stage_number(path: Path) -> int:
    match = re.search(r"(?:version|stage|v)[-_ ]?(\d+)", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else -1


def discover_versions(directory: Path) -> list[Path]:
    try:
        files = style_fingerprint.input_files([str(directory)])
    except style_fingerprint.UserError as exc:
        pdfs = sorted(directory.rglob("*.pdf"))
        if pdfs:
            raise UserError(
                "PDF stages are not parsed directly; extract each PDF to a private .txt file with "
                "scripts/extract_pdf_text.py, then rerun on that text directory"
            ) from exc
        raise UserError(str(exc)) from exc
    files.sort(key=lambda path: (stage_number(path), str(path).lower()))
    if len(files) < 2:
        raise UserError(f"need at least two .tex, .md, or .txt stages in {directory}")
    return files


def revision_text(text: str, suffix: str) -> str:
    """Remove document scaffolding while preserving inline frozen LaTeX."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if suffix != ".tex":
        return text
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(
        r"\\(?:documentclass|usepackage|title|author|date)\*?\s*(?:\[[^\]]*\]\s*)*\{[^{}]*\}",
        " ",
        text,
    )
    text = re.sub(r"\\(?:begin|end)\{document\}|\\maketitle\b", " ", text)
    for environment in (
        "table", "table*", "tabular", "tabular*", "longtable", "equation", "equation*",
        "align", "align*", "gather", "gather*", "multline", "multline*", "displaymath",
    ):
        text = re.sub(
            rf"\\begin\{{{re.escape(environment)}\}}.*?\\end\{{{re.escape(environment)}\}}",
            " ",
            text,
            flags=re.DOTALL,
        )
    text = re.sub(r"\\label\s*\{[^{}]*\}", " ", text)
    return text


def paragraphs(path: Path) -> list[dict[str, Any]]:
    raw = style_fingerprint.read_utf8(path)
    results: list[dict[str, Any]] = []
    for section, content in style_fingerprint.raw_sections(raw, path.suffix.lower()):
        if section == "Preamble":
            continue
        clean = revision_text(content, path.suffix.lower())
        for text in style_fingerprint.split_paragraphs(clean):
            results.append({"index": len(results) + 1, "section": section, "text": text})
    return results


def similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, left.casefold(), right.casefold(), autojunk=False).ratio()


def align_paragraphs(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_text = [item["text"].casefold() for item in before]
    after_text = [item["text"].casefold() for item in after]
    matcher = difflib.SequenceMatcher(None, before_text, after_text, autojunk=False)
    aligned: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for old, new in zip(before[i1:i2], after[j1:j2]):
                aligned.append({"status": "unchanged", "before": old, "after": new, "similarity": 1.0})
            continue
        if tag == "delete":
            aligned.extend({"status": "deleted", "before": old, "after": None, "similarity": 0.0} for old in before[i1:i2])
            continue
        if tag == "insert":
            aligned.extend({"status": "inserted", "before": None, "after": new, "similarity": 0.0} for new in after[j1:j2])
            continue

        old_block = before[i1:i2]
        new_block = after[j1:j2]
        candidates = sorted(
            (
                (similarity(old["text"], new["text"]), old_index, new_index)
                for old_index, old in enumerate(old_block)
                for new_index, new in enumerate(new_block)
            ),
            reverse=True,
        )
        used_old: set[int] = set()
        used_new: set[int] = set()
        for score, old_index, new_index in candidates:
            if score < 0.2 or old_index in used_old or new_index in used_new:
                continue
            used_old.add(old_index)
            used_new.add(new_index)
            aligned.append({
                "status": "modified",
                "before": old_block[old_index],
                "after": new_block[new_index],
                "similarity": round(score, 4),
            })
        aligned.extend(
            {"status": "deleted", "before": old, "after": None, "similarity": 0.0}
            for index, old in enumerate(old_block) if index not in used_old
        )
        aligned.extend(
            {"status": "inserted", "before": None, "after": new, "similarity": 0.0}
            for index, new in enumerate(new_block) if index not in used_new
        )
    return sorted(
        aligned,
        key=lambda item: (
            item["before"]["index"] if item["before"] else 10**9,
            item["after"]["index"] if item["after"] else 10**9,
        ),
    )


def rule_counter(text: str) -> Counter[int]:
    return Counter(item.rule for item in check_ai_tells.scan_text(text))


def classify_change(item: dict[str, Any]) -> tuple[list[int], list[str]]:
    before_text = item["before"]["text"] if item["before"] else ""
    after_text = item["after"]["text"] if item["after"] else ""
    before_rules = rule_counter(before_text)
    after_rules = rule_counter(after_text)
    rule_ids = sorted(rule for rule in set(before_rules) | set(after_rules) if before_rules[rule] != after_rules[rule])
    passes: set[str] = set()
    if item["status"] in {"inserted", "deleted"}:
        passes.add("P2")
    if CLAIM_SCOPE_RE.findall(before_text) != CLAIM_SCOPE_RE.findall(after_text):
        passes.add("P1")
    if 3 in rule_ids:
        passes.add("P3")
    if item["status"] == "modified":
        passes.add("P4")
    if rule_ids:
        passes.add("P5")
    return rule_ids, sorted(passes, key=lambda value: int(value[1:]))


def parse_pairs(values: list[str]) -> set[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for value in values:
        match = re.fullmatch(r"(\d+)\s*[:>-]\s*(\d+)", value)
        if not match:
            raise UserError(f"invalid stage pair {value!r}; use forms such as 2:3")
        pairs.add((int(match.group(1)), int(match.group(2))))
    return pairs


def pair_driver(left: int, right: int, reviewer: set[tuple[int, int]], advisor: set[tuple[int, int]]) -> str:
    if (left, right) in reviewer:
        return "reviewer-driven"
    if (left, right) in advisor:
        return "author-advisor"
    return "unclassified"


def common_unchanged_sentences(version_paragraphs: list[list[dict[str, Any]]]) -> list[str]:
    sentence_maps: list[dict[str, str]] = []
    for items in version_paragraphs:
        mapping: dict[str, str] = {}
        for item in items:
            for sentence in style_fingerprint.split_sentences(item["text"]):
                key = re.sub(r"\s+", " ", sentence).strip().casefold()
                if key:
                    mapping.setdefault(key, sentence)
        sentence_maps.append(mapping)
    common = set(sentence_maps[0])
    for mapping in sentence_maps[1:]:
        common &= set(mapping)
    return [sentence_maps[0][key] for key in sorted(common)]


def common_unchanged_terms(version_paragraphs: list[list[dict[str, Any]]]) -> list[str]:
    maps: list[dict[str, str]] = []
    for items in version_paragraphs:
        mapping: dict[str, str] = {}
        for match in TECHNICAL_TERM_RE.finditer(" ".join(item["text"] for item in items)):
            mapping.setdefault(match.group(0).casefold(), match.group(0))
        maps.append(mapping)
    common = set(maps[0])
    for mapping in maps[1:]:
        common &= set(mapping)
    return [maps[0][key] for key in sorted(common)]


def common_unchanged_expressions(version_paragraphs: list[list[dict[str, Any]]]) -> list[str]:
    ngram_maps: list[dict[tuple[str, ...], str]] = []
    for items in version_paragraphs:
        words = [word.casefold() for word in style_fingerprint.WORD_RE.findall(" ".join(item["text"] for item in items))]
        mapping = {
            tuple(words[index:index + 4]): " ".join(words[index:index + 4])
            for index in range(max(0, len(words) - 3))
            if any(len(word) >= 6 for word in words[index:index + 4])
        }
        ngram_maps.append(mapping)
    common = set(ngram_maps[0])
    for mapping in ngram_maps[1:]:
        common &= set(mapping)
    return [ngram_maps[0][key] for key in sorted(common)[:20]]


def dominant_stages(counter: Counter[str]) -> list[str]:
    if not counter:
        return []
    maximum = max(counter.values())
    return sorted((stage for stage, count in counter.items() if count == maximum), key=lambda value: int(value[1:]))


def analyze(
    directory: Path,
    paper_id: str | None,
    reviewer_pairs: set[tuple[int, int]],
    advisor_pairs: set[tuple[int, int]],
) -> dict[str, Any]:
    files = discover_versions(directory)
    all_paragraphs = [paragraphs(path) for path in files]
    pairs: list[dict[str, Any]] = []
    preference_rules: Counter[int] = Counter()
    primary_stage_sequence: list[tuple[str, str]] = []
    exemplar_candidates: list[dict[str, Any]] = []
    for index, (before_path, after_path) in enumerate(zip(files, files[1:])):
        left = stage_number(before_path) if stage_number(before_path) >= 0 else index + 1
        right = stage_number(after_path) if stage_number(after_path) >= 0 else index + 2
        driver = pair_driver(left, right, reviewer_pairs, advisor_pairs)
        aligned = align_paragraphs(all_paragraphs[index], all_paragraphs[index + 1])
        rule_frequency: Counter[int] = Counter()
        pass_frequency: Counter[str] = Counter()
        changes: list[dict[str, Any]] = []
        for item in aligned:
            if item["status"] == "unchanged":
                continue
            rule_ids, passes = classify_change(item)
            rule_frequency.update(rule_ids)
            pass_frequency.update(passes)
            change = {
                "status": item["status"],
                "before_index": item["before"]["index"] if item["before"] else None,
                "after_index": item["after"]["index"] if item["after"] else None,
                "section": (item["after"] or item["before"])["section"],
                "similarity": item["similarity"],
                "rule_ids": rule_ids,
                "pass_candidates": passes,
            }
            changes.append(change)
            before_text = item["before"]["text"] if item["before"] else ""
            after_text = item["after"]["text"] if item["after"] else ""
            sentence_count = max(len(style_fingerprint.split_sentences(before_text)), len(style_fingerprint.split_sentences(after_text)))
            if item["status"] == "modified" and rule_ids and 2 <= sentence_count <= 4:
                kept_terms = sorted(set(TECHNICAL_TERM_RE.findall(before_text)) & set(TECHNICAL_TERM_RE.findall(after_text)), key=str.casefold)
                exemplar_candidates.append({
                    "paper_id": paper_id or directory.name,
                    "stage_pair": f"v{left}->v{right}",
                    "pair_driver": driver,
                    "section_type": change["section"],
                    "rule_ids": rule_ids,
                    "before": before_text,
                    "after": after_text,
                    "what_changed": f"Addressed P5 rules {rule_ids} with paragraph form preserved where possible.",
                    "what_was_deliberately_kept": kept_terms,
                })
        included = driver != "reviewer-driven"
        if included:
            preference_rules.update(rule_frequency)
        dominant = dominant_stages(pass_frequency)
        if dominant:
            primary_stage_sequence.append((f"v{left}->v{right}", dominant[0]))
        pairs.append({
            "stage_pair": f"v{left}->v{right}",
            "before_file": str(before_path),
            "after_file": str(after_path),
            "driver": driver,
            "included_in_author_preference": included,
            "alignment": dict(Counter(item["status"] for item in aligned)),
            "rule_frequencies": {str(rule): count for rule, count in sorted(rule_frequency.items())},
            "pass_frequencies": dict(sorted(pass_frequency.items())),
            "dominant_passes": dominant,
            "changes": changes,
        })

    conflicts: list[str] = []
    for (earlier_pair, earlier), (later_pair, later) in zip(primary_stage_sequence, primary_stage_sequence[1:]):
        if int(later[1:]) < int(earlier[1:]):
            conflicts.append(
                f"observed dominant order {earlier_pair}:{earlier} then {later_pair}:{later} conflicts with P1-P7 order; pipeline unchanged"
            )
    unclassified = [item["stage_pair"] for item in pairs if item["driver"] == "unclassified"]
    return {
        "schema": "helicon-revision-direction-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "paper_id": paper_id or directory.name,
        "versions": [str(path) for path in files],
        "pairs": pairs,
        "author_preference_rule_frequencies": {str(rule): count for rule, count in sorted(preference_rules.items())},
        "observed_pair_order": [{"stage_pair": pair, "dominant_pass": stage} for pair, stage in primary_stage_sequence],
        "pipeline_conflicts": conflicts,
        "pipeline_definition_changed": False,
        "unchanged_candidates": {
            "expressions": common_unchanged_expressions(all_paragraphs),
            "sentences": common_unchanged_sentences(all_paragraphs),
            "terms": common_unchanged_terms(all_paragraphs),
            "requires_author_confirmation_before_profile_write": True,
        },
        "exemplar_candidates": exemplar_candidates,
        "warnings": [
            f"mark the driver for {pair}; unclassified pairs cannot establish provenance"
            for pair in unclassified
        ],
    }


def private_output(path: Path) -> Path:
    resolved = path.resolve()
    lowered = tuple(part.casefold() for part in resolved.parts)
    if not any(left == ".helicon" and right == "style" for left, right in zip(lowered, lowered[1:])):
        raise UserError(f"revision direction must stay under .helicon/style: {resolved}")
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="directory containing ordered .tex, .md, or .txt stages")
    parser.add_argument("--paper-id", help="explicit paper identity")
    parser.add_argument("--review-driven-pair", action="append", default=[], help="stage pair excluded from author preference, for example 2:3")
    parser.add_argument("--author-advisor-pair", action="append", default=[], help="stage pair produced with author/advisor discussion, for example 1:2")
    parser.add_argument("--output", help="private .helicon/style/revision_direction.json path")
    parser.add_argument("--write", action="store_true", help="write the private report")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        directory = Path(args.directory).resolve()
        if not directory.is_dir():
            raise UserError(f"version directory not found: {directory}")
        reviewer = parse_pairs(args.review_driven_pair)
        advisor = parse_pairs(args.author_advisor_pair)
        overlap = reviewer & advisor
        if overlap:
            raise UserError(f"stage pairs cannot have two drivers: {sorted(overlap)}")
        result = analyze(directory, args.paper_id, reviewer, advisor)
        output = private_output(Path(args.output) if args.output else directory / ".helicon/style/revision_direction.json")
        if args.write:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload = {**result, "output": str(output), "written": args.write}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UserError, style_fingerprint.UserError) as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
