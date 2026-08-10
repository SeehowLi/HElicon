#!/usr/bin/env python3
"""Check machine-enforced synchronization among HElicon docs and scripts."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any

RULE_RE = re.compile(r"(?m)^(\d+)\.\s+\*\*")
COMMAND_RE = re.compile(r"\bH-[A-Z][A-Z0-9-]*\b")
THRESHOLD_RE = re.compile(r"threshold:.*?at least\s+(\d+)\s+distinct papers", re.IGNORECASE)


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
