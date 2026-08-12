#!/usr/bin/env python3
"""Quantify P5 AI-tell rules R1-R14 from language_polish.md.

This script owns every numbered P5 audit rule. It does not own the separate
Chinese-literal and sentence-level overclaim checks in check_style_rules.py.
Future pass-pipeline contract: consume its single JSON object after P4; the
default is report-only exit 0, while --max-density or --exit-code-on may make a
configured violation exit 1. Input/configuration errors exit 2.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Iterable

EXTENSIONS = {".tex", ".md", ".txt"}
SEVERITY_RANK = {"info": 0, "warn": 1, "block": 2}
PRESERVED_HEDGES = ("suggests", "is consistent with", "we conjecture", "appears to")
SUPPORT_RE = re.compile(r"\\(?:cite\w*|ref|autoref|eqref|cref)\s*\{|\b\d+(?:\.\d+)?\s*(?:%|ms|s|GB|MB|KB|bits?)?\b")
RULE2_RE = re.compile(
    r"\b(?:secure\s+and\s+efficient|significantly|dramatically|practical|scalable|efficient)\b",
    re.IGNORECASE,
)
RULE2_SUPPORT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|x|×|ns|us|ms|s|sec(?:onds?)?|min(?:utes?)?|h(?:ours?)?|"
    r"KB|MB|GB|TB|bits?|bytes?|queries?|records?|vectors?|samples?|entries?|slots?|cores?|threads?)\b|"
    r"\b(?:latency|throughput|runtime|memory|communication|bandwidth|accuracy|error|speedup|CPU|GPU|"
    r"threat model|security model|semi-honest|malicious|IND-CPA|IND-CCA)\b|"
    r"\b(?:under|for|on)\s+(?:the\s+)?(?:evaluated|fixed|specified|target)\s+(?:dataset|workload|batch)\b",
    re.IGNORECASE,
)
RULE10_EVIDENCE_RE = re.compile(
    r"\\(?:cite\w*|(?:auto|eq|c|C)?ref)\s*\{|"
    r"\b\d+(?:\.\d+)?\s*(?:%|x|×|ns|us|ms|s|sec(?:onds?)?|min(?:utes?)?|h(?:ours?)?|"
    r"KB|MB|GB|TB|bits?|bytes?|queries?|records?|vectors?|samples?|entries?|slots?|cores?|threads?)"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)
RULE10_MECHANISM_RE = re.compile(
    r"\b(?:by|via|through)\s+(?:[A-Za-z][\w-]*\s+){0,3}[A-Za-z][\w-]*ing\b|"
    r"\b(?:using|applying|employing|computing|evaluating|encoding|encrypting|decrypting|"
    r"packing|batching|precomputing|caching|parallelizing|offloading)\s+"
    r"(?:an?\s+|the\s+)?[A-Za-z][\w-]*(?:\s+[A-Za-z][\w-]*){0,4}",
    re.IGNORECASE,
)


@dataclass
class Finding:
    file: str
    line: int
    column: int
    rule: int
    severity: str
    match: str
    suggestion: str


@dataclass(frozen=True)
class PatternRule:
    number: int
    severity: str
    pattern: re.Pattern[str]
    suggestion: str


PATTERN_RULES = (
    PatternRule(1, "warn", re.compile(r"\b(?:groundbreaking|transformative|pivotal|remarkable|revolutionary|unprecedented|game-changing|breakthrough)\b", re.IGNORECASE), "Remove inflated importance unless a precise, supported comparison earns it."),
    PatternRule(3, "block", re.compile(r"\b(?:technical packaging|large model privacy inference|homomorphic realization|full homomorphic encryption)\b", re.IGNORECASE), "Use the glossary's technically valid, scoped term."),
    PatternRule(4, "info", re.compile(r"\b(?:delve|tapestry|landscape|showcase|seamless|intricate|leverage|underscore)\w*\b", re.IGNORECASE), "Keep only a precise technical use; otherwise state the mechanism directly."),
    PatternRule(6, "warn", re.compile(r"\b(?:it is (?:important|worthwhile|notable) to (?:note|observe)|it should be noted that)\b", re.IGNORECASE), "Remove the shell and state the supported claim directly."),
    PatternRule(8, "warn", re.compile(r"\b(?:in other words|that is|essentially)\b", re.IGNORECASE), "Check whether this repeats the previous claim; keep formal definitions and real disambiguation."),
    PatternRule(10, "info", re.compile(r",\s+(?:thereby\s+)?\w+ing\b[^.!?]{0,90}(?=[.!?])", re.IGNORECASE), "Give the clause a clear subject and mechanism, or remove unsupported pseudo-depth."),
    PatternRule(11, "info", re.compile(r"\b(?:serves as|stands as|boasts)\b", re.IGNORECASE), "Prefer is or has unless the role distinction is technical."),
    PatternRule(12, "warn", re.compile(r"\bnot only\b[^.!?]{0,120}\bbut also\b", re.IGNORECASE), "State the direct relation unless the contrast is logically necessary."),
    PatternRule(13, "info", re.compile(r"\b[A-Za-z][\w-]+,\s+[A-Za-z][\w-]+,\s+and\s+[A-Za-z][\w-]+\b"), "Confirm that the source genuinely contains three distinct items."),
)


class UserError(Exception):
    """A concise command-line error."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except FileNotFoundError as exc:
        raise UserError(f"file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise UserError(f"file is not valid UTF-8: {path} ({exc})") from exc
    except OSError as exc:
        raise UserError(f"cannot read {path}: {exc}") from exc


def collect_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        if not path.exists():
            raise UserError(f"input does not exist: {path}")
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() in EXTENSIONS)
        elif path.suffix.lower() in EXTENSIONS:
            files.append(path)
        else:
            raise UserError(f"unsupported input type: {path}")
    unique = sorted({path.resolve() for path in files}, key=lambda item: str(item).lower())
    if not unique:
        raise UserError("no .tex, .md, or .txt files found")
    return unique


def location(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    prior = text.rfind("\n", 0, offset)
    column = offset + 1 if prior < 0 else offset - prior
    return line, column


def paragraph_spans(text: str) -> Iterable[tuple[int, str]]:
    for match in re.finditer(r"(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", text, re.DOTALL):
        paragraph = match.group(1)
        if paragraph.strip():
            yield match.start(1), paragraph


def sentence_spans(text: str) -> Iterable[tuple[int, str]]:
    for match in re.finditer(r"[^.!?\n]+[.!?]?", text):
        if match.group(0).strip():
            yield match.start(), match.group(0)


def add_finding(findings: list[Finding], path: Path, text: str, offset: int, rule: int, severity: str, matched: str, suggestion: str) -> None:
    line, column = location(text, offset)
    findings.append(Finding(str(path), line, column, rule, severity, re.sub(r"\s+", " ", matched).strip(), suggestion))


def scan_text(text: str, path: Path = Path("<memory>")) -> list[Finding]:
    findings: list[Finding] = []
    for rule in PATTERN_RULES:
        for match in rule.pattern.finditer(text):
            if rule.number == 10 and (
                RULE10_EVIDENCE_RE.search(match.group(0))
                or RULE10_MECHANISM_RE.search(match.group(0))
            ):
                continue
            add_finding(findings, path, text, match.start(), rule.number, rule.severity, match.group(0), rule.suggestion)

    # Rule 2: an adjective is scoped when its sentence or one adjacent sentence
    # names a metric, workload, hardware setting, or threat/security model.
    sentences = list(sentence_spans(text))
    for match in RULE2_RE.finditer(text):
        index = next(
            (i for i, (start, sentence) in enumerate(sentences) if start <= match.start() < start + len(sentence)),
            None,
        )
        context = " ".join(
            sentence for _, sentence in sentences[max(0, (index or 0) - 1):min(len(sentences), (index or 0) + 2)]
        )
        if RULE2_SUPPORT_RE.search(context):
            continue
        add_finding(
            findings,
            path,
            text,
            match.start(),
            2,
            "warn",
            match.group(0),
            "State the metric, workload, hardware, or threat model that scopes this adjective.",
        )

    # Rule 7: several abstract nominalizations in one sentence can hide the actor.
    nominal_re = re.compile(r"\b[A-Za-z]+(?:tion|sion|ment|ance|ence|ity|ization)\b", re.IGNORECASE)
    for start, sentence in sentence_spans(text):
        hits = nominal_re.findall(sentence)
        if len(hits) >= 3:
            add_finding(findings, path, text, start, 7, "info", ", ".join(hits[:4]), "Name the actor and action; keep established operation names unchanged.")

    # Rule 5: repeated sentence-opening connectors within one paragraph.
    opening_connective = re.compile(r"(?:^|(?<=[.!?])\s+)(Moreover|Furthermore|Additionally|However),?", re.IGNORECASE)
    for start, paragraph in paragraph_spans(text):
        hits = list(opening_connective.finditer(paragraph))
        if len(hits) >= 3:
            add_finding(
                findings,
                path,
                text,
                start + hits[0].start(1),
                5,
                "warn",
                ", ".join(match.group(1) for match in hits),
                "Keep only connectors that name distinct logical relations; restructure the paragraph if needed.",
            )

    # Rule 9: preserve supported hedges; warn on unsupported or excessive clusters.
    for start, paragraph in paragraph_spans(text):
        lowered = paragraph.lower()
        hits = [phrase for phrase in PRESERVED_HEDGES for _ in re.finditer(rf"\b{re.escape(phrase)}\b", lowered)]
        if hits and (len(hits) > 3 or not SUPPORT_RE.search(paragraph)):
            first = min((lowered.find(phrase) for phrase in set(hits) if lowered.find(phrase) >= 0), default=0)
            add_finding(findings, path, text, start + first, 9, "warn", ", ".join(hits), "Preserve evidence-bound hedging, but remove unsupported hedge stacking.")

    # Rule 14: one density finding per document, never a blanket punctuation ban.
    words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text)
    dash_count = text.count("—")
    density = dash_count * 1000 / max(len(words), 1)
    if dash_count and density > 3:
        add_finding(findings, path, text, text.index("—"), 14, "warn", f"{dash_count} em dashes ({density:.2f}/1000 words)", "Keep at most the domain threshold and do not substitute a dash for a colon or semicolon.")

    return sorted(findings, key=lambda item: (item.file.lower(), item.line, item.column, item.rule))


def scan(path: Path) -> list[Finding]:
    return scan_text(read_utf8(path), path)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="files or directories")
    parser.add_argument("--severity", choices=("block", "warn", "info"), default="info", help="minimum severity to display")
    parser.add_argument("--exit-code-on", choices=("block", "warn", "info"), help="return nonzero when this severity or higher is found")
    parser.add_argument("--max-density", type=float, help="return exit 1 when total findings per 1000 words exceeds this value")
    parser.add_argument("--json", action="store_true", help="accepted for backward compatibility; output is always JSON")
    return parser


def main() -> int:
    parser = build_parser()
    try:
        args = parser.parse_args()
        if args.max_density is not None and args.max_density < 0:
            raise UserError("--max-density must be non-negative")
        files = collect_files(args.paths)
        all_findings = [finding for path in files for finding in scan(path)]
        shown = [finding for finding in all_findings if SEVERITY_RANK[finding.severity] >= SEVERITY_RANK[args.severity]]
        word_count = sum(
            len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", read_utf8(path)))
            for path in files
        )
        by_rule = []
        for rule in range(1, 15):
            hits = [item for item in shown if item.rule == rule]
            by_rule.append({
                "rule": f"R{rule:02d}",
                "hit_count": len(hits),
                "positions": [
                    {"file": item.file, "line": item.line, "column": item.column}
                    for item in hits
                ],
                "density_per_1000_words": round(1000.0 * len(hits) / max(word_count, 1), 6),
            })
        total_density = 1000.0 * len(shown) / max(word_count, 1)
        threshold_exceeded = args.max_density is not None and total_density > args.max_density
        print(json.dumps({
            "schema": "helicon-ai-tell-check-v1",
            "files": [str(path) for path in files],
            "word_count": word_count,
            "rules": by_rule,
            "findings": [asdict(item) for item in shown],
            "finding_count": len(shown),
            "total_density_per_1000_words": round(total_density, 6),
            "max_density": args.max_density,
            "threshold_exceeded": threshold_exceeded,
        }, ensure_ascii=False, indent=2))
        if args.exit_code_on:
            threshold = SEVERITY_RANK[args.exit_code_on]
            if any(SEVERITY_RANK[item.severity] >= threshold for item in all_findings):
                return 1
        if threshold_exceeded:
            return 1
        return 0
    except (UserError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema": "helicon-ai-tell-check-v1", "ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
