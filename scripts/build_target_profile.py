#!/usr/bin/env python3
"""Screen one final-stage exemplar and preview or write a private target profile."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

import check_ai_tells
import extract_revision_direction
import style_fingerprint

RULE_VALUES: dict[str, Any] = {
    "sentence_length": {"mean_range_words": [12, 30], "minimum_sd_words": 4.0},
    "paragraph_length": {"word_range": [40, 180], "sentences_per_paragraph": [2, 7]},
    "opening_structure": {"policy": "Use at least two functional opening types when logic permits."},
    "connectives": {"maximum_per_sentence": 0.6, "allowed": "Only connectors that name a real logical relation."},
    "active_passive_by_section": {"policy": "Keep voice section-sensitive; passive voice is valid when the actor is irrelevant."},
    "first_person": {"policy": "Use first-person plural only for attributable author actions and claims."},
    "hedging": {"policy": "Keep evidence-bound hedges and avoid empty stacked hedge layers."},
    "claim_position": {"policy": "Place the claim before its support unless a scoped condition must lead."},
    "contribution_limitation_moves": {"policy": "State contribution, scope, evidence, and limitation as functions, not reusable prose."},
}

DIMENSION_RULES = {
    "sentence_length": {6, 7, 8, 10, 12, 13, 14},
    "paragraph_length": {8},
    "opening_structure": {5, 6},
    "connectives": {5},
    "active_passive_by_section": set(),
    "first_person": set(),
    "hedging": {9},
    "claim_position": {1, 2, 3},
    "contribution_limitation_moves": {1, 2, 3},
}


class UserError(Exception):
    """A concise command-line error."""


def version_number(path: Path) -> int:
    match = re.search(r"(?:version|stage|v)[-_ ]?(\d+)", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else -1


def choose_target(directory: Path, explicit: str | None) -> Path:
    if explicit:
        target = Path(explicit).resolve()
        if not target.is_file():
            raise UserError(f"target file not found: {target}")
        if target.suffix.lower() not in style_fingerprint.EXTENSIONS:
            allowed = ", ".join(sorted(style_fingerprint.EXTENSIONS))
            raise UserError(f"target file must use one of: {allowed}")
        return target
    files = style_fingerprint.input_files([str(directory)])
    return max(files, key=lambda path: (version_number(path), str(path).lower()))


def filtered_report(path: Path, holdout: set[int]) -> tuple[dict[str, Any], str, int]:
    raw = style_fingerprint.read_utf8(path)
    sections: list[dict[str, Any]] = []
    all_paragraphs: list[str] = []
    kept_text: list[str] = []
    paragraph_index = 0
    for title, content in style_fingerprint.raw_sections(raw, path.suffix.lower()):
        clean = style_fingerprint.protect_latex(content) if path.suffix.lower() == ".tex" else content
        included: list[str] = []
        for paragraph in style_fingerprint.split_paragraphs(clean):
            paragraph_index += 1
            if paragraph_index not in holdout:
                included.append(paragraph)
                all_paragraphs.append(paragraph)
                kept_text.append(paragraph)
        sections.append({"title": title, "metrics": style_fingerprint.metric_block(included)})
    invalid = sorted(index for index in holdout if index < 1 or index > paragraph_index)
    if invalid:
        raise UserError(f"hold-out paragraph indices are out of range: {invalid}; paragraph_count={paragraph_index}")
    if not all_paragraphs:
        raise UserError("hold-out selection removed every target paragraph")
    return {
        "path": str(path),
        "format": path.suffix.lower(),
        "title": style_fingerprint.extract_title(raw, path.suffix.lower()),
        "document": style_fingerprint.metric_block(all_paragraphs),
        "sections": sections,
    }, "\n\n".join(kept_text), paragraph_index


def rounded_range(center: float, spread: float) -> list[float]:
    half = max(spread / 2, 1.0)
    return [round(max(1.0, center - half), 4), round(center + half, 4)]


def exemplar_value(dimension: str, report: dict[str, Any]) -> Any:
    metrics = report["document"]
    if dimension == "sentence_length":
        return {
            "mean_range_words": rounded_range(metrics["mean_sentence_length"], metrics["sentence_length_sd"]),
            "minimum_sd_words": metrics["sentence_length_sd"],
            "distribution": metrics["sentence_length_distribution"],
        }
    if dimension == "paragraph_length":
        return {
            "mean_words": metrics["mean_paragraph_words"],
            "word_sd": metrics["paragraph_word_sd"],
            "mean_sentences": metrics["mean_sentences_per_paragraph"],
        }
    if dimension == "opening_structure":
        total = max(metrics["sentence_count"], 1)
        return {name: round(count / total, 4) for name, count in metrics["opening_types"].items()}
    if dimension == "connectives":
        return {"density_per_sentence": metrics["connective_density"], "allowed": sorted(metrics["connective_frequency"])}
    if dimension == "active_passive_by_section":
        return {
            section["title"]: {
                "active_ratio": section["metrics"]["active_sentence_ratio"],
                "passive_ratio": section["metrics"]["passive_sentence_ratio"],
            }
            for section in report["sections"] if section["metrics"]["sentence_count"]
        }
    if dimension == "first_person":
        return {"per_1000_words": metrics["first_person_per_1000_words"]}
    if dimension == "hedging":
        return {"per_1000_words": metrics["hedges_per_1000_words"], "maximum_layers_per_sentence": metrics["max_hedges_in_sentence"]}
    if dimension == "claim_position":
        return {
            "mean_normalized_position": metrics["mean_claim_position"],
            "observations": metrics["claim_sentence_count"],
            "per_paragraph": [
                {
                    "paragraph": item["paragraph"],
                    "normalized_positions": item["claim_sentence_positions"],
                }
                for item in metrics["paragraphs"] if item["claim_sentence_positions"]
            ],
        }
    if dimension == "contribution_limitation_moves":
        return {
            "contribution_move_count": metrics["contribution_move_count"],
            "limitation_move_count": metrics["limitation_move_count"],
            "form_only": True,
        }
    raise UserError(f"unknown target dimension: {dimension}")


def screening_decision(dimension: str, metrics: dict[str, Any], rule_counts: Counter[int]) -> tuple[bool, str]:
    hits = sorted(rule for rule in DIMENSION_RULES[dimension] if rule_counts[rule])
    reasons: list[str] = []
    if hits:
        reasons.append(f"AI-tell rules hit: {hits}")
    if dimension == "sentence_length" and (metrics["sentence_count"] < 4 or metrics["sentence_length_sd"] < 4.0):
        reasons.append("sentence sample or variance below policy threshold")
    elif dimension == "paragraph_length" and metrics["paragraph_count"] < 2:
        reasons.append("fewer than 2 paragraphs")
    elif dimension == "opening_structure" and len(metrics["opening_types"]) < 2:
        reasons.append("fewer than 2 opening types")
    elif dimension == "connectives" and metrics["connective_density"] > 0.6:
        reasons.append("connective density exceeds policy threshold")
    elif dimension == "active_passive_by_section" and metrics["sentence_count"] < 4:
        reasons.append("too few sentences for a voice ratio")
    elif dimension == "first_person" and metrics["word_count"] < 50:
        reasons.append("fewer than 50 words")
    elif dimension == "hedging" and metrics["max_hedges_in_sentence"] == 0:
        reasons.append("no hedge observation")
    elif dimension == "claim_position" and metrics["claim_sentence_count"] == 0:
        reasons.append("no claim-position observation")
    elif dimension == "contribution_limitation_moves" and not (metrics["contribution_move_count"] or metrics["limitation_move_count"]):
        reasons.append("no contribution or limitation move observed")
    return not reasons, "; ".join(reasons) if reasons else "clean and sufficiently observed"


def performance_text(dimension: str, metrics: dict[str, Any], rule_density: dict[str, float], reason: str) -> str:
    summaries = {
        "sentence_length": f"mean={metrics['mean_sentence_length']}, sd={metrics['sentence_length_sd']}",
        "paragraph_length": f"paragraphs={metrics['paragraph_count']}, mean_words={metrics['mean_paragraph_words']}",
        "opening_structure": f"opening_types={sorted(metrics['opening_types'])}",
        "connectives": f"density={metrics['connective_density']}, R5/1000={rule_density['5']}",
        "active_passive_by_section": f"active={metrics['active_sentence_ratio']}, passive={metrics['passive_sentence_ratio']}",
        "first_person": f"per_1000_words={metrics['first_person_per_1000_words']}",
        "hedging": f"per_1000_words={metrics['hedges_per_1000_words']}, max_layers={metrics['max_hedges_in_sentence']}",
        "claim_position": f"observations={metrics['claim_sentence_count']}, mean_position={metrics['mean_claim_position']}",
        "contribution_limitation_moves": f"contribution={metrics['contribution_move_count']}, limitation={metrics['limitation_move_count']}",
    }
    return f"{summaries[dimension]}; {reason}"


def build(
    directory: Path,
    target_file: Path,
    holdout: set[int],
    paper_id: str | None,
    direction: dict[str, Any],
) -> dict[str, Any]:
    report, screened_text, paragraph_count = filtered_report(target_file, holdout)
    findings = check_ai_tells.scan_text(screened_text, target_file)
    rule_counts: Counter[int] = Counter(item.rule for item in findings)
    word_count = max(report["document"]["word_count"], 1)
    rule_density = {str(rule): round(rule_counts[rule] * 1000 / word_count, 4) for rule in range(1, 15)}
    fields: dict[str, Any] = {}
    table: list[dict[str, Any]] = []
    for dimension in DIMENSION_RULES:
        adopted, reason = screening_decision(dimension, report["document"], rule_counts)
        source = "exemplar" if adopted else "rule"
        fields[dimension] = {
            "source": source,
            "confidence": "high" if adopted and report["document"]["sentence_count"] >= 8 else "medium",
            "value": exemplar_value(dimension, report) if adopted else RULE_VALUES[dimension],
        }
        table.append({
            "dimension": dimension,
            "v3_performance": performance_text(dimension, report["document"], rule_density, reason),
            "adopt_as_target": adopted,
            "source": source,
        })
    title_key = style_fingerprint.normalize_title(report["title"] or "")
    candidates = [item for item in direction["exemplar_candidates"] if item["pair_driver"] != "reviewer-driven"]
    excluded_reviewer_cards = len(direction["exemplar_candidates"]) - len(candidates)
    return {
        "screening": {
            "schema": "helicon-target-screening-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "target_file": str(target_file),
            "word_count": report["document"]["word_count"],
            "ai_tell_density_per_1000_words": rule_density,
            "ai_tell_finding_count": len(findings),
            "structural_metrics": report,
            "holdout_target_paragraphs": sorted(holdout),
            "total_target_paragraphs": paragraph_count,
            "decision_table": table,
            "reviewer_driven_exemplar_candidates_excluded": excluded_reviewer_cards,
        },
        "profile": {
            "schema": "helicon-target-profile-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "paper_id": paper_id or (f"title:{title_key}" if title_key else f"directory:{style_fingerprint.normalize_title(directory.name)}"),
            "purpose": "prescriptive convergence target; never a drift baseline",
            "target_file": str(target_file),
            "holdout_target_paragraphs": sorted(holdout),
            "exemplar_card_count": len(candidates),
            "fields": fields,
        },
        "exemplar_candidates": candidates,
        "direction_summary": {
            "pairs": [
                {
                    "stage_pair": pair["stage_pair"],
                    "driver": pair["driver"],
                    "included_in_author_preference": pair["included_in_author_preference"],
                }
                for pair in direction["pairs"]
            ],
            "warnings": direction["warnings"],
        },
    }


def private_output(path: Path) -> Path:
    resolved = path.resolve()
    lowered = tuple(part.casefold() for part in resolved.parts)
    if not any(left == ".helicon" and right == "style" for left, right in zip(lowered, lowered[1:])):
        raise UserError(f"private target artifacts must stay under .helicon/style: {resolved}")
    return resolved


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_exemplar_cards(directory: Path, candidates: list[dict[str, Any]]) -> list[str]:
    root = private_output(directory / ".helicon/style/exemplars")
    root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for index, item in enumerate(candidates, 1):
        path = root / f"exemplar-{index:03d}.md"
        kept = ", ".join(item["what_was_deliberately_kept"]) or "None identified; author confirmation required."
        text = (
            "# Exemplar Card\n\n"
            f"- Paper ID: {item['paper_id']}\n"
            f"- Stage pair: {item['stage_pair']}\n"
            f"- Pair driver: {item['pair_driver']}\n"
            f"- Section type: {item['section_type']}\n"
            f"- Rule IDs: {', '.join(str(rule) for rule in item['rule_ids'])}\n\n"
            f"## Before\n\n{item['before']}\n\n"
            f"## After\n\n{item['after']}\n\n"
            f"## What changed\n\n{item['what_changed']}\n\n"
            f"## What was deliberately kept\n\n{kept}\n"
        )
        path.write_text(text, encoding="utf-8")
        written.append(str(path))
    return written


def print_human(result: dict[str, Any], profile_path: Path, screening_path: Path, wrote: bool) -> None:
    print("| Dimension | v3 performance | Adopt as target |")
    print("|---|---|---|")
    for row in result["screening"]["decision_table"]:
        decision = f"yes; source: {row['source']}" if row["adopt_as_target"] else "no; source: rule"
        print(f"| {row['dimension']} | {row['v3_performance']} | {decision} |")
    print(f"target_profile={profile_path}")
    print(f"target_screening={screening_path}")
    print(f"exemplar_candidates={len(result['exemplar_candidates'])}")
    for index, item in enumerate(result["exemplar_candidates"], 1):
        print(f"candidate {index}: {item['stage_pair']} | {item['section_type']} | rules={item['rule_ids']}")
        print(f"  before: {item['before']}")
        print(f"  after: {item['after']}")
    for warning in result["direction_summary"]["warnings"]:
        print(f"warning: {warning}")
    print("written=true" if wrote else "written=false; confirm, then rerun with --write")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="directory containing ordered paper versions")
    parser.add_argument("--target-file", help="explicit final-stage .tex, .md, or .txt file")
    parser.add_argument("--paper-id", help="explicit paper identity")
    parser.add_argument("--holdout", action="append", type=int, default=[], help="1-based target paragraph index reserved from profile construction; repeat as needed")
    parser.add_argument("--review-driven-pair", action="append", default=[], help="stage pair excluded from author preference and default cards, for example 2:3")
    parser.add_argument("--author-advisor-pair", action="append", default=[], help="author/advisor stage pair, for example 1:2")
    parser.add_argument("--profile-output", help="private .helicon/style/target_profile.json path")
    parser.add_argument("--screening-output", help="private .helicon/style/target_screening.json path")
    parser.add_argument("--write", action="store_true", help="write after the preview has been confirmed")
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
        target = choose_target(directory, args.target_file)
        profile_path = private_output(Path(args.profile_output) if args.profile_output else directory / ".helicon/style/target_profile.json")
        screening_path = private_output(Path(args.screening_output) if args.screening_output else directory / ".helicon/style/target_screening.json")
        reviewer = extract_revision_direction.parse_pairs(args.review_driven_pair)
        advisor = extract_revision_direction.parse_pairs(args.author_advisor_pair)
        overlap = reviewer & advisor
        if overlap:
            raise UserError(f"stage pairs cannot have two drivers: {sorted(overlap)}")
        direction = extract_revision_direction.analyze(directory, args.paper_id, reviewer, advisor)
        result = build(directory, target, set(args.holdout), args.paper_id, direction)
        cards: list[str] = []
        if args.write:
            if direction["warnings"]:
                raise UserError("cannot write target artifacts until every adjacent stage pair has explicit provenance")
            write_json(profile_path, result["profile"])
            write_json(screening_path, result["screening"])
            cards = write_exemplar_cards(directory, result["exemplar_candidates"])
        payload = {
            **result,
            "profile_output": str(profile_path),
            "screening_output": str(screening_path),
            "exemplar_card_outputs": cards,
            "written": args.write,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_human(result, profile_path, screening_path, args.write)
        return 0
    except (OSError, UserError) as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
