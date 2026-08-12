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
ROUND5_TASK_IDS = {"R5-0", "R5-1", "R4-ITERATION"}
ROUND5_EVIDENCE_ID_RE = re.compile(r"^R5-E\d{3}$")
ROUND5_DECISION_ID_RE = re.compile(r"^R5-D\d{3}$")
ROUND3_ITEMS = {*(f"R3-U{i:02d}" for i in range(1, 11)), *(f"R3-OQ{i:02d}" for i in range(1, 4))}
ROUND4_UNVERIFIED_IDS = [f"R4-U{i:02d}" for i in range(1, 11)]
ROUND4_BASE = "a52366983621b6481284f0c9a09f9fe3a866f2d8"
ROUND4_PUBLISHED = "a18364d535e3691b49be1c6c9ce3de1a087be14d"
ROUND5_BUNDLE_COMMIT = "bb388871f8a568f4a452fbae9dae98ac716a2705"
ROUND4_PUBLISHED_JSON_SHA256 = "sha256:8a19becb2db78645f359f7cf9104f0d8af5ac567a0a100ea06dd987be813df4e"
ROUND4_PUBLISHED_MANIFEST_SHA256 = "sha256:9180cfccbedef8f3f58b9c5b407f5a25ab2a0807c021012ccab77959a5416998"
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
ROUND5_CLAIM_POLICY = {
    "R4-U01": ("corpus", "corpus-qc", "carried-forward"),
    "R4-U02": ("corpus", "authority-approval", "carried-forward"),
    "R4-U03": ("corpus", "revision-attribution", "carried-forward"),
    "R4-U04": ("target", "revision-attribution", "carried-forward"),
    "R4-U05": ("privacy", "privacy-review", "carried-forward"),
    "R4-U06": ("evaluation", "evaluator-only", "carried-forward"),
    "R4-U07": ("evaluation", "structural", "blocked"),
    "R4-U08": ("evaluation", "fixture-provenance", "carried-forward"),
    "R4-U09": ("install", "install-rollback", "blocked"),
    "R4-U10": ("repository", "repository-integrity", "closed"),
}
ROUND5_REQUIRED_REQUEST_MARKERS = {
    "request_status=proposal-only-not-authorized",
    "holdout_before_profile_required=true",
    "holdout_precondition_status=declared-not-executed",
    "failure_mode=fail-closed",
    "structural_status=insufficient-coverage",
    "eligible_observations=6",
    "scorable_observations=2",
    "zero_denominator_cases=1",
    "aggregate_convergence_percent=null",
    "R4-ITERATION=partial",
    "authorized_closure_claims=R4-U01,R4-U02",
    "deferred_claims=R4-U03,R4-U04,R4-U05,R4-U06,R4-U07,R4-U08,R4-U09",
    "conditional_source_read_requires_stop=true",
    "stage1_summary_create_once=true",
    "holdout_receipt_creation_authorized=false",
    "profile_screening_target_direction_authorized=false",
    "private_paths_are_aliases=true",
    "structural_option_A_expands_private_paths=false",
    "structural_option_B_expands_private_paths=false",
    "structural_option_C_expands_private_paths=true",
}
ROUND5_REQUIRED_REQUEST_ALIASES = {
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/extraction_qc.md",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v1.txt",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v2.md",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v3.txt",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/v2_authority.md",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/versions.yaml",
    "<PRIVATE_SOURCE_ROOT>/version-2.tex",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stage1_summary.json",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/holdout_freeze_receipt.json",
}
ROUND5_REQUEST_ACCESS = {
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/extraction_qc.md": "READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v1.txt": "READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v2.md": "READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v3.txt": "READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/v2_authority.md": "READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/versions.yaml": "READ",
    "<PRIVATE_SOURCE_ROOT>/version-2.tex": "CONDITIONAL READ",
    "<PRIVATE_PAPER_ROOT>/.helicon/corpus/stage1_summary.json": "CREATE-ONCE",
}
ROUND5_REQUIRED_PROHIBITIONS = {
    "target_profile.json",
    "target_screening.json",
    "revision_direction.json",
    "reviewer_patterns.md",
    "holdout_manifest.md",
    "holdout_freeze_receipt.json",
    "live skill",
}
ROUND5_EXACT_CONTRACT_FRAGMENTS = {
    "u01_verdict_gate": "任一维度 verdict 为 `rejected` 或 `unknown` 时，`R4-U01` 必须保持 carried-forward，不得关闭。",
    "u02_approve_only": "只有明确的 `approve` author decision 才可关闭 `R4-U02`；`reject` 或 `unknown` 必须保持 carried-forward。",
    "u05_human_review": "| R4-U05 | R4-3 | `private-real-data + human_review != none`；最低为 `author-attested`，只有另行授权独立审阅者读取候选时才可用 `independent-human-reviewed`；候选始终私有 | 不可关闭 |",
    "holdout_future_authorization": "该门禁在本轮仅被声明，状态为 `declared-not-executed`。R4-2 不读取 hold-out、不生成 receipt；未来 R4-3 必须先单独获权，才能执行以下步骤：",
}
REQUEST_WINDOWS_PATH_RE = re.compile(r"(?i)(?:^|[\s`\"'(])(?:[a-z]:[\\/]|\\\\[^\\/\s]+[\\/][^\\/\s]+)")
REQUEST_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
# Hashes avoid publishing the private identifiers themselves. This is defense
# in depth only: a small known candidate set can still be reversed by targeted
# guessing, so semantic non-disclosure remains an external review boundary.
REQUEST_PRIVATE_PROJECT_TOKEN_SHA256 = frozenset(
    {
        "663efa1518d37bceeb16ff815e480eec81bf04c4156b42ac3e330a9cfd565fdd",
        "350758b0184945a325a2792d34f7de0539f99641837f450eb04ecae1fac7124f",
        "8384e0ba4b9db56bcf5c806b153603313d17a0b75e30aba9662ec5772aa8ee9a",
        "5111124f8cd7267e336944d87e243ace292bb6515abd30543c303d33422ce4b9",
        "b27a4f57f9d7b89fddbb1bbb8c97927f2707b8637d35988a779f56e027190b83",
        "394f322976d014c72d80df2a46a5ebbbd3765558e44ae2bae705c881c5228e10",
    }
)
REQUEST_PRIVATE_PROJECT_TOKEN_COUNT = 6
REQUEST_PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256 = (
    "bfc62c0661aa5e34baf279c924d405f1fbb8c028e74ffa0cc65682208b81d60a"
)
REQUEST_PROJECT_MENTION_SHA256 = frozenset(
    {"d1a52efc266a3bf735265ebd8bf73166268049054784dfa42293f460bebbda5d"}
)
REQUEST_PROJECT_MENTION_COUNT = 1
REQUEST_PROJECT_MENTION_MANIFEST_SHA256 = (
    "7581fc6d5284feb16fbc9d885601cc9a97585999b71867a85a23845aaf21691c"
)
ROUND6_TARGET_SEMANTICS = "imitation-fidelity-to-author-approved-ai-assisted-target"
CONVERGENCE_CLAIM_SCOPES = {"evaluator-only", "rule-direction", "structural"}
ROUND5_DIGEST_RECOMPUTATION_COMMAND = (
    "python -B -c \"import hashlib,json,os,runpy;"
    "v=json.loads(os.environ['HELICON_F1R_AUTHORITATIVE_LIST_JSON']);"
    "assert len(v)==len(set(v))==6 and all(isinstance(x,str) and x for x in v);"
    "d=frozenset(hashlib.sha256(x.casefold().encode('utf-8')).hexdigest() for x in v);"
    "m=('\\n'.join(sorted(d))+'\\n').encode('ascii');"
    "q=runpy.run_path('handoff/validate.py');"
    "assert d==q['REQUEST_PRIVATE_PROJECT_TOKEN_SHA256'];"
    "assert hashlib.sha256(m).hexdigest()==q['REQUEST_PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256'];"
    "assert all(q['contains_private_identifier_digest']([x],d) for x in v);"
    "print(json.dumps({'digest_set_matches_pinned':True,'manifest_matches_pinned':True,'per_item_rejected':6},"
    "sort_keys=True,separators=(',',':')))\""
)
ROUND5_DIGEST_LIMITATION_DEVIATION = {
    "what": "Round 5 uses a six-entry case-folded SHA-256 digest denylist as defense in depth.",
    "why": "It blocks bounded literal matches without publishing the literals.",
    "impact": (
        "A small known candidate set is vulnerable to targeted dictionary guessing; an external audit recovered "
        "five of six digests. This does not verify semantic non-disclosure, which remains an external human-review boundary."
    ),
}
HANDOFF_GITATTRIBUTES = b"* text=auto eol=lf\n"
ROUND5_EXTERNAL_COMMANDS = [
    "python -B scripts/selftest_checks.py",
    "python -B scripts/check_contract_sync.py",
    "python -B scripts/check_skill_integrity.py .",
    "python -B scripts/check_core_contamination.py .",
    "python -B evals/run_all.py",
    "python -B handoff/validate.py --selftest",
    "git diff --check",
    "git status --porcelain=v1",
]


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


def canonical_lf_bytes(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_lf_sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(canonical_lf_bytes(value)).hexdigest()


def first_difference_byte_offset(expected: bytes, actual: bytes) -> int | None:
    for offset, (expected_byte, actual_byte) in enumerate(zip(expected, actual)):
        if expected_byte != actual_byte:
            return offset
    return len(expected) if len(expected) != len(actual) else None


def validate_private_token_hashes(private_token_hashes: frozenset[str]) -> None:
    require(
        isinstance(private_token_hashes, frozenset)
        and len(private_token_hashes) == REQUEST_PRIVATE_PROJECT_TOKEN_COUNT
        and all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in private_token_hashes),
        "private identifier digest set missing or malformed",
    )
    manifest = ("\n".join(sorted(private_token_hashes)) + "\n").encode("ascii")
    require(
        hashlib.sha256(manifest).hexdigest() == REQUEST_PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256,
        "private identifier digest set incomplete or replaced",
    )


def validate_project_mention_hashes(
    project_mention_hashes: frozenset[str] = REQUEST_PROJECT_MENTION_SHA256,
    expected_count: int = REQUEST_PROJECT_MENTION_COUNT,
    expected_manifest_sha256: str = REQUEST_PROJECT_MENTION_MANIFEST_SHA256,
) -> None:
    require(
        isinstance(project_mention_hashes, frozenset)
        and len(project_mention_hashes) == expected_count
        and all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in project_mention_hashes),
        "project mention digest set missing or malformed",
    )
    manifest = ("\n".join(sorted(project_mention_hashes)) + "\n").encode("ascii")
    require(
        hashlib.sha256(manifest).hexdigest() == expected_manifest_sha256,
        "project mention digest set incomplete or replaced",
    )


def contains_private_identifier_digest(texts: list[str], private_token_hashes: frozenset[str]) -> bool:
    for text in texts:
        for candidate in REQUEST_TOKEN_RE.findall(text.casefold()):
            for start in range(len(candidate)):
                for end in range(start + 1, min(len(candidate), start + 128) + 1):
                    digest = hashlib.sha256(candidate[start:end].encode("utf-8")).hexdigest()
                    if digest in private_token_hashes:
                        return True
    return False


def validate_private_identifier_texts(
    texts: list[str], private_token_hashes: frozenset[str] = REQUEST_PRIVATE_PROJECT_TOKEN_SHA256
) -> None:
    validate_private_token_hashes(private_token_hashes)
    require(
        not contains_private_identifier_digest(texts, private_token_hashes),
        "public handoff contains a private project identifier digest match",
    )


def validate_project_mention_texts(
    texts: list[str],
    project_mention_hashes: frozenset[str] = REQUEST_PROJECT_MENTION_SHA256,
    expected_count: int = REQUEST_PROJECT_MENTION_COUNT,
    expected_manifest_sha256: str = REQUEST_PROJECT_MENTION_MANIFEST_SHA256,
) -> None:
    validate_project_mention_hashes(
        project_mention_hashes,
        expected_count,
        expected_manifest_sha256,
    )
    require(
        not contains_private_identifier_digest(texts, project_mention_hashes),
        "public handoff contains a project mention digest match",
    )


def validate_handoff_private_identifiers(handoff: Path) -> None:
    texts = [
        path.read_text(encoding="utf-8")
        for path in sorted(handoff.rglob("*"))
        if path.is_file()
    ]
    validate_private_identifier_texts(texts)
    validate_project_mention_texts(texts)


def validate_handoff_gitattributes(value: bytes) -> None:
    require(canonical_lf_bytes(value) == HANDOFF_GITATTRIBUTES, "handoff .gitattributes policy mismatch")


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


def canonical_text_manifest(repo: Path, paths: list[str], commit: str | None = None) -> dict:
    entries = []
    for relative in sorted(paths, key=lambda value: value.encode("utf-8")):
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, f"invalid candidate path: {relative}")
        if commit is None:
            target = repo / relative
            require(target.is_file(), f"candidate path invalid: {relative}")
            content = target.read_bytes()
        else:
            content = git(repo, "show", f"{commit}:{relative}")
        content = canonical_lf_bytes(content)
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


def validate_round4_postpublication(current: dict, published: dict, report: str) -> None:
    require(current.get("status") == "partial", "current Round 4 status must remain partial")
    require(
        current.get("unverified_claims") == published.get("unverified_claims", [])[:9],
        "current Round 4 carried claims differ from the published source",
    )
    expected_resolution = {
        "id": "R4-U10",
        "status": "closed-by-external-audit",
        "closed_in_round": 5,
        "repository_ref": "refs/heads/codex/round4-evidence-closure",
        "commit": ROUND4_PUBLISHED,
        "parent": ROUND4_BASE,
        "scope": "repository publication and fresh-clone reproducibility only",
        "capability_implication": False,
    }
    require(current.get("subsequent_resolutions") == [expected_resolution], "current Round 4 U10 resolution mismatch")
    repository = current.get("repository", {})
    require(
        repository.get("round4_containing_commit") == ROUND4_PUBLISHED
        and repository.get("round4_containing_commit_status") == "published-and-independently-audited",
        "current Round 4 publication metadata mismatch",
    )
    iteration = [task for task in current.get("tasks", []) if task.get("id") == "R4-ITERATION"]
    require(
        len(iteration) == 1
        and iteration[0].get("status") == "partial"
        and iteration[0].get("capability_claim") is False
        and iteration[0].get("capability_scopes") == [],
        "current Round 4 iteration state mismatch",
    )
    require("| Status | `partial` |" in report, "current Round 4 report status mismatch")
    require(
        f"| Round 4 containing commit | `{ROUND4_PUBLISHED}`" in report and ROUND4_BASE in report,
        "current Round 4 report publication mirror mismatch",
    )
    require(
        "| R4-ITERATION | `partial` | `false` |" in report,
        "current Round 4 report iteration mirror mismatch",
    )
    require(
        "当前保留 9 项 unverified claims" in report
        and "仓库发布与可复现性" in report
        and "不产生能力证据" in report,
        "current Round 4 report closure mirror mismatch",
    )
    require("bundle uncommitted" not in report, "current Round 4 report retains unpublished wording")


def validate_round5_request(
    request: str,
    private_token_hashes: frozenset[str] = REQUEST_PRIVATE_PROJECT_TOKEN_SHA256,
    project_mention_hashes: frozenset[str] = REQUEST_PROJECT_MENTION_SHA256,
    project_mention_count: int = REQUEST_PROJECT_MENTION_COUNT,
    project_mention_manifest_sha256: str = REQUEST_PROJECT_MENTION_MANIFEST_SHA256,
) -> None:
    validate_private_token_hashes(private_token_hashes)
    validate_project_mention_hashes(
        project_mention_hashes,
        project_mention_count,
        project_mention_manifest_sha256,
    )
    for marker in ROUND5_REQUIRED_REQUEST_MARKERS:
        require(marker in request, f"R4-2 request marker missing: {marker}")
    for alias in ROUND5_REQUIRED_REQUEST_ALIASES:
        require(alias in request, f"R4-2 request alias missing: {alias}")
    for alias, access in ROUND5_REQUEST_ACCESS.items():
        require(f"| {access} | `{alias}` |" in request, f"R4-2 request access mode mismatch: {alias}")
    require("R4-2 明确不授权访问" in request, "R4-2 request prohibition heading missing")
    for item in ROUND5_REQUIRED_PROHIBITIONS:
        require(item in request, f"R4-2 request prohibition missing: {item}")
    for contract, fragment in ROUND5_EXACT_CONTRACT_FRAGMENTS.items():
        require(fragment in request, f"R4-2 exact contract missing: {contract}")
    require("若任一 `CREATE-ONCE` 目标已经存在，执行者必须停下，不得覆盖" in request, "R4-2 create-once stop rule missing")
    require("触发前必须停下并取得精确扩权" in request, "R4-2 conditional-read stop rule missing")
    require(
        "本阶段不得读取 `holdout_manifest.md` 或创建 `holdout_freeze_receipt.json`" in request,
        "R4-2 hold-out non-execution boundary missing",
    )
    require(REQUEST_WINDOWS_PATH_RE.search(request) is None, "R4-2 request contains a Windows absolute or UNC path")
    validate_private_identifier_texts([request], private_token_hashes)
    validate_project_mention_texts(
        [request],
        project_mention_hashes,
        project_mention_count,
        project_mention_manifest_sha256,
    )


def validate_r5_e002_input(
    request_evidence: dict,
    request_bytes: bytes,
    expected_request_bytes: bytes,
) -> None:
    require(not request_bytes.startswith(b"\xef\xbb\xbf"), "R5-E002 authorization request contains a UTF-8 BOM")
    expected_hash = request_evidence["input_manifest_sha256"]
    actual_hash = canonical_lf_sha256(request_bytes)
    if expected_hash != actual_hash:
        offset = first_difference_byte_offset(
            canonical_lf_bytes(expected_request_bytes),
            canonical_lf_bytes(request_bytes),
        )
        raise ValidationError(
            "R5-E002 canonical-LF input hash mismatch: "
            f"expected={expected_hash} actual={actual_hash} "
            f"first_difference_byte_offset={offset if offset is not None else 'none'}"
        )


def validate_round6_quality_boundary(data: dict) -> None:
    if not isinstance(data.get("round"), int) or data["round"] < 6:
        return
    require(
        data.get("target_semantics") == ROUND6_TARGET_SEMANTICS,
        "round 6+ target_semantics boundary mismatch",
    )
    require(data.get("quality_claim_allowed") is False, "round 6+ quality claim must remain disallowed")

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if any("convergence" in str(key).casefold() for key in value):
                require(
                    value.get("claim_scope") in CONVERGENCE_CLAIM_SCOPES,
                    "round 6+ convergence metric has a quality-implicating or missing claim_scope",
                )
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(data.get("metrics", {}))


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


def validate_v2_round4_policy(data: dict) -> dict:
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
    round4_publication = (
        repository.get("round4_containing_commit"),
        repository.get("round4_containing_commit_status"),
    )
    require(
        round4_publication
        in {
            (None, "externally-resolved-after-publication"),
            (ROUND4_PUBLISHED, "published-and-independently-audited"),
        },
        "invalid Round 4 publication metadata",
    )
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


def validate_v2_round4_repository(data: dict, handoff: Path) -> dict:
    repo = handoff.parent
    repository = data["repository"]
    git(repo, "cat-file", "-e", ROUND4_PUBLISHED + "^{commit}")
    published_parents = git(repo, "show", "-s", "--format=%P", ROUND4_PUBLISHED).decode("ascii").strip().split()
    require(published_parents == [ROUND4_BASE], "published Round 4 parent mismatch")
    published_bytes = git(repo, "show", f"{ROUND4_PUBLISHED}:handoff/round_4.json")
    require(
        "sha256:" + hashlib.sha256(published_bytes).hexdigest() == ROUND4_PUBLISHED_JSON_SHA256,
        "published Round 4 JSON hash mismatch",
    )
    published_data = json.loads(published_bytes.decode("utf-8"))
    current_report = (handoff / "ROUND_4_HANDOFF.md").read_text(encoding="utf-8")
    validate_round4_postpublication(data, published_data, current_report)
    require(
        data["metrics"]["synthetic_regression"] == published_data["metrics"]["synthetic_regression"],
        "historical Round 4 synthetic metric was rewritten",
    )
    require(
        data["metrics"]["structural_direction"] == published_data["metrics"]["structural_direction"],
        "historical Round 4 structural metric was rewritten",
    )
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
    require(
        candidate == published_data["metrics"]["round4_policy_bundle_manifest"],
        "historical Round 4 candidate manifest was rewritten",
    )
    require(candidate.get("paths") == CANDIDATE_PATHS, "Round 4 candidate path set mismatch")
    require(len(candidate["paths"]) == len(set(candidate["paths"])), "Round 4 candidate paths duplicated")
    require(
        candidate.get("self_referential_file_excluded") == "handoff/round_4.json"
        and candidate.get("canonical_repository_digest") is False
        and isinstance(candidate.get("note"), str)
        and candidate["note"],
        "Round 4 candidate manifest metadata mismatch",
    )
    actual_candidate = canonical_text_manifest(repo, candidate["paths"], ROUND4_PUBLISHED)
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

    published_report = git(repo, "show", f"{ROUND4_PUBLISHED}:handoff/ROUND_4_HANDOFF.md").decode("utf-8")
    published_index = git(repo, "show", f"{ROUND4_PUBLISHED}:handoff/INDEX.md").decode("utf-8")
    require("HElicon Round 4" in published_report and f"| Status | `{published_data['status']}` |" in published_report, "Round 4 report identity mismatch")
    for field in ("implementation_commit", "handoff_commit", "audited_checkout_commit"):
        require(published_data["repository"][field] in published_report, f"Round 4 report missing {field}")
    for task in published_data["tasks"]:
        require(f"| {task['id']} | `{task['status']}` |" in published_report, f"Round 4 report task mismatch: {task['id']}")
        capability_text = "true" if task["capability_claim"] else "false"
        require(f"| {task['id']} | `{task['status']}` | `{capability_text}` |" in published_report, f"Round 4 report task capability mismatch: {task['id']}")
    for item in published_data["inherited_dispositions"]:
        require(f"| {item['source_id']} | `{item['disposition']}` |" in published_report, f"Round 4 report disposition mismatch: {item['source_id']}")
    structural = published_data["metrics"]["structural_direction"]
    require(f"- eligible：{structural['eligible_observations']}" in published_report, "Round 4 report structural eligible mismatch")
    require(f"- scorable：{structural['scorable_observations']}" in published_report, "Round 4 report structural scorable mismatch")
    require(f"- coverage：{structural['coverage_percent']}%" in published_report, "Round 4 report structural coverage mismatch")
    require(f"- status：`{structural['status']}`" in published_report, "Round 4 report structural status mismatch")
    require(f"- zero-denominator cases：{structural['zero_denominator_cases']}" in published_report, "Round 4 report structural zero-denominator mismatch")
    aggregate_text = "`null`" if structural["aggregate_convergence_percent"] is None else str(structural["aggregate_convergence_percent"])
    require(f"- aggregate：{aggregate_text}" in published_report, "Round 4 report structural aggregate mismatch")
    headline_text = "允许" if structural["headline_allowed"] else "不允许"
    require(f"- headline：{headline_text}" in published_report, "Round 4 report structural headline mismatch")
    require(
        f"{len(published_data['unverified_claims'])} 项" in published_report
        and f"{len(published_data['open_questions'])} 项开放问题" in published_report,
        "Round 4 report outstanding counts mismatch",
    )
    require(f"{len(published_data['deviations'])} 项偏差" in published_report, "Round 4 report deviation count mismatch")
    require(
        f"| 4 |" in published_index
        and f"| {len(published_data['unverified_claims'])} | {len(published_data['open_questions'])} |" in published_index,
        "Round 4 index mismatch",
    )
    return {"repository_metadata_verified": True}


def validate_v2_round5_policy(data: dict) -> dict:
    required = {
        "schema",
        "round",
        "status",
        "taskbook",
        "taskbook_role",
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
    require(not (required - set(data)), "Round 5 v2 missing top-level fields")
    require(data["schema"] == "helicon-handoff-v2" and data["round"] == 5, "invalid Round 5 v2 identity")
    require(data["status"] == "partial", "Round 5 must remain partial")
    require(data["taskbook"] == "handoff/R4_2_AUTHORIZATION_REQUEST.md", "Round 5 request path mismatch")
    require(data["taskbook_role"] == "authorization-request-only", "Round 5 request role mismatch")
    require("head_commit" not in data, "v2 forbids ambiguous head_commit")
    generated_utc = utc(data["generated_utc"], "generated_utc")

    authorization = data["authorization_scope"]
    require(
        authorization.get("authorized_stages") == []
        and authorization.get("requested_stage") == "R4-2"
        and authorization.get("request_status") == "proposal-only-not-authorized"
        and authorization.get("stop_after") == "R4-2-authorization-request"
        and authorization.get("private_data_access") is False
        and authorization.get("stage_computation_authorized") is False
        and authorization.get("live_skill_access") is False
        and authorization.get("installation_authorized") is False
        and authorization.get("merge_tag_push_authorized") is False,
        "Round 5 authorization boundary mismatch",
    )
    for optional_flag in ("merge_authorized", "tag_authorized", "push_authorized"):
        require(authorization.get(optional_flag, False) is False, f"Round 5 authorization exceeds scope: {optional_flag}")

    repository = data["repository"]
    require(repository.get("origin_url") == "https://github.com/SeehowLi/HElicon.git", "Round 5 origin mismatch")
    require(repository.get("work_branch") == "codex/round4-evidence-closure", "Round 5 branch mismatch")
    require(repository.get("round4_bundle_commit") == ROUND4_PUBLISHED, "Round 5 source commit mismatch")
    require(repository.get("round4_bundle_parent") == ROUND4_BASE, "Round 5 source parent mismatch")
    require(repository.get("round5_containing_commit") is None, "unpublished Round 5 commit must be null")
    require(
        repository.get("round5_containing_commit_status") == "unpublished-self-reference-excluded",
        "Round 5 containing-commit status mismatch",
    )

    hash_policy = data["evidence_hash_policy"]
    input_policy = hash_policy.get("input-canonicalization")
    require(
        set(hash_policy) == OUTPUT_HASH_BASES | {"input-canonicalization"},
        "Round 5 evidence hash policy basis mismatch",
    )
    require(
        input_policy
        == {
            "R5-E002": {
                "algorithm": "sha256-canonical-text-v1",
                "encoding": "UTF-8",
                "line_endings": "LF",
            }
        },
        "Round 5 input canonicalization mismatch",
    )
    basis_by_id = {}
    for basis, evidence_ids in hash_policy.items():
        if basis == "input-canonicalization":
            continue
        require(isinstance(evidence_ids, list) and len(evidence_ids) == len(set(evidence_ids)), f"Round 5 duplicate hash-policy ID: {basis}")
        for evidence_id in evidence_ids:
            require(evidence_id not in basis_by_id, f"Round 5 evidence has multiple hash bases: {evidence_id}")
            basis_by_id[evidence_id] = basis

    task_by_id = {}
    evidence_by_id = {}
    evidence_times = []
    for task in data["tasks"]:
        task_id = task.get("id")
        require(task_id in ROUND5_TASK_IDS and task_id not in task_by_id, f"invalid/duplicate Round 5 task: {task_id}")
        task_by_id[task_id] = task
        expected_status = "partial" if task_id == "R4-ITERATION" else "done"
        require(task.get("status") == expected_status, f"Round 5 task status mismatch: {task_id}")
        require(task.get("claim_domains") == ["repository"], f"Round 5 task domain escalation: {task_id}")
        require(task.get("claim_scopes") == ["repository-integrity"], f"Round 5 task scope escalation: {task_id}")
        require(task.get("capability_claim") is False and task.get("capability_scopes") == [], f"Round 5 capability escalation: {task_id}")
        evidence = task.get("evidence", [])
        require(isinstance(evidence, list), f"invalid Round 5 task evidence: {task_id}")
        require((task_id == "R4-ITERATION") == (not evidence), f"Round 5 task evidence/status mismatch: {task_id}")
        require(isinstance(task.get("note"), str) and task["note"], f"Round 5 task note missing: {task_id}")
        for item in evidence:
            evidence_id = item.get("id")
            require(
                isinstance(evidence_id, str)
                and ROUND5_EVIDENCE_ID_RE.match(evidence_id)
                and evidence_id not in evidence_by_id,
                f"invalid/duplicate Round 5 evidence: {evidence_id}",
            )
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
            require(not (required_evidence - set(item)), f"Round 5 evidence fields missing: {evidence_id}")
            require(type(item["exit_code"]) is int and item["exit_code"] == 0, f"Round 5 evidence exit mismatch: {evidence_id}")
            record_type = item.get("record_type", "command-execution")
            require(record_type in {"command-execution", "external-audit-attestation"}, f"invalid Round 5 evidence type: {evidence_id}")
            if record_type == "command-execution":
                evidence_time = utc(item["executed_utc"], f"{evidence_id}.executed_utc")
                require("recorded_utc" not in item, f"Round 5 command evidence must use executed_utc: {evidence_id}")
            else:
                require(item["executed_utc"] is None, f"Round 5 external audit invented execution time: {evidence_id}")
                require(item.get("execution_time_status") == "not-reported-by-source", f"Round 5 external execution-time mismatch: {evidence_id}")
                evidence_time = utc(item.get("recorded_utc", ""), f"{evidence_id}.recorded_utc")
                external_commands = item.get("external_commands", [])
                external_exits = item.get("external_exit_codes", [])
                require(external_commands == ROUND5_EXTERNAL_COMMANDS, f"Round 5 external command bundle mismatch: {evidence_id}")
                require(len(external_exits) == len(ROUND5_EXTERNAL_COMMANDS), f"Round 5 external exit bundle mismatch: {evidence_id}")
                require(all(code == 0 for code in external_exits), f"Round 5 external audit includes unexpected command failure: {evidence_id}")
                require(item["execution_provenance"] == "independent-session", f"Round 5 external audit provenance mismatch: {evidence_id}")
            evidence_times.append(evidence_time)
            require(HASH_RE.match(item["input_manifest_sha256"]) and HASH_RE.match(item["output_summary_sha256"]), f"invalid Round 5 evidence hash: {evidence_id}")
            require(item["input_manifest_sha256"] != "sha256:" + "0" * 64, f"Round 5 placeholder input hash: {evidence_id}")
            require(item["output_summary_sha256"] != "sha256:" + "0" * 64, f"Round 5 placeholder output hash: {evidence_id}")
            require(item["data_provenance"] == "repository-metadata", f"Round 5 non-public data provenance: {evidence_id}")
            require(item["execution_provenance"] in EXECUTION_PROVENANCE, f"invalid Round 5 execution provenance: {evidence_id}")
            require(item["target_provenance"] == "none", f"Round 5 target provenance escalation: {evidence_id}")
            require(item["human_review"] == "none", f"Round 5 human-review evidence escalation: {evidence_id}")
            require(item["claim_domain"] == "repository" and item["claim_scope"] == "repository-integrity", f"Round 5 evidence scope escalation: {evidence_id}")
            evidence_by_id[evidence_id] = item

    require(set(task_by_id) == ROUND5_TASK_IDS, "Round 5 task set mismatch")
    require(set(basis_by_id) == set(evidence_by_id), "Round 5 hash policy must cover every evidence exactly once")
    request_evidence = evidence_by_id.get("R5-E002", {})
    request_command = request_evidence.get("command", "")
    require(
        request_evidence.get("record_type", "command-execution") == "command-execution"
        and (
            request_command.startswith("python -B -c ")
            or ("Get-Content" in request_command and "throw" in request_command)
        ),
        "R5-E002 must contain an executable verification command",
    )
    for evidence_id, basis in basis_by_id.items():
        item = evidence_by_id[evidence_id]
        is_external = item.get("record_type", "command-execution") == "external-audit-attestation"
        require(is_external == (basis == "external-audit-attestation"), f"Round 5 external hash-basis mismatch: {evidence_id}")
        if basis in {"sanitized-key-output", "external-audit-attestation"}:
            require(sha256_text(item["key_output"]) == item["output_summary_sha256"], f"Round 5 recomputable output hash mismatch: {evidence_id}")

    decision_ids = set()
    decision_times = []
    for decision in data["decisions"]:
        decision_id = decision.get("id")
        require(
            isinstance(decision_id, str)
            and ROUND5_DECISION_ID_RE.match(decision_id)
            and decision_id not in decision_ids,
            f"invalid/duplicate Round 5 decision: {decision_id}",
        )
        decision_ids.add(decision_id)
        require(decision.get("actor") == "author" and isinstance(decision.get("decision"), str) and decision["decision"], f"invalid Round 5 decision: {decision_id}")
        decision_times.append(utc(decision.get("recorded_utc", ""), f"{decision_id}.recorded_utc"))
    require(decision_ids, "Round 5 author decision missing")
    require(generated_utc >= max(evidence_times + decision_times), "Round 5 generated_utc precedes evidence or decisions")
    require(generated_utc <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5), "Round 5 generated_utc is implausibly in the future")

    source = data["inherited_source"]
    require(
        source.get("commit") == ROUND4_PUBLISHED
        and source.get("path") == "handoff/round_4.json"
        and source.get("sha256") == ROUND4_PUBLISHED_JSON_SHA256
        and source.get("id_derivation") == "preserved-source-ids-v1"
        and source.get("unverified_claims") == 10
        and source.get("open_questions") == 0,
        "Round 5 inherited source metadata mismatch",
    )

    unverified_ids = [item.get("id") for item in data["unverified_claims"]]
    require(unverified_ids == ROUND4_UNVERIFIED_IDS[:9], "Round 5 remaining claim IDs/order mismatch")
    require(len(data["open_questions"]) == 1, "Round 5 must retain exactly one authorization question")
    authorization_question = data["open_questions"][0]
    require(
        authorization_question.get("id") == "R5-OQ01"
        and isinstance(authorization_question.get("question"), str)
        and authorization_question["question"]
        and isinstance(authorization_question.get("options"), list)
        and authorization_question["options"]
        and isinstance(authorization_question.get("recommendation"), str)
        and authorization_question["recommendation"],
        "invalid Round 5 authorization question",
    )

    disposition_by_id = {}
    for item in data["inherited_dispositions"]:
        source_id = item.get("source_id")
        require(source_id in ROUND5_CLAIM_POLICY and source_id not in disposition_by_id, f"invalid/duplicate Round 5 disposition: {source_id}")
        disposition_by_id[source_id] = item
        expected_domain, expected_scope, expected_disposition = ROUND5_CLAIM_POLICY[source_id]
        require(item.get("source_kind") == "unverified_claim", f"Round 5 disposition kind mismatch: {source_id}")
        require(item.get("source_index") == ROUND4_UNVERIFIED_IDS.index(source_id), f"Round 5 disposition source index mismatch: {source_id}")
        require(item.get("claim_domain") == expected_domain and item.get("claim_scope") == expected_scope, f"Round 5 disposition scope mismatch: {source_id}")
        require(item.get("disposition") == expected_disposition, f"Round 5 disposition mismatch: {source_id}")
        require(isinstance(item.get("evidence_ids"), list) and set(item["evidence_ids"]) <= set(evidence_by_id), f"Round 5 dangling disposition evidence: {source_id}")
        require(isinstance(item.get("decision_ids"), list) and set(item["decision_ids"]) <= decision_ids, f"Round 5 dangling disposition decision: {source_id}")
        require(isinstance(item.get("rationale"), str) and item["rationale"], f"Round 5 disposition rationale missing: {source_id}")
        if source_id != "R4-U10":
            require(item.get("successor_id", source_id) == source_id, f"Round 5 carried claim ID changed: {source_id}")
            require(not item["evidence_ids"], f"Round 5 carried claim received new evidence: {source_id}")
        else:
            require("successor_id" not in item, "closed R4-U10 must not have a successor")
            require(item["evidence_ids"] and item["decision_ids"], "R4-U10 closure lacks evidence or author decision")
            r5_0_evidence_ids = {evidence["id"] for evidence in task_by_id["R5-0"]["evidence"]}
            require(set(item["evidence_ids"]) <= r5_0_evidence_ids, "R4-U10 closure evidence is not attached to R5-0")
            matching = [evidence_by_id[evidence_id] for evidence_id in item["evidence_ids"]]
            require(
                any(
                    evidence.get("record_type") == "external-audit-attestation"
                    and evidence["execution_provenance"] == "independent-session"
                    and evidence["data_provenance"] == "repository-metadata"
                    and evidence["claim_scope"] == "repository-integrity"
                    for evidence in matching
                ),
                "R4-U10 closure lacks independent repository attestation",
            )
    require(set(disposition_by_id) == set(ROUND4_UNVERIFIED_IDS), "Round 5 dispositions must cover R4-U01 through R4-U10")

    legacy = data["legacy_task_dispositions"]
    require(len(legacy) == 1, "Round 5 R4-ITERATION disposition missing")
    require(
        legacy[0].get("source_id") == "R4-ITERATION"
        and legacy[0].get("recorded_status") == "partial"
        and legacy[0].get("round5_disposition") == "retained-partial"
        and isinstance(legacy[0].get("rationale"), str)
        and legacy[0]["rationale"],
        "Round 5 R4-ITERATION disposition mismatch",
    )

    synthetic = data["metrics"]["synthetic_regression"]
    require(synthetic.get("pipeline_runnable") is True, "Round 5 synthetic pipeline state missing")
    require(synthetic.get("capability_validated") is False, "Round 5 synthetic capability escalation")
    require(synthetic.get("claim_scope") == "pipeline-only" and synthetic.get("generation_path_exercised") is False, "Round 5 synthetic scope mismatch")
    structural = data["metrics"]["structural_direction"]
    coverage = structural.get("coverage_percent")
    require(
        structural.get("status") == "insufficient-coverage"
        and structural.get("eligible_observations") == 6
        and structural.get("scorable_observations") == 2
        and isinstance(coverage, (int, float))
        and abs(coverage - 33.3333) <= 0.001
        and structural.get("zero_denominator_cases") == 1
        and structural.get("aggregate_convergence_percent") is None
        and structural.get("headline_allowed") is False,
        "Round 5 structural boundary mismatch",
    )
    external_audit = data["metrics"]["external_audit"]
    closure_evidence_ids = disposition_by_id["R4-U10"]["evidence_ids"]
    require(external_audit.get("evidence_id") in closure_evidence_ids, "Round 5 external-audit evidence link mismatch")
    require(external_audit.get("fresh_https_clone") is True, "Round 5 fresh-clone audit missing")
    require(external_audit.get("public_commands_exit_zero") == 8, "Round 5 public command count mismatch")
    tamper_rejected = external_audit.get("tamper_injections_rejected", external_audit.get("validator_tamper_injections_rejected"))
    require(tamper_rejected == 6 and external_audit.get("tamper_expected_exit_code") == 2, "Round 5 tamper-test summary mismatch")
    require(external_audit.get("capability_validated") is False, "Round 5 external audit capability escalation")
    require(external_audit.get("evidence_truth_verified") is False, "Round 5 validator must not claim evidence truth")

    privacy = data["privacy"]
    require(
        privacy.get("private_data_read") is False
        and privacy.get("live_skill_read") is False
        and privacy.get("private_paths_recorded") is False
        and privacy.get("stage_computations_executed") is False,
        "Round 5 privacy or computation boundary mismatch",
    )
    digest_provenance = privacy.get("digest_set_provenance")
    require(
        digest_provenance
        == {
            "source": "author-supplied-authoritative-six-item-list",
            "source_handling": "ephemeral-in-memory-only",
            "canonical_rule": "sha256(casefold(literal).utf-8)",
            "count": REQUEST_PRIVATE_PROJECT_TOKEN_COUNT,
            "unique_digest_count": REQUEST_PRIVATE_PROJECT_TOKEN_COUNT,
            "manifest_rule": "sha256(ascii-sort-lowercase-hex-lines-with-final-LF)",
            "manifest_bytes": 390,
            "manifest_sha256": "sha256:" + REQUEST_PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256,
            "recomputation_command": ROUND5_DIGEST_RECOMPUTATION_COMMAND,
            "exit_code": 0,
            "executed_utc": "2026-08-12T08:36:17.725531Z",
            "digest_set_matches_pinned": True,
            "manifest_matches_pinned": True,
            "per_item_rejected": 6,
            "private_identifier_literals_processed_ephemerally": True,
            "plaintext_retained": False,
            "plaintext_to_digest_mapping_retained": False,
            "claim_scope": "denylist-derivation-integrity-only",
            "semantic_non_disclosure_verified": False,
        },
        "Round 5 digest-set provenance mismatch",
    )
    require(
        ROUND5_DIGEST_LIMITATION_DEVIATION in data["deviations"],
        "Round 5 digest-set limitation deviation missing",
    )
    require(isinstance(data["reproduce"], list) and all(isinstance(item, str) and item for item in data["reproduce"]), "invalid Round 5 reproduce commands")
    require(all({"what", "why", "impact"} <= set(item) for item in data["deviations"]), "invalid Round 5 deviation")
    return {"tasks": len(task_by_id), "evidence": len(evidence_by_id), "dispositions": len(disposition_by_id)}


def validate_v2_round5_repository(data: dict, handoff: Path) -> dict:
    repo = handoff.parent
    repository = data["repository"]
    git(repo, "cat-file", "-e", ROUND4_PUBLISHED + "^{commit}")
    parents = git(repo, "show", "-s", "--format=%P", ROUND4_PUBLISHED).decode("ascii").strip().split()
    require(parents == [ROUND4_BASE], "Round 5 source parent mismatch")
    require(git(repo, "remote", "get-url", "origin").decode("utf-8").strip() == repository["origin_url"], "Round 5 origin URL mismatch")

    source = data["inherited_source"]
    source_bytes = git(repo, "show", f"{source['commit']}:{source['path']}")
    require("sha256:" + hashlib.sha256(source_bytes).hexdigest() == source["sha256"], "Round 5 inherited source hash mismatch")
    source_data = json.loads(source_bytes.decode("utf-8"))
    require([item.get("id") for item in source_data["unverified_claims"]] == ROUND4_UNVERIFIED_IDS, "published Round 4 claim set mismatch")
    current_round4 = read_json(handoff / "round_4.json")
    current_round4_report = (handoff / "ROUND_4_HANDOFF.md").read_text(encoding="utf-8")
    validate_round4_postpublication(current_round4, source_data, current_round4_report)
    require(data["unverified_claims"] == source_data["unverified_claims"][:9], "Round 5 carried claims were modified")
    require(data["metrics"]["synthetic_regression"] == source_data["metrics"]["synthetic_regression"], "Round 5 synthetic metric drift")
    require(data["metrics"]["structural_direction"] == source_data["metrics"]["structural_direction"], "Round 5 structural metric drift")

    actual_manifest = git_blob_manifest(repo, ROUND4_PUBLISHED)
    require(actual_manifest["sha256"] == ROUND4_PUBLISHED_MANIFEST_SHA256, "published Round 4 manifest drift")
    evidence_by_id = {item["id"]: item for task in data["tasks"] for item in task.get("evidence", [])}
    closure = next(item for item in data["inherited_dispositions"] if item["source_id"] == "R4-U10")
    for evidence_id in closure["evidence_ids"]:
        evidence = evidence_by_id[evidence_id]
        if evidence.get("record_type") == "external-audit-attestation":
            require(evidence["input_manifest_sha256"] == actual_manifest["sha256"], "R4-U10 audit input manifest mismatch")

    request_path = repo / data["taskbook"]
    require(request_path.is_file(), "R4-2 authorization request missing")
    request_bytes = request_path.read_bytes()
    request_evidence = evidence_by_id["R5-E002"]
    expected_request_bytes = git(repo, "show", f"{ROUND5_BUNDLE_COMMIT}:{data['taskbook']}")
    validate_r5_e002_input(request_evidence, request_bytes, expected_request_bytes)
    request = canonical_lf_bytes(request_bytes).decode("utf-8")
    validate_round5_request(request)
    validate_handoff_private_identifiers(handoff)
    attributes_path = handoff / ".gitattributes"
    require(attributes_path.is_file(), "handoff .gitattributes missing")
    validate_handoff_gitattributes(attributes_path.read_bytes())
    for claim_id in ROUND4_UNVERIFIED_IDS[:9]:
        require(claim_id in request, f"R4-2 request omits remaining claim: {claim_id}")

    index = (handoff / "INDEX.md").read_text(encoding="utf-8")
    require("| 4 |" in index and "| 9 | 0 |" in index, "Round 4 index closure count mismatch")
    require("| 5 |" in index and "| 9 | 1 |" in index, "Round 5 index count mismatch")
    require("Round 5 source of truth: `handoff/round_5.json`." in index, "Round 5 index source-of-truth line missing")
    return {"repository_metadata_verified": True}


def validate_v2_policy(data: dict) -> dict:
    validate_round6_quality_boundary(data)
    if data.get("round") == 4:
        return validate_v2_round4_policy(data)
    if data.get("round") == 5:
        return validate_v2_round5_policy(data)
    raise ValidationError(f"unsupported v2 round: {data.get('round')}")


def validate_v2_repository(data: dict, handoff: Path) -> dict:
    if data.get("round") == 4:
        return validate_v2_round4_repository(data, handoff)
    if data.get("round") == 5:
        return validate_v2_round5_repository(data, handoff)
    raise ValidationError(f"unsupported v2 round: {data.get('round')}")


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


def expect_request_failure(
    request: str,
    label: str,
    private_token_hashes: frozenset[str] = REQUEST_PRIVATE_PROJECT_TOKEN_SHA256,
    project_mention_hashes: frozenset[str] = REQUEST_PROJECT_MENTION_SHA256,
    project_mention_count: int = REQUEST_PROJECT_MENTION_COUNT,
    project_mention_manifest_sha256: str = REQUEST_PROJECT_MENTION_MANIFEST_SHA256,
) -> None:
    try:
        validate_round5_request(
            request,
            private_token_hashes,
            project_mention_hashes,
            project_mention_count,
            project_mention_manifest_sha256,
        )
    except ValidationError:
        return
    raise ValidationError(f"negative request selftest did not fail: {label}")


def selftest_v2_round4(data: dict, handoff: Path) -> int:
    validate_v2_round4_policy(data)
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
    changed = copy.deepcopy(data)
    changed["subsequent_resolutions"] = []
    expect_repository_failure(changed, handoff, "Round 4 U10 resolution removal")
    changed = copy.deepcopy(data)
    changed["unverified_claims"][0]["status"] = "closed"
    expect_repository_failure(changed, handoff, "Round 4 carried U01 mutation")
    changed = copy.deepcopy(data)
    next(task for task in changed["tasks"] if task["id"] == "R4-ITERATION")["status"] = "done"
    expect_repository_failure(changed, handoff, "Round 4 iteration overclaim")
    return 19


def selftest_v2_round5(data: dict, handoff: Path) -> int:
    validate_v2_round5_policy(data)
    changed = copy.deepcopy(data)
    changed["tasks"][0]["capability_claim"] = True
    expect_policy_failure(changed, "Round 5 capability escalation")
    changed = copy.deepcopy(data)
    changed["authorization_scope"]["private_data_access"] = True
    expect_policy_failure(changed, "Round 5 private-access escalation")
    changed = copy.deepcopy(data)
    changed["authorization_scope"]["stage_computation_authorized"] = True
    expect_policy_failure(changed, "Round 5 stage-computation escalation")
    changed = copy.deepcopy(data)
    changed["unverified_claims"].pop()
    expect_policy_failure(changed, "Round 5 missing carried claim")
    changed = copy.deepcopy(data)
    changed["unverified_claims"][0]["status"] = "closed"
    expect_repository_failure(changed, handoff, "Round 5 carried claim mutation")
    changed = copy.deepcopy(data)
    next(task for task in changed["tasks"] if task["id"] == "R4-ITERATION")["status"] = "done"
    expect_policy_failure(changed, "Round 5 iteration overclaim")
    changed = copy.deepcopy(data)
    changed["metrics"]["structural_direction"]["headline_allowed"] = True
    expect_policy_failure(changed, "Round 5 structural headline escalation")
    changed = copy.deepcopy(data)
    changed["privacy"]["digest_set_provenance"]["manifest_sha256"] = "sha256:" + "0" * 64
    expect_policy_failure(changed, "Round 5 digest-set provenance drift")
    changed = copy.deepcopy(data)
    changed["deviations"].remove(ROUND5_DIGEST_LIMITATION_DEVIATION)
    expect_policy_failure(changed, "Round 5 digest-set limitation removal")
    changed = copy.deepcopy(data)
    next(item for item in changed["inherited_dispositions"] if item["source_id"] == "R4-U10")["evidence_ids"] = []
    expect_policy_failure(changed, "Round 5 U10 evidence removal")
    changed = copy.deepcopy(data)
    external = next(
        item
        for task in changed["tasks"]
        for item in task.get("evidence", [])
        if item.get("record_type") == "external-audit-attestation"
    )
    external["execution_provenance"] = "builder-session"
    expect_policy_failure(changed, "Round 5 external provenance downgrade")
    changed = copy.deepcopy(data)
    changed["inherited_source"]["sha256"] = "sha256:" + "1" * 64
    expect_repository_failure(changed, handoff, "Round 5 source hash drift")
    changed = copy.deepcopy(data)
    external = next(
        item
        for task in changed["tasks"]
        for item in task.get("evidence", [])
        if item.get("record_type") == "external-audit-attestation"
    )
    external["input_manifest_sha256"] = "sha256:" + "2" * 64
    expect_repository_failure(changed, handoff, "Round 5 audit input drift")
    changed = copy.deepcopy(data)
    changed["taskbook"] = "handoff/INDEX.md"
    expect_repository_failure(changed, handoff, "Round 5 authorization-request mirror removal")
    changed = copy.deepcopy(data)
    request_evidence = next(
        item for task in changed["tasks"] for item in task.get("evidence", []) if item.get("id") == "R5-E002"
    )
    request_evidence["input_manifest_sha256"] = "sha256:" + "3" * 64
    expect_repository_failure(changed, handoff, "Round 5 authorization-request input hash drift")
    request_bytes = (handoff / "R4_2_AUTHORIZATION_REQUEST.md").read_bytes()
    request = canonical_lf_bytes(request_bytes).decode("utf-8")
    request_evidence = next(
        item for task in data["tasks"] for item in task.get("evidence", []) if item.get("id") == "R5-E002"
    )
    crlf_request = canonical_lf_bytes(request_bytes).replace(b"\n", b"\r\n")
    validate_r5_e002_input(request_evidence, crlf_request, request_bytes)
    try:
        validate_r5_e002_input(request_evidence, b"\xef\xbb\xbf" + request_bytes, request_bytes)
    except ValidationError as exc:
        require("UTF-8 BOM" in str(exc), "Round 5 BOM diagnostic is not explicit")
    else:
        raise ValidationError("negative repository selftest did not fail: Round 5 request BOM")
    changed_request = canonical_lf_bytes(request_bytes).replace(
        b"authorized_closure_claims=R4-U01,R4-U02", b"authorized_closure_claims=R4-U01", 1
    )
    try:
        validate_r5_e002_input(request_evidence, changed_request, request_bytes)
    except ValidationError as exc:
        message = str(exc)
        require(
            "expected=sha256:" in message
            and "actual=sha256:" in message
            and re.search(r"first_difference_byte_offset=\d+", message) is not None,
            "Round 5 content-drift diagnostic lacks hashes or byte offset",
        )
    else:
        raise ValidationError("negative repository selftest did not fail: Round 5 request content drift")
    expect_request_failure(request, "Round 5 private identifier digest set missing", frozenset())
    expect_request_failure(
        request,
        "Round 5 project mention digest set missing",
        project_mention_hashes=frozenset(),
    )
    synthetic_project_canary = "SYNTHETIC_PROJECT_MENTION_CANARY"
    synthetic_project_hashes = frozenset(
        {hashlib.sha256(synthetic_project_canary.casefold().encode("utf-8")).hexdigest()}
    )
    synthetic_project_manifest = hashlib.sha256(
        ("\n".join(sorted(synthetic_project_hashes)) + "\n").encode("ascii")
    ).hexdigest()
    expect_request_failure(
        request + "\n" + synthetic_project_canary,
        "Round 5 synthetic project mention match",
        project_mention_hashes=synthetic_project_hashes,
        project_mention_count=1,
        project_mention_manifest_sha256=synthetic_project_manifest,
    )
    expect_request_failure(
        request,
        "Round 5 project mention manifest tamper",
        project_mention_hashes=synthetic_project_hashes,
        project_mention_count=1,
        project_mention_manifest_sha256="0" * 64,
    )
    synthetic_canary = "SYNTHETIC_PRIVATE_CANARY"
    synthetic_hash = frozenset({hashlib.sha256(synthetic_canary.casefold().encode("utf-8")).hexdigest()})
    synthetic_hashes = frozenset(
        set(REQUEST_PRIVATE_PROJECT_TOKEN_SHA256)
        - {next(iter(REQUEST_PRIVATE_PROJECT_TOKEN_SHA256))}
        | {next(iter(synthetic_hash))}
    )
    malformed_hashes = frozenset(
        set(REQUEST_PRIVATE_PROJECT_TOKEN_SHA256)
        - {next(iter(REQUEST_PRIVATE_PROJECT_TOKEN_SHA256))}
        | {"not-a-sha256"}
    )
    for label, bad_hashes in {
        "partial digest set": frozenset(list(REQUEST_PRIVATE_PROJECT_TOKEN_SHA256)[:-1]),
        "replaced digest set": synthetic_hashes,
        "malformed digest set": malformed_hashes,
    }.items():
        expect_request_failure(request, f"Round 5 {label}", bad_hashes)
    for label, injected in {
        "exact private digest match": synthetic_canary,
        "prefixed private digest match": "prefix" + synthetic_canary,
        "suffixed private digest match": synthetic_canary + "-backup",
    }.items():
        require(
            contains_private_identifier_digest([injected], synthetic_hash),
            f"negative request selftest did not fail: Round 5 {label}",
        )
    require(
        contains_private_identifier_digest([request, "other-file:" + synthetic_canary], synthetic_hash),
        "negative request selftest did not fail: Round 5 other-file private digest match",
    )
    try:
        validate_handoff_gitattributes(b"* text=auto eol=crlf\n")
    except ValidationError:
        pass
    else:
        raise ValidationError("negative repository selftest did not fail: handoff .gitattributes drift")
    marker = "authorized_closure_claims=R4-U01,R4-U02"
    expect_request_failure(request.replace(marker, "", 1), "Round 5 authorization marker removal")
    alias = "<PRIVATE_PAPER_ROOT>/.helicon/corpus/extraction_qc.md"
    expect_request_failure(request.replace(alias, "", 1), "Round 5 request alias removal")
    mutations = {
        "u01 verdict weakening": ("u01_verdict_gate", "任一维度 verdict 为 `rejected` 时才不得关闭。"),
        "u02 decision weakening": ("u02_approve_only", "任何 author decision 均可关闭 `R4-U02`。"),
        "u05 review weakening": ("u05_human_review", "| R4-U05 | R4-3 | `private-real-data` | 不可关闭 |"),
        "holdout authorization weakening": ("holdout_future_authorization", "R4-2 可读取 hold-out 并生成 receipt。"),
    }
    for label, (contract, replacement) in mutations.items():
        fragment = ROUND5_EXACT_CONTRACT_FRAGMENTS[contract]
        require(request.count(fragment) == 1, f"request contract multiplicity mismatch: {contract}")
        expect_request_failure(request.replace(fragment, replacement, 1), f"Round 5 {label}")
    return 35


def selftest_round6_quality_boundary() -> int:
    valid = {
        "round": 6,
        "target_semantics": ROUND6_TARGET_SEMANTICS,
        "quality_claim_allowed": False,
        "metrics": {
            "structural_direction": {
                "aggregate_convergence_percent": None,
                "claim_scope": "structural",
            }
        },
    }
    validate_round6_quality_boundary(valid)
    changed = copy.deepcopy(valid)
    changed.pop("target_semantics")
    try:
        validate_round6_quality_boundary(changed)
    except ValidationError:
        pass
    else:
        raise ValidationError("negative selftest did not fail: Round 6 target semantics missing")
    changed = copy.deepcopy(valid)
    changed["quality_claim_allowed"] = True
    try:
        validate_round6_quality_boundary(changed)
    except ValidationError:
        pass
    else:
        raise ValidationError("negative selftest did not fail: Round 6 quality claim enabled")
    changed = copy.deepcopy(valid)
    changed["metrics"]["structural_direction"]["claim_scope"] = "paper-quality-improvement"
    try:
        validate_round6_quality_boundary(changed)
    except ValidationError:
        pass
    else:
        raise ValidationError("negative selftest did not fail: Round 6 quality-implicating convergence scope")
    return 3


def selftest_v2(data: dict, handoff: Path) -> int:
    if data.get("round") == 4:
        return selftest_v2_round4(data, handoff)
    if data.get("round") == 5:
        return selftest_v2_round5(data, handoff)
    raise ValidationError(f"unsupported v2 selftest round: {data.get('round')}")


def repository_root_commit(repo: Path) -> str:
    return git(repo, "rev-list", "--max-parents=0", "HEAD").decode("ascii").strip().splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, choices=(3, 4, 5))
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
            summary.update({"round": data["round"], "schema": data["schema"]})
            results.append(summary)
            if args.selftest:
                selftests += selftest_v2(data, handoff)
        else:
            raise ValidationError(f"unsupported handoff schema: {data.get('schema')}")
    if args.selftest:
        selftests += selftest_round6_quality_boundary()
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
