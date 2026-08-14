#!/usr/bin/env python3
"""Run small regression tests for HElicon's repository checks."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import check_ai_tells
import bootstrap_project_pack
import build_target_profile
import check_contract_sync
import check_core_contamination as checker
import check_claim_strength
import check_command_coverage
import check_immutable_set
import check_live_skill_binding
import check_pass_scope
import check_reference_reachability
import check_terminology_freeze
import check_wiring_integrity
import extract_revision_direction
import latex_guard
import resolve_target_profile
import revision_preflight
import set_project_direction
import target_eval
import style_fingerprint


def scan(
    root: Path,
    rel: str,
    text: str,
    private_token_hashes: frozenset[str] = checker.PRIVATE_PROJECT_TOKEN_SHA256,
    project_mention_hashes: frozenset[str] = checker.PROJECT_MENTION_SHA256,
) -> list[str]:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return checker.scan_file(path, root, private_token_hashes, project_mention_hashes)


def has(findings: list[str], fragment: str) -> bool:
    return any(fragment in finding for finding in findings)


def rejects_digest_config(
    private_token_hashes: frozenset[str],
    expected_count: int = checker.PRIVATE_PROJECT_TOKEN_COUNT,
    expected_manifest_sha256: str = checker.PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256,
) -> bool:
    try:
        checker.validate_private_token_hashes(
            private_token_hashes,
            expected_count,
            expected_manifest_sha256,
        )
    except ValueError:
        return True
    return False


def rejects_project_mention_config(
    project_mention_hashes: frozenset[str],
    expected_count: int = checker.PROJECT_MENTION_COUNT,
    expected_manifest_sha256: str = checker.PROJECT_MENTION_MANIFEST_SHA256,
) -> bool:
    try:
        checker.validate_project_mention_hashes(
            project_mention_hashes,
            expected_count,
            expected_manifest_sha256,
        )
    except ValueError:
        return True
    return False


def ai_rules(path: Path, text: str) -> set[int]:
    path.write_text(text, encoding="utf-8")
    return {finding.rule for finding in check_ai_tells.scan(path)}


def main() -> int:
    tests: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="helicon-selftest-") as temp:
        root = Path(temp)
        synthetic_tokens = ("ZZTESTTOKENALPHA", "ZZTESTPROJECTBETA")
        synthetic_private_hashes = frozenset(
            {hashlib.sha256(synthetic_tokens[0].casefold().encode("utf-8")).hexdigest()}
        )
        synthetic_project_hashes = frozenset(
            {hashlib.sha256(synthetic_tokens[1].casefold().encode("utf-8")).hexdigest()}
        )
        synthetic_hashes = synthetic_private_hashes | synthetic_project_hashes
        correct_round6_contract = root / "round6_contract_ok.py"
        correct_round6_contract.write_text(
            'ROUND6_TARGET_SEMANTICS = "imitation-fidelity-to-author-approved-ai-assisted-target"\n',
            encoding="utf-8",
        )
        tests.append((
            "Round 6 target semantics has an independently hard-coded contract",
            not check_contract_sync.round6_target_semantics_errors(correct_round6_contract),
        ))
        mutated_round6_contract = root / "round6_contract_mutated.py"
        mutated_round6_contract.write_text(
            'ROUND6_TARGET_SEMANTICS = "quality-improvement-validated"\n',
            encoding="utf-8",
        )
        tests.append((
            "Round 6 target semantics mutation fails the contract gate",
            bool(check_contract_sync.round6_target_semantics_errors(mutated_round6_contract)),
        ))

        verifier_root = root / "verifiability"
        verifier_root.mkdir()
        small_glossary = verifier_root / "glossary.json"
        small_glossary.write_text(json.dumps({
            "entries": [{
                "term": "ciphertext scheduler",
                "abbreviation": "CS",
                "forbidden_synonyms": ["encrypted scheduler"],
                "forbidden_variants": ["ciphertext-scheduler"],
            }]
        }), encoding="utf-8")
        math_before = verifier_root / "math_before.txt"
        math_after = verifier_root / "math_after.txt"
        math_before.write_text("A ciphertext scheduler evaluates $x + y$.\n", encoding="utf-8")
        math_after.write_text("The ciphertext scheduler evaluates $x+\n y$.\n", encoding="utf-8")
        immutable_whitespace = check_immutable_set.compare(math_before, math_after, small_glossary)
        tests.append((
            "immutable checker ignores math-only whitespace and line breaks",
            immutable_whitespace["passed"] and immutable_whitespace["total_violations"] == 0,
        ))

        scope_joined = (
            "The synthetic protocol is secure in the semi-honest model, and each ciphertext "
            "carries $N/2$ slots. It records 12.4 ms and 3.2 GB as shown in "
            "\\eqref{eq:synthetic} and \\cite{synthetic}; see \\ref{sec:synthetic}. "
            "We do not claim lower cost. It has higher latency for most database sizes.\n"
        )
        scope_split = scope_joined.replace(
            "semi-honest model, and each ciphertext",
            "semi-honest model. Each ciphertext",
        )
        scope_variants = (
            ("sentence splitting", scope_joined, scope_split),
            ("sentence joining", scope_split, scope_joined),
            (
                "sentence reordering",
                "Each request may finish. Most batches do not fail.\n",
                "Most batches do not fail. Each request may finish.\n",
            ),
            (
                "claim-marker case changes",
                "Each request may finish, but most batches do not fail.\n",
                "EACH request MAY finish, but MOST batches do NOT fail.\n",
            ),
        )
        for index, (label, before_text, after_text) in enumerate(scope_variants, 1):
            scope_before = verifier_root / f"scope_before_{index}.txt"
            scope_after = verifier_root / f"scope_after_{index}.txt"
            scope_before.write_text(before_text, encoding="utf-8")
            scope_after.write_text(after_text, encoding="utf-8")
            scope_result = check_immutable_set.compare(scope_before, scope_after, small_glossary)
            scope_report = scope_result["categories"]["claim_scope"]
            tests.append((
                f"immutable claim-scope multiset ignores {label}",
                scope_report["violation_count"] == 0
                and not scope_report["changed"],
            ))

        scope_before = verifier_root / "scope_violation_before.txt"
        scope_after = verifier_root / "scope_violation_after.txt"
        scope_before.write_text("The scheduler may serve each request.\n", encoding="utf-8")
        scope_after.write_text("The scheduler must serve all requests.\n", encoding="utf-8")
        scope_violation = check_immutable_set.compare(scope_before, scope_after, small_glossary)
        scope_changes = scope_violation["categories"]["claim_scope"]["changed"]
        tests.append((
            "immutable claim-scope multiset retains real changes without identical pairs",
            scope_violation["categories"]["claim_scope"]["violation_count"] > 0
            and all(item["before"] != item["after"] for item in scope_changes),
        ))

        claim_before = verifier_root / "claim_before.txt"
        claim_after = verifier_root / "claim_after.txt"
        claim_before.write_text(
            "The scheduler operates under the fixed workload assumption.\n", encoding="utf-8"
        )
        claim_after.write_text("The scheduler operates.\n", encoding="utf-8")
        qualifier_result = check_claim_strength.compare(claim_before, claim_after)
        tests.append((
            "claim-strength checker rejects scope-qualifier deletion",
            any(item["kind"] == "scope_qualifier_removed" for item in qualifier_result["upward_moves"]),
        ))

        tests.append((
            "cryptographic strength ladder manifest is valid",
            not check_claim_strength.validate_crypto_ladders(),
        ))
        missing_crypto_ladder = dict(check_claim_strength.CRYPTO_LADDERS)
        missing_crypto_ladder.pop("leakage")
        try:
            check_claim_strength.validate_crypto_ladders(missing_crypto_ladder)
            missing_crypto_rejected = False
        except check_claim_strength.UserError:
            missing_crypto_rejected = True
        tests.append((
            "cryptographic strength ladder count drift is rejected",
            missing_crypto_rejected,
        ))
        mutated_crypto_ladder = dict(check_claim_strength.CRYPTO_LADDERS)
        mutated_crypto_ladder["leakage"] = (("bounded leakage",), ("unbounded leakage",))
        try:
            check_claim_strength.validate_crypto_ladders(mutated_crypto_ladder)
            mutated_crypto_rejected = False
        except check_claim_strength.UserError:
            mutated_crypto_rejected = True
        tests.append((
            "cryptographic strength ladder manifest drift is rejected",
            mutated_crypto_rejected,
        ))
        mutated_crypto_anchors = dict(check_claim_strength.CRYPTO_LADDER_ANCHORS)
        mutated_crypto_anchors["exactness"] = mutated_crypto_anchors["exactness"] + ("polynomial",)
        try:
            check_claim_strength.validate_crypto_ladders(anchors=mutated_crypto_anchors)
            mutated_crypto_anchors_rejected = False
        except check_claim_strength.UserError:
            mutated_crypto_anchors_rejected = True
        tests.append((
            "cryptographic strength ladder anchor drift is rejected",
            mutated_crypto_anchors_rejected,
        ))

        anchor_false_positives = (
            (
                "privacy ladder ignores statistical analysis wording",
                "The computational overhead is dominated by rotations. We omit a detailed analysis of the distance distribution.\n",
                "The runtime overhead is dominated by rotations. We provide a statistical analysis of the distance distribution.\n",
            ),
            (
                "exactness ladder ignores polynomial and index wording",
                "We use an approximate polynomial for the sign function. The recovered index is recorded in all trials.\n",
                "We use a Chebyshev polynomial for the sign function. The exact index is recorded in all trials.\n",
            ),
            (
                "adaptivity ladder ignores batching wording",
                "The scheme uses selective batching for the linear layer.\n",
                "The scheme uses adaptive batching for the linear layer.\n",
            ),
            (
                "cryptographic anchor does not cross punctuation",
                "The synthetic label is computational, privacy is discussed separately.\n",
                "The synthetic label is statistical, privacy is discussed separately.\n",
            ),
        )
        for index, (label, before_text, after_text) in enumerate(anchor_false_positives, 1):
            before_path = verifier_root / f"anchor_false_before_{index}.txt"
            after_path = verifier_root / f"anchor_false_after_{index}.txt"
            before_path.write_text(before_text, encoding="utf-8")
            after_path.write_text(after_text, encoding="utf-8")
            result = check_claim_strength.compare(before_path, after_path)
            tests.append((label, result["passed"] and not result["crypto_upward_moves"]))

        unanchored_candidates = (
            (
                "unanchored selective-to-adaptive wording is a nonblocking candidate",
                "We now state the security notion. The definition is selective and the reduction is tight.\n",
                "We now state the security notion. The definition is adaptive and the reduction is tight.\n",
                "security_adaptivity",
            ),
            (
                "unanchored computational-to-statistical guarantee is a nonblocking candidate",
                "Our guarantee is computational. The proof appears in Appendix B.\n",
                "Our guarantee is statistical. The proof appears in Appendix B.\n",
                "privacy_guarantee",
            ),
            (
                "colon-separated selective-to-adaptive wording is a nonblocking candidate",
                "Security model: selective.\n",
                "Security model: adaptive.\n",
                "security_adaptivity",
            ),
            (
                "distant computational-to-statistical wording is a nonblocking candidate",
                "The scheme achieves security that is only computational rather than information-theoretic.\n",
                "The scheme achieves security that is only statistical rather than information-theoretic.\n",
                "privacy_guarantee",
            ),
        )
        for index, (label, before_text, after_text, ladder) in enumerate(unanchored_candidates, 1):
            before_path = verifier_root / f"candidate_before_{index}.txt"
            after_path = verifier_root / f"candidate_after_{index}.txt"
            before_path.write_text(before_text, encoding="utf-8")
            after_path.write_text(after_text, encoding="utf-8")
            result = check_claim_strength.compare(before_path, after_path)
            tests.append((
                label,
                result["passed"]
                and not result["crypto_upward_moves"]
                and len(result["crypto_upward_candidates"]) == 1
                and result["crypto_upward_candidates"][0]["ladder"] == ladder,
            ))

        anchored_upgrades = (
            (
                "anchored adaptive-security upgrade still blocks",
                "The protocol is secure under selective security.\n",
                "The protocol is secure under adaptive security.\n",
                "security_adaptivity",
            ),
            (
                "anchored statistical-privacy upgrade still blocks",
                "The protocol provides computational privacy.\n",
                "The protocol provides statistical privacy.\n",
                "privacy_guarantee",
            ),
            (
                "anchored exact-arithmetic upgrade still blocks",
                "The scheme uses approximate homomorphic arithmetic.\n",
                "The scheme uses exact homomorphic arithmetic.\n",
                "exactness",
            ),
        )
        for index, (label, before_text, after_text, ladder) in enumerate(anchored_upgrades, 1):
            before_path = verifier_root / f"anchor_true_before_{index}.txt"
            after_path = verifier_root / f"anchor_true_after_{index}.txt"
            before_path.write_text(before_text, encoding="utf-8")
            after_path.write_text(after_text, encoding="utf-8")
            result = check_claim_strength.compare(before_path, after_path)
            tests.append((
                label,
                not result["passed"]
                and any(item["ladder"] == ladder for item in result["crypto_upward_moves"]),
            ))

        crypto_low = (
            "Adversary A is semi-honest. Adversary B is honest-but-curious. Security is selective. "
            "Trial A is IND-CPA secure. Trial B is IND-CCA secure. It assumes static corruption. "
            "Guarantee A provides computational privacy. Guarantee B provides statistical privacy. Construction A is somewhat "
            "homomorphic encryption. Construction B is leveled homomorphic encryption. Its result "
            "is approximate. It permits bounded leakage.\n"
        )
        crypto_high = (
            "Adversary A is malicious. Adversary B is malicious. Security is adaptive. Trial A is "
            "IND-CCA secure. Trial B is IND-CCA2 secure. It assumes adaptive corruption. Guarantee "
            "A provides statistical privacy. Guarantee B provides perfect privacy. Construction A is leveled homomorphic "
            "encryption. Construction B is fully homomorphic encryption. Its result is exact. It "
            "permits no leakage.\n"
        )
        crypto_low_path = verifier_root / "crypto_low.txt"
        crypto_high_path = verifier_root / "crypto_high.txt"
        crypto_low_path.write_text(crypto_low, encoding="utf-8")
        crypto_high_path.write_text(crypto_high, encoding="utf-8")
        crypto_up = check_claim_strength.compare(crypto_low_path, crypto_high_path)
        crypto_down = check_claim_strength.compare(crypto_high_path, crypto_low_path)
        crypto_same = check_claim_strength.compare(crypto_low_path, crypto_low_path)
        tests.append((
            "every cryptographic ladder reports an upward move",
            not crypto_up["passed"]
            and len(crypto_up["crypto_upward_moves"]) == 12
            and {item["ladder"] for item in crypto_up["crypto_upward_moves"]}
            == set(check_claim_strength.CRYPTO_LADDERS),
        ))
        tests.append((
            "every cryptographic ladder reports a conservative downward move",
            crypto_down["passed"]
            and len(crypto_down["crypto_downward_moves"]) == 12
            and {item["ladder"] for item in crypto_down["crypto_downward_moves"]}
            == set(check_claim_strength.CRYPTO_LADDERS),
        ))
        tests.append((
            "same-tier cryptographic wording is unchanged",
            crypto_same["passed"]
            and not crypto_same["crypto_upward_moves"]
            and not crypto_same["crypto_downward_moves"]
            and not crypto_same["crypto_relocations"],
        ))

        crypto_relocation_before = verifier_root / "crypto_relocation_before.txt"
        crypto_relocation_after = verifier_root / "crypto_relocation_after.txt"
        crypto_relocation_before.write_text(
            "Protocol A provides computational privacy. Protocol B provides perfect privacy.\n",
            encoding="utf-8",
        )
        crypto_relocation_after.write_text(
            "Protocol A provides perfect privacy. Protocol B provides computational privacy.\n",
            encoding="utf-8",
        )
        crypto_relocation = check_claim_strength.compare(
            crypto_relocation_before, crypto_relocation_after
        )
        tests.append((
            "cryptographic concept relocation warns without blocking",
            crypto_relocation["passed"]
            and len(crypto_relocation["crypto_relocations"]) == 2
            and not crypto_relocation["crypto_upward_moves"],
        ))

        modal_relocation_before = verifier_root / "modal_relocation_before.txt"
        modal_relocation_after = verifier_root / "modal_relocation_after.txt"
        modal_relocation_before.write_text(
            "The bound may hold for all inputs. The reduction holds in the semi-honest model.\n",
            encoding="utf-8",
        )
        modal_relocation_after.write_text(
            "The bound holds for all inputs. The reduction may hold in the semi-honest model.\n",
            encoding="utf-8",
        )
        modal_relocation = check_immutable_set.compare(
            modal_relocation_before, modal_relocation_after, small_glossary
        )
        tests.append((
            "immutable checker reports modal relocation without a violation",
            modal_relocation["total_violations"] == 0
            and modal_relocation["passed"]
            and any(
                item["marker"].startswith("modality:")
                for item in modal_relocation["claim_scope_relocation"]
            ),
        ))

        restored_terms_before = verifier_root / "restored_terms_before.txt"
        restored_terms_after = verifier_root / "restored_terms_after.txt"
        restored_terms_before.write_text(
            "The synthetic configuration fixes the coefficient modulus, evaluation key, and homomorphic multiplication.\n",
            encoding="utf-8",
        )
        restored_terms_after.write_text(
            "The synthetic configuration fixes the coefficient modulus, auxiliary key, and homomorphic multiplication.\n",
            encoding="utf-8",
        )
        restored_term_result = check_immutable_set.compare(
            restored_terms_before,
            restored_terms_after,
            Path(__file__).resolve().parents[1] / "references" / "fhe_lexicon.json",
        )
        tests.append((
            "restored L0 domain term counts remain immutable",
            not restored_term_result["passed"]
            and restored_term_result["categories"]["glossary_terms"]["violation_count"] >= 1,
        ))

        term_before = verifier_root / "term_before.txt"
        term_after = verifier_root / "term_after.txt"
        term_before.write_text("The ciphertext scheduler runs.\n", encoding="utf-8")
        term_after.write_text("A Ciphertext scheduler runs.\n", encoding="utf-8")
        terminology_result = check_terminology_freeze.compare(term_before, term_after, small_glossary)
        tests.append((
            "terminology checker rejects case drift",
            terminology_result["active_rule_count"] == 2
            and any(item["kind"] == "case_inconsistency" for item in terminology_result["replacements"]),
        ))

        capitalization_glossary = verifier_root / "capitalization_glossary.json"
        capitalization_glossary.write_text(json.dumps({
            "entries": [
                {
                    "term": "ciphertext",
                    "abbreviation": None,
                    "forbidden_synonyms": [],
                    "forbidden_variants": ["cipher text"],
                },
                {
                    "term": "ciphertext packing",
                    "abbreviation": None,
                    "forbidden_synonyms": [],
                    "forbidden_variants": ["ciphertext-packing"],
                },
                {
                    "term": "ring dimension",
                    "abbreviation": None,
                    "forbidden_synonyms": [],
                    "forbidden_variants": ["ring-dimension"],
                },
            ]
        }), encoding="utf-8")
        capitalization_before = verifier_root / "capitalization_before.txt"
        capitalization_before.write_text(
            "The scheme is instantiated with a fixed ring dimension, and ciphertext packing matters.\n",
            encoding="utf-8",
        )
        capitalization_cases = (
            (
                "terminology checker permits sentence-initial capitalization after splitting",
                "The scheme is instantiated with a fixed ring dimension. Ciphertext packing matters.\n",
                0,
            ),
            (
                "terminology checker rejects mid-sentence capitalization",
                "The scheme is instantiated with a fixed ring dimension, and Ciphertext packing matters.\n",
                2,
            ),
            (
                "terminology checker rejects all-uppercase terms",
                "The scheme is instantiated with a fixed RING DIMENSION, and ciphertext packing matters.\n",
                1,
            ),
            (
                "terminology checker rejects camel-case terms",
                "The scheme is instantiated with a fixed ring dimension, and CipherText matters.\n",
                1,
            ),
        )
        for index, (label, after_text, expected_count) in enumerate(capitalization_cases, 1):
            capitalization_after = verifier_root / f"capitalization_after_{index}.txt"
            capitalization_after.write_text(after_text, encoding="utf-8")
            result = check_terminology_freeze.compare(
                capitalization_before, capitalization_after, capitalization_glossary
            )
            tests.append((
                label,
                result["replacement_count"] == expected_count
                and all(item["kind"] == "case_inconsistency" for item in result["replacements"]),
            ))

        latex_glossary = verifier_root / "latex_terminology_glossary.json"
        latex_glossary.write_text(json.dumps({
            "entries": [{
                "term": "ciphertext",
                "abbreviation": "CT",
                "forbidden_synonyms": ["encrypted payload"],
                "forbidden_variants": ["cipher-text"],
            }]
        }), encoding="utf-8")
        latex_before = verifier_root / "latex_before.tex"
        latex_text = (
            "The ciphertext scheduler remains stable. An existing CipherText form remains unchanged.\n"
            "\\SafeCommand{value}\\label{sec:safe-anchor} See \\ref{sec:safe-anchor}, "
            "\\eqref{sec:safe-anchor}, \\autoref{sec:safe-anchor}, \\Cref{sec:safe-anchor}, "
            "and \\citep{sec:safe-anchor}.\n"
            "The symbolic checks are $u + v$ and \\[u = v\\].\n"
            "\\begin{equation}u=v\\end{equation}\n"
            "\\begin{align}u&=v\\end{align}\n"
            "\\begin{gather}u=v\\end{gather}\n"
        )
        latex_before.write_text(latex_text, encoding="utf-8")

        identical = check_terminology_freeze.compare(latex_before, latex_before, latex_glossary)
        identical_counts = {
            kind: sum(item["kind"] == kind for item in identical["replacements"])
            for kind in (
                "forbidden_synonym", "plural_or_hyphen_variant",
                "case_inconsistency", "abbreviation_full_name_mix",
            )
        }
        tests.append((
            "terminology zero-diff reports zero findings for every replacement kind",
            identical["passed"] and identical["replacement_count"] == 0
            and set(identical_counts.values()) == {0},
        ))
        tests.append((
            "pre-existing case form with unchanged count is not re-reported",
            identical_counts["case_inconsistency"] == 0,
        ))

        latex_mutations = (
            (
                "LaTeX command names are excluded from terminology matching",
                latex_text.replace("\\SafeCommand", "\\Ciphertext"),
            ),
            (
                "LaTeX label and reference keys are excluded from terminology matching",
                latex_text.replace(
                    "sec:safe-anchor",
                    "sec:Ciphertext,encrypted payload,cipher-text,CT",
                ),
            ),
            (
                "inline math is excluded from all terminology kinds",
                latex_text.replace("$u + v$", "$Ciphertext + encrypted payload + cipher-text + CT$"),
            ),
            (
                "display math and equation-like environments are excluded from terminology matching",
                latex_text.replace("\\[u = v\\]", "\\[Ciphertext + encrypted payload + cipher-text + CT\\]")
                .replace("u=v\\end{equation}", "Ciphertext + encrypted payload + cipher-text + CT\\end{equation}")
                .replace("u&=v\\end{align}", "Ciphertext + encrypted payload + cipher-text + CT\\end{align}")
                .replace("u=v\\end{gather}", "Ciphertext + encrypted payload + cipher-text + CT\\end{gather}"),
            ),
        )
        for index, (label, after_text) in enumerate(latex_mutations, 1):
            latex_after = verifier_root / f"latex_masked_after_{index}.tex"
            latex_after.write_text(after_text, encoding="utf-8")
            masked_result = check_terminology_freeze.compare(
                latex_before, latex_after, latex_glossary
            )
            tests.append((label, masked_result["replacement_count"] == 0))

        differential_cases = (
            (
                "new mid-sentence case form is reported differentially",
                latex_text.replace("The ciphertext scheduler", "The Ciphertext scheduler"),
                "case_inconsistency",
                1,
            ),
            (
                "sentence-initial capitalization exemption remains active",
                latex_text.replace(
                    "The ciphertext scheduler remains stable.",
                    "The scheduler remains stable. Ciphertext processing follows.",
                ),
                "case_inconsistency",
                0,
            ),
            (
                "forbidden synonym remains an added-match violation",
                latex_text.replace("The ciphertext scheduler", "The encrypted payload scheduler"),
                "forbidden_synonym",
                1,
            ),
        )
        for index, (label, after_text, kind, expected_count) in enumerate(differential_cases, 1):
            latex_after = verifier_root / f"latex_differential_after_{index}.tex"
            latex_after.write_text(after_text, encoding="utf-8")
            result = check_terminology_freeze.compare(latex_before, latex_after, latex_glossary)
            observed_count = sum(item["kind"] == kind for item in result["replacements"])
            tests.append((
                label,
                observed_count == expected_count
                and result["replacement_count"] == expected_count,
            ))

        terminology_script = Path(__file__).resolve().parent / "check_terminology_freeze.py"
        invalid_glossaries = (
            (
                "misspelled terminology rule field is a configuration error",
                {"entries": [{"term": "ciphertext scheduler", "forbidden_synonnyms": ["encrypted scheduler"]}]},
            ),
            (
                "empty avoid list is a terminology configuration error",
                {"entries": [{"term": "ciphertext scheduler", "avoid": []}]},
            ),
        )
        for index, (label, payload) in enumerate(invalid_glossaries, 1):
            invalid_glossary = verifier_root / f"invalid_glossary_{index}.json"
            invalid_glossary.write_text(json.dumps(payload), encoding="utf-8")
            invalid_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(terminology_script),
                    str(term_before),
                    str(term_after),
                    "--glossary",
                    str(invalid_glossary),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            tests.append((label, invalid_result.returncode == 2))

        pass_glossary = verifier_root / "pass_scope_glossary.json"
        pass_glossary.write_text(json.dumps({
            "entries": [{
                "term": "ciphertext",
                "abbreviation": None,
                "forbidden_synonyms": ["encrypted payload"],
                "forbidden_variants": ["cipher-text"],
            }]
        }), encoding="utf-8")

        def pass_scope_result(label: str, pass_name: str, before_text: str, after_text: str) -> dict:
            before_path = verifier_root / f"pass_scope_{label}_before.txt"
            after_path = verifier_root / f"pass_scope_{label}_after.txt"
            before_path.write_text(before_text, encoding="utf-8")
            after_path.write_text(after_text, encoding="utf-8")
            return check_pass_scope.evaluate(pass_name, before_path, after_path, pass_glossary)

        p3_fix = pass_scope_result(
            "p3_fix", "P3",
            "The encrypted payload contains $x+1$.",
            "The ciphertext contains $x+1$.",
        )
        tests.append((
            "P3 exempts only glossary-term count changes after a complete terminology repair",
            p3_fix["verdict"] == "proceed"
            and p3_fix["immutable_exit_code"] == 0
            and p3_fix["immutable_raw_exit_code"] == 1
            and p3_fix["exempted_category_counts"] == {"glossary_terms": 1}
            and p3_fix["terminology_forward_check"]["passed"]
            and p3_fix["terminology_residual_check"]["passed"],
        ))
        p3_math = pass_scope_result(
            "p3_math", "P3",
            "The encrypted payload contains $x+1$.",
            "The ciphertext contains $x+2$.",
        )
        tests.append((
            "P3 still rolls back a math change outside its authorized terminology domain",
            p3_math["verdict"] == "rollback" and "math" in p3_math["blocking_categories"],
        ))
        p3_forward = pass_scope_result(
            "p3_forward", "P3",
            "The ciphertext remains stable.",
            "The encrypted payload remains stable.",
        )
        tests.append((
            "P3 rolls back a newly introduced forbidden form",
            p3_forward["verdict"] == "rollback"
            and not p3_forward["terminology_forward_check"]["passed"],
        ))
        p3_residual = pass_scope_result(
            "p3_residual", "P3",
            "The encrypted payload remains stable.",
            "The encrypted payload remains stable.",
        )
        tests.append((
            "P3 rolls back an unchanged forbidden form left in AFTER",
            p3_residual["verdict"] == "rollback"
            and p3_residual["terminology_forward_check"]["passed"]
            and not p3_residual["terminology_residual_check"]["passed"],
        ))
        p5_terms = pass_scope_result(
            "p5_terms", "P5",
            "The ciphertext remains stable.",
            "The encrypted payload remains stable.",
        )
        tests.append((
            "P5 retains glossary_terms as an immutable blocking category",
            p5_terms["verdict"] == "rollback"
            and p5_terms["p3_glossary_exemption"] == "not-applicable"
            and "glossary_terms" in p5_terms["blocking_categories"],
        ))

        graph_root = verifier_root / "graph"
        (graph_root / "references").mkdir(parents=True)
        (graph_root / "templates").mkdir()
        (graph_root / "SKILL.md").write_text(
            "references/command_registry.md references/intent_router.md references/pass_pipeline.md templates/linked.md\n",
            encoding="utf-8",
        )
        for name in ("command_registry.md", "intent_router.md", "pass_pipeline.md"):
            (graph_root / "references" / name).write_text("templates/linked.md\n", encoding="utf-8")
        (graph_root / "templates" / "linked.md").write_text("linked\n", encoding="utf-8")
        reachable_result = check_reference_reachability.analyze(graph_root)
        tests.append((
            "reference reachability accepts a fully reachable synthetic graph",
            reachable_result["orphan_file_count"] == 0,
        ))
        graph_crlf_root = verifier_root / "graph_crlf"
        for relative in (
            "SKILL.md",
            "references/command_registry.md",
            "references/intent_router.md",
            "references/pass_pipeline.md",
            "templates/linked.md",
        ):
            source = graph_root / relative
            target = graph_crlf_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            canonical = source.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            target.write_bytes(canonical.replace("\n", "\r\n").encode("utf-8"))
        reachable_crlf = check_reference_reachability.analyze(graph_crlf_root)
        tests.append((
            "reference reachability canonicalizes LF and CRLF byte totals",
            reachable_result["total_bytes"] == reachable_crlf["total_bytes"],
        ))
        (graph_root / "templates" / "orphan.md").write_text("orphan\n", encoding="utf-8")
        orphan_result = check_reference_reachability.analyze(graph_root)
        tests.append((
            "reference reachability reports a synthetic orphan",
            orphan_result["orphan_file_count"] == 1
            and orphan_result["orphan_files"][0]["path"] == "templates/orphan.md",
        ))

        command_root = verifier_root / "commands"
        (command_root / "references").mkdir(parents=True)
        (command_root / "evals" / "cases").mkdir(parents=True)
        (command_root / "SKILL.md").write_text("H-TEST\n", encoding="utf-8")
        (command_root / "references" / "command_registry.md").write_text("H-TEST\n", encoding="utf-8")
        router_path = command_root / "references" / "intent_router.md"
        router_path.write_text("H-TEST\n", encoding="utf-8")
        (command_root / "evals" / "cases" / "case.json").write_text(
            json.dumps({"command": "H-TEST"}), encoding="utf-8"
        )
        covered_commands = check_command_coverage.analyze(command_root)
        tests.append((
            "command coverage accepts a four-column synthetic contract",
            covered_commands["command_count"] == 1 and covered_commands["gap_count"] == 0,
        ))
        router_path.write_text("no command\n", encoding="utf-8")
        command_gap = check_command_coverage.analyze(command_root)
        tests.append((
            "command coverage reports a missing router contract",
            command_gap["gap_count"] == 1
            and command_gap["gaps"][0]["missing"] == ["intent_router.md"],
        ))
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

        blocked = scan(
            root,
            "references/pass_pipeline.md",
            synthetic_tokens[0],
            synthetic_private_hashes,
            frozenset(),
        )
        tests.append(("private digest scan active", has(blocked, "private identifier digest match")))

        project = scan(
            root,
            "references/pass_pipeline.md",
            synthetic_tokens[1],
            frozenset(),
            synthetic_project_hashes,
        )
        tests.append(("project digest scan active", has(project, "project mention digest match")))
        project_case_variant = scan(
            root,
            "references/project_case_variant.md",
            synthetic_tokens[1].swapcase(),
            frozenset(),
            synthetic_project_hashes,
        )
        tests.append((
            "project mention digest scan is case folded",
            has(project_case_variant, "project mention digest match"),
        ))

        eprint = scan(root, "references/pass_pipeline.md", "See 2025/1234")
        tests.append(("ePrint still active", has(eprint, "ePrint-like identifier")))

        eval_blocked = scan(root, "evals/fixtures/private.txt", synthetic_tokens[0], synthetic_hashes)
        tests.append(("eval txt digest scan active", has(eval_blocked, "private identifier digest match")))

        eval_project = scan(
            root,
            "evals/cases/private.py",
            f"PROJECT = '{synthetic_tokens[1]}'",
            synthetic_hashes,
        )
        tests.append(("eval py digest scan active", has(eval_project, "private identifier digest match")))

        eval_eprint = scan(root, "evals/run_private.py", "SOURCE = '2025/1234'")
        tests.append(("eval py ePrint active", has(eval_eprint, "ePrint-like identifier")))

        script_fixture = scan(
            root,
            "scripts/selftest_fixture.py",
            f"VALUE = '{synthetic_tokens[0]}'",
            synthetic_hashes,
        )
        tests.append((
            "scripts are scanned for private identifier digests",
            has(script_fixture, "private identifier digest match"),
        ))

        tests.append((
            "private digest count mismatch is rejected",
            rejects_digest_config(
                checker.PRIVATE_PROJECT_TOKEN_SHA256,
                checker.PRIVATE_PROJECT_TOKEN_COUNT + 1,
            ),
        ))
        tests.append((
            "private digest manifest mismatch is rejected",
            rejects_digest_config(
                checker.PRIVATE_PROJECT_TOKEN_SHA256,
                expected_manifest_sha256="0" * 64,
            ),
        ))
        tests.append((
            "private digest deletion is rejected",
            rejects_digest_config(
                frozenset(list(checker.PRIVATE_PROJECT_TOKEN_SHA256)[:-1]),
            ),
        ))
        tests.append((
            "project mention digest count mismatch is rejected",
            rejects_project_mention_config(
                checker.PROJECT_MENTION_SHA256,
                checker.PROJECT_MENTION_COUNT + 1,
            ),
        ))
        tests.append((
            "project mention digest manifest mismatch is rejected",
            rejects_project_mention_config(
                checker.PROJECT_MENTION_SHA256,
                expected_manifest_sha256="0" * 64,
            ),
        ))
        tests.append((
            "project mention digest deletion is rejected",
            rejects_project_mention_config(frozenset()),
        ))

        contract_core = root / "contract-core.py"
        contract_handoff = root / "contract-handoff.py"
        contract_core.write_text(
            "PRIVATE_PROJECT_TOKEN_SHA256=frozenset({'" + "a" * 64 + "'})\n"
            "PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256='private-manifest'\n"
            "PROJECT_MENTION_SHA256=frozenset({'" + "b" * 64 + "'})\n"
            "PROJECT_MENTION_COUNT=1\n"
            "PROJECT_MENTION_MANIFEST_SHA256='mention-manifest'\n",
            encoding="utf-8",
        )
        contract_handoff.write_text(
            "REQUEST_PRIVATE_PROJECT_TOKEN_SHA256=frozenset({'" + "a" * 64 + "'})\n"
            "REQUEST_PRIVATE_PROJECT_TOKEN_MANIFEST_SHA256='private-manifest'\n"
            "REQUEST_PROJECT_MENTION_SHA256=frozenset({'" + "b" * 64 + "'})\n"
            "REQUEST_PROJECT_MENTION_COUNT=1\n"
            "REQUEST_PROJECT_MENTION_MANIFEST_SHA256='mention-manifest'\n",
            encoding="utf-8",
        )
        tests.append((
            "digest synchronization accepts matching synthetic contracts",
            not check_contract_sync.digest_sync_errors(contract_core, contract_handoff),
        ))
        contract_handoff.write_text(
            contract_handoff.read_text(encoding="utf-8").replace("b" * 64, "c" * 64),
            encoding="utf-8",
        )
        tests.append((
            "digest synchronization rejects project mention set drift",
            has(
                check_contract_sync.digest_sync_errors(contract_core, contract_handoff),
                "project mention digest sets differ",
            ),
        ))
        contract_handoff.write_text(
            contract_handoff.read_text(encoding="utf-8")
            .replace("c" * 64, "b" * 64)
            .replace("mention-manifest", "changed-manifest"),
            encoding="utf-8",
        )
        tests.append((
            "digest synchronization rejects project mention manifest drift",
            has(
                check_contract_sync.digest_sync_errors(contract_core, contract_handoff),
                "project mention digest manifests differ",
            ),
        ))

        case_variant = scan(
            root,
            "references/case_variant.md",
            synthetic_tokens[0].swapcase(),
            synthetic_hashes,
        )
        tests.append((
            "private digest scan is case folded",
            has(case_variant, "private identifier digest match"),
        ))

        excluded_suffix = scan(
            root,
            "notes/private.txt",
            synthetic_tokens[1],
            synthetic_hashes,
        )
        tests.append((
            "private digest scan covers suffix-filtered text",
            has(excluded_suffix, "private identifier digest match"),
        ))

        undecodable = root / "scripts" / "undecodable.py"
        undecodable.write_bytes(b"\xff\xfe\x00")
        undecodable_findings = checker.scan_file(undecodable, root)
        tests.append((
            "invalid UTF-8 is reported as unscannable",
            has(undecodable_findings, "unscannable file"),
        ))
        with tempfile.TemporaryDirectory(prefix="helicon-invalid-utf8-") as invalid_temp:
            invalid_root = Path(invalid_temp)
            (invalid_root / "bad.txt").write_bytes(b"\xff\xfe\x00")
            invalid_cli = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).parent / "check_core_contamination.py"), str(invalid_root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        tests.append((
            "invalid UTF-8 makes the contamination CLI fail closed",
            invalid_cli.returncode != 0 and "unscannable file" in invalid_cli.stdout,
        ))

        binding_cli = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).parent / "check_live_skill_binding.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        tests.append((
            "live-skill binding defaults to not-executed",
            binding_cli.returncode == 0
            and json.loads(binding_cli.stdout) == {"status": "not-executed"},
        ))
        binding_source = root / "binding-source"
        binding_installed = root / "binding-installed"
        binding_source.mkdir()
        binding_installed.mkdir()
        (binding_source / "sample.txt").write_bytes(b"alpha\nbeta\n")
        (binding_installed / "sample.txt").write_bytes(b"alpha\r\nbeta\r\n")
        binding_match = check_live_skill_binding.compare(binding_source, binding_installed)
        tests.append((
            "live-skill binding canonicalizes UTF-8 line endings",
            binding_match["source_manifest_sha256"] == binding_match["installed_manifest_sha256"]
            and not binding_match["source_only"]
            and not binding_match["installed_only"],
        ))
        (binding_installed / "sample.txt").write_text("changed\n", encoding="utf-8")
        binding_drift = check_live_skill_binding.compare(binding_source, binding_installed)
        tests.append((
            "live-skill binding detects content tampering",
            binding_drift["source_manifest_sha256"] != binding_drift["installed_manifest_sha256"],
        ))
        (binding_installed / "extra.txt").write_text("extra\n", encoding="utf-8")
        binding_extra = check_live_skill_binding.compare(binding_source, binding_installed)
        tests.append((
            "live-skill binding reports installed-only paths",
            binding_extra["installed_only"] == ["extra.txt"],
        ))
        binding_tamper_cli = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(__file__).parent / "check_live_skill_binding.py"),
                str(binding_installed),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        tests.append((
            "live-skill binding CLI exits nonzero on tampering",
            binding_tamper_cli.returncode != 0
            and set(json.loads(binding_tamper_cli.stdout))
            == {
                "source_manifest_sha256",
                "installed_manifest_sha256",
                "source_file_count",
                "installed_file_count",
                "source_only",
                "installed_only",
            },
        ))

        private_target = scan(root, "references/target_profile.json", "{}")
        tests.append(("private target filename blocked", has(private_target, "private target artifact filename")))

        private_card = scan(root, "references/exemplars/filled.md", "# private exemplar")
        tests.append(("filled exemplar path blocked", has(private_card, "filled exemplar card")))

        hidden_style = scan(root, ".helicon/style/note.md", "private")
        tests.append(("repository .helicon blocked", has(hidden_style, "private .helicon artifact")))

        scripts_dir = Path(__file__).resolve().parent
        repository_root = scripts_dir.parent
        wiring_current = check_wiring_integrity.validate(repository_root)
        tests.append((
            "mandatory pass wiring matches every fixed source anchor",
            wiring_current["passed"]
            and wiring_current["anchor_count"] == check_wiring_integrity.WIRING_ANCHOR_COUNT,
        ))
        wiring_config_mutations = {
            "count": dict(list(check_wiring_integrity.WIRING_ANCHOR_SHA256.items())[:-1]),
            "format": {
                **check_wiring_integrity.WIRING_ANCHOR_SHA256,
                "contract_heading": "not-a-sha256",
            },
            "manifest": dict(check_wiring_integrity.WIRING_ANCHOR_SHA256),
        }
        for label, values in wiring_config_mutations.items():
            rejected = False
            try:
                check_wiring_integrity.validate_anchor_config(
                    values,
                    check_wiring_integrity.WIRING_ANCHOR_COUNT,
                    "0" * 64 if label == "manifest" else check_wiring_integrity.WIRING_ANCHOR_MANIFEST_SHA256,
                )
            except check_wiring_integrity.WiringError:
                rejected = True
            tests.append((f"wiring anchor {label} drift fails closed", rejected))

        skill_wiring_text = (repository_root / "SKILL.md").read_text(encoding="utf-8")
        pipeline_wiring_text = (repository_root / "references/pass_pipeline.md").read_text(encoding="utf-8")
        for anchor_name, relative, fragments in check_wiring_integrity.ANCHOR_SELECTORS:
            original = skill_wiring_text if relative == "SKILL.md" else pipeline_wiring_text
            lines = original.splitlines(keepends=True)
            indexes = [
                index for index, line in enumerate(lines)
                if all(fragment in line for fragment in fragments)
            ]
            tests.append((f"wiring fixture uniquely locates {anchor_name}", len(indexes) == 1))
            if len(indexes) != 1:
                continue
            index = indexes[0]
            deleted = "".join(lines[:index] + lines[index + 1:])
            softened_lines = lines.copy()
            softened_lines[index] = "Optionally consider " + softened_lines[index]
            softened = "".join(softened_lines)
            for mutation, changed in (("deletion", deleted), ("soft wording", softened)):
                try:
                    result = check_wiring_integrity.validate_texts(
                        changed if relative == "SKILL.md" else skill_wiring_text,
                        changed if relative != "SKILL.md" else pipeline_wiring_text,
                    )
                    rejected = not result["passed"]
                except check_wiring_integrity.WiringError:
                    rejected = True
                tests.append((
                    f"{anchor_name} {mutation} fails wiring integrity",
                    rejected,
                ))
        exclusion_source = (scripts_dir / "check_live_skill_binding.py").read_text(encoding="utf-8")
        parsed_source_exclusions = check_live_skill_binding.parse_python_exclusions(exclusion_source)
        install_ps1 = (scripts_dir / "install.ps1").read_text(encoding="utf-8")
        install_sh = (scripts_dir / "install.sh").read_text(encoding="utf-8")
        installer_exclusions = check_live_skill_binding.validate_installer_exclusions(
            install_ps1, install_sh, parsed_source_exclusions
        )
        tests.append((
            "PowerShell installer exclusions match the shared payload contract",
            installer_exclusions["powershell"]
            == frozenset(check_live_skill_binding.SOURCE_EXCLUSIONS),
        ))
        tests.append((
            "shell installer exclusions match the shared payload contract",
            installer_exclusions["shell"]
            == frozenset(check_live_skill_binding.SOURCE_EXCLUSIONS),
        ))
        tests.append((
            "installers remove nested Python bytecode",
            '-Filter "__pycache__"' in install_ps1
            and '-Filter "*.pyc"' in install_ps1
            and "-name '__pycache__'" in install_sh
            and "-name '*.pyc'" in install_sh,
        ))
        exclusion_mutations = {
            "PowerShell": (
                install_ps1.replace('"handoff"', '"handoff-mutated"', 1),
                install_sh,
                check_live_skill_binding.SOURCE_EXCLUSIONS,
            ),
            "shell": (
                install_ps1,
                install_sh.replace("|handoff)", "|handoff-mutated)", 1),
                check_live_skill_binding.SOURCE_EXCLUSIONS,
            ),
            "shared source": (
                install_ps1,
                install_sh,
                check_live_skill_binding.parse_python_exclusions(
                    exclusion_source.replace(', "handoff"', "", 1)
                ),
            ),
        }
        for label, values in exclusion_mutations.items():
            rejected = False
            try:
                check_live_skill_binding.validate_installer_exclusions(*values)
            except ValueError:
                rejected = True
            tests.append((f"{label} exclusion drift fails closed", rejected))

        integrity_script = scripts_dir / "check_skill_integrity.py"
        simulated_payload = root / "simulated-installed-payload"
        check_live_skill_binding.copy_source_payload(repository_root, simulated_payload)
        installed_integrity = subprocess.run(
            [sys.executable, "-B", str(integrity_script), str(simulated_payload), "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        installed_payload = json.loads(installed_integrity.stdout)
        tests.append((
            "simulated installed payload passes integrity in installed mode",
            installed_integrity.returncode == 0
            and installed_payload.get("payload_mode") == "installed"
            and installed_payload.get("contract_sync", {}).get("handoff_digest_sync")
            == "skipped-installed-payload",
        ))
        tests.append((
            "simulated installed payload excludes repository-only roots and bytecode",
            all(not (simulated_payload / name).exists() for name in check_live_skill_binding.SOURCE_EXCLUSIONS)
            and not any(simulated_payload.rglob("__pycache__"))
            and not any(simulated_payload.rglob("*.pyc")),
        ))
        installed_wiring = subprocess.run(
            [sys.executable, "-B", str(scripts_dir / "check_wiring_integrity.py"), str(simulated_payload)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tests.append((
            "simulated installed payload passes mandatory wiring integrity",
            installed_wiring.returncode == 0
            and json.loads(installed_wiring.stdout).get("passed") is True,
        ))

        source_integrity = subprocess.run(
            [sys.executable, "-B", str(integrity_script), str(repository_root), "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        source_payload = json.loads(source_integrity.stdout)
        tests.append((
            "source repository enforces handoff digest synchronization",
            source_integrity.returncode == 0
            and source_payload.get("payload_mode") == "source"
            and source_payload.get("contract_sync", {}).get("handoff_digest_sync") == "enforced",
        ))

        tampered_source = root / "tampered-source-payload"
        check_live_skill_binding.copy_source_payload(repository_root, tampered_source)
        (tampered_source / "handoff").mkdir()
        tampered_integrity = subprocess.run(
            [sys.executable, "-B", str(integrity_script), str(tampered_source), "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tests.append((
            "source-shaped payload without handoff validator fails closed",
            tampered_integrity.returncode != 0
            and json.loads(tampered_integrity.stdout).get("payload_mode") == "source",
        ))
        tampered_validator = tampered_source / "handoff" / "validate.py"
        tampered_validator.write_bytes(b"\xff\xfe")
        non_utf8_integrity = subprocess.run(
            [sys.executable, "-B", str(integrity_script), str(tampered_source), "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tests.append((
            "source-shaped payload with non-UTF-8 handoff validator fails closed",
            non_utf8_integrity.returncode != 0,
        ))
        tampered_validator.unlink()
        tampered_validator.mkdir()
        unreadable_integrity = subprocess.run(
            [sys.executable, "-B", str(integrity_script), str(tampered_source), "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tests.append((
            "source-shaped payload with unreadable handoff validator fails closed",
            unreadable_integrity.returncode != 0,
        ))

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

        private_stages = root / ".helicon" / "corpus" / "stages"
        private_stages.mkdir(parents=True)
        stage1 = private_stages / "v1.txt"
        stage2 = private_stages / "v2.txt"
        stage1.write_text("# Introduction\n\nHeld paragraph.\n\nKept paragraph one.\n\n# Evaluation\n\nKept evaluation one.", encoding="utf-8")
        stage2.write_text("# Introduction\n\nHeld paragraph revised.\n\nKept paragraph two.\n\n# Evaluation\n\nKept evaluation two.", encoding="utf-8")
        discovered = style_fingerprint.input_files([str(private_stages)])
        tests.append(("explicit private corpus directory is readable", discovered == [stage1.resolve(), stage2.resolve()]))
        txt_sections = style_fingerprint.raw_sections(stage1.read_text(encoding="utf-8"), ".txt")
        tests.append(("txt Markdown headings preserve sections", [title for title, _ in txt_sections] == ["Introduction", "Evaluation"]))
        holdouts = extract_revision_direction.parse_holdouts(["1:1", "2:1"])
        direction = extract_revision_direction.analyze(private_stages, "synthetic", set(), {(1, 2)}, holdouts)
        tests.append((
            "direction excludes declared hold-outs",
            direction["holdout_paragraphs_by_stage"] == {"1": [1], "2": [1]},
        ))

        unnumbered_stages = root / "unnumbered-stages"
        unnumbered_stages.mkdir()
        unnumbered_files = []
        for name, qualifier in (("alpha.txt", "initial"), ("middle.txt", "revised"), ("target.txt", "final")):
            path = unnumbered_stages / name
            path.write_text(
                f"# Introduction\n\nThe {qualifier} first paragraph states the scope. It has support.\n\n"
                f"The {qualifier} second paragraph states the evidence. It has support.",
                encoding="utf-8",
            )
            unnumbered_files.append(path)

        def run_target_builder(direction_path: Path, *extra: str) -> tuple[int, dict[str, object]]:
            process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(build_target_profile.__file__).resolve()),
                    str(unnumbered_stages),
                    "--target-file",
                    str(unnumbered_files[2]),
                    "--paper-id",
                    "synthetic",
                    "--venue",
                    "Synthetic Venue",
                    "--author-advisor-pair",
                    "1:2",
                    "--review-driven-pair",
                    "2:3",
                    "--direction-input",
                    str(direction_path),
                    "--json",
                    *extra,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            try:
                payload = json.loads(process.stdout)
            except json.JSONDecodeError:
                payload = {}
            return process.returncode, payload

        positioned_direction = extract_revision_direction.analyze(
            unnumbered_stages, "synthetic", {(2, 3)}, {(1, 2)}, {3: {1}}
        )
        positioned_direction_path = root / "direction-positioned.json"
        positioned_direction_path.write_text(json.dumps(positioned_direction), encoding="utf-8")
        positioned_code, positioned_payload = run_target_builder(
            positioned_direction_path, "--holdout", "1"
        )
        tests.append((
            "unnumbered target hold-out aligns to discovered stage 3",
            positioned_code == 0
            and positioned_payload.get("written") is False
            and positioned_payload.get("screening", {}).get("holdout_target_paragraphs") == [1],
        ))

        empty_direction = extract_revision_direction.analyze(
            unnumbered_stages, "synthetic", {(2, 3)}, {(1, 2)}, {}
        )
        empty_direction["holdout_paragraphs_by_stage"] = {"3": []}
        empty_direction_path = root / "direction-empty.json"
        empty_direction_path.write_text(json.dumps(empty_direction), encoding="utf-8")
        empty_code, empty_payload = run_target_builder(empty_direction_path)
        tests.append((
            "empty direction hold-out map does not cause a mismatch",
            empty_code == 0
            and empty_payload.get("written") is False
            and empty_payload.get("screening", {}).get("holdout_target_paragraphs") == [],
        ))

        target = build_target_profile.build(private_stages, stage2, {1}, "synthetic", direction, "Synthetic Venue")
        profile = target["profile"]
        tests.append((
            "target profile is partitioned by venue",
            profile["schema"] == "helicon-target-profile-v3"
            and profile["default_venue"] == "Synthetic Venue"
            and "Synthetic Venue" in profile["venue_profiles"]
            and profile["venue_applicability"]["cross_venue"] == "partial",
        ))
        opening_metrics = style_fingerprint.metric_block([
            "However, the first paragraph opens with contrast. A second sentence follows.",
            "We open the second paragraph with an author action. Another sentence follows.",
        ])
        tests.append((
            "opening structure counts paragraph openings rather than every sentence",
            opening_metrics["paragraph_opening_count"] == 2
            and sum(opening_metrics["paragraph_opening_types"].values()) == 2
            and sum(opening_metrics["opening_types"].values()) == 4,
        ))
        tests.append((
            "section titles normalize to reusable types",
            style_fingerprint.section_type("Experimental Setup") == "Evaluation"
            and style_fingerprint.section_type("Protocol Design") == "Methods"
            and style_fingerprint.section_type("Security Model") == "Threat Model",
        ))

        numbering_contracts = []
        for suffix in (".md", ".txt"):
            numbering_fixture = root / f"preamble-numbering{suffix}"
            numbering_fixture.write_text(
                "Synthetic preamble metadata.\n\n"
                "# Introduction\n\n"
                "The first body paragraph defines the scope. It has a second sentence.\n\n"
                "The second body paragraph records the evidence. It also has a second sentence.\n",
                encoding="utf-8",
            )
            direction_paragraphs = extract_revision_direction.paragraphs(numbering_fixture)
            report = style_fingerprint.document_report(numbering_fixture)
            full_report, full_text, paragraph_count = build_target_profile.filtered_report(
                numbering_fixture, set()
            )
            held_report, held_text, held_count = build_target_profile.filtered_report(
                numbering_fixture, {1}
            )
            direction_hashes = [
                hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
                for item in direction_paragraphs
            ]
            filtered_hashes = [
                hashlib.sha256(text.encode("utf-8")).hexdigest()
                for text in style_fingerprint.split_paragraphs(full_text)
            ]
            held_hashes = [
                hashlib.sha256(text.encode("utf-8")).hexdigest()
                for text in style_fingerprint.split_paragraphs(held_text)
            ]
            numbering_contracts.append(
                len(direction_paragraphs) == 2
                and report["document"]["paragraph_count"] == 2
                and all(section["title"] != "Preamble" for section in report["sections"])
                and full_report["document"]["paragraph_count"] == 2
                and paragraph_count == held_count == 2
                and direction_hashes == filtered_hashes
                and held_report["document"]["paragraph_count"] == 1
                and held_hashes == direction_hashes[1:]
            )
        tests.append((
            "preamble exclusion keeps direction, profile, and document numbering aligned",
            all(numbering_contracts),
        ))

        tex_numbering = root / "preamble-numbering.tex"
        tex_numbering.write_text(
            "\\documentclass{article}\n"
            "\\title{Synthetic Paper}\n"
            "\\begin{document}\n"
            "\\maketitle\n"
            "\\section{Introduction}\n"
            "The first body paragraph defines the scope. It has a second sentence.\n\n"
            "The second body paragraph records the evidence. It also has a second sentence.\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        tex_direction = extract_revision_direction.paragraphs(tex_numbering)
        tex_full, tex_full_text, tex_count = build_target_profile.filtered_report(tex_numbering, set())
        tex_held, tex_held_text, tex_held_count = build_target_profile.filtered_report(tex_numbering, {1})
        tex_direction_hashes = [
            hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
            for item in tex_direction
        ]
        tex_full_hashes = [
            hashlib.sha256(text.encode("utf-8")).hexdigest()
            for text in style_fingerprint.split_paragraphs(tex_full_text)
        ]
        tex_held_hashes = [
            hashlib.sha256(text.encode("utf-8")).hexdigest()
            for text in style_fingerprint.split_paragraphs(tex_held_text)
        ]
        tests.append((
            "TeX preamble exclusion preserves hold-out numbering and paragraph hashes",
            len(tex_direction) == 2
            and tex_count == tex_held_count == 2
            and tex_full["document"]["paragraph_count"] == 2
            and tex_held["document"]["paragraph_count"] == 1
            and all(section["title"] != "Preamble" for section in tex_full["sections"])
            and tex_full_hashes == tex_direction_hashes
            and tex_held_hashes == tex_direction_hashes[1:],
        ))

        project_pack = root / ".helicon"
        (project_pack / "style").mkdir(parents=True, exist_ok=True)
        (project_pack / "project.yaml").write_text(
            'schema: helicon-project-v1\nfingerprint:\n  target_venue: "Synthetic Venue"\n',
            encoding="utf-8",
        )
        profile_path = project_pack / "style" / "target_profile.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        loaded_profile, profile_hash = resolve_target_profile.read_profile(profile_path)
        selected_venue, venue_match = resolve_target_profile.select_venue(
            loaded_profile,
            resolve_target_profile.project_target_venue(project_pack / "project.yaml"),
        )
        resolved_fields, all_exemplar = resolve_target_profile.resolve_fields(
            loaded_profile,
            selected_venue,
            ["P4", "P5"],
            "Introduction",
        )
        tests.append((
            "target resolver selects only P4/P5-owned fields",
            venue_match is True
            and profile_hash.startswith("sha256:")
            and {item["id"] for item in resolved_fields}
            == {"sentence_length", "paragraph_length", "opening_structure", "connectives", "hedging"}
            and not ({item["id"] for item in resolved_fields} & set(resolve_target_profile.P2_ONLY_FIELDS))
            and all_exemplar is False,
        ))
        legacy_profile = json.loads(json.dumps(profile))
        legacy_profile["schema"] = "helicon-target-profile-v2"
        legacy_fields, _ = resolve_target_profile.resolve_fields(
            legacy_profile,
            selected_venue,
            ["P4", "P6"],
            "Introduction",
        )
        legacy_by_id = {item["id"]: item for item in legacy_fields}
        tests.append((
            "legacy v2 opening and raw-heading voice fields are excluded",
            legacy_by_id["opening_structure"]["eligible"] is False
            and legacy_by_id["active_passive_by_section"]["eligible"] is False,
        ))
        trace_root = project_pack / "style" / "target_traces"
        nested_trace = trace_root / "nested" / "case.json"
        tests.append((
            "target trace accepts a nested target_traces file",
            resolve_target_profile.safe_trace_path(
                str(nested_trace), project_pack / "style"
            ) == nested_trace.resolve(),
        ))
        rejected_trace_paths = (
            project_pack / "style" / "target_profile.json",
            project_pack / "style" / "target_screening.json",
            project_pack / "style" / "other-trace.json",
            project_pack / "style" / "other" / "trace.json",
            trace_root,
        )
        rejected_trace_count = 0
        for rejected_trace in rejected_trace_paths:
            try:
                resolve_target_profile.safe_trace_path(
                    str(rejected_trace), project_pack / "style"
                )
            except resolve_target_profile.UserError:
                rejected_trace_count += 1
        tests.append((
            "target trace rejects reserved files, other style paths, and its root directory",
            rejected_trace_count == len(rejected_trace_paths),
        ))

        preflight_project = root / "preflight-project"
        preflight_pack = preflight_project / ".helicon"
        preflight_style = preflight_pack / "style"
        preflight_style.mkdir(parents=True)
        (preflight_pack / "project.yaml").write_text(
            'schema: helicon-project-v1\nfingerprint:\n  target_venue: "Synthetic Venue"\n',
            encoding="utf-8",
        )
        preflight_profile = {
            "schema": "helicon-target-profile-v3",
            "default_venue": "Synthetic Venue",
            "venue_profiles": {
                "Synthetic Venue": {
                    "fields": {
                        "sentence_length": {
                            "source": "rule",
                            "confidence": "high",
                            "value": {"mean_range_words": [1, 100], "minimum_sd_words": 0},
                        },
                        "paragraph_length": {
                            "source": "exemplar",
                            "confidence": "high",
                            "value": {"mean_words": 80, "word_sd": 10, "mean_sentences": 4},
                        },
                        "opening_structure": {
                            "source": "exemplar",
                            "confidence": "high",
                            "value": {"author_action": 0.5, "topic_frame": 0.5},
                        },
                        "connectives": {
                            "source": "exemplar",
                            "confidence": "high",
                            "value": {"density_per_sentence": 0.5, "allowed": []},
                        },
                        "hedging": {
                            "source": "rule",
                            "confidence": "high",
                            "value": {"policy": "Use evidence-bound hedges only."},
                        },
                    }
                }
            },
        }
        preflight_profile_path = preflight_style / "target_profile.json"

        def write_preflight_profile() -> None:
            preflight_profile_path.write_text(
                json.dumps(preflight_profile, ensure_ascii=False), encoding="utf-8"
            )

        write_preflight_profile()
        clean_fragment = preflight_project / "clean.txt"
        clean_fragment.write_text(
            "Requests arrive. The system places each request in a queue. "
            "A worker processes queued items and records their status before returning a response. "
            "An independent checker compares every recorded status with the reference produced during setup.",
            encoding="utf-8",
        )
        clean_preflight, clean_style_dir = revision_preflight.preflight(
            clean_fragment, preflight_project, "Introduction", ["P4", "P5"]
        )
        tests.append((
            "revision preflight preserves a clean four-sentence fragment",
            clean_preflight["decision"] == "preserve"
            and clean_preflight["trigger_reason_ids"] == []
            and clean_preflight["metric_counts"]["sentence_count"] == 4,
        ))
        tests.append((
            "exemplar connective density is a boundary, not a quota",
            clean_preflight["decision"] == "preserve"
            and clean_preflight["metric_counts"]["connective_count"] == 0
            and "connectives" in clean_preflight["evaluated_field_ids"],
        ))
        tests.append((
            "single-paragraph preflight excludes paragraph and opening targets",
            clean_preflight["metric_counts"]["paragraph_count"] == 1
            and {"paragraph_length", "opening_structure"}.issubset(
                clean_preflight["excluded_field_ids"]
            )
            and not ({"paragraph_length", "opening_structure"} & set(
                clean_preflight["evaluated_field_ids"]
            )),
        ))

        preflight_profile["venue_profiles"]["Synthetic Venue"]["fields"]["sentence_length"][
            "value"
        ] = {"mean_range_words": [12, 30], "minimum_sd_words": 4}
        write_preflight_profile()
        flat_fragment = preflight_project / "flat.txt"
        flat_fragment.write_text(
            "Results hold. Results hold. Results hold. Results hold.", encoding="utf-8"
        )
        flat_preflight, _ = revision_preflight.preflight(
            flat_fragment, preflight_project, "Introduction", ["P4"]
        )
        tests.append((
            "revision preflight revises rule mean or variance violations",
            flat_preflight["decision"] == "revise"
            and {
                "P4_RULE_SENTENCE_MEAN_OUT_OF_RANGE",
                "P4_RULE_SENTENCE_SD_LOW",
            }.issubset(flat_preflight["trigger_reason_ids"]),
        ))

        _, low_sd_only_triggers = revision_preflight.evaluate_p4(
            {
                "sentence_length": {
                    "source": "rule",
                    "value": {"mean_range_words": [12, 30], "minimum_sd_words": 4},
                }
            },
            {
                "sentence_count": 4,
                "paragraph_count": 1,
                "mean_sentence_length": 20,
                "sentence_length_sd": 2,
                "opening_types": {"noun_phrase_subject": 2, "condition_or_scope": 2},
            },
        )
        tests.append((
            "low sentence variance alone does not authorize P4 churn",
            low_sd_only_triggers == set(),
        ))

        preflight_profile["venue_profiles"]["Synthetic Venue"]["fields"]["sentence_length"][
            "value"
        ] = {"mean_range_words": [1, 100], "minimum_sd_words": 0}
        write_preflight_profile()
        ai_fragment = preflight_project / "ai-tell.txt"
        ai_fragment.write_text(
            "This groundbreaking method handles requests. The queue records each task. "
            "A worker checks the stored state. The coordinator returns the result.",
            encoding="utf-8",
        )
        ai_preflight, _ = revision_preflight.preflight(
            ai_fragment, preflight_project, "Introduction", ["P5"]
        )
        tests.append((
            "revision preflight revises an AI-tell hit",
            ai_preflight["decision"] == "revise"
            and "R01" in ai_preflight["ai_tells"]["rule_ids"]
            and "P5_AI_R01" in ai_preflight["trigger_reason_ids"],
        ))

        traced_preflight, traced_style_dir = revision_preflight.preflight(
            clean_fragment,
            preflight_project,
            "Introduction",
            ["P4", "P5"],
            "C01",
            "run-001",
        )
        trace_path = resolve_target_profile.safe_trace_path(
            str(preflight_style / "target_traces" / "stage3c" / "C01.json"),
            traced_style_dir,
        )
        resolve_target_profile.write_trace(trace_path, traced_preflight)
        trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
        tests.append((
            "revision preflight trace is privacy-safe and case-bound",
            clean_style_dir == traced_style_dir == preflight_style.resolve()
            and trace_path.parent == (preflight_style / "target_traces" / "stage3c").resolve()
            and trace_payload == traced_preflight
            and trace_payload["schema"] == revision_preflight.OUTPUT_SCHEMA
            and trace_payload["producer"] == revision_preflight.PRODUCER
            and trace_payload["case_id"] == "C01"
            and trace_payload["run_nonce"] == "run-001"
            and trace_payload["fragment_sha256"]
            == "sha256:" + hashlib.sha256(clean_fragment.read_bytes()).hexdigest()
            and set(trace_payload["target"]) == {"status", "schema", "profile_sha256"}
            and "text" not in json.dumps(trace_payload).casefold(),
        ))

        preflight_profile_path.unlink()
        fallback_preflight, _ = revision_preflight.preflight(
            flat_fragment, preflight_project, "Introduction", ["P4"]
        )
        tests.append((
            "revision preflight retains rule-backed P4 without a target profile",
            fallback_preflight["target"]["status"] == "none"
            and fallback_preflight["decision"] == "revise"
            and "sentence_length" in fallback_preflight["evaluated_field_ids"],
        ))
        write_preflight_profile()

        valid_sentence_value = preflight_profile["venue_profiles"]["Synthetic Venue"]["fields"][
            "sentence_length"
        ]["value"]
        preflight_profile["venue_profiles"]["Synthetic Venue"]["fields"]["sentence_length"][
            "value"
        ] = "malformed"
        write_preflight_profile()
        malformed_target_rejected = False
        try:
            revision_preflight.preflight(clean_fragment, preflight_project, "Introduction", ["P4"])
        except resolve_target_profile.UserError:
            malformed_target_rejected = True
        tests.append((
            "current target schema rejects malformed typed field values",
            malformed_target_rejected,
        ))
        preflight_profile["venue_profiles"]["Synthetic Venue"]["fields"]["sentence_length"][
            "value"
        ] = valid_sentence_value
        write_preflight_profile()

        incomplete_token_errors = 0
        for case_id, run_nonce in (("C01", None), (None, "run-001")):
            try:
                revision_preflight.validated_tokens(case_id, run_nonce)
            except revision_preflight.UserError:
                incomplete_token_errors += 1
        tests.append((
            "revision preflight requires case and nonce together",
            incomplete_token_errors == 2,
        ))
        invalid_token_errors = 0
        for case_id, run_nonce in (("bad token", "run-001"), ("C01", "bad/token")):
            try:
                revision_preflight.validated_tokens(case_id, run_nonce)
            except revision_preflight.UserError:
                invalid_token_errors += 1
        tests.append((
            "revision preflight rejects unsafe case and nonce tokens",
            invalid_token_errors == 2,
        ))

        before_holdout = root / "holdout-before.txt"
        output_holdout = root / "holdout-output.txt"
        target_holdout = root / "holdout-target.txt"
        before_holdout.write_text(
            "The groundbreaking method completes the task in 12 ms. It is significantly efficient.",
            encoding="utf-8",
        )
        target_holdout.write_text(
            "The method completes the task in 12 ms. Its design is concise and evidence-bounded.",
            encoding="utf-8",
        )
        output_holdout.write_text(target_holdout.read_text(encoding="utf-8"), encoding="utf-8")
        trailer, trailer_fields = target_eval.read_trailer(
            "[HElicon] synthetic §Introduction · P3 → P4 → P5 · 2处 · frozen:0变化 · baseline:none · target:partial",
            None,
        )
        _, compact_trailer_fields = target_eval.read_trailer(
            "[HElicon] synthetic §Introduction · P3→P4→P5 · 2处 · frozen:0变化 · baseline:none · target:partial",
            None,
        )
        tests.append((
            "documented and compact trailer arrows share one canonical pass sequence",
            trailer_fields["passes"] == compact_trailer_fields["passes"] == "P3→P4→P5",
        ))
        route_sources = {
            "expected_target_status": "partial",
            "dimension_sources": {
                "sentence_length": "exemplar",
                "paragraph_length": "exemplar",
                "opening_structure": "exemplar",
                "connectives": "rule",
                "hedging": "rule",
            },
        }
        p3_target = target_eval.routed_target_contract({"passes": "P3"}, route_sources)
        p7_target = target_eval.routed_target_contract({"passes": "P7"}, route_sources)
        default_target = target_eval.routed_target_contract(trailer_fields, route_sources)
        tests.append((
            "target status follows target-owning routed passes",
            p3_target["routed_dimensions"] == []
            and p3_target["expected_target_status"] == "none"
            and p7_target["routed_dimensions"] == []
            and p7_target["expected_target_status"] == "none"
            and default_target["routed_dimensions"]
            == ["connectives", "hedging", "opening_structure", "paragraph_length", "sentence_length"]
            and default_target["expected_target_status"] == "partial",
        ))
        invalid_trailer_rejected = False
        try:
            target_eval.read_trailer(
                "[HElicon] synthetic §Introduction · P3 -> P4 · 2处 · frozen:0变化 · baseline:none · target:partial",
                None,
            )
        except target_eval.UserError:
            invalid_trailer_rejected = True
        tests.append(("invalid trailer arrow remains rejected", invalid_trailer_rejected))
        txt_eval = target_eval.evaluate(
            before_holdout,
            output_holdout,
            target_holdout,
            None,
            trailer,
            trailer_fields,
            {"expected_target_status": "partial"},
            True,
        )
        tests.append((
            "txt hold-out evaluation preserves immutable data",
            txt_eval["passed"]
            and txt_eval["frozen_set"]["passed"]
            and txt_eval["structural_distance"]["aggregate_convergence_percent"] == 100.0,
        ))
        tests.append((
            "single-paragraph and absent-pass metrics are excluded",
            set(target_eval.PARAGRAPH_DISTANCE_METRICS).issubset(
                txt_eval["structural_distance"]["excluded_metrics"]
            )
            and "active_sentence_ratio" in txt_eval["structural_distance"]["excluded_metrics"]
            and "passive_sentence_ratio" in txt_eval["structural_distance"]["excluded_metrics"]
            and "first_person_per_1000_words" in txt_eval["structural_distance"]["excluded_metrics"],
        ))
        confounded_target = root / "holdout-target-confounded.txt"
        confounded_target.write_text(
            "The method completes the task in 99 ms. Its design is concise and evidence-bounded.",
            encoding="utf-8",
        )
        confounded_eval = target_eval.evaluate(
            before_holdout,
            output_holdout,
            confounded_target,
            None,
            trailer,
            trailer_fields,
            {"expected_target_status": "partial"},
            True,
        )
        tests.append((
            "content-confounded ground truth cannot pass efficacy validation",
            not confounded_eval["ground_truth_compatibility"]["passed"]
            and not confounded_eval["evaluation_valid"]
            and not confounded_eval["passed"],
        ))

        approved_style_dir = root / ".helicon" / "style" / "approved-eval"
        approved_style_dir.mkdir(parents=True)
        approved_before = approved_style_dir / "before.txt"
        approved_output = approved_style_dir / "output.txt"
        approved_target = approved_style_dir / "target.txt"
        approved_screening = approved_style_dir / "target_screening.json"
        approved_manifest = approved_style_dir / "approval.json"
        approved_before.write_text(
            "The method offers flexibility, providing useful support.", encoding="utf-8"
        )
        approved_target.write_text(
            "The method offers flexibility and provides useful support.", encoding="utf-8"
        )
        approved_output.write_text(
            approved_target.read_text(encoding="utf-8"), encoding="utf-8"
        )
        approved_screening.write_text(json.dumps({
            "schema": "helicon-target-screening-v2",
            "decision_table": [
                {"dimension": "sentence_length", "source": "rule"},
                {"dimension": "paragraph_length", "source": "rule"},
                {"dimension": "opening_structure", "source": "rule"},
                {"dimension": "connectives", "source": "exemplar"},
                {"dimension": "hedging", "source": "exemplar"},
                {"dimension": "active_passive_by_section", "source": "exemplar"},
                {"dimension": "first_person", "source": "exemplar"},
            ],
        }), encoding="utf-8")

        def write_approval(**overrides: object) -> None:
            payload: dict[str, object] = {
                "schema": target_eval.APPROVED_TARGET_SCHEMA,
                "source": target_eval.APPROVED_TARGET_SOURCE,
                "approval_status": "approved",
                "approved_utc": "2026-08-11T08:00:00+00:00",
                "content_stable_confirmed": True,
                "before_sha256": target_eval.sha256_file(approved_before),
                "target_sha256": target_eval.sha256_file(approved_target),
                "screening_sha256": target_eval.sha256_file(approved_screening),
            }
            payload.update(overrides)
            approved_manifest.write_text(json.dumps(payload), encoding="utf-8")

        write_approval()
        approved_admission = target_eval.verify_author_approved_target(
            approved_screening,
            approved_manifest,
            approved_before,
            approved_target,
            None,
        )
        approved_eval = target_eval.evaluate(
            approved_before,
            approved_output,
            approved_target,
            None,
            trailer,
            trailer_fields,
            approved_admission,
            approved_admission["content_stable_confirmed"],
        )
        tests.append((
            "author-approved style-only target has explicit non-v3 provenance",
            approved_admission["admission_kind"] == "author-approved-style-only-target"
            and approved_eval["schema"] == "helicon-author-approved-target-eval-v1"
            and approved_eval["target_provenance"]["source"]
            == "author-approved-ai-assisted"
            and approved_eval["target_provenance"]["before_sha256"]
            == target_eval.sha256_file(approved_before)
            and approved_eval["target_provenance"]["target_sha256"]
            == target_eval.sha256_file(approved_target)
            and "holdout" not in approved_eval
            and "v3" not in approved_eval["ai_tells_by_rule"]
            and "v1_to_v3" not in approved_eval["alignment"],
        ))
        tests.append((
            "author-approved rule evidence can pass with null structural convergence",
            approved_eval["structural_distance"]["aggregate_convergence_percent"] is None
            and approved_eval["directional_evidence"]["structural"]["status"]
            == "insufficient_signal"
            and approved_eval["directional_evidence"]["ai_tell_rule_distance"][
                "convergence_percent"
            ] == 100.0
            and approved_eval["directional_evidence"]["overall_status"] == "improved"
            and approved_eval["directional_improvement"] is True
            and approved_eval["passed"],
        ))
        approved_output.write_text(
            "However, the method offers flexibility and provides useful support.",
            encoding="utf-8",
        )
        drifted_approved_eval = target_eval.evaluate(
            approved_before,
            approved_output,
            approved_target,
            None,
            trailer,
            trailer_fields,
            approved_admission,
            True,
        )
        tests.append((
            "exact-match structural drift blocks an otherwise improved rule channel",
            drifted_approved_eval["structural_distance"][
                "aggregate_convergence_percent"
            ] is None
            and drifted_approved_eval["directional_evidence"]["structural"]["status"]
            == "worsened"
            and drifted_approved_eval["directional_evidence"]["ai_tell_rule_distance"][
                "status"
            ] == "improved"
            and drifted_approved_eval["directional_evidence"]["overall_status"]
            == "mixed_or_worsened"
            and not drifted_approved_eval["passed"],
        ))
        approved_output.write_text(
            approved_target.read_text(encoding="utf-8"), encoding="utf-8"
        )
        zero_rules = {str(rule): 0 for rule in range(1, 15)}
        rule_before = {**zero_rules, "10": 1}
        rule_output = {**zero_rules, "1": 1}
        off_target_rule = target_eval.ai_tell_directional_distance(
            rule_before, rule_output, zero_rules
        )
        tests.append((
            "new AI-tell outside target-changing rules blocks rule-channel improvement",
            off_target_rule["convergence_percent"] == 100.0
            and off_target_rule["status"] == "worsened"
            and off_target_rule["directional_improvement"] is False
            and set(off_target_rule["off_target_regressions"]) == {"R1"},
        ))

        write_approval(approval_status="candidate")
        unapproved_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                approved_manifest,
                approved_before,
                approved_target,
                None,
            )
        except target_eval.UserError:
            unapproved_rejected = True
        tests.append(("unapproved style target is rejected", unapproved_rejected))

        non_boolean_confirmations_rejected = 0
        for value in (1, "true"):
            write_approval(content_stable_confirmed=value)
            try:
                target_eval.verify_author_approved_target(
                    approved_screening,
                    approved_manifest,
                    approved_before,
                    approved_target,
                    None,
                )
            except target_eval.UserError:
                non_boolean_confirmations_rejected += 1
        tests.append((
            "content-stable approval requires the JSON true literal",
            non_boolean_confirmations_rejected == 2,
        ))

        write_approval(target_sha256="0" * 64)
        stale_approval_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                approved_manifest,
                approved_before,
                approved_target,
                None,
            )
        except target_eval.UserError:
            stale_approval_rejected = True
        tests.append(("stale approved-target hash is rejected", stale_approval_rejected))
        write_approval()

        valid_screening_text = approved_screening.read_text(encoding="utf-8")
        approved_screening.write_text("{}", encoding="utf-8")
        tampered_screening_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                approved_manifest,
                approved_before,
                approved_target,
                None,
            )
        except target_eval.UserError:
            tampered_screening_rejected = True
        tests.append((
            "approved target manifest binds the screening hash",
            tampered_screening_rejected,
        ))

        valid_screening_payload = json.loads(valid_screening_text)
        missing_source_payload = json.loads(valid_screening_text)
        missing_source_payload["decision_table"] = [
            item for item in missing_source_payload["decision_table"]
            if item["dimension"] != "hedging"
        ]
        approved_screening.write_text(json.dumps(missing_source_payload), encoding="utf-8")
        write_approval()
        missing_source_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                approved_manifest,
                approved_before,
                approved_target,
                None,
            )
        except target_eval.UserError:
            missing_source_rejected = True

        duplicate_source_payload = json.loads(valid_screening_text)
        duplicate_source_payload["decision_table"].append(
            dict(duplicate_source_payload["decision_table"][0])
        )
        approved_screening.write_text(json.dumps(duplicate_source_payload), encoding="utf-8")
        write_approval()
        duplicate_source_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                approved_manifest,
                approved_before,
                approved_target,
                None,
            )
        except target_eval.UserError:
            duplicate_source_rejected = True
        tests.append((
            "approved screening rejects missing or duplicate routed sources",
            missing_source_rejected and duplicate_source_rejected,
        ))
        malformed_screening_rejected = 0
        for malformed_screening in ([], {"decision_table": [None]}):
            try:
                target_eval.screening_route_sources(malformed_screening)  # type: ignore[arg-type]
            except target_eval.UserError:
                malformed_screening_rejected += 1
        tests.append((
            "screening root and decision entries have explicit type errors",
            malformed_screening_rejected == 2,
        ))
        approved_screening.write_text(
            json.dumps(valid_screening_payload), encoding="utf-8"
        )
        write_approval()

        approved_cli_args = [
            sys.executable,
            "-B",
            str(Path(target_eval.__file__).resolve()),
            str(approved_before),
            str(approved_output),
            str(approved_target),
            "--screening",
            str(approved_screening),
            "--approval-manifest",
            str(approved_manifest),
            "--trailer",
            trailer,
            "--execution-evidence-class",
            "independent-session",
            "--output-report",
            str(approved_style_dir / "cli-report.json"),
            "--json",
        ]
        approved_cli = subprocess.run(
            approved_cli_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        approved_cli_payload = json.loads(approved_cli.stdout)
        tests.append((
            "author-approved CLI separates execution class from target provenance",
            approved_cli.returncode == 0
            and approved_cli_payload["execution_provenance"]["evidence_class"]
            == "independent-session"
            and approved_cli_payload["target_provenance"]["source"]
            == "author-approved-ai-assisted"
            and "execution" in approved_cli_payload["execution_provenance"]["scope"]
            and approved_cli_payload["written"] is False,
        ))
        approved_manifest.write_text("[]", encoding="utf-8")
        malformed_manifest_cli = subprocess.run(
            approved_cli_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        malformed_manifest_payload = json.loads(malformed_manifest_cli.stdout)
        tests.append((
            "malformed manifest root preserves JSON error and exit-code contract",
            malformed_manifest_cli.returncode == 2
            and malformed_manifest_payload["ok"] is False
            and "JSON root must be an object" in malformed_manifest_payload["error"]
            and "Traceback" not in malformed_manifest_cli.stderr,
        ))
        write_approval()

        malformed_holdout_screening = approved_style_dir / "malformed-holdout-screening.json"
        malformed_holdout_screening.write_text(json.dumps({
            "schema": target_eval.APPROVED_SCREENING_SCHEMA,
            "holdout_target_paragraphs": 1,
            "target_file": str(approved_target),
            "decision_table": [],
        }), encoding="utf-8")
        malformed_holdout_cli = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(target_eval.__file__).resolve()),
                str(approved_before),
                str(approved_output),
                str(approved_target),
                "--screening",
                str(malformed_holdout_screening),
                "--target-paragraph",
                "1",
                "--trailer",
                trailer,
                "--json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        malformed_holdout_payload = json.loads(malformed_holdout_cli.stdout)
        tests.append((
            "malformed screened-v3 shape preserves JSON error and exit-code contract",
            malformed_holdout_cli.returncode == 2
            and malformed_holdout_payload["ok"] is False
            and "positive integers" in malformed_holdout_payload["error"]
            and "Traceback" not in malformed_holdout_cli.stderr,
        ))

        guard_before = approved_style_dir / "guard-before.txt"
        guard_target = approved_style_dir / "guard-target.txt"
        guard_manifest = approved_style_dir / "guard-approval.json"
        guard_before.write_text("The method completes the task in 12 ms.", encoding="utf-8")
        guard_target.write_text("The method completes the task in 99 ms.", encoding="utf-8")
        guard_manifest.write_text(json.dumps({
            "schema": target_eval.APPROVED_TARGET_SCHEMA,
            "source": target_eval.APPROVED_TARGET_SOURCE,
            "approval_status": "approved",
            "approved_utc": "2026-08-11T08:00:00+00:00",
            "content_stable_confirmed": True,
            "before_sha256": target_eval.sha256_file(guard_before),
            "target_sha256": target_eval.sha256_file(guard_target),
            "screening_sha256": target_eval.sha256_file(approved_screening),
        }), encoding="utf-8")
        immutable_target_rejected = False
        try:
            target_eval.verify_author_approved_target(
                approved_screening,
                guard_manifest,
                guard_before,
                guard_target,
                None,
            )
        except target_eval.UserError:
            immutable_target_rejected = True
        tests.append((
            "author-approved target still requires before-target immutable guard",
            immutable_target_rejected,
        ))

        preservation_before = root / "preservation-before.txt"
        preservation_output = root / "preservation-output.txt"
        preservation_target = root / "preservation-target.txt"
        preservation_text = "This paragraph already matches the approved target."
        preservation_before.write_text(preservation_text + "\n", encoding="utf-8")
        preservation_output.write_text(preservation_text, encoding="utf-8")
        preservation_target.write_text(preservation_text + "\n", encoding="utf-8")
        preservation_trailer, preservation_fields = target_eval.read_trailer(
            "[HElicon] synthetic §Introduction · P3 → P4 → P5 · 0处 · "
            "frozen:0变化 · baseline:none · target:partial",
            None,
        )
        preservation = target_eval.evaluate_preservation(
            preservation_before,
            preservation_output,
            preservation_target,
            None,
            preservation_trailer,
            preservation_fields,
            {"expected_target_status": "partial", "verified": True},
        )
        tests.append((
            "preservation mode passes canonical exact output",
            preservation["schema"] == "helicon-target-preservation-eval-v1"
            and preservation["passed"]
            and preservation["exact_preservation"]["passed"]
            and preservation["exact_preservation"]["byte_output_equals_before"] is False
            and preservation["frozen_set"]["passed"]
            and preservation["directional_improvement"] is None
            and preservation["structural_distance"]["aggregate_convergence_percent"] is None
            and target_eval.result_exit_code(preservation) == 0,
        ))

        preservation_output.write_text(
            "This paragraph changes text that was already approved.", encoding="utf-8"
        )
        changed_preservation = target_eval.evaluate_preservation(
            preservation_before,
            preservation_output,
            preservation_target,
            None,
            preservation_trailer,
            preservation_fields,
            {"expected_target_status": "partial", "verified": True},
        )
        tests.append((
            "preservation text change is a report and exit failure",
            not changed_preservation["exact_preservation"]["passed"]
            and changed_preservation["frozen_set"]["passed"]
            and not changed_preservation["passed"]
            and target_eval.result_exit_code(changed_preservation) == 1,
        ))

        mismatched_target = root / "preservation-mismatched-target.txt"
        mismatched_target.write_text("A different approved target.", encoding="utf-8")
        preservation_admission_rejected = False
        try:
            target_eval.evaluate_preservation(
                preservation_before,
                preservation_output,
                mismatched_target,
                None,
                preservation_trailer,
                preservation_fields,
                {"expected_target_status": "partial", "verified": True},
            )
        except target_eval.UserError:
            preservation_admission_rejected = True
        tests.append((
            "preservation mode rejects before-target mismatch",
            preservation_admission_rejected,
        ))

        def claim_guard(
            label: str, before_text: str, after_text: str, allowed: set[str] | None = None
        ) -> dict[str, object]:
            before_path = root / f"claim-{label}-before.txt"
            after_path = root / f"claim-{label}-after.txt"
            before_path.write_text(before_text, encoding="utf-8")
            after_path.write_text(after_text, encoding="utf-8")
            return latex_guard.compare(before_path, after_path, None, allowed or set())

        contraction_guard = claim_guard(
            "contraction",
            "The system cannot process requests.",
            "The system can't process requests.",
        )
        tests.append((
            "claim-scope guard normalizes equivalent contractions",
            contraction_guard["passed"]
            and not contraction_guard["differences"]["negation"]["changed"]
            and not contraction_guard["differences"]["modality"]["changed"],
        ))

        rhetorical_parallel = claim_guard(
            "not-only",
            "The method not only reduces latency but also lowers memory use.",
            "The method reduces latency and lowers memory use.",
        )
        tests.append((
            "claim-scope guard permits the documented Rule 12 correlative repair",
            rhetorical_parallel["passed"]
            and not rhetorical_parallel["differences"]["negation"]["changed"]
            and not rhetorical_parallel["differences"]["quantifier_scope"]["changed"],
        ))

        redundant_hedge = claim_guard(
            "redundant-hedge",
            "The method may possibly support this workload.",
            "The method may support this workload.",
        )
        tests.append((
            "claim-scope guard permits same-tier hedge deduplication",
            redundant_hedge["passed"]
            and not redundant_hedge["differences"]["claim_strength"]["changed"],
        ))

        lexical_modal = claim_guard(
            "lexical-modal",
            "The system may process queued requests under this policy.",
            "Under this policy, the system may handle queued requests.",
        )
        tests.append((
            "claim-scope guard permits lexical rewrite around an unchanged modal",
            lexical_modal["passed"]
            and not lexical_modal["differences"]["modality"]["changed"],
        ))

        lexical_negation = claim_guard(
            "lexical-negation",
            "Method A does not rely on trusted hardware for execution.",
            "Method A does not require trusted hardware during execution.",
        )
        tests.append((
            "claim-scope guard permits lexical rewrite around unchanged negation",
            lexical_negation["passed"]
            and not lexical_negation["differences"]["negation"]["changed"],
        ))

        appearance_dedup = claim_guard(
            "appearance-dedup",
            "The measurements appear to suggest that the trend is stable.",
            "The measurements suggest that the trend remains stable.",
        )
        tests.append((
            "claim-scope guard treats appearance plus suggestion as one hedge layer",
            appearance_dedup["passed"]
            and not appearance_dedup["differences"]["claim_strength"]["changed"],
        ))

        probability_dedup = claim_guard(
            "probability-dedup",
            "The observed effect seems likely under this workload.",
            "The observed effect is likely for this workload.",
        )
        tests.append((
            "claim-scope guard treats appearance plus probability as one hedge layer",
            probability_dedup["passed"]
            and not probability_dedup["differences"]["claim_strength"]["changed"],
        ))

        shifted_scope = claim_guard(
            "shifted-scope",
            "Method A is not robust. Method B may execute the task.",
            "The setting is fixed. Method A is not reliable. Method B may run the task.",
        )
        tests.append((
            "claim-scope alignment tolerates an inserted leading scope",
            shifted_scope["passed"]
            and not shifted_scope["differences"]["negation"]["changed"]
            and not shifted_scope["differences"]["modality"]["changed"],
        ))

        strengthened_modal = claim_guard(
            "strengthened-modal",
            "The system may process this request.",
            "The system must process this request.",
        )
        tests.append((
            "claim-scope guard rejects may-to-must strengthening",
            not strengthened_modal["passed"]
            and "modality" in strengthened_modal["failed_categories"],
        ))

        lost_hedge = claim_guard(
            "lost-hedge",
            "The method is likely secure under this model.",
            "The method is secure under this model.",
        )
        tests.append((
            "claim-scope guard rejects removal of the last hedge layer",
            not lost_hedge["passed"]
            and "claim_strength" in lost_hedge["failed_categories"],
        ))

        moved_negation = claim_guard(
            "moved-negation",
            "Method A is not secure. Method B is secure.",
            "Method A is secure. Method B is not secure.",
        )
        tests.append((
            "claim-scope guard binds markers to coarse clause position",
            not moved_negation["passed"]
            and "negation" in moved_negation["failed_categories"],
        ))
        reordered_negation = claim_guard(
            "reordered-negation",
            "Method A is not secure. Method B is secure.",
            "Method B is not secure. Method A is secure.",
        )
        tests.append((
            "claim-scope guard follows the subject across reordered scopes",
            not reordered_negation["passed"]
            and "negation" in reordered_negation["failed_categories"],
        ))
        boilerplate_negation = claim_guard(
            "boilerplate-negation",
            "The method is not secure. The system is efficient.",
            "Security follows from the proof. The method is not scalable.",
        )
        tests.append((
            "claim-scope guard rejects boilerplate-based negation rebinding",
            not boilerplate_negation["passed"]
            and "negation" in boilerplate_negation["failed_categories"],
        ))
        radical_modal = claim_guard(
            "radical-modal",
            "The construction may fail.",
            "Failure may occur.",
        )
        tests.append((
            "claim-scope guard conservatively rejects an unverifiable radical paraphrase",
            not radical_modal["passed"]
            and "modality" in radical_modal["failed_categories"],
        ))
        marker_payload = json.dumps(
            {name: moved_negation["differences"][name] for name in latex_guard.ALLOW_CHOICES[5:]}
        )
        tests.append((
            "claim-scope report exposes marker classes without prose anchors",
            "@" not in marker_payload
            and "method" not in marker_payload.casefold()
            and "secure" not in marker_payload.casefold(),
        ))

        claim_scope_cases = {
            "negation": (
                "The system does not process requests.",
                "The system processes requests.",
            ),
            "modality": (
                "The system may process requests.",
                "The system processes requests.",
            ),
            "quantifier_scope": (
                "The system processes every request.",
                "The system processes requests.",
            ),
            "comparison": (
                "The system is faster.",
                "The system is responsive.",
            ),
            "claim_strength": (
                "The results suggest a stable trend.",
                "The results summarize a stable trend.",
            ),
        }
        for category, (before_text, after_text) in claim_scope_cases.items():
            result = claim_guard(category, before_text, after_text)
            tests.append((
                f"claim-scope guard rejects {category} changes",
                not result["passed"]
                and category in result["failed_categories"]
                and result["differences"][category]["changed"],
            ))

        allowed_negation = claim_guard(
            "allowed-negation",
            "The system does not process requests.",
            "The system processes requests.",
            {"negation"},
        )
        tests.append((
            "claim-scope guard honors an explicit allowed category",
            allowed_negation["passed"]
            and allowed_negation["differences"]["negation"]["changed"]
            and allowed_negation["differences"]["negation"]["allowed"],
        ))

        exact = {metric: 0.0 for metric in target_eval.DISTANCE_METRICS}
        drifted = dict(exact)
        drifted["connective_density"] = 1.0
        exact_mask = target_eval.distance_eligibility(exact, drifted, exact, set(), {"P5"})
        exact_report = target_eval.distances(exact, drifted, exact, exact_mask)
        tests.append((
            "exact-match drift is reported explicitly",
            exact_report["metrics"]["connective_density"]["status"] == "diverged_from_exact_match"
            and any(
                item["metric"] == "connective_density"
                and item["status"] == "diverged_from_exact_match"
                for item in exact_report["unconverged_dimensions"]
            ),
        ))

        directions = bootstrap_project_pack.available_directions()
        tests.append((
            "project direction choices come from installed direction-pack directories",
            directions == tuple(sorted(directions))
            and "private_llm_inference" in directions
            and all((Path(bootstrap_project_pack.__file__).resolve().parent.parent / "references" / "direction_packs" / item).is_dir() for item in directions),
        ))
        synthetic_fp = {
            "title": "Synthetic Direction Project",
            "target_venue": "",
            "key_terms": [],
            "sections": [],
            "content_hash": "sha256:" + "0" * 64,
        }
        directed_yaml = bootstrap_project_pack.project_yaml(
            "Synthetic", root, synthetic_fp, "2026-01-01T00:00:00+00:00", "private_llm_inference"
        )
        null_yaml = bootstrap_project_pack.project_yaml(
            "Synthetic", root, synthetic_fp, "2026-01-01T00:00:00+00:00", None
        )
        tests.append((
            "bootstrap project YAML appends a selected direction immediately before fingerprint",
            'direction: "private_llm_inference"\nfingerprint:' in directed_yaml,
        ))
        tests.append((
            "bootstrap project YAML records an absent direction as null",
            "direction: null\nfingerprint:" in null_yaml,
        ))

        inserted_pack = root / "direction-insert"
        inserted_pack.mkdir()
        inserted_path = inserted_pack / "project.yaml"
        inserted_path.write_text(
            'schema: helicon-project-v1\nname: "Synthetic"\nfingerprint:\n  title: "Keep"\n',
            encoding="utf-8",
        )
        set_project_direction.update_project_yaml(inserted_path, "encrypted_knn_search", False)
        tests.append((
            "direction setter inserts before fingerprint without changing other project fields",
            inserted_path.read_text(encoding="utf-8")
            == 'schema: helicon-project-v1\nname: "Synthetic"\ndirection: "encrypted_knn_search"\nfingerprint:\n  title: "Keep"\n',
        ))

        protected_pack = root / "direction-protected"
        protected_pack.mkdir()
        protected_path = protected_pack / "project.yaml"
        protected_text = (
            'schema: helicon-project-v1\nname: "Synthetic"\n'
            'direction: "private_llm_inference"\nfingerprint:\n  title: "Keep"\n'
        )
        protected_path.write_text(protected_text, encoding="utf-8")
        refused = False
        try:
            set_project_direction.update_project_yaml(protected_path, "encrypted_knn_search", False)
        except set_project_direction.UserError:
            refused = True
        tests.append((
            "direction setter refuses a non-null overwrite without force",
            refused and protected_path.read_text(encoding="utf-8") == protected_text,
        ))
        set_project_direction.update_project_yaml(protected_path, "encrypted_knn_search", True)
        tests.append((
            "direction setter force-replaces only the top-level direction",
            protected_path.read_text(encoding="utf-8")
            == protected_text.replace('direction: "private_llm_inference"', 'direction: "encrypted_knn_search"'),
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
