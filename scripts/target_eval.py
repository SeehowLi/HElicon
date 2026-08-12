#!/usr/bin/env python3
"""Evaluate a private revision against a screened or author-approved target."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
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

APPROVED_TARGET_SCHEMA = "helicon-author-approved-style-target-v1"
APPROVED_TARGET_SOURCE = "author-approved-ai-assisted"
APPROVED_SCREENING_SCHEMA = "helicon-target-screening-v2"
EXECUTION_EVIDENCE_CLASSES = (
    "self-authored-fixture",
    "real-data",
    "independent-session",
)

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
PARAGRAPH_DISTANCE_METRICS = {
    "mean_paragraph_words",
    "paragraph_word_sd",
    "mean_sentences_per_paragraph",
}
DESCRIPTIVE_ONLY_METRICS = {
    "active_sentence_ratio": "redundant with passive_sentence_ratio for aggregate distance",
}
DIMENSION_DISTANCE_METRICS = {
    "sentence_length": {
        "mean_sentence_length",
        "sentence_length_sd",
        "alternation_index",
    },
    "paragraph_length": PARAGRAPH_DISTANCE_METRICS,
    "opening_structure": set(),
    "connectives": {"connective_density"},
    "active_passive_by_section": {
        "active_sentence_ratio",
        "passive_sentence_ratio",
    },
    "first_person": {"first_person_per_1000_words"},
    "hedging": {"hedges_per_1000_words"},
}
DIMENSION_PASS = {
    "sentence_length": "P4",
    "paragraph_length": "P4",
    "opening_structure": "P4",
    "connectives": "P5",
    "hedging": "P5",
    "active_passive_by_section": "P6",
    "first_person": "P6",
}
TRAILER_RE = re.compile(
    r"^\[HElicon\] (?P<project>.+?) §(?P<section>.+?) · "
    r"(?P<passes>P[1-7](?:[ \t]*→[ \t]*P[1-7])*) · (?P<changes>\d+)处 · "
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ai_tell_directional_distance(
    before: dict[str, int], output: dict[str, int], target: dict[str, int]
) -> dict[str, Any]:
    """Measure count convergence only for rules that distinguish before and target."""
    rows: dict[str, Any] = {}
    off_target_regressions: dict[str, Any] = {}
    initial_total = 0
    revised_total = 0
    for rule in sorted(before, key=int):
        initial = abs(before[rule] - target[rule])
        if initial == 0:
            if output[rule] != target[rule]:
                off_target_regressions[f"R{rule}"] = {
                    "before": before[rule],
                    "output": output[rule],
                    "approved_style_target": target[rule],
                }
            continue
        revised = abs(output[rule] - target[rule])
        initial_total += initial
        revised_total += revised
        rows[f"R{rule}"] = {
            "before": before[rule],
            "output": output[rule],
            "approved_style_target": target[rule],
            "before_to_target_l1": initial,
            "output_to_target_l1": revised,
        }
    if off_target_regressions:
        status = "worsened"
        convergence = (
            round((1 - revised_total / initial_total) * 100, 4)
            if rows else None
        )
        improved = False
    elif not rows:
        status = "insufficient_signal"
        convergence = None
        improved = None
    else:
        convergence = round((1 - revised_total / initial_total) * 100, 4)
        status = "improved" if revised_total < initial_total else (
            "unchanged" if revised_total == initial_total else "worsened"
        )
        improved = status == "improved"
    return {
        "method": "L1 count distance on rule IDs where before and approved target differ",
        "eligible_rule_ids": list(rows),
        "per_rule": rows,
        "off_target_regressions": off_target_regressions,
        "before_to_target_l1": initial_total if rows else None,
        "output_to_target_l1": revised_total if rows else None,
        "convergence_percent": convergence,
        "status": status,
        "directional_improvement": improved,
        "separate_from_structural_convergence": True,
    }


def distance_eligibility(
    before: dict[str, Any],
    output: dict[str, Any],
    target: dict[str, Any],
    rule_sourced_dimensions: set[str],
    active_passes: set[str],
) -> dict[str, dict[str, Any]]:
    """Return an explicit mask for metrics eligible for aggregate distance."""
    reasons: dict[str, list[str]] = {metric: [] for metric in DISTANCE_METRICS}
    for metric, reason in DESCRIPTIVE_ONLY_METRICS.items():
        reasons[metric].append(reason)
    if any(int(report.get("paragraph_count", 0)) < 2 for report in (before, output, target)):
        for metric in PARAGRAPH_DISTANCE_METRICS:
            reasons[metric].append("fewer than 2 paragraphs in at least one compared fragment")
    for dimension in sorted(rule_sourced_dimensions):
        for metric in DIMENSION_DISTANCE_METRICS.get(dimension, set()):
            reasons[metric].append(f"target screening uses source=rule for {dimension}")
    for dimension, owner in DIMENSION_PASS.items():
        if owner in active_passes:
            continue
        for metric in DIMENSION_DISTANCE_METRICS.get(dimension, set()):
            reasons[metric].append(f"{owner} does not appear in the actual routed pass sequence")
    return {
        metric: {
            "eligible": not reasons[metric],
            "reasons": reasons[metric],
            "descriptive_only": metric in DESCRIPTIVE_ONLY_METRICS,
            "redundant_with": "passive_sentence_ratio" if metric == "active_sentence_ratio" else None,
        }
        for metric in DISTANCE_METRICS
    }


def distances(
    before: dict[str, Any],
    output: dict[str, Any],
    target: dict[str, Any],
    eligibility: dict[str, dict[str, Any]] | None = None,
    approved_style_target: bool = False,
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    before_normalized: list[float] = []
    output_normalized: list[float] = []
    unconverged: list[dict[str, Any]] = []
    eligibility = eligibility or {
        metric: {
            "eligible": metric not in DESCRIPTIVE_ONLY_METRICS,
            "reasons": ([DESCRIPTIVE_ONLY_METRICS[metric]] if metric in DESCRIPTIVE_ONLY_METRICS else []),
            "descriptive_only": metric in DESCRIPTIVE_ONLY_METRICS,
            "redundant_with": "passive_sentence_ratio" if metric == "active_sentence_ratio" else None,
        }
        for metric in DISTANCE_METRICS
    }
    for metric in DISTANCE_METRICS:
        before_value = float(before[metric])
        output_value = float(output[metric])
        target_value = float(target[metric])
        original = abs(before_value - target_value)
        revised = abs(output_value - target_value)
        scale = max(abs(target_value), 1.0)
        metric_mask = eligibility[metric]
        if metric_mask["eligible"]:
            before_normalized.append(original / scale)
            output_normalized.append(revised / scale)
        convergence = None if original == 0 else round((1 - revised / original) * 100, 4)
        if original == 0 and revised > 0:
            status = "diverged_from_exact_match"
            unconverged.append({
                "metric": metric,
                "status": status,
                "aggregation_eligible": metric_mask["eligible"],
                "possible_reason": (
                    "the original already matched the target exactly on this metric, but the revision moved away"
                ),
            })
        elif original == 0:
            status = "exact_match_preserved"
        elif revised < original:
            status = "closer"
        elif revised == original:
            status = "unchanged"
        else:
            status = "farther"
        if metric_mask["eligible"] and revised >= original and original > 0:
            relation = "unchanged" if revised == original else "farther"
            unconverged.append({
                "metric": metric,
                "status": status,
                "aggregation_eligible": True,
                "possible_reason": (
                    f"the revision left this metric {relation} relative to "
                    f"{'the approved style-only target' if approved_style_target else 'v3'}; "
                    "the selected pass may not control this structural feature, or the hold-out sample may be too short"
                ),
            })
        row = {
            "output": output_value,
            "convergence_percent": convergence,
            "status": status,
            "aggregation_eligible": metric_mask["eligible"],
            "exclusion_reasons": metric_mask["reasons"],
            "descriptive_only": metric_mask["descriptive_only"],
            "redundant_with": metric_mask["redundant_with"],
        }
        if approved_style_target:
            row.update({
                "before": before_value,
                "approved_style_target": target_value,
                "before_to_approved_style_target_distance": round(original, 6),
                "output_to_approved_style_target_distance": round(revised, 6),
            })
        else:
            row.update({
                "v1": before_value,
                "v3": target_value,
                "v1_to_v3_distance": round(original, 6),
                "output_to_v3_distance": round(revised, 6),
            })
        rows[metric] = row
    initial = statistics.fmean(before_normalized) if before_normalized else None
    revised = statistics.fmean(output_normalized) if output_normalized else None
    aggregate = None if initial in (None, 0) else round((1 - revised / initial) * 100, 4)
    eligible_metrics = [metric for metric in DISTANCE_METRICS if eligibility[metric]["eligible"]]
    excluded_metrics = [metric for metric in DISTANCE_METRICS if not eligibility[metric]["eligible"]]
    aggregate_candidates = len(DISTANCE_METRICS) - len(DESCRIPTIVE_ONLY_METRICS)
    result = {
        "metrics": rows,
        "eligible_metrics": eligible_metrics,
        "excluded_metrics": excluded_metrics,
        "eligibility_mask": {
            metric: eligibility[metric]["eligible"] for metric in DISTANCE_METRICS
        },
        "exclusion_reasons": {
            metric: eligibility[metric]["reasons"] for metric in excluded_metrics
        },
        "coverage": {
            "eligible_metric_count": len(eligible_metrics),
            "aggregate_candidate_count": aggregate_candidates,
            "all_reported_metric_count": len(DISTANCE_METRICS),
            "eligible_fraction": round(len(eligible_metrics) / aggregate_candidates, 4),
        },
        "descriptive_only": sorted(DESCRIPTIVE_ONLY_METRICS),
        "aggregate_convergence_percent": aggregate,
        "unconverged_dimensions": unconverged,
    }
    if approved_style_target:
        result.update({
            "target_role": "author-approved-style-only-target",
            "normalized_before_to_target_distance": round(initial, 6) if initial is not None else None,
            "normalized_output_to_target_distance": round(revised, 6) if revised is not None else None,
        })
    else:
        result.update({
            "normalized_v1_to_v3_distance": round(initial, 6) if initial is not None else None,
            "normalized_output_to_v3_distance": round(revised, 6) if revised is not None else None,
        })
    return result


def alignment_summary(left: Path, right: Path) -> dict[str, int]:
    aligned = extract_revision_direction.align_paragraphs(
        extract_revision_direction.paragraphs(left),
        extract_revision_direction.paragraphs(right),
    )
    return dict(Counter(item["status"] for item in aligned))


def paragraph_similarity(left: Path, right: Path) -> dict[str, Any]:
    """Return sanitized difflib similarity statistics without retaining prose."""
    aligned = extract_revision_direction.align_paragraphs(
        extract_revision_direction.paragraphs(left),
        extract_revision_direction.paragraphs(right),
    )
    similarities = [float(item["similarity"]) for item in aligned]
    return {
        "method": "difflib paragraph alignment; descriptive only; no acceptance threshold",
        "aligned_item_count": len(similarities),
        "mean_similarity": round(statistics.fmean(similarities), 4) if similarities else None,
        "minimum_similarity": round(min(similarities), 4) if similarities else None,
        "maximum_similarity": round(max(similarities), 4) if similarities else None,
    }


def read_trailer(value: str | None, path: str | None) -> tuple[str, dict[str, str | None]]:
    trailer = value if value is not None else Path(path or "").read_text(encoding="utf-8").strip()
    match = TRAILER_RE.fullmatch(trailer)
    if not match:
        raise UserError(f"trailer does not match intent_router.md: {trailer!r}")
    fields = match.groupdict()
    fields["passes"] = re.sub(r"[ \t]*→[ \t]*", "→", fields["passes"] or "")
    return trailer, fields


def normalized_paragraph(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def screening_route_sources(screening: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(screening, dict):
        raise UserError("target screening JSON root must be an object")
    decision_table = screening.get("decision_table", [])
    if not isinstance(decision_table, list) or any(
        not isinstance(item, dict) for item in decision_table
    ):
        raise UserError("target screening decision_table must be a list of objects")
    rule_sourced_dimensions = sorted({
        str(item.get("dimension"))
        for item in decision_table
        if item.get("source") == "rule" and item.get("dimension")
    })
    dimension_sources = {
        str(item.get("dimension")): str(item.get("source"))
        for item in decision_table
        if item.get("dimension") and item.get("source") in {"exemplar", "rule"}
    }
    return {
        "expected_target_status": "partial" if rule_sourced_dimensions else "ok",
        "rule_sourced_dimensions": rule_sourced_dimensions,
        "dimension_sources": dimension_sources,
    }


def approved_screening_route_sources(screening: dict[str, Any]) -> dict[str, Any]:
    """Validate the field-source contract used by an approved style target."""
    route_sources = screening_route_sources(screening)
    if screening.get("schema") != APPROVED_SCREENING_SCHEMA:
        raise UserError(
            f"author-approved target requires {APPROVED_SCREENING_SCHEMA} screening"
        )
    decision_table = screening.get("decision_table")
    if not isinstance(decision_table, list):
        raise UserError("author-approved target screening requires a decision_table list")
    for dimension in DIMENSION_PASS:
        entries = [
            item for item in decision_table
            if isinstance(item, dict) and item.get("dimension") == dimension
        ]
        if len(entries) != 1:
            raise UserError(
                f"author-approved target screening requires exactly one source for {dimension}"
            )
        if entries[0].get("source") not in {"exemplar", "rule"}:
            raise UserError(
                f"author-approved target screening has invalid source for {dimension}"
            )
    return route_sources


def verify_holdout(screening_path: Path, target_paragraphs: list[int], target_path: Path) -> dict[str, Any]:
    try:
        screening = json.loads(screening_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UserError(f"cannot read target screening {screening_path}: {exc}") from exc
    if not isinstance(screening, dict):
        raise UserError("target screening JSON root must be an object")
    if screening.get("schema") != APPROVED_SCREENING_SCHEMA:
        raise UserError(f"target hold-out requires {APPROVED_SCREENING_SCHEMA} screening")
    reserved_values = screening.get("holdout_target_paragraphs")
    if not isinstance(reserved_values, list) or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 1
        for value in reserved_values
    ):
        raise UserError("holdout_target_paragraphs must be a list of positive integers")
    if any(value < 1 for value in target_paragraphs):
        raise UserError("--target-paragraph values must be positive integers")
    target_file = screening.get("target_file")
    if not isinstance(target_file, str) or not target_file.strip():
        raise UserError("target screening target_file must be a non-empty string")
    reserved = set(reserved_values)
    requested = set(target_paragraphs)
    missing = sorted(requested - reserved)
    if missing:
        raise UserError(f"target paragraphs were not reserved from profile construction: {missing}")
    screened_target = Path(target_file).resolve()
    if not screened_target.is_file():
        raise UserError(f"screened full target is unavailable: {screened_target}")
    full_paragraphs = extract_revision_direction.paragraphs(screened_target)
    selected = [
        item["text"] for item in full_paragraphs if item["index"] in requested
    ]
    fragment = [item["text"] for item in extract_revision_direction.paragraphs(target_path)]
    if [normalized_paragraph(text) for text in selected] != [normalized_paragraph(text) for text in fragment]:
        raise UserError("target hold-out fragment does not exactly match the reserved paragraphs in the screened final version")
    route_sources = screening_route_sources(screening)
    return {
        "verified": True,
        "admission_kind": "screened-final-version-holdout",
        "screening": str(screening_path),
        "screened_target": str(screened_target),
        "target_paragraphs": sorted(requested),
        "fragment_matches_screened_target": True,
        **route_sources,
    }


def private_output(path: Path) -> Path:
    resolved = path.resolve()
    lowered = tuple(part.casefold() for part in resolved.parts)
    if not any(left == ".helicon" and right == "style" for left, right in zip(lowered, lowered[1:])):
        raise UserError(f"target evaluation must stay under .helicon/style: {resolved}")
    return resolved


def canonical_text(path: Path) -> str:
    """Normalize line endings and ignore at most one terminal newline."""
    text = style_fingerprint.read_utf8(path).replace("\r\n", "\n").replace("\r", "\n")
    return text[:-1] if text.endswith("\n") else text


def verify_author_approved_target(
    screening_path: Path,
    manifest_path: Path,
    before_path: Path,
    target_path: Path,
    glossary: Path | None,
) -> dict[str, Any]:
    """Admit a human-approved style-only target without claiming it is a v3 hold-out."""
    private_output(manifest_path)
    try:
        screening = json.loads(screening_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UserError(f"cannot read author-approved target provenance: {exc}") from exc
    if not isinstance(screening, dict):
        raise UserError("target screening JSON root must be an object")
    if not isinstance(manifest, dict):
        raise UserError("author-approved target manifest JSON root must be an object")

    required = {
        "schema": APPROVED_TARGET_SCHEMA,
        "source": APPROVED_TARGET_SOURCE,
        "approval_status": "approved",
        "content_stable_confirmed": True,
    }
    mismatched = {
        key: {"expected": expected, "actual": manifest.get(key)}
        for key, expected in required.items()
        if manifest.get(key) != expected
    }
    if manifest.get("content_stable_confirmed") is not True:
        mismatched["content_stable_confirmed"] = {
            "expected": True,
            "actual": manifest.get("content_stable_confirmed"),
        }
    if mismatched:
        raise UserError(f"author-approved target manifest is not admissible: {mismatched}")

    approved_utc = manifest.get("approved_utc")
    try:
        parsed_approval = datetime.fromisoformat(str(approved_utc).replace("Z", "+00:00"))
    except ValueError as exc:
        raise UserError("author-approved target manifest has an invalid approved_utc") from exc
    if parsed_approval.tzinfo is None:
        raise UserError("author-approved target approved_utc must include a timezone")

    actual_hashes = {
        "before_sha256": sha256_file(before_path),
        "target_sha256": sha256_file(target_path),
        "screening_sha256": sha256_file(screening_path),
    }
    hash_mismatches = {
        key: {"expected": actual, "actual": manifest.get(key)}
        for key, actual in actual_hashes.items()
        if manifest.get(key) != actual
    }
    if hash_mismatches:
        raise UserError(f"author-approved target hash mismatch: {hash_mismatches}")
    if canonical_text(before_path) == canonical_text(target_path):
        raise UserError("author-approved style-only target must differ from before; use preservation mode otherwise")

    guard = latex_guard.compare(before_path, target_path, glossary, set())
    if not guard["passed"]:
        raise UserError(
            "author-approved style-only target changes immutable content: "
            + ", ".join(guard["failed_categories"])
        )

    return {
        "verified": True,
        "admission_kind": "author-approved-style-only-target",
        "screening": str(screening_path),
        "target_paragraphs": [],
        "fragment_matches_screened_target": False,
        "content_stable_confirmed": True,
        **approved_screening_route_sources(screening),
        "target_provenance": {
            "source": APPROVED_TARGET_SOURCE,
            "approval_status": "approved",
            "approved_utc": approved_utc,
            "manifest": str(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            **actual_hashes,
            "screened_final_version_holdout": False,
            "before_to_target_guard": {
                "check": "latex_guard",
                "passed": True,
                "failed_categories": [],
            },
        },
    }


def routed_target_contract(
    trailer_fields: dict[str, str | None], holdout: dict[str, Any]
) -> dict[str, Any]:
    active_passes = set((trailer_fields.get("passes") or "").split("→"))
    routed_dimensions = sorted(
        dimension
        for dimension, owner in DIMENSION_PASS.items()
        if owner in active_passes
    )
    dimension_sources = holdout.get("dimension_sources", {})
    if not routed_dimensions:
        expected_target_status = "none"
    elif dimension_sources:
        expected_target_status = (
            "partial"
            if any(dimension_sources.get(dimension) == "rule" for dimension in routed_dimensions)
            else "ok"
        )
    else:
        expected_target_status = holdout["expected_target_status"]
    return {
        "active_passes": sorted(active_passes),
        "routed_dimensions": routed_dimensions,
        "expected_target_status": expected_target_status,
    }


def evaluate_preservation(
    before_path: Path,
    output_path: Path,
    target_path: Path,
    glossary: Path | None,
    trailer: str,
    trailer_fields: dict[str, str | None],
    holdout: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate do-no-harm behavior when the input already equals the target."""
    for path in (before_path, output_path, target_path):
        if path.suffix.lower() not in style_fingerprint.EXTENSIONS:
            allowed = ", ".join(sorted(style_fingerprint.EXTENSIONS))
            raise UserError(f"hold-out evaluation requires one of {allowed}: {path}")
    before_text = canonical_text(before_path)
    target_text = canonical_text(target_path)
    if before_text != target_text:
        raise UserError("preservation mode requires canonical(before) == canonical(target)")

    output_text = canonical_text(output_path)
    exact_preserved = output_text == before_text
    frozen = latex_guard.compare(before_path, output_path, glossary, set())
    target_contract = routed_target_contract(trailer_fields, holdout)
    field_checks = {
        "project_present": bool(trailer_fields["project"]),
        "section_present": bool(trailer_fields["section"]),
        "pass_sequence_valid": True,
        "change_count_zero": trailer_fields["changes"] == "0",
        "frozen_zero": trailer_fields["frozen"] == "0变化",
        "frozen_consistent": trailer_fields["frozen"]
        == ("0变化" if frozen["passed"] else f"{len(frozen['failed_categories'])}处告警"),
        "baseline_format_valid": True,
        "target_consistent": trailer_fields["target"]
        == target_contract["expected_target_status"],
    }
    preservation_passed = exact_preserved and frozen["passed"] and all(field_checks.values())
    return {
        "schema": "helicon-target-preservation-eval-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "preservation",
        "before": str(before_path),
        "output": str(output_path),
        "target": str(target_path),
        "holdout": holdout,
        "admission": {
            "canonical_before_equals_target": True,
            "whole_paragraph_holdout_verified": bool(holdout.get("verified", False)),
        },
        "exact_preservation": {
            "passed": exact_preserved,
            "canonical_output_equals_before": exact_preserved,
            "byte_output_equals_before": output_path.read_bytes() == before_path.read_bytes(),
            "byte_before_equals_target": before_path.read_bytes() == target_path.read_bytes(),
            "byte_equality_is_descriptive": True,
        },
        "frozen_set": frozen,
        "target_contract": target_contract,
        "structural_distance": {
            "mode": "preservation",
            "aggregate_convergence_percent": None,
            "reason": "directional convergence is undefined because canonical(before) equals canonical(target)",
        },
        "trailer": {
            "value": trailer,
            "matches_fixed_format": True,
            "fields": trailer_fields,
            "field_checks": field_checks,
            "all_fields_consistent": all(field_checks.values()),
        },
        "contract_checks_passed": preservation_passed,
        "evaluation_valid": True,
        "directional_improvement": None,
        "preservation_passed": preservation_passed,
        "passed": preservation_passed,
    }


def evaluate(
    before_path: Path,
    output_path: Path,
    target_path: Path,
    glossary: Path | None,
    trailer: str,
    trailer_fields: dict[str, str | None],
    holdout: dict[str, Any],
    content_stable_confirmed: bool = False,
) -> dict[str, Any]:
    for path in (before_path, output_path, target_path):
        if path.suffix.lower() not in style_fingerprint.EXTENSIONS:
            allowed = ", ".join(sorted(style_fingerprint.EXTENSIONS))
            raise UserError(f"hold-out evaluation requires one of {allowed}: {path}")
    before = style_fingerprint.document_report(before_path)["document"]
    output = style_fingerprint.document_report(output_path)["document"]
    target = style_fingerprint.document_report(target_path)["document"]
    approved_style_target = (
        holdout.get("admission_kind") == "author-approved-style-only-target"
    )
    target_contract = routed_target_contract(trailer_fields, holdout)
    active_passes = set(target_contract["active_passes"])
    routed_dimensions = target_contract["routed_dimensions"]
    expected_target_status = target_contract["expected_target_status"]
    eligibility = distance_eligibility(
        before,
        output,
        target,
        set(holdout.get("rule_sourced_dimensions", [])),
        active_passes,
    )
    distance_report = distances(
        before, output, target, eligibility, approved_style_target
    )
    frozen = latex_guard.compare(before_path, output_path, glossary, set())
    ground_truth_guard = latex_guard.compare(before_path, target_path, glossary, set())
    ground_truth_compatibility = {
        "check": "latex_guard",
        "passed": ground_truth_guard["passed"],
        "failed_categories": ground_truth_guard["failed_categories"],
        "content_stable_confirmed": content_stable_confirmed,
        "paragraph_similarity": paragraph_similarity(before_path, target_path),
        "efficacy_claim_allowed": ground_truth_guard["passed"] and content_stable_confirmed,
    }
    if not ground_truth_guard["passed"]:
        ground_truth_compatibility["interpretation"] = "content-confounded: immutable before/target items differ"
    elif not content_stable_confirmed:
        ground_truth_compatibility["interpretation"] = "content stability requires explicit human confirmation"
    else:
        ground_truth_compatibility["interpretation"] = (
            "eligible author-approved style-only target"
            if approved_style_target
            else "eligible for a directional efficacy claim"
        )
    expected_frozen = "0变化" if frozen["passed"] else f"{len(frozen['failed_categories'])}处告警"
    field_checks = {
        "project_present": bool(trailer_fields["project"]),
        "section_present": bool(trailer_fields["section"]),
        "pass_sequence_valid": True,
        "change_count_valid": int(trailer_fields["changes"] or "-1") >= 0,
        "frozen_consistent": trailer_fields["frozen"] == expected_frozen,
        "baseline_format_valid": True,
        "target_consistent": trailer_fields["target"] == expected_target_status,
    }
    contract_checks_passed = frozen["passed"] and all(field_checks.values())
    aggregate = distance_report["aggregate_convergence_percent"]
    evaluation_valid = contract_checks_passed and ground_truth_compatibility["efficacy_claim_allowed"]
    before_ai = ai_counts(before_path)
    output_ai = ai_counts(output_path)
    target_ai = ai_counts(target_path)
    if approved_style_target:
        ai_tells = {
            "before": before_ai,
            "output": output_ai,
            "approved_style_target": target_ai,
        }
        rule_distance = ai_tell_directional_distance(before_ai, output_ai, target_ai)
        if aggregate is None:
            initial_distance = distance_report["normalized_before_to_target_distance"]
            revised_distance = distance_report["normalized_output_to_target_distance"]
            structural_status = (
                "worsened"
                if initial_distance == 0 and revised_distance not in (None, 0)
                else "insufficient_signal"
            )
        else:
            structural_status = (
                "improved" if aggregate > 0 else (
                    "unchanged" if aggregate == 0 else "worsened"
                )
            )
        channel_statuses = {structural_status, rule_distance["status"]}
        if "worsened" in channel_statuses:
            overall_status = "mixed_or_worsened" if "improved" in channel_statuses else "not_improved"
        elif "improved" in channel_statuses:
            overall_status = "improved"
        elif channel_statuses == {"insufficient_signal"}:
            overall_status = "insufficient_evidence"
        else:
            overall_status = "not_improved"
        directional_improvement: bool | None = (
            True if overall_status == "improved" else (
                None if overall_status == "insufficient_evidence" else False
            )
        )
        directional_evidence = {
            "structural": {
                "status": structural_status,
                "aggregate_convergence_percent": aggregate,
                "eligible_metrics": distance_report["eligible_metrics"],
                "excluded_metrics": distance_report["excluded_metrics"],
            },
            "ai_tell_rule_distance": rule_distance,
            "overall_status": overall_status,
            "decision_rule": (
                "at least one measured channel improves and no measured channel worsens; "
                "insufficient structural signal never becomes a fabricated structural percentage"
            ),
        }
    else:
        ai_tells = {"v1": before_ai, "output": output_ai, "v3": target_ai}
        directional_evidence = None
        directional_improvement = aggregate is not None and aggregate > 0

    admission_field = (
        {"target_admission": holdout}
        if approved_style_target
        else {"holdout": holdout}
    )
    alignment = (
        {
            "before_to_approved_style_target": alignment_summary(before_path, target_path),
            "output_to_approved_style_target": alignment_summary(output_path, target_path),
        }
        if approved_style_target
        else {
            "v1_to_v3": alignment_summary(before_path, target_path),
            "output_to_v3": alignment_summary(output_path, target_path),
        }
    )
    result = {
        "schema": (
            "helicon-author-approved-target-eval-v1"
            if approved_style_target
            else "helicon-target-eval-v2"
        ),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "before": str(before_path),
        "output": str(output_path),
        "target": str(target_path),
        **admission_field,
        "target_contract": target_contract,
        "structural_distance": distance_report,
        "ai_tells_by_rule": ai_tells,
        "frozen_set": frozen,
        "ground_truth_compatibility": ground_truth_compatibility,
        "efficacy_claim_allowed": ground_truth_compatibility["efficacy_claim_allowed"],
        "descriptive_only": not evaluation_valid,
        "alignment": alignment,
        "trailer": {
            "value": trailer,
            "matches_fixed_format": True,
            "fields": trailer_fields,
            "field_checks": field_checks,
            "all_fields_consistent": all(field_checks.values()),
        },
        "contract_checks_passed": contract_checks_passed,
        "evaluation_valid": evaluation_valid,
        "directional_improvement": directional_improvement,
        "passed": bool(evaluation_valid and directional_improvement is True),
    }
    if approved_style_target:
        result["target_provenance"] = holdout["target_provenance"]
        result["directional_evidence"] = directional_evidence
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("directional", "preservation"),
        default="directional",
        help="evaluation contract; directional remains the default",
    )
    parser.add_argument("before", help="private before fragment in .tex, .md, or .txt")
    parser.add_argument("output", help="private HElicon revision .tex, .md, or .txt file")
    parser.add_argument("target", help="private screened-v3 hold-out or manifest-bound style target")
    parser.add_argument("--screening", required=True, help="target_screening.json supplying routed field sources and target status")
    parser.add_argument("--target-paragraph", action="append", type=int, help="1-based v3 paragraph reserved from profile construction; repeat as needed")
    parser.add_argument(
        "--approval-manifest",
        help=(
            "private author-approved style-only target manifest; mutually exclusive with "
            "--target-paragraph and directional mode only"
        ),
    )
    trailer = parser.add_mutually_exclusive_group(required=True)
    trailer.add_argument("--trailer", help="actual HElicon trailer")
    trailer.add_argument("--trailer-file", help="UTF-8 file containing the actual trailer")
    parser.add_argument("--glossary", help="optional Markdown or CSV glossary for latex_guard.py")
    parser.add_argument(
        "--content-stable-confirmed",
        action="store_true",
        help="confirm that before and target express the same intended content; required before efficacy claims",
    )
    parser.add_argument("--output-report", help="private .helicon/style/target_eval.json path")
    parser.add_argument(
        "--execution-evidence-class",
        choices=EXECUTION_EVIDENCE_CLASSES,
        help="provenance of this evaluation execution only; never changes target authorship",
    )
    parser.add_argument("--write", action="store_true", help="write the private report")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def result_exit_code(result: dict[str, Any]) -> int:
    """Map a valid evaluation result to its stable CLI exit code."""
    return 0 if result["passed"] else 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
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
        trailer, trailer_fields = read_trailer(args.trailer, args.trailer_file)
        glossary = Path(args.glossary).resolve() if args.glossary else None
        if bool(args.target_paragraph) == bool(args.approval_manifest):
            raise UserError("choose exactly one target admission: --target-paragraph or --approval-manifest")
        if args.approval_manifest:
            if args.mode != "directional":
                raise UserError("--approval-manifest is available only in directional mode")
            holdout = verify_author_approved_target(
                screening,
                Path(args.approval_manifest).resolve(),
                before,
                target,
                glossary,
            )
        else:
            holdout = verify_holdout(screening, args.target_paragraph or [], target)
        if args.mode == "preservation":
            result = evaluate_preservation(
                before,
                output,
                target,
                glossary,
                trailer,
                trailer_fields,
                holdout,
            )
        else:
            result = evaluate(
                before,
                output,
                target,
                glossary,
                trailer,
                trailer_fields,
                holdout,
                args.content_stable_confirmed
                or bool(holdout.get("content_stable_confirmed", False)),
            )
        if args.execution_evidence_class:
            result["execution_provenance"] = {
                "evidence_class": args.execution_evidence_class,
                "scope": "evaluation execution only; does not change target source or approval provenance",
            }
        report = private_output(Path(args.output_report) if args.output_report else before.parent / ".helicon/style/target_eval.json")
        if args.write:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload = {**result, "output_report": str(report), "written": args.write}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return result_exit_code(result)
    except (
        OSError,
        UserError,
        style_fingerprint.UserError,
        extract_revision_direction.UserError,
        latex_guard.UserError,
    ) as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
