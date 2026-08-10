#!/usr/bin/env python3
"""Run small regression tests for HElicon's repository checks."""
from __future__ import annotations

import tempfile
from pathlib import Path

import check_core_contamination as checker
import style_fingerprint


def scan(root: Path, rel: str, text: str) -> list[str]:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return checker.scan_file(path, root)


def has(findings: list[str], fragment: str) -> bool:
    return any(fragment in finding for finding in findings)


def main() -> int:
    tests: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="helicon-selftest-") as temp:
        root = Path(temp)
        for index, sample in enumerate(("37%", "0.5%", "1.5x", "12 GB", "20 ms"), 1):
            findings = scan(root, f"references/numeric_{index}.md", sample)
            tests.append((f"numeric {sample}", has(findings, "numeric result-like token")))

        threshold = scan(root, "references/threshold.md", "- threshold: 20 s per pass")
        tests.append(("threshold exemption", not has(threshold, "numeric result-like token")))

        marked = scan(
            root,
            "references/marked.md",
            "Latency is 20 ms. <!-- helicon:allow-numeric -->",
        )
        tests.append(("inline marker exemption", not has(marked, "numeric result-like token")))

        whitelisted = scan(
            root,
            "references/pass_pipeline.md",
            "| metric | target |\n|---|---:|\n| latency | 20 ms |",
        )
        tests.append(("whitelisted numeric table", not has(whitelisted, "numeric result-like token")))

        blocked = scan(root, "references/pass_pipeline.md", "sp27.pdf")
        tests.append(("blocklist still active", has(blocked, "blocked token")))

        project = scan(root, "references/pass_pipeline.md", "NOMOS")
        tests.append(("project check still active", has(project, "project token")))

        eprint = scan(root, "references/pass_pipeline.md", "See 2025/1234")
        tests.append(("ePrint still active", has(eprint, "ePrint-like identifier")))

        versions = []
        for index in range(5):
            version = root / f"paper-a-v{index + 1}.txt"
            version.write_text(f"We present version {index + 1}. The evaluation remains consistent.", encoding="utf-8")
            versions.append(version)
        baseline = style_fingerprint.baseline_data(versions, ["paper-a"])
        tests.append((
            "same-paper versions count once",
            baseline["status"] == "thin(n=1)"
            and baseline["source_file_count"] == 5
            and all(item["sd"] == 0.0 for item in baseline["metric_stats"].values()),
        ))

    failed = [name for name, passed in tests if not passed]
    for name, passed in tests:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if failed:
        print("Self-test failures: " + ", ".join(failed))
        return 1
    print(f"All {len(tests)} repository self-tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
