#!/usr/bin/env python3
"""Check HElicon core files for project-specific contamination."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

PRIVATE_PROJECT_TOKEN_SHA256 = frozenset(
    {
        "663efa1518d37bceeb16ff815e480eec81bf04c4156b42ac3e330a9cfd565fdd",
        "350758b0184945a325a2792d34f7de0539f99641837f450eb04ecae1fac7124f",
        "8384e0ba4b9db56bcf5c806b153603313d17a0b75e30aba9662ec5772aa8ee9a",
        "5111124f8cd7267e336944d87e243ace292bb6515abd30543c303d33422ce4b9",
        "b27a4f57f9d7b89fddbb1bbb8c97927f2707b8637d35988a779f56e027190b83",
        "394f322976d014c72d80df2a46a5ebbbd3765558e44ae2bae705c881c5228e10",
    }
)
PRIVATE_PROJECT_TOKEN_COUNT = 6
PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256 = (
    "bfc62c0661aa5e34baf279c924d405f1fbb8c028e74ffa0cc65682208b81d60a"
)
PROJECT_MENTION_SHA256 = frozenset(
    {"d1a52efc266a3bf735265ebd8bf73166268049054784dfa42293f460bebbda5d"}
)
PROJECT_MENTION_COUNT = 1
PROJECT_MENTION_MANIFEST_SHA256 = (
    "7581fc6d5284feb16fbc9d885601cc9a97585999b71867a85a23845aaf21691c"
)
PRIVATE_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")

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
CORE_TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".csv", ".json"}
EVAL_TEXT_SUFFIXES = {".txt", ".py"}


def private_token_manifest(private_token_hashes: frozenset[str]) -> bytes:
    return ("\n".join(sorted(private_token_hashes)) + "\n").encode("ascii")


def validate_private_token_hashes(
    private_token_hashes: frozenset[str] = PRIVATE_PROJECT_TOKEN_SHA256,
    expected_count: int = PRIVATE_PROJECT_TOKEN_COUNT,
    expected_manifest_sha256: str = PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256,
) -> None:
    if (
        not isinstance(private_token_hashes, frozenset)
        or len(private_token_hashes) != expected_count
        or not all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in private_token_hashes)
    ):
        raise ValueError("private identifier digest set missing or malformed")
    if hashlib.sha256(private_token_manifest(private_token_hashes)).hexdigest() != expected_manifest_sha256:
        raise ValueError("private identifier digest set incomplete or replaced")


def line_has_private_token(line: str, private_token_hashes: frozenset[str]) -> bool:
    # Token-level matching avoids publishing private literals but is weaker than
    # substring matching: an identifier embedded as xTOKENy is no longer found.
    return any(
        hashlib.sha256(token.casefold().encode("utf-8")).hexdigest() in private_token_hashes
        for token in PRIVATE_TOKEN_RE.findall(line)
    )


def validate_project_mention_hashes(
    project_mention_hashes: frozenset[str] = PROJECT_MENTION_SHA256,
    expected_count: int = PROJECT_MENTION_COUNT,
    expected_manifest_sha256: str = PROJECT_MENTION_MANIFEST_SHA256,
) -> None:
    validate_private_token_hashes(
        project_mention_hashes,
        expected_count,
        expected_manifest_sha256,
    )


def allows_numeric_fact(rel: str, line: str) -> bool:
    """Allow explicit policy thresholds without weakening other checks."""
    if rel in NUMERIC_OK_FILES or NUMERIC_MARKER in line:
        return True
    normalized = re.sub(r"^\s*(?:[-*+]\s*)+", "", line).lstrip().lower()
    return normalized.startswith(NUMERIC_PREFIXES)


def scan_file(
    path: Path,
    root: Path,
    private_token_hashes: frozenset[str] = PRIVATE_PROJECT_TOKEN_SHA256,
    project_mention_hashes: frozenset[str] = PROJECT_MENTION_SHA256,
) -> list[str]:
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
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        findings.append(f"{rel}: unscannable file (invalid UTF-8)")
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line_has_private_token(line, private_token_hashes):
            findings.append(f"{rel}:{lineno}: private identifier digest match")
        if line_has_private_token(line, project_mention_hashes):
            findings.append(f"{rel}:{lineno}: project mention digest match")
    suffix = path.suffix.lower()
    if suffix not in CORE_TEXT_SUFFIXES and not (
        rel.startswith("evals/") and suffix in EVAL_TEXT_SUFFIXES
    ):
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
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
    try:
        validate_private_token_hashes()
        validate_project_mention_hashes()
    except ValueError as exc:
        print(f"Core contamination check configuration failed: {exc}")
        return 2
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
