#!/usr/bin/env python3
"""Apply the pass-aware mechanical contract before a P3-P7 candidate is delivered."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import check_immutable_set
import check_terminology_freeze


PASSES = ("P3", "P4", "P5", "P6", "P7")
P3_EXEMPTION = "glossary_terms"


class UserError(Exception):
    """A deterministic command or configuration error."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserError(message)


def check_summary(payload: dict[str, Any], applicable: bool) -> dict[str, Any]:
    return {
        "applicable": applicable,
        "passed": payload["replacement_count"] == 0,
        "replacement_count": payload["replacement_count"],
    }


def evaluate(pass_name: str, before: Path, after: Path, glossary: Path) -> dict[str, Any]:
    if pass_name not in PASSES:
        raise UserError(f"unsupported pass: {pass_name}")
    immutable = check_immutable_set.compare(before, after, glossary)
    forward = check_terminology_freeze.compare(before, after, glossary)
    residual = check_terminology_freeze.scan_residual(after, glossary)
    counts = {
        name: report["violation_count"]
        for name, report in immutable["categories"].items()
    }
    if pass_name == "P3":
        blocking_counts = {
            name: count for name, count in counts.items()
            if name != P3_EXEMPTION and count
        }
        exempted_counts = {P3_EXEMPTION: counts.get(P3_EXEMPTION, 0)}
        terminology_ok = forward["replacement_count"] == 0 and residual["replacement_count"] == 0
    else:
        blocking_counts = {name: count for name, count in counts.items() if count}
        exempted_counts = {}
        terminology_ok = True
    verdict = "proceed" if not blocking_counts and terminology_ok else "rollback"
    immutable_raw_exit = 0 if immutable["passed"] else 1
    immutable_effective_exit = 0 if not blocking_counts else 1
    return {
        "schema": "helicon-pass-scope-check-v1",
        "pass": pass_name,
        "immutable_exit_code": immutable_effective_exit,
        "immutable_raw_exit_code": immutable_raw_exit,
        "immutable_total_violations": immutable["total_violations"],
        "blocking_categories": sorted(blocking_counts),
        "blocking_category_counts": blocking_counts,
        "exempted_categories": sorted(exempted_counts),
        "exempted_category_counts": exempted_counts,
        "terminology_forward_check": check_summary(forward, pass_name == "P3"),
        "terminology_residual_check": check_summary(residual, pass_name == "P3"),
        "p3_glossary_exemption": "applied" if pass_name == "P3" else "not-applicable",
        "verdict": verdict,
    }


def parser() -> argparse.ArgumentParser:
    value = JsonArgumentParser(description=__doc__)
    value.add_argument("--pass", dest="pass_name", required=True, choices=PASSES)
    value.add_argument("before")
    value.add_argument("after")
    value.add_argument("--glossary", required=True)
    return value


def main() -> int:
    try:
        args = parser().parse_args()
        result = evaluate(
            args.pass_name,
            Path(args.before),
            Path(args.after),
            Path(args.glossary),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verdict"] == "proceed" else 1
    except (
        UserError,
        check_immutable_set.UserError,
        check_terminology_freeze.UserError,
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(json.dumps({
            "schema": "helicon-pass-scope-check-v1",
            "verdict": "error",
            "error": str(exc),
        }, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
