#!/usr/bin/env python3
"""Measure structural writing style without retaining source prose."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import statistics
import sys
from typing import Any

EXTENSIONS = {".tex", ".md", ".txt"}
MIN_BASELINE_PAPERS = 5
WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|\d+(?:\.\d+)?")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`\\])")
CONNECTIVES = {
    "accordingly", "additionally", "although", "because", "consequently",
    "conversely", "furthermore", "hence", "however", "moreover", "nevertheless",
    "otherwise", "therefore", "thus", "whereas", "while",
}
CLAUSE_OPENERS = {"although", "because", "if", "since", "unless", "when", "whereas", "while"}
PREPOSITION_OPENERS = {"after", "at", "before", "by", "during", "for", "from", "in", "on", "through", "under", "with", "without"}
HEDGE_PHRASES = ("may", "might", "could", "suggests", "appears to", "is consistent with", "we conjecture", "likely", "approximately")
PASSIVE_RE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b", re.IGNORECASE)
CLAIM_RE = re.compile(
    r"\b(?:we (?:show|demonstrate|present|propose|introduce|find)|our (?:method|system|evaluation) "
    r"(?:achieves|reduces|improves)|(?:the )?results? (?:show|indicate|suggest))\b",
    re.IGNORECASE,
)
CONTRIBUTION_RE = re.compile(r"\b(?:our contributions?|we (?:present|propose|introduce|design|develop))\b", re.IGNORECASE)
LIMITATION_RE = re.compile(r"\b(?:limitation|limited to|does not|do not|however|future work)\b", re.IGNORECASE)
SYNONYM_GROUPS = {
    "ciphertext object": ("ciphertext", "encrypted value", "encrypted input"),
    "method referent": ("method", "approach", "framework", "technique"),
    "cost referent": ("cost", "overhead", "expense"),
}
BASELINE_METRICS = (
    "mean_sentence_length",
    "sentence_length_sd",
    "alternation_index",
    "connective_density",
    "em_dash_per_1000_words",
)


class UserError(Exception):
    """A concise command-line error."""


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path} ({exc})") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def input_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if not path.exists():
            raise UserError(f"input does not exist: {path}")
        if path.is_dir():
            files.extend(
                child for child in path.rglob("*")
                if child.is_file() and child.suffix.lower() in EXTENSIONS and ".helicon" not in child.parts
            )
        elif path.suffix.lower() in EXTENSIONS:
            files.append(path)
        else:
            raise UserError(f"unsupported input type: {path}; expected .tex, .md, or .txt")
    unique = sorted({path.resolve() for path in files}, key=lambda item: str(item).lower())
    if not unique:
        raise UserError("no .tex, .md, or .txt inputs found")
    return unique


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_title(text: str, suffix: str) -> str | None:
    if suffix == ".tex":
        match = re.search(r"\\title\s*(?:\[[^\]]*\]\s*)*\{([^{}]+)\}", text, re.DOTALL)
    elif suffix == ".md":
        match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    else:
        match = re.search(r"(?im)^\s*(?:paper\s+)?title\s*:\s*(.+?)\s*$", text)
    return normalize_space(match.group(1)) if match else None


def normalize_title(title: str) -> str:
    without_commands = re.sub(r"\\[A-Za-z@]+\*?", " ", title)
    return re.sub(r"[\W_]+", " ", without_commands.casefold(), flags=re.UNICODE).strip()


def protect_latex(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(
        r"\\(?:documentclass|usepackage|title|author|date)\*?\s*(?:\[[^\]]*\]\s*)*\{[^{}]*\}",
        " ",
        text,
    )
    text = re.sub(r"\\(?:begin|end)\{document\}", " ", text)
    for env in ("table", "table*", "tabular", "tabular*", "longtable", "equation", "equation*", "align", "align*", "gather", "gather*", "multline", "multline*", "displaymath", "math"):
        pattern = rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}"
        text = re.sub(pattern, " ", text, flags=re.DOTALL)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\\(.*?\\\)", " ", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\(?:cite\w*|ref|autoref|eqref|cref|label)\s*(?:\[[^\]]*\]\s*)*\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:section|subsection|subsubsection)\*?\{[^{}]*\}", "\n\n", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    return text


def raw_sections(text: str, suffix: str) -> list[tuple[str, str]]:
    if suffix == ".tex":
        pattern = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^{}]+)\}")
        matches = list(pattern.finditer(text))
    elif suffix == ".md":
        pattern = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
        matches = list(pattern.finditer(text))
    else:
        matches = []
    if not matches:
        return [("Document", text)]
    sections: list[tuple[str, str]] = []
    if text[:matches[0].start()].strip():
        sections.append(("Preamble", text[:matches[0].start()]))
    for index, match in enumerate(matches):
        title = normalize_space(match.group(2))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((title, text[match.end():end]))
    return sections


def split_paragraphs(text: str) -> list[str]:
    return [normalize_space(part) for part in re.split(r"\n\s*\n", text) if normalize_space(part)]


def split_sentences(paragraph: str) -> list[str]:
    parts = SENTENCE_RE.split(paragraph)
    return [normalize_space(part) for part in parts if len(WORD_RE.findall(part)) > 1]


def opening_type(sentence: str) -> str:
    words = [word.lower() for word in WORD_RE.findall(sentence)]
    if not words:
        return "other"
    first = words[0]
    if first in CONNECTIVES:
        return "connective"
    if first in CLAUSE_OPENERS:
        return "clause"
    if first in PREPOSITION_OPENERS:
        return "prepositional_phrase"
    if first.endswith("ly"):
        return "adverbial"
    if first in {"the", "a", "an", "we", "this", "these", "our"} or sentence[:1].isupper():
        return "noun_phrase_subject"
    return "other"


def length_distribution(lengths: list[int]) -> dict[str, int]:
    return {
        "short_1_14": sum(length <= 14 for length in lengths),
        "medium_15_29": sum(15 <= length <= 29 for length in lengths),
        "long_30_plus": sum(length >= 30 for length in lengths),
    }


def metric_block(paragraphs: list[str]) -> dict[str, Any]:
    paragraph_results: list[dict[str, Any]] = []
    all_sentences: list[str] = []
    all_lengths: list[int] = []
    alternations: list[float] = []
    openings: Counter[str] = Counter()
    connectives: Counter[str] = Counter()
    synonym_hits: list[dict[str, Any]] = []
    em_dash_count = 0
    word_count = 0
    paragraph_word_counts: list[int] = []
    paragraph_sentence_counts: list[int] = []
    passive_sentences = 0
    first_person_count = 0
    hedge_count = 0
    max_hedges_in_sentence = 0
    claim_positions: list[float] = []
    contribution_moves = 0
    limitation_moves = 0

    for index, paragraph in enumerate(paragraphs, 1):
        sentences = split_sentences(paragraph)
        paragraph_claim_positions: list[float] = []
        lengths = [len(WORD_RE.findall(sentence)) for sentence in sentences]
        words = WORD_RE.findall(paragraph)
        word_count += len(words)
        paragraph_word_counts.append(len(words))
        paragraph_sentence_counts.append(len(sentences))
        em_dash_count += paragraph.count("—")
        first_person_count += len(re.findall(r"\b(?:we|our|ours)\b", paragraph, re.IGNORECASE))
        contribution_moves += len(CONTRIBUTION_RE.findall(paragraph))
        limitation_moves += len(LIMITATION_RE.findall(paragraph))
        all_sentences.extend(sentences)
        all_lengths.extend(lengths)
        for sentence_index, sentence in enumerate(sentences, 1):
            openings[opening_type(sentence)] += 1
            passive_sentences += bool(PASSIVE_RE.search(sentence))
            sentence_hedges = sum(len(re.findall(rf"\b{re.escape(phrase)}\b", sentence, re.IGNORECASE)) for phrase in HEDGE_PHRASES)
            hedge_count += sentence_hedges
            max_hedges_in_sentence = max(max_hedges_in_sentence, sentence_hedges)
            if CLAIM_RE.search(sentence):
                normalized_claim_position = sentence_index / max(len(sentences), 1)
                claim_positions.append(normalized_claim_position)
                paragraph_claim_positions.append(normalized_claim_position)
            lowered = {word.lower() for word in WORD_RE.findall(sentence)}
            for connective in CONNECTIVES:
                if connective in lowered:
                    connectives[connective] += 1
        alternation = statistics.fmean(abs(a - b) for a, b in zip(lengths, lengths[1:])) if len(lengths) > 1 else 0.0
        if len(lengths) > 1:
            alternations.append(alternation)
        paragraph_results.append({
            "paragraph": index,
            "sentence_count": len(lengths),
            "word_count": len(words),
            "sentence_lengths": lengths,
            "alternation_index": round(alternation, 4),
            "claim_sentence_positions": [round(value, 4) for value in paragraph_claim_positions],
        })

    lowered_text = " ".join(paragraphs).lower()
    for concept, variants in SYNONYM_GROUPS.items():
        present = [variant for variant in variants if re.search(rf"\b{re.escape(variant)}\b", lowered_text)]
        if len(present) > 1:
            synonym_hits.append({"concept": concept, "variants": present})

    mean = statistics.fmean(all_lengths) if all_lengths else 0.0
    sd = statistics.pstdev(all_lengths) if len(all_lengths) > 1 else 0.0
    return {
        "sentence_count": len(all_lengths),
        "word_count": word_count,
        "paragraph_count": len(paragraphs),
        "mean_paragraph_words": round(statistics.fmean(paragraph_word_counts), 4) if paragraph_word_counts else 0.0,
        "paragraph_word_sd": round(statistics.pstdev(paragraph_word_counts), 4) if len(paragraph_word_counts) > 1 else 0.0,
        "mean_sentences_per_paragraph": round(statistics.fmean(paragraph_sentence_counts), 4) if paragraph_sentence_counts else 0.0,
        "mean_sentence_length": round(mean, 4),
        "sentence_length_sd": round(sd, 4),
        "min_sentence_length": min(all_lengths, default=0),
        "max_sentence_length": max(all_lengths, default=0),
        "sentence_length_distribution": length_distribution(all_lengths),
        "alternation_index": round(statistics.fmean(alternations), 4) if alternations else 0.0,
        "opening_types": dict(sorted(openings.items())),
        "connective_frequency": dict(sorted(connectives.items())),
        "connective_density": round(sum(connectives.values()) / max(len(all_lengths), 1), 4),
        "em_dash_per_1000_words": round(em_dash_count * 1000 / max(word_count, 1), 4),
        "active_sentence_ratio": round((len(all_lengths) - passive_sentences) / max(len(all_lengths), 1), 4),
        "passive_sentence_ratio": round(passive_sentences / max(len(all_lengths), 1), 4),
        "first_person_per_1000_words": round(first_person_count * 1000 / max(word_count, 1), 4),
        "hedges_per_1000_words": round(hedge_count * 1000 / max(word_count, 1), 4),
        "max_hedges_in_sentence": max_hedges_in_sentence,
        "claim_sentence_count": len(claim_positions),
        "mean_claim_position": round(statistics.fmean(claim_positions), 4) if claim_positions else None,
        "contribution_move_count": contribution_moves,
        "limitation_move_count": limitation_moves,
        "synonym_candidates": synonym_hits,
        "paragraphs": paragraph_results,
    }


def document_report(path: Path) -> dict[str, Any]:
    raw = read_utf8(path)
    document_title = extract_title(raw, path.suffix.lower())
    section_results: list[dict[str, Any]] = []
    all_clean: list[str] = []
    for section_title, content in raw_sections(raw, path.suffix.lower()):
        clean = protect_latex(content) if path.suffix.lower() == ".tex" else content.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = split_paragraphs(clean)
        all_clean.extend(paragraphs)
        section_results.append({"title": section_title, "metrics": metric_block(paragraphs)})
    return {
        "path": str(path),
        "format": path.suffix.lower(),
        "title": document_title,
        "document": metric_block(all_clean),
        "sections": section_results,
    }


def compact_metrics(report: dict[str, Any]) -> dict[str, float]:
    document = report["document"]
    return {name: float(document[name]) for name in BASELINE_METRICS}


def baseline_data(files: list[Path], paper_ids: list[str] | None = None) -> dict[str, Any]:
    reports = [document_report(path) for path in files]
    document_metrics = [compact_metrics(report) for report in reports]
    grouping_warnings: list[str] = []
    if paper_ids is None:
        paper_ids = []
        paper_id_sources = []
        for path, report in zip(files, reports):
            title_key = normalize_title(report["title"] or "")
            parent_key = normalize_title(path.parent.name)
            if title_key:
                paper_ids.append(f"title:{title_key}")
                paper_id_sources.append("title")
            elif parent_key:
                paper_ids.append(f"directory:{parent_key}")
                paper_id_sources.append("parent_directory")
            else:
                paper_ids.append(f"path:{str(path).casefold()}")
                paper_id_sources.append("path_fallback")
                grouping_warnings.append(f"could not infer title or parent directory; used path: {path}")
    else:
        paper_id_sources = ["explicit"] * len(paper_ids)
    paper_ids = [paper_id.strip() for paper_id in paper_ids]
    if len(paper_ids) == 1:
        paper_ids = paper_ids * len(files)
        paper_id_sources = paper_id_sources * len(files)
    if len(paper_ids) != len(files) or any(not paper_id.strip() for paper_id in paper_ids):
        raise UserError("--paper-id must be supplied once for all inputs or once per resolved input file")

    grouped: dict[str, list[dict[str, float]]] = {}
    for paper_id, metrics in zip(paper_ids, document_metrics):
        grouped.setdefault(paper_id, []).append(metrics)
    papers = [
        {
            "paper_id": paper_id,
            "source_count": len(items),
            "files": [str(path) for path, item_paper_id in zip(files, paper_ids) if item_paper_id == paper_id],
            "id_sources": sorted({source for source, item_paper_id in zip(paper_id_sources, paper_ids) if item_paper_id == paper_id}),
            "metrics": {name: round(statistics.fmean(item[name] for item in items), 6) for name in BASELINE_METRICS},
        }
        for paper_id, items in grouped.items()
    ]

    stats: dict[str, dict[str, float]] = {}
    for name in BASELINE_METRICS:
        values = [paper["metrics"][name] for paper in papers]
        stats[name] = {
            "mean": round(statistics.fmean(values), 6),
            "sd": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
        }
    count = len(papers)
    return {
        "schema": "helicon-style-baseline-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "document_count": count,
        "paper_count": count,
        "source_file_count": len(files),
        "status": "ok" if count >= MIN_BASELINE_PAPERS else f"thin(n={count})",
        "drift_alerts_enabled": count >= MIN_BASELINE_PAPERS,
        "documents": [
            {"path": str(path), "paper_id": paper_id, "paper_id_source": source, "metrics": metrics}
            for path, paper_id, source, metrics in zip(files, paper_ids, paper_id_sources, document_metrics)
        ],
        "papers": papers,
        "grouping": {
            "summary": f"grouped: {len(files)} files -> {count} papers",
            "groups": [{"paper_id": paper["paper_id"], "files": paper["files"]} for paper in papers],
            "warnings": grouping_warnings,
        },
        "metric_stats": stats,
    }


def read_baseline(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(read_utf8(path))
    except json.JSONDecodeError as exc:
        raise UserError(f"invalid baseline JSON: {path} ({exc})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("metric_stats"), dict) or "document_count" not in data:
        raise UserError(f"not a HElicon baseline JSON: {path}")
    for name in BASELINE_METRICS:
        item = data["metric_stats"].get(name)
        if not isinstance(item, dict) or not isinstance(item.get("mean"), (int, float)) or not isinstance(item.get("sd"), (int, float)):
            raise UserError(f"baseline JSON is missing metric {name!r}: {path}")
    if not isinstance(data["document_count"], int) or data["document_count"] < 1:
        raise UserError(f"baseline JSON has invalid document_count: {path}")
    return data


def comparison(baseline: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    current = compact_metrics(report)
    deviations: dict[str, dict[str, Any]] = {}
    for name in BASELINE_METRICS:
        center = float(baseline["metric_stats"][name]["mean"])
        sd = float(baseline["metric_stats"][name]["sd"])
        value = current[name]
        z = (value - center) / sd if sd > 0 else None
        deviations[name] = {
            "value": value,
            "baseline_mean": center,
            "baseline_sd": sd,
            "sd_distance": round(z, 4) if z is not None else None,
        }
    count = int(baseline["document_count"])
    thin = count < MIN_BASELINE_PAPERS
    return {
        "target": report["path"],
        "baseline_status": f"thin(n={count})" if thin else "ok",
        "drift_alerts_enabled": not thin,
        "deviations": deviations,
    }


def print_human(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def write_json(path: Path, data: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise UserError(f"cannot write {path}: {exc}") from exc


def add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_json_flag(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    report = subparsers.add_parser("report", help="report metrics for files or a directory")
    report.add_argument("inputs", nargs="+", help=".tex, .md, .txt, or directory")
    add_json_flag(report)

    baseline = subparsers.add_parser("baseline", help="build a local baseline JSON")
    baseline.add_argument("inputs", nargs="+", help="documents or directories")
    baseline.add_argument(
        "--paper-id",
        action="append",
        help="paper identity; supply once for all inputs or once per resolved input file",
    )
    baseline.add_argument("--output", required=True, help="local fingerprint JSON path")
    add_json_flag(baseline)

    compare = subparsers.add_parser("compare", help="compare a document with a baseline")
    compare.add_argument("baseline", help="baseline JSON")
    compare.add_argument("input", help="target document")
    add_json_flag(compare)

    drift = subparsers.add_parser("drift", help="report qualified baseline drift")
    drift.add_argument("baseline", help="baseline JSON")
    drift.add_argument("input", help="target document")
    drift.add_argument("--threshold", type=float, default=1.5, help="absolute SD distance")
    add_json_flag(drift)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "report":
        files = input_files(args.inputs)
        return {"command": "report", "documents": [document_report(path) for path in files]}
    if args.command == "baseline":
        files = input_files(args.inputs)
        data = baseline_data(files, args.paper_id)
        output = Path(args.output)
        write_json(output, data)
        return {"command": "baseline", "output": str(output), "baseline": data}
    if args.command in {"compare", "drift"}:
        baseline = read_baseline(Path(args.baseline))
        files = input_files([args.input])
        if len(files) != 1:
            raise UserError("compare and drift require exactly one target document")
        result = comparison(baseline, document_report(files[0]))
        result["command"] = args.command
        if args.command == "drift":
            warnings: list[dict[str, Any]] = []
            if result["drift_alerts_enabled"]:
                for name, item in result["deviations"].items():
                    distance = item["sd_distance"]
                    if distance is not None and abs(distance) > args.threshold:
                        warnings.append({"metric": name, "sd_distance": distance})
            result["drift_warnings"] = warnings
            result["threshold_sd"] = args.threshold
        return result
    raise UserError(f"unsupported command: {args.command}")


def main() -> int:
    parser = build_parser()
    json_requested = "--json" in sys.argv
    try:
        args = parser.parse_args()
        data = run(args)
        print_human(data)
        return 0
    except UserError as exc:
        if json_requested:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
