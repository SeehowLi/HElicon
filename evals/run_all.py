#!/usr/bin/env python3
"""Run repository-safe synthetic regressions; never claim capability efficacy."""
from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CASES = EVALS / "cases"
FIXTURES = EVALS / "fixtures"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    import latex_guard  # noqa: E402
    import target_eval  # noqa: E402
except ImportError as exc:
    print(json.dumps({
        "schema": "helicon-regression-summary-v1",
        "pipeline_runnable": False,
        "capability_validated": False,
        "evidence_class": "self-authored-fixture",
        "status": "harness-error",
        "error": str(exc),
    }, ensure_ascii=False, indent=2))
    raise SystemExit(2) from exc


class HarnessError(Exception):
    """Invalid suite data or an unusable execution environment."""


def repo_path(raw: str) -> Path:
    path = (ROOT / raw).resolve()
    if ROOT not in path.parents or not path.is_file():
        raise HarnessError(f"invalid repository file: {raw}")
    return path


def fixture(raw: str) -> Path:
    path = (FIXTURES / raw).resolve()
    if path.parent != FIXTURES.resolve() or not path.is_file():
        raise HarnessError(f"invalid fixture file: {raw}")
    return path


def command(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def json_stdout(result: subprocess.CompletedProcess[str], label: str) -> dict[str, Any]:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"{label} did not emit one JSON object") from exc
    if not isinstance(payload, dict):
        raise HarnessError(f"{label} JSON root is not an object")
    return payload


def file_sha256(path: Path, prefix: bool = False) -> str:
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{value}" if prefix else value


def project_pack(root: Path, profile_fixture: Path, venue: str) -> Path:
    style = root / ".helicon" / "style"
    style.mkdir(parents=True)
    shutil.copyfile(profile_fixture, style / "target_profile.json")
    (root / ".helicon" / "project.yaml").write_text(
        "schema: helicon-project-v1\nfingerprint:\n"
        f"  target_venue: {json.dumps(venue, ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    return style


def case_result(case: dict[str, Any], checks: dict[str, bool], details: dict[str, Any]) -> dict[str, Any]:
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "id": case["id"],
        "status": "assertions-satisfied" if not failed else "assertions-failed",
        "evidence_class": case["evidence_class"],
        "provenance": case["provenance"],
        "contains_real_manuscript_text": case["contains_real_manuscript_text"],
        "failed_assertions": failed,
        "details": details,
    }


def run_selftest(case: dict[str, Any], _: Path) -> dict[str, Any]:
    expected = case["expected"]
    result = command(repo_path(case["input"]["script"]))
    integrity = command(repo_path(case["input"]["integrity_checker"]), str(ROOT))
    contamination = command(repo_path(case["input"]["contamination_checker"]), str(ROOT))
    pass_count = sum(line.startswith("PASS:") for line in result.stdout.splitlines())
    checks = {
        "exit_code": result.returncode == expected["exit_code"],
        "integrity_exit_code": integrity.returncode == expected["exit_code"],
        "contamination_exit_code": contamination.returncode == expected["exit_code"],
        "minimum_pass_count": pass_count >= expected["minimum_pass_count"],
        "failure_marker_absent": "FAIL:" not in result.stdout,
    }
    return case_result(case, checks, {
        "selftest_exit_code": result.returncode,
        "integrity_exit_code": integrity.returncode,
        "contamination_exit_code": contamination.returncode,
        "pass_count": pass_count,
    })


def representative_route_count(text: str) -> int:
    try:
        table = text.split("## Representative routes", 1)[1]
    except IndexError:
        return 0
    rows = [line for line in table.splitlines() if line.startswith("|")]
    return sum(not line.startswith("|---") and "| Input wording |" not in line for line in rows)


def run_router_contracts(case: dict[str, Any], _: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    router = repo_path(inputs["router"]).read_text(encoding="utf-8")
    registry = repo_path(inputs["registry"]).read_text(encoding="utf-8")
    sync = command(repo_path(inputs["contract_checker"]))
    route_count = representative_route_count(router)
    checks = {
        "contract_exit_code": sync.returncode == expected["contract_exit_code"],
        "route_count": route_count >= expected["minimum_representative_routes"],
        "required_routes": all(value in router for value in inputs["required_routes"]),
        "registry_tokens": all(value in registry for value in inputs["required_registry_tokens"]),
        "fixed_target_field": expected["fixed_target_field"] in router,
        "canonical_arrow": expected["canonical_passes"] in router.replace(" ", ""),
        "historical_arrow_normalized": "historical compact form" in router,
    }
    return case_result(
        case,
        checks,
        {"contract_exit_code": sync.returncode, "representative_route_count": route_count},
    )


def resolver_args(case: dict[str, Any], project: Path) -> list[str]:
    args = ["--project-dir", str(project)]
    for pass_id in case["input"]["passes"]:
        args.extend(("--pass", pass_id))
    args.extend(("--section-type", case["input"]["section_type"]))
    return args


def run_target_profile_hash(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    project = temp_root / case["id"]
    style = project_pack(project, fixture(inputs["profile_fixture"]), inputs["project_venue"])
    profile = style / "target_profile.json"
    first = command(SCRIPTS / "resolve_target_profile.py", *resolver_args(case, project))
    first_payload = json_stdout(first, case["id"])
    first_hash = file_sha256(profile, prefix=True)
    profile.write_bytes(profile.read_bytes() + b"\n")
    second = command(SCRIPTS / "resolve_target_profile.py", *resolver_args(case, project))
    second_payload = json_stdout(second, case["id"])
    second_hash = file_sha256(profile, prefix=True)
    field_ids = sorted(item["id"] for item in first_payload.get("fields", []))
    checks = {
        "exit_code": first.returncode == second.returncode == expected["exit_code"],
        "resolved_status": first_payload.get("resolved_status") == expected["resolved_status"],
        "venue_match": first_payload.get("venue_match") is expected["venue_match"],
        "profile_schema": first_payload.get("schema") == expected["profile_schema"],
        "field_ids": field_ids == expected["field_ids"],
        "first_hash_exact": first_payload.get("profile_sha256") == first_hash,
        "second_hash_exact": second_payload.get("profile_sha256") == second_hash,
        "hash_prefix": str(first_payload.get("profile_sha256", "")).startswith(expected["hash_prefix"]),
        "hash_refresh_on_byte_change": first_hash != second_hash,
    }
    return case_result(
        case,
        checks,
        {"exit_codes": [first.returncode, second.returncode], "resolved_field_count": len(field_ids), "hash_refreshed": first_hash != second_hash},
    )


def preflight_args(case: dict[str, Any], fragment: Path, project: Path) -> list[str]:
    args = [str(fragment), "--project-dir", str(project), "--section-type", case["input"]["section_type"]]
    for pass_id in case["input"]["passes"]:
        args.extend(("--pass", pass_id))
    return args


def run_revision_preflight(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    project = temp_root / case["id"]
    project_pack(project, fixture(inputs["profile_fixture"]), inputs["project_venue"])
    clean = project / "clean.txt"
    flagged = project / "flagged.txt"
    shutil.copyfile(fixture(inputs["clean_fixture"]), clean)
    shutil.copyfile(fixture(inputs["flagged_fixture"]), flagged)
    clean_run = command(SCRIPTS / "revision_preflight.py", *preflight_args(case, clean, project))
    flagged_run = command(SCRIPTS / "revision_preflight.py", *preflight_args(case, flagged, project))
    clean_payload = json_stdout(clean_run, f"{case['id']} clean")
    flagged_payload = json_stdout(flagged_run, f"{case['id']} flagged")
    trigger_ids = set(flagged_payload.get("trigger_reason_ids", []))
    rule_ids = set(flagged_payload.get("ai_tells", {}).get("rule_ids", []))
    checks = {
        "exit_code": clean_run.returncode == flagged_run.returncode == expected["exit_code"],
        "clean_decision": clean_payload.get("decision") == expected["clean_decision"],
        "clean_has_no_triggers": clean_payload.get("trigger_reason_ids") == [],
        "flagged_decision": flagged_payload.get("decision") == expected["flagged_decision"],
        "required_trigger_ids": set(expected["required_trigger_ids"]).issubset(trigger_ids),
        "required_rule_ids": set(expected["required_rule_ids"]).issubset(rule_ids),
    }
    return case_result(
        case,
        checks,
        {"exit_codes": [clean_run.returncode, flagged_run.returncode], "clean_decision": clean_payload.get("decision"), "flagged_decision": flagged_payload.get("decision"), "flagged_trigger_ids": sorted(trigger_ids)},
    )


def approval_manifest(screening: Path, before: Path, target: Path) -> dict[str, Any]:
    return {
        "schema": target_eval.APPROVED_TARGET_SCHEMA,
        "source": target_eval.APPROVED_TARGET_SOURCE,
        "approval_status": "approved",
        "approved_utc": "2026-01-01T00:00:00+00:00",
        "content_stable_confirmed": True,
        "before_sha256": file_sha256(before),
        "target_sha256": file_sha256(target),
        "screening_sha256": file_sha256(screening),
    }


def rejected(call: Callable[[], Any], error: type[Exception]) -> bool:
    try:
        call()
    except error:
        return True
    return False


def run_target_eval_guards(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    style = temp_root / case["id"] / ".helicon" / "style" / "synthetic_eval"
    style.mkdir(parents=True)
    screening = style / "screening.json"
    screening.write_text(
        json.dumps({
            "schema": target_eval.APPROVED_SCREENING_SCHEMA,
            "decision_table": [
                {"dimension": name, "source": "rule"}
                for name in target_eval.DIMENSION_PASS
            ],
        }),
        encoding="utf-8",
    )
    seed = style / "seed.txt"
    goal = style / "goal.txt"
    output = style / "output.txt"
    shutil.copyfile(fixture(inputs["directional_seed_fixture"]), seed)
    shutil.copyfile(fixture(inputs["directional_goal_fixture"]), goal)
    shutil.copyfile(goal, output)
    manifest = style / "approval.json"
    manifest.write_text(json.dumps(approval_manifest(screening, seed, goal)), encoding="utf-8")
    admission = target_eval.verify_author_approved_target(screening, manifest, seed, goal, None)
    trailer, trailer_fields = target_eval.read_trailer(
        f"[HElicon] {inputs['project']} §{inputs['section']} · P3 → P4 → P5 · 1处 · "
        "frozen:0变化 · baseline:none · target:partial",
        None,
    )
    directional = target_eval.evaluate(
        seed, output, goal, None, trailer, trailer_fields, admission, True
    )

    stale = approval_manifest(screening, seed, goal)
    stale["target_sha256"] = "0" * 64
    manifest.write_text(json.dumps(stale), encoding="utf-8")
    stale_hash_rejected = rejected(
        lambda: target_eval.verify_author_approved_target(screening, manifest, seed, goal, None),
        target_eval.UserError,
    )

    preserve_before = style / "preserve_seed.txt"
    preserve_output = style / "preserve_output.txt"
    preserve_goal = style / "preserve_goal.txt"
    for path in (preserve_before, preserve_output, preserve_goal):
        shutil.copyfile(fixture(inputs["preservation_fixture"]), path)
    preserve_trailer, preserve_fields = target_eval.read_trailer(
        f"[HElicon] {inputs['project']} §{inputs['section']} · P3 → P4 → P5 · 0处 · "
        "frozen:0变化 · baseline:none · target:partial",
        None,
    )
    holdout = {"expected_target_status": "partial", "verified": True}
    preservation = target_eval.evaluate_preservation(
        preserve_before, preserve_output, preserve_goal, None, preserve_trailer, preserve_fields, holdout
    )
    preserve_output.write_text("The scheduler rewrites an accepted passage.\n", encoding="utf-8")
    changed_preservation = target_eval.evaluate_preservation(
        preserve_before, preserve_output, preserve_goal, None, preserve_trailer, preserve_fields, holdout
    )

    qualified = style / "qualified.txt"
    equivalent = style / "equivalent.txt"
    strengthened = style / "strengthened.txt"
    qualified.write_text("The scheduler may possibly support this workload.\n", encoding="utf-8")
    equivalent.write_text("The scheduler may support this workload.\n", encoding="utf-8")
    strengthened.write_text("The scheduler supports this workload.\n", encoding="utf-8")
    equivalent_guard = latex_guard.compare(qualified, equivalent, None, set())
    strengthened_guard = latex_guard.compare(qualified, strengthened, None, set())

    unsafe_manifest = style / "unsafe_approval.json"
    unsafe_manifest.write_text(
        json.dumps(approval_manifest(screening, qualified, strengthened)), encoding="utf-8"
    )
    unsafe_approved_target_rejected = rejected(
        lambda: target_eval.verify_author_approved_target(
            screening, unsafe_manifest, qualified, strengthened, None
        ),
        target_eval.UserError,
    )
    checks = {
        "approved_directional_passed": directional.get("passed") is expected["approved_directional_passed"],
        "rule_direction_status": directional["directional_evidence"]["ai_tell_rule_distance"]["status"] == expected["rule_direction_status"],
        "stale_hash_rejected": stale_hash_rejected is expected["stale_hash_rejected"],
        "preservation_passed": preservation.get("passed") is expected["preservation_passed"],
        "changed_preservation_exit_code": target_eval.result_exit_code(changed_preservation) == expected["changed_preservation_exit_code"],
        "equivalent_claim_scope_passed": equivalent_guard["passed"] is expected["equivalent_claim_scope_passed"],
        "strengthened_claim_scope_rejected": (not strengthened_guard["passed"]) is expected["strengthened_claim_scope_rejected"],
        "unsafe_approved_target_rejected": unsafe_approved_target_rejected is expected["unsafe_approved_target_rejected"],
    }
    return case_result(
        case,
        checks,
        {
            "directional_rule_status": directional["directional_evidence"]["ai_tell_rule_distance"]["status"],
            "structural_convergence_percent": directional["structural_distance"]["aggregate_convergence_percent"],
            "preservation_exit_code": target_eval.result_exit_code(preservation),
            "changed_preservation_exit_code": target_eval.result_exit_code(changed_preservation),
            "strengthened_claim_failed_categories": strengthened_guard["failed_categories"],
        },
    )


RUNNERS: dict[str, Callable[[dict[str, Any], Path], dict[str, Any]]] = {
    "selftest": run_selftest,
    "router-contracts": run_router_contracts,
    "target-profile-hash": run_target_profile_hash,
    "revision-preflight": run_revision_preflight,
    "target-eval-guards": run_target_eval_guards,
}


def load_cases() -> list[dict[str, Any]]:
    paths = sorted(CASES.glob("*.json"))
    if len(paths) != 5:
        raise HarnessError(f"expected 5 case definitions, found {len(paths)}")
    required = {
        "id", "input", "expected", "assertion", "evidence_class",
        "provenance", "contains_real_manuscript_text",
    }
    loaded: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not required.issubset(payload):
            raise HarnessError(f"invalid case definition: {path.name}")
        if payload.get("schema") != "helicon-eval-case-v1":
            raise HarnessError(f"invalid case schema: {path.name}")
        if payload["evidence_class"] != "self-authored-fixture":
            raise HarnessError(f"invalid evidence_class: {path.name}")
        if payload["provenance"] != "synthetic" or payload["contains_real_manuscript_text"] is not False:
            raise HarnessError(f"non-synthetic case metadata: {path.name}")
        if not isinstance(payload["input"], dict) or not isinstance(payload["expected"], dict):
            raise HarnessError(f"input and expected must be objects: {path.name}")
        if not isinstance(payload["assertion"], str) or not payload["assertion"].strip():
            raise HarnessError(f"assertion must be a non-empty string: {path.name}")
        if payload["id"] not in RUNNERS:
            raise HarnessError(f"unknown case id: {payload['id']}")
        loaded.append(payload)
    if len({item["id"] for item in loaded}) != len(loaded):
        raise HarnessError("duplicate case id")
    return loaded


def main() -> int:
    try:
        cases = load_cases()
        with tempfile.TemporaryDirectory(prefix="helicon-evals-") as raw_temp:
            temp_root = Path(raw_temp)
            results = [RUNNERS[case["id"]](case, temp_root) for case in cases]
    except (
        HarnessError,
        OSError,
        ImportError,
        AttributeError,
        target_eval.UserError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(json.dumps({
            "schema": "helicon-regression-summary-v1",
            "pipeline_runnable": False,
            "capability_validated": False,
            "evidence_class": "self-authored-fixture",
            "status": "harness-error",
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 2

    satisfied = all(result["status"] == "assertions-satisfied" for result in results)
    print(json.dumps({
        "schema": "helicon-regression-summary-v1",
        "pipeline_runnable": True,
        "capability_validated": False,
        "evidence_class": "self-authored-fixture",
        "interpretation": "Synthetic fixtures prove only that the regression pipeline is runnable.",
        "status": "pipeline-runnable" if satisfied else "regression-assertions-failed",
        "groups_satisfied": sum(
            result["status"] == "assertions-satisfied" for result in results
        ),
        "groups_total": len(results),
        "groups": results,
    }, ensure_ascii=False, indent=2))
    return 0 if satisfied else 1


if __name__ == "__main__":
    raise SystemExit(main())
