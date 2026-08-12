#!/usr/bin/env python3
"""Decide whether a fragment needs P4/P5 revision without exposing prose or targets."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_ai_tells
import build_target_profile
import resolve_target_profile
import style_fingerprint


EXTENSIONS = {".tex", ".md", ".txt"}
PASSES = ("P4", "P5")
OUTPUT_SCHEMA = "helicon-revision-preflight-v1"
PRODUCER = "scripts/revision_preflight.py"
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$", re.ASCII)
RULE_SENTENCE_MEAN_RANGE = (12.0, 30.0)
RULE_SENTENCE_SD_MIN = 4.0
RULE_CONNECTIVE_DENSITY_MAX = 0.6


class UserError(Exception):
    """A concise command-line error."""


def numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def numeric_range(value: Any, keys: Iterable[str]) -> tuple[float, float] | None:
    if not isinstance(value, dict):
        return None
    for key in keys:
        raw = value.get(key)
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            continue
        lower, upper = numeric(raw[0]), numeric(raw[1])
        if lower is not None and upper is not None and lower <= upper:
            return lower, upper
    return None


def numeric_member(value: Any, keys: Iterable[str]) -> float | None:
    if not isinstance(value, dict):
        return None
    for key in keys:
        result = numeric(value.get(key))
        if result is not None:
            return result
    return None


def upper_bound(value: Any, scalar_keys: Iterable[str], range_keys: Iterable[str] = ()) -> float | None:
    scalar = numeric_member(value, scalar_keys)
    if scalar is not None:
        return scalar
    pair = numeric_range(value, range_keys)
    return pair[1] if pair is not None else None


def validate_fragment(path: Path) -> Path:
    if not path.exists():
        raise UserError("fragment file not found")
    if not path.is_file():
        raise UserError("fragment must be one .tex, .md, or .txt file")
    if path.suffix.lower() not in EXTENSIONS:
        raise UserError("unsupported fragment type; expected .tex, .md, or .txt")
    return path.resolve()


def fragment_sha256(path: Path) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise UserError(f"cannot hash fragment: {exc}") from exc
    return f"sha256:{digest}"


def load_target(
    helicon: Path, passes: list[str], section_type: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profile_path = helicon / "style" / "target_profile.json"
    if not profile_path.is_file():
        fields = [
            {
                "id": field_id,
                "pass": pass_id,
                "source": "rule",
                "confidence": "medium",
                "eligible": True,
                "exclusion_reason": None,
                "value": build_target_profile.RULE_VALUES[field_id],
            }
            for pass_id in passes
            for field_id in resolve_target_profile.PASS_FIELDS[pass_id]
        ]
        return {"status": "none", "schema": None, "profile_sha256": None}, fields

    profile, profile_hash = resolve_target_profile.read_profile(profile_path)
    target_venue = resolve_target_profile.project_target_venue(helicon / "project.yaml")
    selected_venue, venue_match = resolve_target_profile.select_venue(profile, target_venue)
    fields, all_exemplar = resolve_target_profile.resolve_fields(
        profile, selected_venue, passes, section_type
    )
    any_eligible = any(field["eligible"] for field in fields)
    legacy_profile = profile["schema"] != resolve_target_profile.CURRENT_SCHEMA
    status = (
        "ok"
        if venue_match is True and all_exemplar and any_eligible and not legacy_profile
        else "partial"
    )
    return {
        "status": status,
        "schema": profile["schema"],
        "profile_sha256": profile_hash,
    }, fields


def evaluate_p4(
    fields: dict[str, dict[str, Any]], metrics: dict[str, Any]
) -> tuple[set[str], set[str]]:
    evaluated: set[str] = set()
    triggers: set[str] = set()
    sentence_count = int(metrics["sentence_count"])
    paragraph_count = int(metrics["paragraph_count"])

    field = fields.get("sentence_length")
    if field is not None and sentence_count >= 4:
        value = field["value"]
        if field["source"] == "rule":
            mean_range = numeric_range(value, ("mean_range_words",)) or RULE_SENTENCE_MEAN_RANGE
            minimum_sd = numeric_member(value, ("minimum_sd_words",))
            if minimum_sd is None:
                minimum_sd = RULE_SENTENCE_SD_MIN
            evaluated.add("sentence_length")
            mean = float(metrics["mean_sentence_length"])
            if not mean_range[0] <= mean <= mean_range[1]:
                triggers.add("P4_RULE_SENTENCE_MEAN_OUT_OF_RANGE")
            opening_type_count = sum(bool(count) for count in metrics["opening_types"].values())
            if float(metrics["sentence_length_sd"]) < minimum_sd and opening_type_count <= 1:
                triggers.add("P4_RULE_SENTENCE_SD_LOW")
        else:
            mean_range = numeric_range(value, ("mean_range_words", "mean_sentence_length_range"))
            minimum_sd = numeric_member(value, ("minimum_sd_words", "minimum_sentence_length_sd"))
            if mean_range is not None:
                evaluated.add("sentence_length")
                mean = float(metrics["mean_sentence_length"])
                if not mean_range[0] <= mean <= mean_range[1]:
                    triggers.add("P4_TARGET_SENTENCE_MEAN_OUT_OF_RANGE")
            if minimum_sd is not None:
                evaluated.add("sentence_length")
                opening_type_count = sum(bool(count) for count in metrics["opening_types"].values())
                if float(metrics["sentence_length_sd"]) < minimum_sd and opening_type_count <= 1:
                    triggers.add("P4_TARGET_SENTENCE_SD_LOW")

    field = fields.get("paragraph_length")
    if field is not None and paragraph_count > 1:
        value = field["value"]
        word_range = numeric_range(value, ("word_range", "mean_word_range"))
        sentence_range = numeric_range(
            value, ("sentences_per_paragraph", "mean_sentences_per_paragraph_range")
        )
        if word_range is not None:
            evaluated.add("paragraph_length")
            mean_words = float(metrics["mean_paragraph_words"])
            if not word_range[0] <= mean_words <= word_range[1]:
                triggers.add("P4_PARAGRAPH_WORDS_OUT_OF_RANGE")
        if sentence_range is not None:
            evaluated.add("paragraph_length")
            mean_sentences = float(metrics["mean_sentences_per_paragraph"])
            if not sentence_range[0] <= mean_sentences <= sentence_range[1]:
                triggers.add("P4_PARAGRAPH_SENTENCES_OUT_OF_RANGE")

    field = fields.get("opening_structure")
    if field is not None and paragraph_count > 1:
        minimum_types = numeric_member(field["value"], ("minimum_distinct_types",))
        if minimum_types is not None:
            evaluated.add("opening_structure")
            observed = sum(bool(count) for count in metrics["paragraph_opening_types"].values())
            if observed < minimum_types:
                triggers.add("P4_OPENING_DIVERSITY_LOW")

    return evaluated, triggers


def evaluate_p5(
    fields: dict[str, dict[str, Any]], metrics: dict[str, Any], findings: list[Any]
) -> tuple[set[str], set[str]]:
    evaluated: set[str] = set()
    triggers = {f"P5_AI_R{finding.rule:02d}" for finding in findings}

    field = fields.get("connectives")
    if field is not None:
        limit = upper_bound(
            field["value"],
            ("maximum_per_sentence", "max_per_sentence", "density_upper_bound"),
            ("density_upper_range",),
        )
        uses_policy_limit = limit is None
        if uses_policy_limit:
            limit = RULE_CONNECTIVE_DENSITY_MAX
        evaluated.add("connectives")
        if float(metrics["connective_density"]) > limit:
            triggers.add(
                "P5_CONNECTIVE_DENSITY_ABOVE_POLICY"
                if uses_policy_limit
                else "P5_CONNECTIVE_DENSITY_ABOVE_LIMIT"
            )

    field = fields.get("hedging")
    if field is not None:
        density_limit = upper_bound(
            field["value"],
            ("maximum_per_1000_words", "max_per_1000_words", "per_1000_words_upper_bound"),
            ("per_1000_words_upper_range",),
        )
        layer_limit = numeric_member(
            field["value"], ("maximum_layers_per_sentence", "max_layers_per_sentence")
        )
        if density_limit is not None or layer_limit is not None:
            evaluated.add("hedging")
        if density_limit is not None and float(metrics["hedges_per_1000_words"]) > density_limit:
            triggers.add("P5_HEDGE_DENSITY_ABOVE_LIMIT")
        if layer_limit is not None and int(metrics["max_hedges_in_sentence"]) > layer_limit:
            triggers.add("P5_HEDGE_LAYER_COUNT_ABOVE_LIMIT")

    return evaluated, triggers


def metric_counts(metrics: dict[str, Any]) -> dict[str, int]:
    words = int(metrics["word_count"])
    distribution = metrics["sentence_length_distribution"]
    return {
        "word_count": words,
        "sentence_count": int(metrics["sentence_count"]),
        "paragraph_count": int(metrics["paragraph_count"]),
        "short_sentence_count": int(distribution["short_1_14"]),
        "medium_sentence_count": int(distribution["medium_15_29"]),
        "long_sentence_count": int(distribution["long_30_plus"]),
        "paragraph_opening_count": int(metrics["paragraph_opening_count"]),
        "paragraph_opening_type_count": sum(
            bool(count) for count in metrics["paragraph_opening_types"].values()
        ),
        "connective_count": sum(int(count) for count in metrics["connective_frequency"].values()),
        "hedge_count": int(round(float(metrics["hedges_per_1000_words"]) * words / 1000)),
        "max_hedge_layer_count": int(metrics["max_hedges_in_sentence"]),
    }


def preflight(
    fragment: Path,
    project_dir: Path,
    section_type: str,
    passes: list[str],
    case_id: str | None = None,
    run_nonce: str | None = None,
) -> tuple[dict[str, Any], Path]:
    case_id, run_nonce = validated_tokens(case_id, run_nonce)
    fragment = validate_fragment(fragment)
    fragment_hash = fragment_sha256(fragment)
    helicon = resolve_target_profile.find_helicon(project_dir)
    ordered = [pass_id for pass_id in PASSES if pass_id in set(passes)]
    target, resolved_fields = load_target(helicon, ordered, section_type)

    report = style_fingerprint.document_report(fragment)
    metrics = report["document"]
    if int(metrics["word_count"]) == 0 or int(metrics["sentence_count"]) == 0:
        raise UserError("fragment contains no measurable prose")

    eligible_fields = {
        field["id"]: field for field in resolved_fields if field.get("eligible") is True
    }
    requested_fields = {
        field_id
        for pass_id in ordered
        for field_id in resolve_target_profile.PASS_FIELDS[pass_id]
    }
    evaluated: set[str] = set()
    triggers: set[str] = set()
    findings: list[Any] = []

    if "P4" in ordered:
        p4_evaluated, p4_triggers = evaluate_p4(eligible_fields, metrics)
        evaluated.update(p4_evaluated)
        triggers.update(p4_triggers)
    if "P5" in ordered:
        findings = check_ai_tells.scan(fragment)
        p5_evaluated, p5_triggers = evaluate_p5(eligible_fields, metrics, findings)
        evaluated.update(p5_evaluated)
        triggers.update(p5_triggers)

    rule_ids = sorted({f"R{finding.rule:02d}" for finding in findings})
    result = {
        "schema": OUTPUT_SCHEMA,
        "producer": PRODUCER,
        "event": "revision_preflight",
        "section_type": section_type,
        "passes": ordered,
        "fragment_sha256": fragment_hash,
        "decision": "revise" if triggers else "preserve",
        "target": target,
        "eligible_field_ids": sorted(eligible_fields),
        "evaluated_field_ids": sorted(evaluated),
        "excluded_field_ids": sorted(requested_fields - evaluated),
        "ai_tells": {"rule_ids": rule_ids, "count": len(findings)},
        "metric_counts": metric_counts(metrics),
        "trigger_reason_ids": sorted(triggers),
    }
    if case_id is not None:
        result["case_id"] = case_id
        result["run_nonce"] = run_nonce
    return result, helicon / "style"


def validated_tokens(case_id: str | None, run_nonce: str | None) -> tuple[str | None, str | None]:
    if (case_id is None) != (run_nonce is None):
        raise UserError("--case-id and --run-nonce must be supplied together")
    for option, value in (("--case-id", case_id), ("--run-nonce", run_nonce)):
        if value is not None and TOKEN_RE.fullmatch(value) is None:
            raise UserError(f"{option} must be a 1-64 character ASCII token")
    return case_id, run_nonce


def build_parser() -> argparse.ArgumentParser:
    parser = resolve_target_profile.JsonArgumentParser(description=__doc__)
    parser.add_argument("fragment", help="one UTF-8 .tex, .md, or .txt fragment")
    parser.add_argument(
        "--project-dir",
        required=True,
        help="paper or child directory; search it and at most three parents for .helicon",
    )
    parser.add_argument(
        "--section-type",
        required=True,
        choices=resolve_target_profile.SECTION_TYPES,
        help="normalized section type for target selection",
    )
    parser.add_argument(
        "--pass",
        dest="passes",
        required=True,
        action="append",
        choices=PASSES,
        help="preflight pass; repeat to evaluate both P4 and P5",
    )
    parser.add_argument(
        "--trace-output",
        help="optional JSON trace below .helicon/style/target_traces/",
    )
    parser.add_argument("--case-id", help="optional privacy-safe Stage3C case token")
    parser.add_argument("--run-nonce", help="optional privacy-safe Stage3C run token")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    try:
        args = parser.parse_args()
        case_id, run_nonce = validated_tokens(args.case_id, args.run_nonce)
        result, style_dir = preflight(
            Path(args.fragment),
            Path(args.project_dir),
            args.section_type,
            args.passes,
            case_id,
            run_nonce,
        )
        if args.trace_output:
            trace_path = resolve_target_profile.safe_trace_path(args.trace_output, style_dir)
            resolve_target_profile.write_trace(trace_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (
        OSError,
        UnicodeError,
        UserError,
        resolve_target_profile.UserError,
        style_fingerprint.UserError,
        check_ai_tells.UserError,
    ) as exc:
        print(json.dumps({"event": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
