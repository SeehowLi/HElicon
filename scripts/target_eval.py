#!/usr/bin/env python3
"""Evaluate a hold-out revision against its approved target."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
import sys
from typing import Any

import check_ai_tells
import extract_revision_direction
import latex_guard
import style_fingerprint

DISTANCE_METRICS = (
    "mean_sentence_length",
    "sentence_length_sd",
    "mean_paragraph_words",
    "paragraph_word_sd",
    "mean_sentences_per_paragraph",
    "alternation_index",
    "connective_density",
    "active_sentence_ratio",
    "passive_sentence_ratio",
    "first_person_per_1000_words",
    "hedges_per_1000_words",
)
TRAILER_RE = re.compile(
    r"^\[HElicon\] (?P<project>.+?) §(?P<section>.+?) · "
    r"(?P<passes>P[1-7](?:→P[1-7])*) · (?P<changes>\d+)处 · "
    r"frozen:(?P<frozen>0变化|\d+处告警) · "
    r"baseline:(?P<baseline>ok|thin\(n=\d+\)|none) · "
    r"target:(?P<target>ok|partial|none)"
    r"(?: · (?P<sample>sample:too-short))?(?: · (?P<upstream>⬆\d+ upstream))?$"
)


class UserError(Exception):
    """A concise command-line error."""


def ai_counts(path: Path) -> dict[str, int]:
    counts = Counter(item.rule for item in check_ai_tells.scan(path))
    return {str(rule): counts[rule] for rule in range(1, 15)}


def distances(before: dict[str, Any], output: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    before_normalized: list[float] = []
    output_normalized: list[float] = []
    unconverged: list[dict[str, str]] = []
    for metric in DISTANCE_METRICS:
        before_value = float(before[metric])
        output_value = float(output[metric])
        target_value = float(target[metric])
        original = abs(before_value - target_value)
        revised = abs(output_value - target_value)
        scale = max(abs(target_value), 1.0)
        before_normalized.append(original / scale)
        output_normalized.append(revised / scale)
        convergence = None if original == 0 else round((1 - revised / original) * 100, 4)
        if revised >= original and original > 0:
            relation = "unchanged" if revised == original else "farther"
            unconverged.append({
                "metric": metric,
                "possible_reason": (
                    f"the revision left this metric {relation} relative to v3; "
                    "the selected pass may not control this structural feature, or the hold-out sample may be too short"
                ),
            })
        rows[metric] = {
            "v1": before_value,
            "output": output_value,
            "v3": target_value,
            "v1_to_v3_distance": round(original, 6),
            "output_to_v3_distance": round(revised, 6),
            "convergence_percent": convergence,
        }
    initial = statistics.fmean(before_normalized)
    revised = statistics.fmean(output_normalized)
    aggregate = None if initial == 0 else round((1 - revised / initial) * 100, 4)
    return {
        "metrics": rows,
        "normalized_v1_to_v3_distance": round(initial, 6),
        "normalized_output_to_v3_distance": round(revised, 6),
        "aggregate_convergence_percent": aggregate,
        "unconverged_dimensions": unconverged,
    }


def alignment_summary(left: Path, right: Path) -> dict[str, int]:
    aligned = extract_revision_direction.align_paragraphs(
        extract_revision_direction.paragraphs(left),
        extract_revision_direction.paragraphs(right),
    )
    return dict(Counter(item["status"] for item in aligned))


def read_trailer(value: str | None, path: str | None) -> tuple[str, dict[str, str | None]]:
    trailer = value if value is not None else Path(path or "").read_text(encoding="utf-8").strip()
    match = TRAILER_RE.fullmatch(trailer)
    if not match:
        raise UserError(f"trailer does not match intent_router.md: {trailer!r}")
    return trailer, match.groupdict()


def normalized_paragraph(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_holdout(screening_path: Path, target_paragraphs: list[int], target_path: Path) -> dict[str, Any]:
    try:
        screening = json.loads(screening_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UserError(f"cannot read target screening {screening_path}: {exc}") from exc
    reserved = set(screening.get("holdout_target_paragraphs", []))
    requested = set(target_paragraphs)
    missing = sorted(requested - reserved)
    if missing:
        raise UserError(f"target paragraphs were not reserved from profile construction: {missing}")
    screened_target = Path(screening.get("target_file", "")).resolve()
    if not screened_target.is_file():
        raise UserError(f"screened full target is unavailable: {screened_target}")
    full_paragraphs = extract_revision_direction.paragraphs(screened_target)
    selected = [
        item["text"] for item in full_paragraphs if item["index"] in requested
    ]
    fragment = [item["text"] for item in extract_revision_direction.paragraphs(target_path)]
    if [normalized_paragraph(text) for text in selected] != [normalized_paragraph(text) for text in fragment]:
        raise UserError("target hold-out fragment does not exactly match the reserved paragraphs in the screened final version")
    decision_table = screening.get("decision_table", [])
    expected_target_status = "partial" if any(item.get("source") == "rule" for item in decision_table) else "ok"
    return {
        "verified": True,
        "screening": str(screening_path),
        "screened_target": str(screened_target),
        "target_paragraphs": sorted(requested),
        "fragment_matches_screened_target": True,
        "expected_target_status": expected_target_status,
    }


def private_output(path: Path) -> Path:
    resolved = path.resolve()
    lowered = tuple(part.casefold() for part in resolved.parts)
    if not any(left == ".helicon" and right == "style" for left, right in zip(lowered, lowered[1:])):
        raise UserError(f"target evaluation must stay under .helicon/style: {resolved}")
    return resolved


def evaluate(
    before_path: Path,
    output_path: Path,
    target_path: Path,
    glossary: Path | None,
    trailer: str,
    trailer_fields: dict[str, str | None],
    holdout: dict[str, Any],
) -> dict[str, Any]:
    for path in (before_path, output_path, target_path):
        if path.suffix.lower() != ".tex":
            raise UserError(f"hold-out evaluation requires .tex input for latex_guard.py: {path}")
    before = style_fingerprint.document_report(before_path)["document"]
    output = style_fingerprint.document_report(output_path)["document"]
    target = style_fingerprint.document_report(target_path)["document"]
    distance_report = distances(before, output, target)
    frozen = latex_guard.compare(before_path, output_path, glossary, set())
    expected_frozen = "0变化" if frozen["passed"] else f"{len(frozen['failed_categories'])}处告警"
    field_checks = {
        "project_present": bool(trailer_fields["project"]),
        "section_present": bool(trailer_fields["section"]),
        "pass_sequence_valid": True,
        "change_count_valid": int(trailer_fields["changes"] or "-1") >= 0,
        "frozen_consistent": trailer_fields["frozen"] == expected_frozen,
        "baseline_format_valid": True,
        "target_consistent": trailer_fields["target"] == holdout["expected_target_status"],
    }
    return {
        "schema": "helicon-target-eval-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "before": str(before_path),
        "output": str(output_path),
        "target": str(target_path),
        "holdout": holdout,
        "structural_distance": distance_report,
        "ai_tells_by_rule": {
            "v1": ai_counts(before_path),
            "output": ai_counts(output_path),
            "v3": ai_counts(target_path),
        },
        "frozen_set": frozen,
        "alignment": {
            "v1_to_v3": alignment_summary(before_path, target_path),
            "output_to_v3": alignment_summary(output_path, target_path),
        },
        "trailer": {
            "value": trailer,
            "matches_fixed_format": True,
            "fields": trailer_fields,
            "field_checks": field_checks,
            "all_fields_consistent": all(field_checks.values()),
        },
        "passed": (
            frozen["passed"]
            and distance_report["aggregate_convergence_percent"] is not None
            and distance_report["aggregate_convergence_percent"] > 0
            and all(field_checks.values())
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="private v1 hold-out .tex file")
    parser.add_argument("output", help="private HElicon revision .tex file")
    parser.add_argument("target", help="private v3 ground-truth .tex file")
    parser.add_argument("--screening", required=True, help="target_screening.json proving the target paragraphs were excluded")
    parser.add_argument("--target-paragraph", action="append", type=int, required=True, help="1-based target paragraph reserved from profile construction; repeat as needed")
    trailer = parser.add_mutually_exclusive_group(required=True)
    trailer.add_argument("--trailer", help="actual HElicon trailer")
    trailer.add_argument("--trailer-file", help="UTF-8 file containing the actual trailer")
    parser.add_argument("--glossary", help="optional Markdown or CSV glossary for latex_guard.py")
    parser.add_argument("--output-report", help="private .helicon/style/target_eval.json path")
    parser.add_argument("--write", action="store_true", help="write the private report")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        before = Path(args.before).resolve()
        output = Path(args.output).resolve()
        target = Path(args.target).resolve()
        for path in (before, output, target):
            if not path.is_file():
                raise UserError(f"hold-out file not found: {path}")
        screening = Path(args.screening).resolve()
        holdout = verify_holdout(screening, args.target_paragraph, target)
        trailer, trailer_fields = read_trailer(args.trailer, args.trailer_file)
        result = evaluate(
            before,
            output,
            target,
            Path(args.glossary).resolve() if args.glossary else None,
            trailer,
            trailer_fields,
            holdout,
        )
        report = private_output(Path(args.output_report) if args.output_report else before.parent / ".helicon/style/target_eval.json")
        if args.write:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload = {**result, "output_report": str(report), "written": args.write}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result["passed"] else 1
    except (OSError, UserError) as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
