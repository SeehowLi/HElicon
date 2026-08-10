#!/usr/bin/env python3
"""Check machine-enforced synchronization among HElicon docs and scripts."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable

import check_ai_tells

RULE_RE = re.compile(r"(?m)^(\d+)\.\s+\*\*")
COMMAND_RE = re.compile(r"\bH-[A-Z][A-Z0-9-]*\b")
THRESHOLD_RE = re.compile(r"threshold:.*?at least\s+(\d+)\s+distinct papers", re.IGNORECASE)

# Every backticked item in the numbered P5 list has an executable contract.
# "context-dependent" cases require both a trigger and an exemption sample.
# "protected" items are examples the rule explicitly says not to flag.
RULE_KEYWORD_CASES: dict[tuple[int, str], dict[str, str]] = {
    (1, "groundbreaking"): {"kind": "direct", "positive": "This is a groundbreaking method."},
    (1, "transformative"): {"kind": "direct", "positive": "This is a transformative method."},
    (1, "pivotal"): {"kind": "direct", "positive": "This is a pivotal method."},
    (1, "remarkable"): {"kind": "direct", "positive": "This is a remarkable method."},
    (2, "significantly"): {
        "kind": "context-dependent",
        "positive": "The method is significantly better.",
        "negative": "The method is significantly faster. Latency is 12 ms on one CPU core.",
    },
    (2, "dramatically"): {
        "kind": "context-dependent",
        "positive": "The method is dramatically better.",
        "negative": "The method is dramatically faster. Latency is 12 ms on one CPU core.",
    },
    (2, "practical"): {
        "kind": "context-dependent",
        "positive": "The method is practical.",
        "negative": "The method is practical. Latency is 12 ms on one CPU core.",
    },
    (2, "scalable"): {
        "kind": "context-dependent",
        "positive": "The method is scalable.",
        "negative": "The method is scalable. Latency is 12 ms on one CPU core.",
    },
    (2, "efficient"): {
        "kind": "context-dependent",
        "positive": "The method is efficient.",
        "negative": "The method is efficient. Latency is 12 ms on one CPU core.",
    },
    (2, "secure and efficient"): {
        "kind": "context-dependent",
        "positive": "The method is secure and efficient.",
        "negative": "The method is secure and efficient under the malicious threat model.",
    },
    (3, "technical packaging"): {"kind": "direct", "positive": "We use technical packaging."},
    (3, "large model privacy inference"): {"kind": "direct", "positive": "We study large model privacy inference."},
    (3, "homomorphic realization"): {"kind": "direct", "positive": "We provide a homomorphic realization."},
    (3, "full homomorphic encryption"): {"kind": "direct", "positive": "We use full homomorphic encryption."},
    (4, "delve"): {"kind": "direct", "positive": "We delve into the construction."},
    (4, "tapestry"): {"kind": "direct", "positive": "The design is a tapestry of techniques."},
    (4, "landscape"): {"kind": "direct", "positive": "We survey the landscape."},
    (4, "showcase"): {"kind": "direct", "positive": "The results showcase the method."},
    (4, "seamless"): {"kind": "direct", "positive": "The method is seamless."},
    (4, "intricate"): {"kind": "direct", "positive": "The method is intricate."},
    (4, "leverage"): {"kind": "direct", "positive": "We leverage the construction."},
    (4, "underscore"): {"kind": "direct", "positive": "The results underscore the claim."},
    (5, "Moreover, furthermore, additionally"): {
        "kind": "context-dependent",
        "positive": "Moreover, we define A. Furthermore, we evaluate B. Additionally, we report C.",
        "negative": "Moreover, we define A. Furthermore, we evaluate B.",
    },
    (6, "It is important to note that"): {
        "kind": "direct",
        "positive": "It is important to note that the method works.",
    },
    (7, "key switching"): {"kind": "protected", "negative": "We perform key switching."},
    (8, "in other words"): {"kind": "direct", "positive": "In other words, the claim is repeated."},
    (8, "that is"): {"kind": "direct", "positive": "That is, the claim is repeated."},
    (8, "essentially"): {"kind": "direct", "positive": "Essentially, the claim is repeated."},
    (10, "-ing"): {
        "kind": "context-dependent",
        "positive": "The method improves the design, highlighting its broad potential.",
        "negative": "The method is faster, reducing latency to 12 ms on one CPU core.",
    },
    (11, "is"): {"kind": "protected", "negative": "The method is a protocol."},
    (11, "has"): {"kind": "protected", "negative": "The method has two phases."},
    (11, "serves as"): {"kind": "direct", "positive": "The method serves as a protocol."},
    (11, "stands as"): {"kind": "direct", "positive": "The method stands as a protocol."},
    (11, "boasts"): {"kind": "direct", "positive": "The method boasts a simple design."},
    (12, "not only X but also Y"): {
        "kind": "direct",
        "positive": "The method not only saves time but also saves memory.",
    },
}


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def emitted_rule_numbers(path: Path) -> set[int]:
    tree = ast.parse(read_utf8(path), filename=str(path))
    numbers: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id == "PatternRule" and node.args and isinstance(node.args[0], ast.Constant):
            numbers.add(int(node.args[0].value))
        elif node.func.id == "add_finding" and len(node.args) > 4 and isinstance(node.args[4], ast.Constant):
            numbers.add(int(node.args[4].value))
    return numbers


def documented_rule_keywords(polish_text: str) -> set[tuple[int, str]]:
    keywords: set[tuple[int, str]] = set()
    for line in polish_text.splitlines():
        match = re.match(r"^(\d+)\.\s+\*\*", line)
        if not match:
            continue
        number = int(match.group(1))
        keywords.update((number, value) for value in re.findall(r"`([^`]+)`", line))
    return keywords


def validate_rule_behaviors(
    polish_text: str,
    scanner: Callable[[str, Path], list[Any]] = check_ai_tells.scan_text,
) -> dict[str, Any]:
    documented = documented_rule_keywords(polish_text)
    registered = set(RULE_KEYWORD_CASES)
    errors: list[str] = []
    missing_cases = sorted(documented - registered)
    stale_cases = sorted(registered - documented)
    if missing_cases:
        errors.append(f"documented rule keywords lack behavior cases: {missing_cases}")
    if stale_cases:
        errors.append(f"behavior cases no longer documented: {stale_cases}")

    positive_count = 0
    negative_count = 0
    for number, keyword in sorted(documented & registered):
        case = RULE_KEYWORD_CASES[(number, keyword)]
        kind = case.get("kind", "")
        positive = case.get("positive")
        negative = case.get("negative")
        if kind == "context-dependent" and (not positive or not negative):
            errors.append(f"R{number:02d} `{keyword}` context-dependent case needs positive and negative samples")
        elif kind == "direct" and not positive:
            errors.append(f"R{number:02d} `{keyword}` direct case needs a positive sample")
        elif kind == "protected" and (positive or not negative):
            errors.append(f"R{number:02d} `{keyword}` protected case needs only a negative sample")
        elif kind not in {"direct", "context-dependent", "protected"}:
            errors.append(f"R{number:02d} `{keyword}` has unknown behavior kind: {kind!r}")

        if positive:
            positive_count += 1
            emitted = {finding.rule for finding in scanner(positive, Path("<contract-positive>"))}
            if number not in emitted:
                errors.append(f"R{number:02d} `{keyword}` positive sample did not emit its rule")
        if negative:
            negative_count += 1
            emitted = {finding.rule for finding in scanner(negative, Path("<contract-negative>"))}
            if number in emitted:
                errors.append(f"R{number:02d} `{keyword}` negative sample unexpectedly emitted its rule")

    return {
        "passed": not errors,
        "documented_keyword_count": len(documented),
        "registered_keyword_count": len(registered),
        "positive_sample_count": positive_count,
        "negative_sample_count": negative_count,
        "context_dependent": [
            f"R{number:02d}:{keyword}"
            for (number, keyword), case in sorted(RULE_KEYWORD_CASES.items())
            if case["kind"] == "context-dependent"
        ],
        "protected": [
            f"R{number:02d}:{keyword}"
            for (number, keyword), case in sorted(RULE_KEYWORD_CASES.items())
            if case["kind"] == "protected"
        ],
        "errors": errors,
    }


def description_text(skill_text: str) -> str:
    for line in skill_text.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return ""


def python_constant(path: Path, name: str) -> int | None:
    tree = ast.parse(read_utf8(path), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                return node.value.value
    return None


def validate_contracts(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    polish = read_utf8(root / "references/language_polish.md")
    documented_rules = {int(value) for value in RULE_RE.findall(polish)}
    emitted_rules = emitted_rule_numbers(root / "scripts/check_ai_tells.py")
    missing_rules = sorted(documented_rules - emitted_rules)
    extra_rules = sorted(emitted_rules - documented_rules)
    if missing_rules:
        errors.append(f"check_ai_tells.py does not emit documented rules: {missing_rules}")
    if extra_rules:
        errors.append(f"check_ai_tells.py emits undocumented rules: {extra_rules}")

    behavior = validate_rule_behaviors(polish)
    errors.extend(f"rule behavior: {error}" for error in behavior["errors"])

    registry_commands = set(COMMAND_RE.findall(read_utf8(root / "references/command_registry.md")))
    description_commands = set(COMMAND_RE.findall(description_text(read_utf8(root / "SKILL.md"))))
    unknown_description_commands = sorted(description_commands - registry_commands)
    if unknown_description_commands:
        errors.append(f"SKILL.md description names commands absent from registry: {unknown_description_commands}")

    policy = read_utf8(root / "references/style_baseline_policy.md")
    match = THRESHOLD_RE.search(policy)
    policy_threshold = int(match.group(1)) if match else None
    code_threshold = python_constant(root / "scripts/style_fingerprint.py", "MIN_BASELINE_PAPERS")
    if policy_threshold is None:
        errors.append("style_baseline_policy.md has no parseable distinct-paper threshold")
    if code_threshold is None:
        errors.append("style_fingerprint.py has no integer MIN_BASELINE_PAPERS")
    if policy_threshold is not None and code_threshold is not None and policy_threshold != code_threshold:
        errors.append(f"baseline threshold mismatch: policy={policy_threshold}, code={code_threshold}")

    return {
        "passed": not errors,
        "documented_rules": sorted(documented_rules),
        "emitted_rules": sorted(emitted_rules),
        "missing_rules": missing_rules,
        "extra_rules": extra_rules,
        "rule_behavior": behavior,
        "registry_command_count": len(registry_commands),
        "description_commands": sorted(description_commands),
        "unknown_description_commands": unknown_description_commands,
        "policy_threshold": policy_threshold,
        "code_threshold": code_threshold,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="HElicon repository root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    try:
        result = validate_contracts(Path(args.root))
    except (OSError, SyntaxError, ValueError) as exc:
        result = {"passed": False, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["passed"]:
        print(
            "Contract sync passed: "
            f"rules={result['emitted_rules']}, "
            f"keyword_samples={result['rule_behavior']['positive_sample_count']}+"
            f"{result['rule_behavior']['negative_sample_count']}, "
            f"description_commands={result['description_commands']}, "
            f"baseline_threshold={result['code_threshold']}"
        )
    else:
        print("Contract sync failed:")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
