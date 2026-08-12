#!/usr/bin/env python3
"""Validate public HElicon handoffs without claiming semantic evidence truth."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path


STATUSES = {"done", "partial", "blocked", "skipped"}
LEGACY_EVIDENCE = {"self-authored-fixture", "real-data", "independent-session"}
DATA_PROVENANCE = {"synthetic", "private-real-data", "repository-metadata"}
EXECUTION_PROVENANCE = {"builder-session", "independent-session"}
TARGET_PROVENANCE = {"none", "qualified-original", "author-approved-ai-assisted", "synthetic-oracle"}
HUMAN_REVIEW = {"none", "author-attested", "independent-human-reviewed"}
CLAIM_DOMAINS = {"repository", "corpus", "target", "evaluation", "privacy", "install"}
CLAIM_SCOPES = {
    "repository-integrity",
    "corpus-qc",
    "authority-approval",
    "revision-attribution",
    "privacy-review",
    "pipeline-only",
    "evaluator-only",
    "preservation",
    "rule-direction",
    "structural",
    "fixture-provenance",
    "install-rollback",
}
DISPOSITIONS = {"closed", "carried-forward", "retired-known-gap", "blocked", "reframed-and-tested"}
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
TASK_ID_RE = re.compile(r"^R4-(?:ITERATION|\d+)$")
EVIDENCE_ID_RE = re.compile(r"^R4-E\d{3}$")
DECISION_ID_RE = re.compile(r"^R4-D\d{3}$")
ROUND3_ITEMS = {*(f"R3-U{i:02d}" for i in range(1, 11)), *(f"R3-OQ{i:02d}" for i in range(1, 4))}
ROUND4_BASE = "a52366983621b6481284f0c9a09f9fe3a866f2d8"
ROUND3_IMPLEMENTATION = "230dc4ddbedccb8fe263b4180d0b110dc6961bcf"
CANDIDATE_PATHS = [
    "handoff/HELICON_ROUND4_TASKBOOK.md",
    "handoff/INDEX.md",
    "handoff/ROUND_4_HANDOFF.md",
    "handoff/validate.py",
]
OUTPUT_HASH_BASES = {
    "captured-combined-stdout-stderr",
    "sanitized-key-output",
    "external-audit-attestation",
}
DISPOSITION_POLICY = {
    "R3-U01": ("corpus", "corpus-qc"),
    "R3-U02": ("corpus", "authority-approval"),
    "R3-U03": ("corpus", "revision-attribution"),
    "R3-U04": ("target", "revision-attribution"),
    "R3-U05": ("privacy", "privacy-review"),
    "R3-U06": ("evaluation", "evaluator-only"),
    "R3-U07": ("evaluation", "structural"),
    "R3-U08": ("repository", "repository-integrity"),
    "R3-U09": ("evaluation", "fixture-provenance"),
    "R3-U10": ("install", "install-rollback"),
    "R3-OQ01": ("corpus", "corpus-qc"),
    "R3-OQ02": ("evaluation", "structural"),
    "R3-OQ03": ("privacy", "privacy-review"),
}
CAPABILITY_SCOPE_DOMAIN = {
    "preservation": "evaluation",
    "rule-direction": "evaluation",
    "structural": "evaluation",
    "corpus-qc": "corpus",
    "authority-approval": "corpus",
    "revision-attribution": "corpus",
    "privacy-review": "privacy",
    "fixture-provenance": "evaluation",
    "install-rollback": "install",
}


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def utc(value: str, label: str) -> dt.datetime:
    require(isinstance(value, str) and UTC_RE.match(value) is not None, f"invalid UTC timestamp: {label}")
    body = value[:-1]
    if "." in body:
        prefix, fraction = body.split(".", 1)
        body = prefix + "." + fraction[:6]
    parsed = dt.datetime.fromisoformat(body + "+00:00")
    require(parsed.tzinfo is not None, f"timezone missing: {label}")
    return parsed


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if completed.returncode:
        raise ValidationError(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return completed.stdout


def git_blob_manifest(repo: Path, commit: str, prefix: str = "") -> dict:
    args = ["ls-tree", "-r", "-z", "--full-tree", commit]
    if prefix:
        args.extend(["--", prefix])
    entries = []
    for record in git(repo, *args).split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        _mode, object_type, object_id = metadata.split(b" ", 2)
        require(object_type == b"blob", f"non-blob entry in manifest: {raw_path!r}")
        path = raw_path.decode("utf-8")
        relative = path[len(prefix) + 1 :] if prefix else path
        blob = git(repo, "cat-file", "blob", object_id.decode("ascii"))
        entries.append((relative.encode("utf-8"), hashlib.sha256(blob).hexdigest(), len(blob)))
    entries.sort(key=lambda item: item[0])
    manifest = b"".join(digest.encode("ascii") + b"  " + path + b"\n" for path, digest, _size in entries)
    return {
        "algorithm": "git-blob-manifest-v1",
        "path_basis": "subtree-relative" if prefix else "repository-root-relative",
        "path_sort": "raw-utf8-bytes",
        "files": len(entries),
        "blob_bytes": sum(size for _path, _digest, size in entries),
        "manifest_bytes": len(manifest),
        "sha256": "sha256:" + hashlib.sha256(manifest).hexdigest(),
    }


def canonical_text_manifest(repo: Path, paths: list[str]) -> dict:
    entries = []
    for relative in sorted(paths, key=lambda value: value.encode("utf-8")):
        target = (repo / relative).resolve()
        try:
            target.relative_to(repo.resolve())
        except ValueError:
            raise ValidationError(f"candidate path outside repository: {relative}")
        require(target.is_file(), f"candidate path invalid: {relative}")
        content = target.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        entries.append((relative, hashlib.sha256(content).hexdigest(), len(content)))
    manifest = "".join(f"{digest}  {relative}\n" for relative, digest, _size in entries).encode("utf-8")
    return {
        "algorithm": "canonical-text-candidate-v1",
        "path_basis": "repository-root-relative",
        "path_sort": "raw-utf8-bytes",
        "line_endings": "LF",
        "files": len(entries),
        "content_bytes": sum(size for _relative, _digest, size in entries),
        "manifest_bytes": len(manifest),
        "sha256": "sha256:" + hashlib.sha256(manifest).hexdigest(),
    }


def validate_v1(data: dict, handoff: Path) -> dict:
    required = {
        "round",
        "branch",
        "head_commit",
        "base_commit",
        "taskbook",
        "tasks",
        "unverified_claims",
        "deviations",
        "open_questions",
        "metrics",
        "privacy",
        "reproduce",
        "next_round_candidates",
    }
    require(not (required - set(data)), "v1 missing top-level fields")
    require(data["round"] == 3 and data["status"] in STATUSES, "invalid v1 round/status")
    require((handoff.parent / data["taskbook"]).is_file(), "v1 taskbook missing")
    task_ids = [task["id"] for task in data["tasks"]]
    require(len(task_ids) == len(set(task_ids)), "duplicate v1 task id")
    for task in data["tasks"]:
        require(task["status"] in STATUSES and task["evidence"] and task.get("note"), "invalid v1 task")
        for evidence in task["evidence"]:
            require(
                {"command", "exit_code", "key_output", "evidence_class"} <= set(evidence),
                "invalid v1 evidence",
            )
            require(evidence["evidence_class"] in LEGACY_EVIDENCE, "invalid legacy evidence class")
    report = (handoff / "ROUND_3_HANDOFF.md").read_text(encoding="utf-8")
    index = (handoff / "INDEX.md").read_text(encoding="utf-8")
    require(data["head_commit"] in report and data["base_commit"] in report, "v1 report identity mismatch")
    require(f"| {data['round']} |" in index, "v1 index missing")
    require(f"| {len(data['unverified_claims'])} | {len(data['open_questions'])} |" in index, "v1 counts mismatch")
    return {"round": 3, "schema": data["schema"], "tasks": len(data["tasks"]), "evidence": sum(len(t["evidence"]) for t in data["tasks"])}


def validate_v2_policy(data: dict) -> dict:
    required = {
        "schema",
        "round",
        "status",
        "taskbook",
        "generated_utc",
        "authorization_scope",
        "repository",
        "evidence_hash_policy",
        "tasks",
        "decisions",
        "inherited_source",
        "inherited_dispositions",
        "legacy_task_dispositions",
        "unverified_claims",
        "open_questions",
        "deviations",
        "metrics",
        "privacy",
        "reproduce",
    }
    require(not (required - set(data)), "v2 missing top-level fields")
    require(data["schema"] == "helicon-handoff-v2" and data["round"] == 4, "invalid v2 identity")
    generated_utc = utc(data["generated_utc"], "generated_utc")
    require(data["status"] in STATUSES, "invalid v2 status")
    require("head_commit" not in data, "v2 forbids ambiguous head_commit")
    authorization = data["authorization_scope"]
    require(
        authorization.get("authorized_stages") == ["R4-0", "R4-1"]
        and authorization.get("stop_after") == "R4-1"
        and authorization.get("private_data_access") is False
        and authorization.get("live_skill_access") is False
        and authorization.get("installation_authorized") is False
        and authorization.get("merge_tag_push_authorized") is False,
        "authorization boundary mismatch",
    )

    repository = data["repository"]
    commit_fields = ("base_commit", "implementation_commit", "handoff_commit", "audited_checkout_commit", "audited_checkout_parent")
    for field in commit_fields:
        require(COMMIT_RE.match(repository.get(field, "")) is not None, f"invalid repository {field}")
    require(repository.get("round4_containing_commit") is None, "unpublished Round 4 commit must be null")
    require(repository.get("round4_containing_commit_status") == "externally-resolved-after-publication", "invalid Round 4 commit status")
    require(repository["base_commit"] == ROUND4_BASE, "Round 4 base commit mismatch")
    require(repository["implementation_commit"] == ROUND3_IMPLEMENTATION, "Round 3 implementation commit mismatch")
    require(repository["handoff_commit"] == ROUND4_BASE and repository["audited_checkout_commit"] == ROUND4_BASE, "Round 3 audited checkout mismatch")

    hash_policy = data["evidence_hash_policy"]
    require(set(hash_policy) == OUTPUT_HASH_BASES, "evidence hash policy basis mismatch")
    basis_by_id = {}
    for basis, evidence_ids in hash_policy.items():
        require(isinstance(evidence_ids, list) and len(evidence_ids) == len(set(evidence_ids)), f"duplicate evidence hash policy id: {basis}")
        for evidence_id in evidence_ids:
            require(evidence_id not in basis_by_id, f"evidence has multiple hash bases: {evidence_id}")
            basis_by_id[evidence_id] = basis

    evidence_by_id = {}
    evidence_times = []
    task_ids = set()
    for task in data["tasks"]:
        task_id = task.get("id")
        require(isinstance(task_id, str) and TASK_ID_RE.match(task_id) and task_id not in task_ids, "duplicate/missing/invalid v2 task id")
        task_ids.add(task_id)
        require(task.get("status") in STATUSES and isinstance(task.get("capability_claim"), bool), f"invalid task {task_id}")
        domains = set(task.get("claim_domains", []))
        scopes = set(task.get("claim_scopes", []))
        require(domains and domains <= CLAIM_DOMAINS and scopes and scopes <= CLAIM_SCOPES, f"invalid task scopes {task_id}")
        capability_scopes = set(task.get("capability_scopes", []))
        require(capability_scopes <= scopes, f"capability scopes exceed task scopes: {task_id}")
        require(task["capability_claim"] or not capability_scopes, f"non-capability task declares capability scopes: {task_id}")
        evidence = task.get("evidence", [])
        require(task["status"] != "done" or evidence, f"done task lacks evidence: {task_id}")
        for item in evidence:
            evidence_id = item.get("id")
            require(isinstance(evidence_id, str) and EVIDENCE_ID_RE.match(evidence_id) and evidence_id not in evidence_by_id, f"duplicate/missing/invalid evidence id: {evidence_id}")
            evidence_by_id[evidence_id] = item
            required_evidence = {
                "id",
                "command",
                "exit_code",
                "executed_utc",
                "key_output",
                "input_manifest_sha256",
                "output_summary_sha256",
                "data_provenance",
                "execution_provenance",
                "target_provenance",
                "human_review",
                "claim_domain",
                "claim_scope",
            }
            require(not (required_evidence - set(item)), f"evidence fields missing: {evidence_id}")
            require(type(item["exit_code"]) is int, f"invalid evidence exit code: {evidence_id}")
            record_type = item.get("record_type", "command-execution")
            require(record_type in {"command-execution", "external-audit-attestation"}, f"invalid evidence record type: {evidence_id}")
            if record_type == "command-execution":
                evidence_time = utc(item["executed_utc"], f"{evidence_id}.executed_utc")
                require("recorded_utc" not in item, f"command evidence must use executed_utc only: {evidence_id}")
            else:
                require(item["executed_utc"] is None, f"external attestation must not invent execution time: {evidence_id}")
                require(item.get("execution_time_status") == "not-reported-by-source", f"external execution-time status mismatch: {evidence_id}")
                evidence_time = utc(item.get("recorded_utc", ""), f"{evidence_id}.recorded_utc")
                external_commands = item.get("external_commands", [])
                external_exits = item.get("external_exit_codes", [])
                require(external_commands and len(external_commands) == len(external_exits), f"external command bundle mismatch: {evidence_id}")
                require(all(isinstance(command, str) and command for command in external_commands), f"invalid external command: {evidence_id}")
                require(all(code == 0 for code in external_exits), f"external audit includes a failing command: {evidence_id}")
                require(item["execution_provenance"] == "independent-session", f"external audit provenance mismatch: {evidence_id}")
            evidence_times.append(evidence_time)
            require(HASH_RE.match(item["input_manifest_sha256"]) and HASH_RE.match(item["output_summary_sha256"]), f"invalid evidence hash: {evidence_id}")
            require(item["input_manifest_sha256"] != "sha256:" + "0" * 64, f"placeholder input hash: {evidence_id}")
            require(item["output_summary_sha256"] != "sha256:" + "0" * 64, f"placeholder output hash: {evidence_id}")
            require(item["data_provenance"] in DATA_PROVENANCE, f"invalid data provenance: {evidence_id}")
            require(item["execution_provenance"] in EXECUTION_PROVENANCE, f"invalid execution provenance: {evidence_id}")
            require(item["target_provenance"] in TARGET_PROVENANCE, f"invalid target provenance: {evidence_id}")
            require(item["human_review"] in HUMAN_REVIEW, f"invalid human review: {evidence_id}")
            require(item["claim_domain"] in domains and item["claim_scope"] in scopes, f"evidence/task scope mismatch: {evidence_id}")
            require(item["exit_code"] == 0 or task["status"] != "done", f"done task cites failing evidence: {evidence_id}")
            if item["data_provenance"] == "synthetic":
                require(item["claim_scope"] in {"pipeline-only", "evaluator-only", "fixture-provenance"}, f"synthetic capability escalation: {evidence_id}")
            if item["data_provenance"] == "private-real-data":
                require(authorization["private_data_access"] is True, f"private evidence exceeds authorization: {evidence_id}")
            if item["target_provenance"] == "synthetic-oracle":
                require(item["claim_scope"] == "evaluator-only", f"synthetic oracle scope mismatch: {evidence_id}")
                require(item.get("generation_path_exercised") is False, f"synthetic oracle presented as generation: {evidence_id}")
        if task["status"] == "done" and task["capability_claim"]:
            require(authorization["private_data_access"] is True, f"capability task exceeds private-access authorization: {task_id}")
            require(capability_scopes, f"capability task lacks capability scopes: {task_id}")
            for capability_scope in capability_scopes:
                expected_domain = CAPABILITY_SCOPE_DOMAIN.get(capability_scope)
                require(expected_domain is not None and expected_domain in domains, f"capability scope/domain mismatch: {task_id}/{capability_scope}")
                matching = [
                    item
                    for item in evidence
                    if item["claim_scope"] == capability_scope
                    and item["claim_domain"] == expected_domain
                    and item["data_provenance"] == "private-real-data"
                    and item["execution_provenance"] == "independent-session"
                    and item["exit_code"] == 0
                ]
                require(matching, f"capability scope lacks matching private independent evidence: {task_id}/{capability_scope}")
                if capability_scope in {"preservation", "rule-direction", "structural"}:
                    require(any(item["target_provenance"] != "none" for item in matching), f"capability scope lacks target provenance: {task_id}/{capability_scope}")
                if capability_scope == "structural":
                    require(any(item["human_review"] != "none" for item in matching), f"structural capability lacks human review: {task_id}")

    require(set(basis_by_id) == set(evidence_by_id), "evidence hash policy must cover every evidence exactly once")
    for evidence_id, basis in basis_by_id.items():
        item = evidence_by_id[evidence_id]
        record_type = item.get("record_type", "command-execution")
        require(
            (record_type == "external-audit-attestation") == (basis == "external-audit-attestation"),
            f"external attestation hash basis mismatch: {evidence_id}",
        )
        if basis in {"sanitized-key-output", "external-audit-attestation"}:
            require(sha256_text(item["key_output"]) == item["output_summary_sha256"], f"recomputable evidence hash mismatch: {evidence_id}")
        if basis == "external-audit-attestation":
            require(item.get("record_type") == "external-audit-attestation", f"external hash basis/record mismatch: {evidence_id}")

    decision_ids = set()
    decision_times = []
    for decision in data["decisions"]:
        decision_id = decision.get("id")
        require(isinstance(decision_id, str) and DECISION_ID_RE.match(decision_id) and decision_id not in decision_ids, "duplicate/missing/invalid decision id")
        decision_ids.add(decision_id)
        require(decision.get("actor") == "author", f"invalid decision actor: {decision_id}")
        decision_times.append(utc(decision.get("recorded_utc", ""), f"{decision_id}.recorded_utc"))
    require(generated_utc >= max(evidence_times + decision_times), "generated_utc precedes contained evidence or decisions")
    require(generated_utc <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), "generated_utc is implausibly in the future")

    dispositions = data["inherited_dispositions"]
    source_ids = [item.get("source_id") for item in dispositions]
    require(set(source_ids) == ROUND3_ITEMS and len(source_ids) == len(ROUND3_ITEMS), "Round 3 dispositions must cover 13 items exactly once")
    for item in dispositions:
        expected_kind = "unverified_claim" if item["source_id"].startswith("R3-U") else "open_question"
        require(item.get("source_kind") == expected_kind, f"disposition kind mismatch: {item['source_id']}")
        expected_domain, expected_scope = DISPOSITION_POLICY[item["source_id"]]
        require(item.get("claim_domain") == expected_domain and item.get("claim_scope") == expected_scope, f"disposition claim boundary mismatch: {item['source_id']}")
        require(item.get("disposition") in DISPOSITIONS and item.get("rationale"), f"invalid disposition: {item.get('source_id')}")
        evidence_ids = item.get("evidence_ids", [])
        cited_decisions = item.get("decision_ids", [])
        require(set(evidence_ids) <= set(evidence_by_id), f"dangling disposition evidence: {item['source_id']}")
        require(set(cited_decisions) <= decision_ids, f"dangling disposition decision: {item['source_id']}")
        for evidence_id in evidence_ids:
            evidence = evidence_by_id[evidence_id]
            require(evidence["exit_code"] == 0, f"disposition cites failing evidence: {item['source_id']}/{evidence_id}")
            require(evidence["claim_domain"] == expected_domain and evidence["claim_scope"] == expected_scope, f"disposition cites unrelated evidence: {item['source_id']}/{evidence_id}")
        if item["disposition"] in {"closed", "reframed-and-tested"}:
            if expected_kind == "unverified_claim":
                require(evidence_ids, f"factual disposition lacks direct evidence: {item['source_id']}")
            else:
                require(cited_decisions, f"question disposition lacks author decision: {item['source_id']}")
        if item["source_id"] == "R3-U08" and item["disposition"] == "closed":
            require(
                any(evidence_by_id[evidence_id]["execution_provenance"] == "independent-session" for evidence_id in evidence_ids),
                "R3-U08 closure lacks independent-session repository evidence",
            )

    unverified_ids = [item.get("id") for item in data["unverified_claims"]]
    require(len(unverified_ids) == len(set(unverified_ids)) and all(re.match(r"^R4-U\d{2}$", item or "") for item in unverified_ids), "invalid R4 unverified ids")
    require(all(isinstance(item.get("claim"), str) and item["claim"] and isinstance(item.get("status"), str) and item["status"] and isinstance(item.get("how_to_verify"), str) and item["how_to_verify"] for item in data["unverified_claims"]), "invalid R4 unverified claim")
    question_ids = [item.get("id") for item in data["open_questions"]]
    require(len(question_ids) == len(set(question_ids)) and all(re.match(r"^R4-OQ\d{2}$", item or "") for item in question_ids), "invalid R4 question ids")
    require(all(isinstance(item.get("question"), str) and item["question"] and isinstance(item.get("options"), list) and item["options"] and isinstance(item.get("recommendation"), str) and item["recommendation"] for item in data["open_questions"]), "invalid R4 open question")
    deviation_ids = [item.get("id") for item in data["deviations"]]
    require(len(deviation_ids) == len(set(deviation_ids)) and all(re.match(r"^R4-DEV\d{2}$", item or "") for item in deviation_ids), "invalid R4 deviation ids")
    require(all({"what", "why", "impact"} <= set(item) for item in data["deviations"]), "invalid R4 deviation")
    successor_ids = set(unverified_ids) | set(question_ids)
    for item in dispositions:
        if "successor_id" in item:
            require(item["successor_id"] in successor_ids, f"dangling disposition successor: {item['source_id']}")
    legacy = data["legacy_task_dispositions"]
    require(len(legacy) == 1, "Round 3 iteration task disposition missing")
    require(
        legacy[0].get("source_id") == "R3-T08"
        and legacy[0].get("recorded_status") == "done"
        and legacy[0].get("round4_disposition") == "superseded-partial"
        and bool(legacy[0].get("rationale")),
        "Round 3 iteration task disposition mismatch",
    )

    pipeline = data["metrics"]["synthetic_regression"]
    require(pipeline["pipeline_runnable"] is True, "synthetic pipeline must remain runnable")
    require(pipeline["capability_validated"] is False, "synthetic fixtures cannot validate capability")
    require(pipeline["claim_scope"] == "pipeline-only" and pipeline["generation_path_exercised"] is False, "synthetic scope mismatch")
    structural = data["metrics"]["structural_direction"]
    eligible = structural["eligible_observations"]
    scorable = structural["scorable_observations"]
    coverage = structural["coverage_percent"]
    zero_denominator = structural["zero_denominator_cases"]
    require(isinstance(eligible, int) and isinstance(scorable, int) and 0 <= scorable <= eligible, "structural observation counts invalid")
    require(isinstance(zero_denominator, int) and 0 <= zero_denominator <= eligible, "structural zero-denominator count invalid")
    expected_coverage = 0.0 if eligible == 0 else 100.0 * scorable / eligible
    require(isinstance(coverage, (int, float)) and abs(coverage - expected_coverage) <= 0.001, "structural coverage/count mismatch")
    threshold_met = (
        eligible >= 6
        and scorable >= 5
        and coverage >= 80
        and zero_denominator == 0
        and structural["aggregate_convergence_percent"] is not None
    )
    if not threshold_met:
        require(structural["status"] == "insufficient-coverage", "structural status overclaim")
        require(structural["headline_allowed"] is False and structural["aggregate_convergence_percent"] is None, "structural headline overclaim")
    else:
        aggregate = structural["aggregate_convergence_percent"]
        require(isinstance(aggregate, (int, float)) and -100.0 <= aggregate <= 100.0, "structural aggregate invalid")
        require(structural["status"] == "validated" and structural["headline_allowed"] is True, "structural positive status mismatch")
        require("R4-STRUCTURAL" in authorization.get("authorized_stages", []), "structural headline was not authorized")
        require(
            any(
                task["status"] == "done"
                and task["capability_claim"]
                and "structural" in task.get("capability_scopes", [])
                for task in data["tasks"]
            ),
            "structural headline lacks a completed structural capability task",
        )
    for task in data["tasks"]:
        if task["status"] == "done" and task["capability_claim"] and "structural" in task.get("capability_scopes", []):
            require(threshold_met, f"structural capability task precedes coverage admission: {task['id']}")
    return {"tasks": len(data["tasks"]), "evidence": len(evidence_by_id), "dispositions": len(dispositions)}


def validate_v2_repository(data: dict, handoff: Path) -> dict:
    repo = handoff.parent
    repository = data["repository"]
    for field in ("base_commit", "implementation_commit", "handoff_commit", "audited_checkout_commit", "audited_checkout_parent"):
        git(repo, "cat-file", "-e", repository[field] + "^{commit}")
    parents = git(repo, "show", "-s", "--format=%P", repository["audited_checkout_commit"]).decode("ascii").strip().split()
    require(parents == [repository["audited_checkout_parent"]], "audited checkout parent mismatch")
    git(repo, "merge-base", "--is-ancestor", repository["implementation_commit"], repository["audited_checkout_commit"])
    require(repository["handoff_commit"] == repository["audited_checkout_commit"], "Round 3 handoff/audited checkout mismatch")
    require(git(repo, "remote", "get-url", "origin").decode("utf-8").strip() == repository["origin_url"], "origin URL mismatch")
    require((repo / data["taskbook"]).is_file(), "Round 4 taskbook missing")

    source = data["inherited_source"]
    require(source.get("commit") == repository["audited_checkout_commit"], "inherited source commit mismatch")
    require(source.get("id_derivation") == "array-order-v1", "inherited source ID derivation mismatch")
    source_bytes = git(repo, "show", f"{source['commit']}:{source['path']}")
    require("sha256:" + hashlib.sha256(source_bytes).hexdigest() == source["sha256"], "inherited source hash mismatch")
    source_data = json.loads(source_bytes.decode("utf-8"))
    source_unverified = source_data.get("unverified_claims", [])
    source_questions = source_data.get("open_questions", [])
    require(len(source_unverified) == source.get("unverified_claims") == 10, "inherited unverified count mismatch")
    require(len(source_questions) == source.get("open_questions") == 3, "inherited question count mismatch")
    disposition_by_id = {item["source_id"]: item for item in data["inherited_dispositions"]}
    for index, _source_item in enumerate(source_unverified):
        source_id = f"R3-U{index + 1:02d}"
        require(disposition_by_id[source_id].get("source_index") == index, f"inherited unverified source index mismatch: {source_id}")
    for index, _source_item in enumerate(source_questions):
        source_id = f"R3-OQ{index + 1:02d}"
        require(disposition_by_id[source_id].get("source_index") == index, f"inherited question source index mismatch: {source_id}")

    for key, prefix in (("repository_blob_manifest", ""), ("evals_blob_manifest", "evals")):
        expected = data["metrics"][key]
        require(expected.get("commit") == repository["audited_checkout_commit"], f"{key} commit mismatch")
        actual = git_blob_manifest(repo, expected["commit"], prefix)
        for field in ("algorithm", "path_basis", "path_sort", "files", "blob_bytes", "manifest_bytes", "sha256"):
            require(actual[field] == expected[field], f"{key} mismatch: {field}")
        if key == "evals_blob_manifest":
            require(expected["files"] > 0 and expected["blob_bytes"] > 0, "evals manifest must bind a non-empty tracked suite")
    candidate = data["metrics"]["round4_policy_bundle_manifest"]
    require(candidate.get("paths") == CANDIDATE_PATHS, "Round 4 candidate path set mismatch")
    require(len(candidate["paths"]) == len(set(candidate["paths"])), "Round 4 candidate paths duplicated")
    require(
        candidate.get("self_referential_file_excluded") == "handoff/round_4.json"
        and candidate.get("canonical_repository_digest") is False
        and isinstance(candidate.get("note"), str)
        and candidate["note"],
        "Round 4 candidate manifest metadata mismatch",
    )
    actual_candidate = canonical_text_manifest(repo, candidate["paths"])
    for field in (
        "algorithm",
        "path_basis",
        "path_sort",
        "line_endings",
        "files",
        "content_bytes",
        "manifest_bytes",
        "sha256",
    ):
        require(actual_candidate[field] == candidate[field], f"round4_policy_bundle_manifest mismatch: {field}")

    evidence_by_id = {item["id"]: item for task in data["tasks"] for item in task.get("evidence", [])}
    repository_input_ids = {
        evidence_id
        for evidence_id in evidence_by_id
        if evidence_id not in {"R4-E019", "R4-E020", "R4-E021", "R4-E022"}
    }
    policy_input_ids = {"R4-E019", "R4-E020", "R4-E021", "R4-E022"}
    require(repository_input_ids | policy_input_ids == set(evidence_by_id), "evidence input binding set mismatch")
    for evidence_id in repository_input_ids:
        require(
            evidence_by_id[evidence_id]["input_manifest_sha256"] == data["metrics"]["repository_blob_manifest"]["sha256"],
            f"repository evidence input manifest mismatch: {evidence_id}",
        )
    for evidence_id in policy_input_ids:
        require(
            evidence_by_id[evidence_id]["input_manifest_sha256"] == candidate["sha256"],
            f"policy evidence input manifest mismatch: {evidence_id}",
        )

    report = (handoff / "ROUND_4_HANDOFF.md").read_text(encoding="utf-8")
    index = (handoff / "INDEX.md").read_text(encoding="utf-8")
    require("HElicon Round 4" in report and f"| Status | `{data['status']}` |" in report, "Round 4 report identity mismatch")
    for field in ("implementation_commit", "handoff_commit", "audited_checkout_commit"):
        require(repository[field] in report, f"Round 4 report missing {field}")
    for task in data["tasks"]:
        require(f"| {task['id']} | `{task['status']}` |" in report, f"Round 4 report task mismatch: {task['id']}")
        capability_text = "true" if task["capability_claim"] else "false"
        require(f"| {task['id']} | `{task['status']}` | `{capability_text}` |" in report, f"Round 4 report task capability mismatch: {task['id']}")
    for item in data["inherited_dispositions"]:
        require(f"| {item['source_id']} | `{item['disposition']}` |" in report, f"Round 4 report disposition mismatch: {item['source_id']}")
    structural = data["metrics"]["structural_direction"]
    require(f"- eligible：{structural['eligible_observations']}" in report, "Round 4 report structural eligible mismatch")
    require(f"- scorable：{structural['scorable_observations']}" in report, "Round 4 report structural scorable mismatch")
    require(f"- coverage：{structural['coverage_percent']}%" in report, "Round 4 report structural coverage mismatch")
    require(f"- status：`{structural['status']}`" in report, "Round 4 report structural status mismatch")
    require(f"- zero-denominator cases：{structural['zero_denominator_cases']}" in report, "Round 4 report structural zero-denominator mismatch")
    aggregate_text = "`null`" if structural["aggregate_convergence_percent"] is None else str(structural["aggregate_convergence_percent"])
    require(f"- aggregate：{aggregate_text}" in report, "Round 4 report structural aggregate mismatch")
    headline_text = "允许" if structural["headline_allowed"] else "不允许"
    require(f"- headline：{headline_text}" in report, "Round 4 report structural headline mismatch")
    require(f"{len(data['unverified_claims'])} 项" in report and f"{len(data['open_questions'])} 项开放问题" in report, "Round 4 report outstanding counts mismatch")
    require(f"{len(data['deviations'])} 项偏差" in report, "Round 4 report deviation count mismatch")
    require(f"| 4 |" in index and f"| {len(data['unverified_claims'])} | {len(data['open_questions'])} |" in index, "Round 4 index mismatch")
    return {"repository_metadata_verified": True}


def expect_policy_failure(data: dict, label: str) -> None:
    try:
        validate_v2_policy(data)
    except ValidationError:
        return
    raise ValidationError(f"negative selftest did not fail: {label}")


def expect_repository_failure(data: dict, handoff: Path, label: str) -> None:
    try:
        validate_v2_repository(data, handoff)
    except ValidationError:
        return
    raise ValidationError(f"negative repository selftest did not fail: {label}")


def selftest_v2(data: dict, handoff: Path) -> int:
    validate_v2_policy(data)
    changed = copy.deepcopy(data)
    changed["tasks"][0]["capability_claim"] = True
    changed["tasks"][0]["capability_scopes"] = ["structural"]
    changed["tasks"][0]["claim_scopes"].append("structural")
    changed["tasks"][0]["evidence"][0]["data_provenance"] = "private-real-data"
    changed["tasks"][0]["evidence"][0]["execution_provenance"] = "independent-session"
    changed["tasks"][0]["evidence"][0]["target_provenance"] = "qualified-original"
    changed["tasks"][0]["evidence"][0]["human_review"] = "author-attested"
    changed["tasks"][0]["evidence"][0]["claim_scope"] = "structural"
    expect_policy_failure(changed, "synthetic capability escalation")
    changed = copy.deepcopy(data)
    changed["metrics"]["structural_direction"]["headline_allowed"] = True
    expect_policy_failure(changed, "insufficient structural coverage")
    changed = copy.deepcopy(data)
    changed["metrics"]["structural_direction"].update(
        {
            "status": "validated",
            "eligible_observations": 100,
            "scorable_observations": 80,
            "coverage_percent": 80.0,
            "zero_denominator_cases": 0,
            "aggregate_convergence_percent": 0.0,
            "headline_allowed": True,
        }
    )
    expect_policy_failure(changed, "unsupported structural positive branch")
    changed = copy.deepcopy(data)
    changed["inherited_dispositions"].pop()
    expect_policy_failure(changed, "missing inherited disposition")
    changed = copy.deepcopy(data)
    u07 = next(item for item in changed["inherited_dispositions"] if item["source_id"] == "R3-U07")
    u07["disposition"] = "closed"
    u07["evidence_ids"] = ["R4-E001"]
    expect_policy_failure(changed, "unrelated disposition evidence")
    changed = copy.deepcopy(data)
    u08 = next(item for item in changed["inherited_dispositions"] if item["source_id"] == "R3-U08")
    u08["evidence_ids"] = [evidence_id for evidence_id in u08["evidence_ids"] if evidence_id != "R4-E026"]
    expect_policy_failure(changed, "U08 independent evidence removal")
    changed = copy.deepcopy(data)
    changed["repository"]["implementation_commit"] = "bad"
    expect_policy_failure(changed, "malformed commit")
    changed = copy.deepcopy(data)
    changed["tasks"][0]["id"] = "x"
    expect_policy_failure(changed, "malformed task ID")
    changed = copy.deepcopy(data)
    changed["tasks"][0]["evidence"][0]["id"] = "y"
    expect_policy_failure(changed, "malformed evidence ID")
    changed = copy.deepcopy(data)
    changed["decisions"][0]["id"] = "z"
    expect_policy_failure(changed, "malformed decision ID")
    changed = copy.deepcopy(data)
    changed["tasks"][0]["evidence"][0]["executed_utc"] = "2099-01-01T00:00:00Z"
    expect_policy_failure(changed, "evidence after generated time")
    changed = copy.deepcopy(data)
    changed["evidence_hash_policy"]["external-audit-attestation"].remove("R4-E026")
    changed["evidence_hash_policy"]["captured-combined-stdout-stderr"].append("R4-E026")
    changed["tasks"][0]["evidence"][-1]["output_summary_sha256"] = "sha256:" + "1" * 64
    expect_policy_failure(changed, "external attestation hash-basis downgrade")

    changed = copy.deepcopy(data)
    changed["metrics"]["round4_policy_bundle_manifest"]["paths"] = ["handoff/validate.py"]
    expect_repository_failure(changed, handoff, "shrunken candidate manifest")
    changed = copy.deepcopy(data)
    changed["metrics"]["evals_blob_manifest"]["commit"] = repository_root_commit(handoff.parent)
    expect_repository_failure(changed, handoff, "blob manifest commit drift")
    changed = copy.deepcopy(data)
    changed["inherited_dispositions"][0]["source_index"] = 9
    expect_repository_failure(changed, handoff, "inherited source index drift")
    changed = copy.deepcopy(data)
    changed["tasks"][1]["evidence"][0]["input_manifest_sha256"] = "sha256:" + "2" * 64
    expect_repository_failure(changed, handoff, "policy evidence input drift")
    changed = copy.deepcopy(data)
    changed["metrics"]["structural_direction"]["zero_denominator_cases"] = 2
    expect_repository_failure(changed, handoff, "structural Markdown mirror drift")
    return 16


def repository_root_commit(repo: Path) -> str:
    return git(repo, "rev-list", "--max-parents=0", "HEAD").decode("ascii").strip().splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, choices=(3, 4))
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    handoff = Path(__file__).resolve().parent
    paths = sorted(handoff.glob("round_*.json"))
    if args.round:
        paths = [handoff / f"round_{args.round}.json"]
    results = []
    selftests = 0
    for path in paths:
        data = read_json(path)
        if data.get("schema") == "helicon-handoff-v1":
            results.append(validate_v1(data, handoff))
        elif data.get("schema") == "helicon-handoff-v2":
            summary = validate_v2_policy(data)
            summary.update(validate_v2_repository(data, handoff))
            summary.update({"round": 4, "schema": data["schema"]})
            results.append(summary)
            if args.selftest:
                selftests += selftest_v2(data, handoff)
        else:
            raise ValidationError(f"unsupported handoff schema: {data.get('schema')}")
    print(
        json.dumps(
            {
                "schema_valid": True,
                "policy_consistent": True,
                "repository_metadata_verified": all(item.get("repository_metadata_verified", True) for item in results),
                "evidence_truth_verified": False,
                "validation_scope": "schema-policy-and-repository-metadata-only",
                "negative_selftests": selftests,
                "rounds": results,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_valid": False, "error": str(exc)}, sort_keys=True))
        raise SystemExit(2)
