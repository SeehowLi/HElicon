#!/usr/bin/env python3
"""Resolve a paper-local target profile into pass-specific model context."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


CURRENT_SCHEMA = "helicon-target-profile-v3"
SUPPORTED_SCHEMAS = {"helicon-target-profile-v2", CURRENT_SCHEMA}
PASS_FIELDS = {
    "P4": ("sentence_length", "paragraph_length", "opening_structure"),
    "P5": ("connectives", "hedging"),
    "P6": ("active_passive_by_section", "first_person"),
}
P2_ONLY_FIELDS = ("claim_position", "contribution_limitation_moves")
SECTION_TYPES = (
    "Introduction",
    "Related Work",
    "Evaluation",
    "Contributions",
    "Threat Model",
    "Conclusion",
    "Methods",
    "Other",
)
VALUE_KEYS = {
    "sentence_length": {
        "rule": {"mean_range_words", "minimum_sd_words"},
        "exemplar": {"mean_range_words", "minimum_sd_words", "distribution"},
    },
    "paragraph_length": {
        "rule": {"word_range", "sentences_per_paragraph"},
        "exemplar": {"mean_words", "word_sd", "mean_sentences"},
    },
    "opening_structure": {"rule": {"policy"}, "exemplar": ()},
    "connectives": {
        "rule": {"maximum_per_sentence", "allowed"},
        "exemplar": {"density_per_sentence", "allowed"},
    },
    "active_passive_by_section": {"rule": {"policy"}, "exemplar": ()},
    "first_person": {"rule": {"policy"}, "exemplar": {"per_1000_words"}},
    "hedging": {
        "rule": {"policy"},
        "exemplar": {"per_1000_words", "maximum_layers_per_sentence"},
    },
    "claim_position": {
        "rule": {"policy"},
        "exemplar": {"mean_normalized_position", "observations", "per_paragraph"},
    },
    "contribution_limitation_moves": {
        "rule": {"policy"},
        "exemplar": {"contribution_move_count", "limitation_move_count", "form_only"},
    },
}


class UserError(Exception):
    """A concise command-line error."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep command-line failures machine-readable like runtime failures."""

    def error(self, message: str) -> None:
        print(json.dumps({"event": "error", "error": message}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path.name}") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path.name}: {exc}") from exc


def find_helicon(project_dir: Path) -> Path:
    start = project_dir.resolve()
    if not start.exists():
        raise UserError(f"project directory not found: {project_dir}")
    if start.is_file():
        start = start.parent
    base = start
    for _ in range(4):
        candidate = base if base.name.casefold() == ".helicon" else base / ".helicon"
        if candidate.is_dir():
            return candidate.resolve()
        if base.parent == base:
            break
        base = base.parent
    raise UserError("no .helicon project pack found at the project directory or within three parent levels")


def yaml_scalar(raw: str) -> str | None:
    value = raw.strip()
    if not value or value.casefold() in {"null", "~"}:
        return None
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise UserError("project.yaml contains an invalid quoted target_venue") from exc
        return str(parsed).strip() or None
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise UserError("project.yaml contains an invalid quoted target_venue")
        return value[1:-1].replace("''", "'").strip() or None
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    return value or None


def project_target_venue(project_yaml: Path) -> str | None:
    if not project_yaml.is_file():
        return None
    matches: list[str] = []
    for line in read_utf8(project_yaml).splitlines():
        match = re.match(r"^\s*target_venue\s*:\s*(.*?)\s*$", line)
        if match:
            value = yaml_scalar(match.group(1))
            if value:
                matches.append(value)
    distinct = list(dict.fromkeys(matches))
    if len(distinct) > 1:
        raise UserError("project.yaml contains conflicting target_venue values")
    return distinct[0] if distinct else None


def read_profile(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UserError(f"cannot read {path.name}: {exc}") from exc
    try:
        profile = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise UserError(f"invalid JSON in {path.name}: line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(profile, dict):
        raise UserError("target_profile.json must contain a JSON object")
    if profile.get("schema") not in SUPPORTED_SCHEMAS:
        raise UserError(
            f"unsupported target profile schema: expected one of {sorted(SUPPORTED_SCHEMAS)!r}, "
            f"got {profile.get('schema')!r}"
        )
    return profile, f"sha256:{hashlib.sha256(raw).hexdigest()}"


def normalized_venue(value: str) -> str:
    return " ".join(value.split()).casefold()


def finite_number(value: Any, *, minimum: float = 0.0, maximum: float | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return math.isfinite(number) and number >= minimum and (maximum is None or number <= maximum)


def numeric_pair(value: Any, *, minimum: float = 0.0) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and finite_number(value[0], minimum=minimum)
        and finite_number(value[1], minimum=minimum)
        and float(value[0]) <= float(value[1])
    )


def validate_current_value(field_id: str, source: str, value: Any) -> None:
    """Validate the typed v3 value without exposing it in an error."""
    if not isinstance(value, dict):
        raise UserError(f"target profile field {field_id!r} value must be an object")
    required = set(VALUE_KEYS[field_id][source])
    if not required.issubset(value):
        raise UserError(f"target profile field {field_id!r} value has the wrong typed shape")
    if source == "rule":
        if field_id in {"opening_structure", "active_passive_by_section", "first_person", "hedging", "claim_position", "contribution_limitation_moves"}:
            if not isinstance(value.get("policy"), str) or not value["policy"].strip():
                raise UserError(f"target profile field {field_id!r} has an invalid rule policy")
        elif field_id == "sentence_length" and not (
            numeric_pair(value["mean_range_words"], minimum=1.0)
            and finite_number(value["minimum_sd_words"])
        ):
            raise UserError("target profile sentence_length rule value is invalid")
        elif field_id == "paragraph_length" and not (
            numeric_pair(value["word_range"], minimum=1.0)
            and numeric_pair(value["sentences_per_paragraph"], minimum=1.0)
        ):
            raise UserError("target profile paragraph_length rule value is invalid")
        elif field_id == "connectives" and not finite_number(value["maximum_per_sentence"]):
            raise UserError("target profile connectives rule value is invalid")
        return

    if field_id == "sentence_length" and not (
        numeric_pair(value["mean_range_words"], minimum=1.0)
        and finite_number(value["minimum_sd_words"])
        and isinstance(value["distribution"], dict)
    ):
        raise UserError("target profile sentence_length exemplar value is invalid")
    if field_id == "paragraph_length" and not all(
        finite_number(value[key]) for key in ("mean_words", "word_sd", "mean_sentences")
    ):
        raise UserError("target profile paragraph_length exemplar value is invalid")
    if field_id == "opening_structure" and (
        not value or not all(isinstance(key, str) and finite_number(item, maximum=1.0) for key, item in value.items())
    ):
        raise UserError("target profile opening_structure exemplar value is invalid")
    if field_id == "connectives" and not (
        finite_number(value["density_per_sentence"])
        and isinstance(value["allowed"], list)
        and all(isinstance(item, str) for item in value["allowed"])
    ):
        raise UserError("target profile connectives exemplar value is invalid")
    if field_id == "active_passive_by_section" and (
        not value
        or not all(
            isinstance(item, dict)
            and finite_number(item.get("active_ratio"), maximum=1.0)
            and finite_number(item.get("passive_ratio"), maximum=1.0)
            for item in value.values()
        )
    ):
        raise UserError("target profile active_passive_by_section exemplar value is invalid")
    if field_id == "first_person" and not finite_number(value["per_1000_words"]):
        raise UserError("target profile first_person exemplar value is invalid")
    if field_id == "hedging" and not (
        finite_number(value["per_1000_words"])
        and finite_number(value["maximum_layers_per_sentence"])
    ):
        raise UserError("target profile hedging exemplar value is invalid")
    if field_id == "claim_position" and not (
        finite_number(value["mean_normalized_position"], maximum=1.0)
        and finite_number(value["observations"])
        and isinstance(value["per_paragraph"], list)
    ):
        raise UserError("target profile claim_position exemplar value is invalid")
    if field_id == "contribution_limitation_moves" and not (
        finite_number(value["contribution_move_count"])
        and finite_number(value["limitation_move_count"])
        and value["form_only"] is True
    ):
        raise UserError("target profile contribution_limitation_moves exemplar value is invalid")


def select_venue(profile: dict[str, Any], target_venue: str | None) -> tuple[str, bool | None]:
    venue_profiles = profile.get("venue_profiles")
    if not isinstance(venue_profiles, dict) or not venue_profiles:
        raise UserError("target_profile.json has no venue_profiles object")
    if not all(isinstance(key, str) and isinstance(value, dict) for key, value in venue_profiles.items()):
        raise UserError("target_profile.json contains an invalid venue_profiles entry")

    default_venue = profile.get("default_venue")
    if not isinstance(default_venue, str) or default_venue not in venue_profiles:
        raise UserError("target_profile.json default_venue does not name a venue_profiles entry")

    if target_venue:
        wanted = normalized_venue(target_venue)
        matched = next((name for name in venue_profiles if normalized_venue(name) == wanted), None)
        if matched is not None:
            return matched, True
        return default_venue, False
    return default_venue, None


def resolve_fields(
    profile: dict[str, Any], selected_venue: str, passes: list[str], section_type: str | None
) -> tuple[list[dict[str, Any]], bool]:
    venue_profile = profile["venue_profiles"][selected_venue]
    fields = venue_profile.get("fields")
    if not isinstance(fields, dict):
        raise UserError(f"target profile venue {selected_venue!r} has no fields object")

    resolved: list[dict[str, Any]] = []
    all_exemplar = True
    for pass_id in passes:
        for field_id in PASS_FIELDS[pass_id]:
            field = fields.get(field_id)
            if not isinstance(field, dict):
                raise UserError(f"target profile field missing or invalid: {field_id}")
            source = field.get("source")
            if source not in {"exemplar", "rule"}:
                raise UserError(f"target profile field {field_id!r} has invalid source: {source!r}")
            if "confidence" not in field or "value" not in field:
                raise UserError(f"target profile field {field_id!r} must contain confidence and value")
            value = field["value"]
            if profile["schema"] == CURRENT_SCHEMA:
                if not isinstance(field["confidence"], str) or not field["confidence"].strip():
                    raise UserError(f"target profile field {field_id!r} has invalid confidence")
                validate_current_value(field_id, source, value)
            eligible = True
            exclusion_reason = None
            if profile["schema"] == "helicon-target-profile-v2" and field_id in {
                "opening_structure",
                "active_passive_by_section",
            }:
                value = None
                eligible = False
                exclusion_reason = (
                    "legacy v2 field used all-sentence openings or raw section headings; rebuild as v3"
                )
            if field_id == "active_passive_by_section" and source == "exemplar" and section_type:
                if eligible and not isinstance(value, dict):
                    raise UserError("active_passive_by_section exemplar value must be an object")
                if eligible and section_type in value:
                    value = {section_type: value[section_type]}
                elif eligible:
                    value = None
                    eligible = False
                    exclusion_reason = f"no exemplar voice target for section type {section_type}"
            resolved.append({
                "id": field_id,
                "pass": pass_id,
                "source": source,
                "confidence": field["confidence"],
                "eligible": eligible,
                "exclusion_reason": exclusion_reason,
                "value": value,
            })
            if eligible:
                all_exemplar = all_exemplar and source == "exemplar"
    return resolved, all_exemplar


def safe_trace_path(raw_path: str, style_dir: Path) -> Path:
    path = Path(raw_path).resolve()
    style = style_dir.resolve()
    trace_root_path = style / "target_traces"
    if trace_root_path.is_symlink():
        raise UserError("the resolved .helicon/style/target_traces directory must not be a symlink")
    trace_root = trace_root_path.resolve()
    if trace_root.parent != style:
        raise UserError("the resolved .helicon/style/target_traces directory escaped the style directory")
    reserved = {
        (style / "target_profile.json").resolve(),
        (style / "target_screening.json").resolve(),
    }
    if path in reserved:
        raise UserError("--trace-output cannot overwrite target_profile.json or target_screening.json")
    if path == trace_root or trace_root not in path.parents:
        raise UserError(
            "--trace-output must be a file below the resolved .helicon/style/target_traces directory"
        )
    return path


def write_trace(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise UserError(f"cannot write trace output: {exc}") from exc


def ordered_passes(items: list[str]) -> list[str]:
    requested = set(items)
    return [pass_id for pass_id in PASS_FIELDS if pass_id in requested]


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-dir",
        required=True,
        help="paper or child directory; search it and at most three parents for .helicon",
    )
    parser.add_argument(
        "--pass",
        dest="passes",
        action="append",
        choices=tuple(PASS_FIELDS),
        required=True,
        help="routed pass to resolve; repeat for multiple passes",
    )
    parser.add_argument(
        "--trace-output",
        help="optional privacy-safe JSON trace file below the resolved .helicon/style/target_traces directory",
    )
    parser.add_argument(
        "--section-type",
        choices=SECTION_TYPES,
        help="normalized section type used to select section-specific P6 values",
    )
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    try:
        args = parser.parse_args()
        helicon = find_helicon(Path(args.project_dir))
        style_dir = helicon / "style"
        target_venue = project_target_venue(helicon / "project.yaml")
        profile_path = style_dir / "target_profile.json"
        passes = ordered_passes(args.passes)

        if profile_path.is_file():
            profile, profile_hash = read_profile(profile_path)
            selected_venue, venue_match = select_venue(profile, target_venue)
            fields, all_exemplar = resolve_fields(profile, selected_venue, passes, args.section_type)
            any_eligible = any(field["eligible"] for field in fields)
            legacy_profile = profile["schema"] != CURRENT_SCHEMA
            status = "ok" if venue_match is True and all_exemplar and any_eligible and not legacy_profile else "partial"
            context: dict[str, Any] = {
                "event": "resolved",
                "status": status,
                "resolved_status": status,
                "schema": profile["schema"],
                "current_schema": CURRENT_SCHEMA,
                "legacy_profile": legacy_profile,
                "profile_sha256": profile_hash,
                "target_venue": target_venue,
                "selected_venue": selected_venue,
                "venue_match": venue_match,
                "section_type": args.section_type,
                "passes": passes,
                "fields": fields,
            }
        else:
            profile_hash = None
            venue_match = None
            fields = []
            status = "none"
            context = {
                "event": "resolved",
                "status": status,
                "resolved_status": status,
                "schema": None,
                "current_schema": CURRENT_SCHEMA,
                "legacy_profile": False,
                "profile_sha256": None,
                "target_venue": target_venue,
                "selected_venue": None,
                "venue_match": None,
                "section_type": args.section_type,
                "passes": passes,
                "fields": [],
            }

        trace = {
            "schema": "helicon-target-use-trace-v1",
            "producer": "resolve_target_profile.py",
            "event": "resolved",
            "status": status,
            "resolved_status": status,
            "profile_sha256": profile_hash,
            "profile_schema": context["schema"],
            "venue_match": venue_match,
            "section_type": args.section_type,
            "fields": [
                {
                    "id": field["id"],
                    "source": field["source"],
                    "pass": field["pass"],
                    "eligible": field["eligible"],
                }
                for field in fields
            ],
        }
        if args.trace_output:
            write_trace(safe_trace_path(args.trace_output, style_dir), trace)
        print(json.dumps(context, ensure_ascii=False, indent=2))
        return 0
    except UserError as exc:
        print(json.dumps({"event": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
