#!/usr/bin/env python3
"""Run repository-safe synthetic regressions; never claim capability efficacy."""
from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re
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
    import check_ai_tells  # noqa: E402
    import check_claim_strength  # noqa: E402
    import check_command_coverage  # noqa: E402
    import check_immutable_set  # noqa: E402
    import check_live_skill_binding  # noqa: E402
    import check_reference_reachability  # noqa: E402
    import check_terminology_freeze  # noqa: E402
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


def synthetic_word_count(text: str) -> int:
    import re

    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text))


def run_verifiability(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    mode = inputs["mode"]
    checker = repo_path(inputs["checker"])
    source_paths: list[Path] = []
    args: list[str]

    if mode == "ai-tells":
        input_path = fixture(inputs["fixture"])
        source_paths.append(input_path)
        args = [str(input_path)]
        if "max_density" in inputs:
            args.extend(["--max-density", str(inputs["max_density"])])
    else:
        before = fixture(inputs["before_fixture"])
        after_source = fixture(inputs["after_fixture"])
        source_paths.extend([before, after_source])
        text = after_source.read_text(encoding="utf-8")
        for replacement in inputs.get("replacements", []):
            if not isinstance(replacement, list) or len(replacement) != 2:
                raise HarnessError(f"invalid replacement in {case['id']}")
            old, new = replacement
            if old not in text:
                raise HarnessError(f"replacement source absent in {case['id']}: {old!r}")
            text = text.replace(old, new)
        after = temp_root / f"{case['id']}.txt"
        after.write_text(text, encoding="utf-8")
        source_paths.append(after)
        args = [str(before), str(after)]
        if mode in {"immutable", "terminology"}:
            args.extend(["--glossary", str(fixture(inputs["glossary_fixture"]))])

    result = command(checker, *args)
    payload = json_stdout(result, case["id"])
    counts = [synthetic_word_count(path.read_text(encoding="utf-8")) for path in source_paths]
    checks: dict[str, bool] = {
        "exit_code": result.returncode == expected["exit_code"],
        "fixture_word_range": all(150 <= count <= 300 for count in counts),
        "schema": payload.get("schema") == expected["schema"],
    }
    if "passed" in expected:
        checks["passed"] = payload.get("passed") is expected["passed"]
    if mode == "immutable":
        category = expected["category"]
        checks["category"] = payload["categories"][category]["violation_count"] >= expected.get("minimum_count", 1)
        checks["total"] = payload["total_violations"] >= expected.get("minimum_total", 0)
        if "maximum_count" in expected:
            checks["category_maximum"] = payload["categories"][category]["violation_count"] <= expected["maximum_count"]
        if "maximum_total" in expected:
            checks["total_maximum"] = payload["total_violations"] <= expected["maximum_total"]
        if "relocation_marker_prefix" in expected:
            checks["relocation"] = any(
                item["marker"].startswith(expected["relocation_marker_prefix"])
                for item in payload["claim_scope_relocation"]
            )
    elif mode == "claim-strength":
        if "kind" in expected:
            checks["move_kind"] = any(
                item["kind"].startswith(expected["kind"])
                for item in payload["upward_moves"]
            )
        checks["move_count"] = payload["upward_move_count"] >= expected.get("minimum_count", 0)
        for field in (
            "crypto_upward_moves", "crypto_upward_candidates",
            "crypto_downward_moves", "crypto_relocations",
        ):
            expected_ladders = expected.get(f"{field}_ladders")
            if expected_ladders is not None:
                checks[field] = {item["ladder"] for item in payload[field]} == set(expected_ladders)
            minimum = expected.get(f"minimum_{field}_count")
            if minimum is not None:
                checks[f"{field}_count"] = len(payload[field]) >= minimum
    elif mode == "terminology":
        if "kind" in expected:
            checks["replacement_kind"] = any(
                item["kind"] == expected["kind"]
                for item in payload["replacements"]
            )
        checks["replacement_count"] = payload["replacement_count"] >= expected.get("minimum_count", 0)
        if "maximum_count" in expected:
            checks["replacement_count_maximum"] = payload["replacement_count"] <= expected["maximum_count"]
    elif mode == "ai-tells":
        checks["minimum_finding_count"] = payload["finding_count"] >= expected.get("minimum_finding_count", 0)
        if "maximum_finding_count" in expected:
            checks["maximum_finding_count"] = payload["finding_count"] <= expected["maximum_finding_count"]
        checks["threshold"] = payload["threshold_exceeded"] is expected["threshold_exceeded"]
    else:
        raise HarnessError(f"unknown verifiability mode: {mode}")
    return case_result(case, checks, {
        "mode": mode,
        "exit_code": result.returncode,
        "fixture_word_counts": counts,
        "finding_count": payload.get("finding_count"),
        "total_violations": payload.get("total_violations"),
        "upward_move_count": payload.get("upward_move_count"),
        "crypto_upward_move_count": len(payload.get("crypto_upward_moves", [])),
        "crypto_upward_candidate_count": len(payload.get("crypto_upward_candidates", [])),
        "crypto_downward_move_count": len(payload.get("crypto_downward_moves", [])),
        "crypto_relocation_count": len(payload.get("crypto_relocations", [])),
        "claim_scope_relocation_count": payload.get("claim_scope_relocation_count"),
        "replacement_count": payload.get("replacement_count"),
    })


def run_layered_glossary(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    case_root = temp_root / case["id"] / "repository"
    case_root.mkdir(parents=True)
    for item in inputs.get("layer_files", []):
        source = repo_path(item["source"])
        target = (case_root / item["target"]).resolve()
        if case_root.resolve() not in target.parents:
            raise HarnessError(f"invalid layered target in {case['id']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    output = temp_root / case["id"] / "output.json"
    args: list[str] = []
    for raw in inputs["args"]:
        if raw == "{root}":
            args.append(str(case_root))
        elif raw == "{output}":
            args.append(str(output))
        elif raw.startswith("repo:"):
            args.append(str(repo_path(raw[5:])))
        else:
            args.append(raw)
    result = command(repo_path(inputs["script"]), *args)
    payload = json_stdout(result, case["id"])
    output_matches = output.is_file() and json.loads(output.read_text(encoding="utf-8")) == payload
    checks = {
        "exit_code": result.returncode == case["expected"]["exit_code"],
        "output_file_matches": output_matches,
        **{
            f"field:{name}": payload.get(name) == value
            for name, value in case["expected"]["fields"].items()
        },
    }
    return case_result(case, checks, {
        "exit_code": result.returncode,
        "output_file_matches": output_matches,
        "checked_fields": sorted(case["expected"]["fields"]),
    })


def run_crypto_contract(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    source = repo_path(inputs["script"]).read_text(encoding="utf-8")
    before = fixture(inputs["before_fixture"])
    after = fixture(inputs["after_fixture"])
    mutations = {
        "count": ("CRYPTO_LADDER_COUNT = 8", "CRYPTO_LADDER_COUNT = 7"),
        "manifest": (
            'CRYPTO_LADDER_MANIFEST_SHA256 = "bd698e056038d59be3c38c9479b94721a33d9f6bfd881eee3ef37a7c73957b3e"',
            'CRYPTO_LADDER_MANIFEST_SHA256 = "0d698e056038d59be3c38c9479b94721a33d9f6bfd881eee3ef37a7c73957b3e"',
        ),
        "anchor": ('"TFHE",\n    ),', '"TFHE", "POLY",\n    ),'),
        "anchored_manifest": (
            'CRYPTO_LADDER_ANCHORED_MANIFEST_SHA256 = "eef87d52f5b29469d79ea2d69706616458f1b8112106beb244a6ae783d861421"',
            'CRYPTO_LADDER_ANCHORED_MANIFEST_SHA256 = "0ef87d52f5b29469d79ea2d69706616458f1b8112106beb244a6ae783d861421"',
        ),
    }
    return_codes: dict[str, int] = {}
    errors: dict[str, str] = {}
    for name, (old, new) in mutations.items():
        if source.count(old) != 1:
            raise HarnessError(f"crypto contract source drift: {name}")
        script = temp_root / case["id"] / f"{name}.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(source.replace(old, new), encoding="utf-8")
        result = command(script, str(before), str(after))
        payload = json_stdout(result, f"{case['id']} {name}")
        return_codes[name] = result.returncode
        errors[name] = str(payload.get("error", ""))
    checks = {
        **{
            f"{name}_exit_code": code == case["expected"]["exit_code"]
            for name, code in return_codes.items()
        },
        **{f"{name}_error": "ladder" in errors[name] for name in mutations},
    }
    return case_result(case, checks, {"return_codes": return_codes})


def run_direction_matrix(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    glossary_paths: dict[str, Path] = {}
    build_codes: dict[str, int] = {}
    for direction in inputs["directions"]:
        output = temp_root / case["id"] / f"{direction}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        result = command(
            repo_path(inputs["builder"]), "--direction", direction, "-o", str(output)
        )
        json_stdout(result, f"{case['id']} build {direction}")
        build_codes[direction] = result.returncode
        glossary_paths[direction] = output

    sources = {
        name: (fixture(values["before_fixture"]), fixture(values["after_fixture"]))
        for name, values in inputs["texts"].items()
    }
    matrix: dict[str, dict[str, int]] = {}
    checker_codes: list[int] = []
    for text_name, (before, after) in sources.items():
        matrix[text_name] = {}
        for direction, glossary in glossary_paths.items():
            result = command(
                repo_path(inputs["checker"]), str(before), str(after), "--glossary", str(glossary)
            )
            payload = json_stdout(result, f"{case['id']} {text_name} {direction}")
            checker_codes.append(result.returncode)
            matrix[text_name][direction] = payload["replacement_count"]
    search, inference = inputs["directions"]
    diagonal_dominates = (
        matrix["search"][search] > matrix["search"][inference]
        and matrix["inference"][inference] > matrix["inference"][search]
    )
    counts = [
        synthetic_word_count(path.read_text(encoding="utf-8"))
        for pair in sources.values()
        for path in pair
    ]
    checks = {
        "build_exit_codes": all(code == 0 for code in build_codes.values()),
        "checker_exit_codes": all(code in (0, 1) for code in checker_codes),
        "fixture_word_range": all(150 <= count <= 300 for count in counts),
        "matrix": matrix == case["expected"]["matrix"],
        "diagonal_dominates": diagonal_dominates is case["expected"]["diagonal_dominates"],
    }
    return case_result(case, checks, {
        "matrix": matrix,
        "diagonal_dominates": diagonal_dominates,
        "direction_partition_failed": not diagonal_dominates,
        "fixture_word_counts": counts,
    })


def run_mechanical_contract(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    case_root = temp_root / case["id"] / "repository"
    core_target = case_root / "references" / "fhe_lexicon.json"
    core_target.parent.mkdir(parents=True)
    shutil.copyfile(fixture(inputs["core_fixture"]), core_target)
    project_root = case_root / "project"
    project_root.mkdir()
    project_yaml = project_root / "project.yaml"
    project_yaml.write_text(inputs["project_yaml"], encoding="utf-8")
    local_glossary = project_root / "local_glossary.md"
    if "project_glossary_fixture" in inputs:
        shutil.copyfile(fixture(inputs["project_glossary_fixture"]), local_glossary)

    direction_match = re.search(
        r"(?m)^direction:\s*(null|[a-z0-9_]+)\s*$", project_yaml.read_text(encoding="utf-8")
    )
    direction = direction_match.group(1) if direction_match and direction_match.group(1) != "null" else None
    merged = temp_root / case["id"] / "merged.json"
    build_args = ["--root", str(case_root)]
    if direction:
        build_args.extend(["--direction", direction])
    if local_glossary.is_file():
        build_args.extend(["--project", str(local_glossary)])
    build_args.extend(["-o", str(merged)])
    build = command(repo_path(inputs["builder"]), *build_args)
    build_payload = json_stdout(build, f"{case['id']}:glossary")

    before = fixture(inputs["before_fixture"])
    after_source = fixture(inputs["after_fixture"])
    after_text = after_source.read_text(encoding="utf-8")
    for old, new in inputs.get("replacements", []):
        if old not in after_text:
            raise HarnessError(f"replacement source absent in {case['id']}: {old!r}")
        after_text = after_text.replace(old, new)
    after = temp_root / case["id"] / "after.txt"
    after.write_text(after_text, encoding="utf-8")

    commands = (
        ("immutable", inputs["immutable_checker"], [str(before), str(after), "--glossary", str(merged)]),
        ("claim_strength", inputs["claim_checker"], [str(before), str(after)]),
        ("terminology", inputs["terminology_checker"], [str(before), str(after), "--glossary", str(merged)]),
        ("ai_tells", inputs["ai_checker"], ["--json", str(after)]),
    )
    steps: dict[str, dict[str, Any]] = {}
    for name, raw_script, args in commands:
        result = command(repo_path(raw_script), *args)
        steps[name] = {"exit_code": result.returncode, "payload": json_stdout(result, f"{case['id']}:{name}")}

    terminology_blocking = any(
        item.get("kind") != "case_inconsistency"
        for item in steps["terminology"]["payload"].get("replacements", [])
    )
    blocking_step = None
    if steps["immutable"]["exit_code"] != 0:
        blocking_step = 1
    elif steps["claim_strength"]["exit_code"] != 0:
        blocking_step = 2
    elif steps["terminology"]["exit_code"] == 2 or terminology_blocking:
        blocking_step = 3
    elif steps["ai_tells"]["exit_code"] == 2:
        blocking_step = 4
    decision = "rollback" if blocking_step is not None else "deliver"
    details = {
        "build_exit_code": build.returncode,
        "builder_direction": direction,
        "direction_layer_entry_count": build_payload.get("direction_layer_entry_count"),
        "project_layer": build_payload.get("project_layer"),
        "step_exit_codes": {name: item["exit_code"] for name, item in steps.items()},
        "blocking_step": blocking_step,
        "decision": decision,
    }
    checks = {
        "build_exit_code": build.returncode == expected["build_exit_code"],
        **{name: details.get(name) == value for name, value in expected["fields"].items()},
    }
    return case_result(case, checks, details)


def project_direction(text: str) -> str | None:
    match = re.search(r'(?m)^direction:\s*(null|"[^"]+")\s*$', text)
    if not match:
        raise HarnessError("project.yaml has no parseable top-level direction")
    return None if match.group(1) == "null" else json.loads(match.group(1))


def run_direction_binding(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    scenario = inputs["scenario"]
    case_root = temp_root / case["id"]
    case_root.mkdir(parents=True)

    details: dict[str, Any]
    if scenario.startswith("bootstrap"):
        paper = case_root / "synthetic-paper"
        paper.mkdir()
        (paper / "main.tex").write_text(
            "\\documentclass{article}\n\\title{Synthetic Direction Fixture}\n"
            "\\begin{document}\nSynthetic fixture only.\n\\end{document}\n",
            encoding="utf-8",
        )
        args = ["--paper-dir", str(paper), "--registry", str(case_root / "registry.json"), "--json"]
        if "direction" in inputs:
            args.extend(["--direction", inputs["direction"]])
        result = command(repo_path(inputs["script"]), *args)
        manifest = paper / ".helicon" / "project.yaml"
        actual_direction = project_direction(manifest.read_text(encoding="utf-8")) if manifest.is_file() else None
        details = {
            "exit_code": result.returncode,
            "direction": actual_direction,
            "legal_values_listed": all(value in result.stderr for value in inputs.get("legal_values", [])),
        }
    elif scenario == "set-protected":
        pack = case_root / ".helicon"
        pack.mkdir()
        manifest = pack / "project.yaml"
        original = (
            'schema: helicon-project-v1\nname: "Synthetic"\n'
            'direction: "private_llm_inference"\nfingerprint:\n  title: "Keep"\n'
        )
        manifest.write_text(original, encoding="utf-8")
        result = command(
            repo_path(inputs["script"]), str(pack), "--direction", inputs["direction"]
        )
        details = {
            "exit_code": result.returncode,
            "unchanged": manifest.read_text(encoding="utf-8") == original,
            "previous_value_reported": 'Previous direction: "private_llm_inference"' in result.stdout,
        }
    else:
        raise HarnessError(f"unsupported direction-binding scenario: {scenario}")

    checks = {
        "exit_code": details["exit_code"] == expected["exit_code"],
        **{name: details.get(name) == value for name, value in expected.get("fields", {}).items()},
    }
    return case_result(case, checks, details)


def run_installed_payload(case: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    inputs = case["input"]
    expected = case["expected"]
    scenario = inputs["scenario"]
    integrity_checker = repo_path(inputs["integrity_checker"])
    case_root = temp_root / case["id"]
    case_root.mkdir()

    if scenario in {"installed", "tampered-handoff"}:
        payload_root = case_root / "payload"
        check_live_skill_binding.copy_source_payload(ROOT, payload_root)
        if scenario == "tampered-handoff":
            (payload_root / "handoff").mkdir()
        result = command(integrity_checker, str(payload_root), "--json")
        payload = json_stdout(result, case["id"])
        details = {
            "exit_code": result.returncode,
            "payload_mode": payload.get("payload_mode"),
            "handoff_digest_sync": payload.get("contract_sync", {}).get("handoff_digest_sync"),
        }
    elif scenario == "source":
        result = command(integrity_checker, str(ROOT), "--json")
        payload = json_stdout(result, case["id"])
        details = {
            "exit_code": result.returncode,
            "payload_mode": payload.get("payload_mode"),
            "handoff_digest_sync": payload.get("contract_sync", {}).get("handoff_digest_sync"),
        }
    elif scenario in {"exclusions-consistent", "exclusions-mutated"}:
        powershell = repo_path(inputs["install_ps1"]).read_text(encoding="utf-8")
        shell = repo_path(inputs["install_sh"]).read_text(encoding="utf-8")
        source_text = repo_path(inputs["source_script"]).read_text(encoding="utf-8")
        source_exclusions = check_live_skill_binding.parse_python_exclusions(source_text)
        if scenario == "exclusions-consistent":
            observed = check_live_skill_binding.validate_installer_exclusions(
                powershell, shell, source_exclusions
            )
            details = {
                "exit_code": 0,
                "sets_equal": len(set(map(frozenset, observed.values()))) == 1,
            }
        else:
            mutations = [
                (powershell.replace('"handoff"', '"handoff-mutated"', 1), shell,
                 source_exclusions),
                (powershell, shell.replace("|handoff)", "|handoff-mutated)", 1),
                 source_exclusions),
                (powershell, shell,
                 check_live_skill_binding.parse_python_exclusions(
                     source_text.replace(', "handoff"', "", 1)
                 )),
            ]
            mutation_exit_codes: list[int] = []
            for values in mutations:
                try:
                    check_live_skill_binding.validate_installer_exclusions(*values)
                except ValueError:
                    mutation_exit_codes.append(2)
                else:
                    mutation_exit_codes.append(0)
            details = {
                "exit_code": 2 if all(code != 0 for code in mutation_exit_codes) else 0,
                "mutation_exit_codes": mutation_exit_codes,
            }
    else:
        raise HarnessError(f"unsupported installed-payload scenario: {scenario}")

    checks = {
        "exit_code": details["exit_code"] == expected["exit_code"],
        **{name: details.get(name) == value for name, value in expected.get("fields", {}).items()},
    }
    return case_result(case, checks, details)


RUNNERS: dict[str, Callable[[dict[str, Any], Path], dict[str, Any]]] = {
    "selftest": run_selftest,
    "router-contracts": run_router_contracts,
    "target-profile-hash": run_target_profile_hash,
    "revision-preflight": run_revision_preflight,
    "target-eval-guards": run_target_eval_guards,
    "verifiability": run_verifiability,
    "layered-glossary": run_layered_glossary,
    "crypto-contract": run_crypto_contract,
    "direction-matrix": run_direction_matrix,
    "mechanical-contract": run_mechanical_contract,
    "direction-binding": run_direction_binding,
    "installed-payload": run_installed_payload,
}


def load_cases() -> list[dict[str, Any]]:
    paths = sorted(CASES.glob("*.json"))
    if len(paths) < 15:
        raise HarnessError(f"expected at least 15 case definitions, found {len(paths)}")
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
        runner = payload.get("runner", payload["id"])
        if runner not in RUNNERS:
            raise HarnessError(f"unknown case runner: {runner}")
        payload["runner"] = runner
        loaded.append(payload)
    if len({item["id"] for item in loaded}) != len(loaded):
        raise HarnessError("duplicate case id")
    return loaded


def main() -> int:
    try:
        cases = load_cases()
        with tempfile.TemporaryDirectory(prefix="helicon-evals-") as raw_temp:
            temp_root = Path(raw_temp)
            results = [RUNNERS[case["runner"]](case, temp_root) for case in cases]
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
