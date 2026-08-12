#!/usr/bin/env python3
"""Validate the current HElicon handoff bundle without private data."""
from __future__ import annotations

import json
from pathlib import Path


VALID_STATUSES = {"done", "partial", "blocked", "skipped"}
VALID_EVIDENCE = {"self-authored-fixture", "real-data", "independent-session"}
REQUIRED_TOP = {
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


def main() -> int:
    root = Path(__file__).resolve().parent
    data = json.loads((root / "round_3.json").read_text(encoding="utf-8"))
    missing = REQUIRED_TOP - set(data)
    assert not missing, f"missing top-level fields: {sorted(missing)}"
    assert data["round"] == 3
    assert data["status"] in VALID_STATUSES
    repository_state = data["metrics"]["repository_state"]
    assert repository_state["implementation_commit"] == data["head_commit"]
    assert repository_state["snapshot_phase"] == "post-implementation-commit/pre-handoff-commit"
    assert repository_state["tracked_modified_files"] == 0
    assert repository_state["untracked_handoff_files"] == repository_state["handoff_files"] == 5
    assert repository_state["implementation_committed"] is True
    assert repository_state["implementation_pushed"] is True
    assert repository_state["github_origin_clone_verified"] is True
    assert (root.parent / data["taskbook"]).is_file(), "taskbook file missing"
    task_ids = [task["id"] for task in data["tasks"]]
    assert len(task_ids) == len(set(task_ids)), "duplicate task id"
    for task in data["tasks"]:
        assert task["status"] in VALID_STATUSES
        assert task["evidence"], f"task {task['id']} has no evidence"
        assert isinstance(task.get("note"), str) and task["note"].strip()
        for evidence in task["evidence"]:
            assert {"command", "exit_code", "key_output", "evidence_class"} <= set(evidence)
            assert isinstance(evidence["exit_code"], int)
            assert evidence["evidence_class"] in VALID_EVIDENCE
    for item in data["unverified_claims"]:
        assert {"claim", "why_unverified", "how_to_verify"} <= set(item)
    for item in data["deviations"]:
        assert {"what", "why", "impact"} <= set(item)
    for item in data["open_questions"]:
        assert {"question", "options", "recommendation"} <= set(item)
        assert item["options"]
    privacy = data["privacy"]
    assert {"files_read", "private_outputs", "repo_contamination_check"} <= set(privacy)
    assert privacy["files_read"] and privacy["private_outputs"]
    assert {"command", "exit_code"} <= set(privacy["repo_contamination_check"])
    assert isinstance(data["reproduce"], list) and all(
        isinstance(command, str) and command.strip() for command in data["reproduce"]
    )
    assert any(data["head_commit"] in command and "exclude)handoff/**" in command for command in data["reproduce"])
    for item in data["next_round_candidates"]:
        assert {"item", "reason", "priority"} <= set(item)
    report = (root / "ROUND_3_HANDOFF.md").read_text(encoding="utf-8")
    index = (root / "INDEX.md").read_text(encoding="utf-8")
    assert f"Round {data['round']}" in report
    assert f"| Status | `{data['status']}` |" in report
    assert data["branch"] in report
    assert data["head_commit"] in report
    assert data["base_commit"] in report
    task_labels = {
        "2": "Stage 0 / §2",
        "3": "Stage 1 / §3",
        "4": "Stage 2 / §4",
        "5": "Stage 3 / §5",
        "6": "Stage 4 / §6",
        "7": "Stage 5 / §7",
        "8": "Iteration protocol / §8",
    }
    for task in data["tasks"]:
        assert f"| {task_labels[task['id']]} | `{task['status']}` |" in report
    assert f"{len(data['unverified_claims'])} 项" in report
    assert f"{len(data['deviations'])} 项偏差" in report
    open_section = report.split("## Open questions", 1)[1].split("## Privacy", 1)[0]
    assert sum(line.startswith(tuple(f"{n}. " for n in range(1, 10))) for line in open_section.splitlines()) == len(
        data["open_questions"]
    )
    assert str(data["metrics"]["repository_selftests"]) in report
    assert str(data["metrics"]["rule_directional_cases"]["convergence_percent"]) in report
    assert data["metrics"]["structural_direction"]["status"] in report
    assert data["metrics"]["evals_tree"]["sha256"] in report
    assert "评估派生物" in report and "未进入仓库" in report
    assert f"| {data['round']} |" in index
    assert f"| {len(data['unverified_claims'])} | {len(data['open_questions'])} |" in index
    print(
        json.dumps(
            {
                "schema_valid": True,
                "round": data["round"],
                "tasks": len(data["tasks"]),
                "evidence": sum(len(task["evidence"]) for task in data["tasks"]),
                "unverified": len(data["unverified_claims"]),
                "deviations": len(data["deviations"]),
                "open_questions": len(data["open_questions"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
