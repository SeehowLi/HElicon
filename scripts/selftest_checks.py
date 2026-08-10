#!/usr/bin/env python3
"""Run small regression tests for HElicon's repository checks."""
from __future__ import annotations

import tempfile
from pathlib import Path

import check_ai_tells
import check_contract_sync
import check_core_contamination as checker
import style_fingerprint


def scan(root: Path, rel: str, text: str) -> list[str]:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return checker.scan_file(path, root)


def has(findings: list[str], fragment: str) -> bool:
    return any(fragment in finding for finding in findings)


def ai_rules(path: Path, text: str) -> set[int]:
    path.write_text(text, encoding="utf-8")
    return {finding.rule for finding in check_ai_tells.scan(path)}


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

        private_target = scan(root, "references/target_profile.json", "{}")
        tests.append(("private target filename blocked", has(private_target, "private target artifact filename")))

        private_card = scan(root, "references/exemplars/filled.md", "# private exemplar")
        tests.append(("filled exemplar path blocked", has(private_card, "filled exemplar card")))

        hidden_style = scan(root, ".helicon/style/note.md", "private")
        tests.append(("repository .helicon blocked", has(hidden_style, "private .helicon artifact")))

        tests.append(("AI-tell rule 1", 1 in ai_rules(root / "rule1.txt", "This is a groundbreaking method.")))
        for index, keyword in enumerate((
            "significantly",
            "dramatically",
            "practical",
            "scalable",
            "efficient",
            "secure and efficient",
        ), 1):
            tests.append((
                f"AI-tell rule 2 keyword: {keyword}",
                2 in ai_rules(root / f"rule2-keyword-{index}.txt", f"The method is {keyword}."),
            ))
        tests.append((
            "AI-tell rule 2 generic workload is not an exemption",
            2 in ai_rules(root / "rule2-generic.txt", "This practical vector-query design is useful."),
        ))
        rule3_path = root / "rule3.txt"
        rule3_path.write_text("We use full homomorphic encryption.", encoding="utf-8")
        rule3 = check_ai_tells.scan(rule3_path)
        tests.append(("AI-tell rule 3", any(item.rule == 3 and item.severity == "block" for item in rule3)))
        tests.append((
            "AI-tell rule 2 scoped exemption",
            2 not in ai_rules(
                root / "rule2-scoped.txt",
                "The method is efficient. On 32 CPU cores, latency is 12 ms for 1024 vectors.",
            ),
        ))
        tests.append((
            "AI-tell rule 10 measured-clause exemption",
            10 not in ai_rules(
                root / "rule10-measured.txt",
                "Our scheme is significantly faster, reducing latency to 12 ms on one CPU core.",
            ),
        ))
        tests.append((
            "AI-tell rule 10 citation exemption",
            10 not in ai_rules(
                root / "rule10-citation.txt",
                r"The construction reduces setup work, matching the bound in \ref{sec:proof}.",
            ),
        ))
        tests.append((
            "AI-tell rule 10 mechanism exemption",
            10 not in ai_rules(
                root / "rule10-mechanism.txt",
                "The construction reduces communication, reducing transfers by batching adjacent requests.",
            ),
        ))
        tests.append((
            "AI-tell rule 10 hollow clause remains visible",
            10 in ai_rules(
                root / "rule10-hollow.txt",
                "The construction improves the design, highlighting its broad potential.",
            ),
        ))

        polish_text = (Path(__file__).resolve().parent.parent / "references" / "language_polish.md").read_text(encoding="utf-8")
        behavior = check_contract_sync.validate_rule_behaviors(polish_text)
        tests.append(("rule-keyword behavior contract", behavior["passed"]))

        def scanner_without_dramatically(text: str, path: Path) -> list[check_ai_tells.Finding]:
            return [
                finding
                for finding in check_ai_tells.scan_text(text, path)
                if not (finding.rule == 2 and finding.match.lower() == "dramatically")
            ]

        mutation = check_contract_sync.validate_rule_behaviors(polish_text, scanner_without_dramatically)
        tests.append((
            "rule-keyword contract catches injected R02 omission",
            not mutation["passed"]
            and any("R02 `dramatically` positive sample" in error for error in mutation["errors"]),
        ))

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

        titled_versions = []
        for index in range(3):
            version = root / f"same-title-v{index + 1}.md"
            version.write_text(
                f"# One Synthetic Paper\n\nVersion {index + 1} uses deliberately different prose.",
                encoding="utf-8",
            )
            titled_versions.append(version)
        inferred = style_fingerprint.baseline_data(titled_versions)
        tests.append((
            "same-title versions infer one paper",
            inferred["status"] == "thin(n=1)"
            and inferred["drift_alerts_enabled"] is False
            and inferred["grouping"]["summary"] == "grouped: 3 files -> 1 papers",
        ))

        distinct_titles = []
        for index, title in enumerate(("Synthetic Paper Alpha", "Synthetic Paper Beta"), 1):
            version = root / f"distinct-title-{index}.md"
            version.write_text(f"# {title}\n\n## Limitations\n\nA shared section title must not merge different papers.", encoding="utf-8")
            distinct_titles.append(version)
        distinct = style_fingerprint.baseline_data(distinct_titles)
        tests.append((
            "different document titles remain distinct",
            distinct["paper_count"] == 2
            and distinct["grouping"]["summary"] == "grouped: 2 files -> 2 papers",
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
