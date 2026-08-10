#!/usr/bin/env python3
"""Check HElicon core files for project-specific contamination."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_BLOCKLIST = [
    "sp27.pdf",
    "NDSS27_submit1.pdf",
    "Review_Usenix",
    "PaperGuide",
    "SNIP_SP27",
    "CKKS-KNN",
]

ALLOWED_PROJECT_MENTIONS = {
    "NOMOS": []
}

NUMERIC_FACT = re.compile(r"\b\d+(?:\.\d+)?\s*(?:x|X|%|ms|s|GB|MB|KB|bits?)(?![A-Za-z0-9])")
EPRINT = re.compile(r"\b(?:20[0-2][0-9])/(?:[0-9]{3,5})\b|\b20[0-2][0-9]-[0-9]{3,5}\b")

NUMERIC_OK_FILES = {
    "references/pass_pipeline.md",
    "references/language_polish.md",
    "references/deadline_compression.md",
    "references/style_baseline_policy.md",
    "references/intent_router.md",
}
NUMERIC_PREFIXES = ("threshold:", "budget:", "target:", "limit:", "range:")
NUMERIC_MARKER = "<!-- helicon:allow-numeric -->"
PRIVATE_ARTIFACT_NAMES = {
    "target_profile.json",
    "target_screening.json",
    "revision_direction.json",
    "holdout_manifest.json",
    "target_eval.json",
}


def is_allowed_line(token: str, line: str) -> bool:
    return any(allowed in line for allowed in ALLOWED_PROJECT_MENTIONS.get(token, []))


def allows_numeric_fact(rel: str, line: str) -> bool:
    """Allow explicit policy thresholds without weakening other checks."""
    if rel in NUMERIC_OK_FILES or NUMERIC_MARKER in line:
        return True
    normalized = re.sub(r"^\s*(?:[-*+]\s*)+", "", line).lstrip().lower()
    return normalized.startswith(NUMERIC_PREFIXES)


def scan_file(path: Path, root: Path) -> list[str]:
    rel = path.relative_to(root).as_posix()
    if ".git/" in rel:
        return []
    findings: list[str] = []
    if ".helicon" in path.relative_to(root).parts:
        findings.append(f"{rel}: private .helicon artifact inside skill repository")
    if path.name in PRIVATE_ARTIFACT_NAMES:
        findings.append(f"{rel}: private target artifact filename")
    if "/exemplars/" in f"/{rel}" and rel != "templates/exemplar_card.md":
        findings.append(f"{rel}: filled exemplar card inside skill repository")
    if rel.startswith("scripts/"):
        return findings
    if path.suffix.lower() not in {".md", ".yaml", ".yml", ".csv", ".json"}:
        return findings
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for token in DEFAULT_BLOCKLIST:
            if token in line:
                findings.append(f"{rel}:{lineno}: blocked token {token!r}")
        for token in ALLOWED_PROJECT_MENTIONS:
            if token in line and not is_allowed_line(token, line):
                findings.append(f"{rel}:{lineno}: project token {token!r}")
        if (
            rel.startswith("references/")
            and not allows_numeric_fact(rel, line)
            and NUMERIC_FACT.search(line)
        ):
            findings.append(f"{rel}:{lineno}: numeric result-like token")
        if EPRINT.search(line):
            findings.append(f"{rel}:{lineno}: ePrint-like identifier")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    targets = [p for p in root.rglob("*") if p.is_file()]
    findings: list[str] = []
    for path in targets:
        findings.extend(scan_file(path, root))
    if findings:
        print("Core contamination check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Core contamination check passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
