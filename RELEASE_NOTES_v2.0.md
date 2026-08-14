# HElicon v2.0 Release Notes

## Evidence boundary

This release records mechanically reproducible repository and pass-contract facts. It makes no claim about paper quality, review outcomes, or acceptance probability. Synthetic regressions establish only that the checked code paths and rejection branches are runnable.

## Layered terminology

The terminology system has three layers with merge priority `L2 > L1 > L0`; every same-term override is recorded as a conflict.

- L0 reusable FHE core: 119 entries.
- L1 `private_llm_inference`: 48 entries.
- L1 `fhe_algorithm_optimization`: 46 entries.
- L1 `security_top_conference_writing`: 46 entries.
- L1 `fhe_systems`: 45 entries.
- L1 `encrypted_knn_search`: 42 entries.
- L2 project layer: loaded only when a project-local glossary is supplied.

Markdown conversion and layered builds report `deletion_risk` when a longer forbidden form contains its shorter term and replacement would necessarily delete extra words. The report is warning-only by default; `--fail-on-deletion-risk` makes a nonzero count exit 1.

## Mechanical verifiers

| Verifier | Bound rule or contract responsibility |
|---|---|
| `check_immutable_set.py` | Iron Rule 1: detect changes to protected numbers, keys, math, figure/table references, glossary-term counts, and claim-scope markers. |
| `check_terminology_freeze.py` | Iron Rule 2 and P3: detect newly introduced forbidden synonyms, variants, capitalization drift, and abbreviation/full-name mixing. |
| `check_claim_strength.py` | Iron Rule 3: block assertion-strength increases and report bounded cryptographic direction changes. |
| `check_ai_tells.py` | P5 reporting contract: quantify R1-R14 findings without independently authorizing semantic edits. |
| `check_reference_reachability.py` | Progressive-disclosure contract: report reachable and orphaned reference/template payload. |
| `check_command_coverage.py` | Command-contract consistency: report registry, router, skill, and synthetic-eval coverage for H-* commands. |

`check_pass_scope.py` is the normative pass-aware decision layer. For P3 it exempts only `glossary_terms`; `numbers_with_units`, `latex_keys`, `math`, `figure_table`, and `claim_scope` remain blocking. P4-P7 retain all immutable categories as blocking.

## Four-step pre-delivery contract

Every P3-P7 candidate is checked before delivery:

1. `check_pass_scope.py` applies immutable-set checks under the current pass domain.
2. `check_claim_strength.py` blocks assertion-strength increases and reports conservative or candidate movements.
3. `check_terminology_freeze.py` rejects blocking terminology drift and reports capitalization-only warnings under the documented boundary.
4. `check_ai_tells.py` reports density without independently blocking delivery.

P3 correctness uses the forward BEFORE/AFTER terminology difference. Absolute residual scans are applied to both texts with the same ruler; only a positive `terminology_residual_delta` blocks as `residual_increased`. Unchanged or reduced absolute residuals are warning evidence, not zero-threshold failures.

## Installation and wiring verification

The installed payload contains 107 files. Source and installed trees are compared with canonical UTF-8/LF manifests, while `payload_mode` distinguishes source-repository and installed-payload checks. Wiring integrity binds seven mandatory anchors by digest; deleting an anchor or softening mandatory language fails closed.

## Release validation counts

Before the deletion-risk addition, the v2.0.1 baseline had 233 repository selftests and 89 synthetic evals. The post-lint release gate passes 239 repository selftests and 95 synthetic evals. The fixed checks retained by this release are:

- Eight public gates: all exit 0 at the accepted baseline.
- Handoff negative selftests: 58.
- `SKILL.md` body: 363/500 lines.
- `SKILL.md` description: 896/1024 characters.
- Orphan files: 7.

## Bounded real-corpus observations

The following observations come from one 805-word technical subsection in one direction. The sample is small and does not support a generalization claim. P4 and P6 were never executed on real data because the project lacked a resolved target and style profile.

### run_a

The input was already qualified. Every pass produced a deterministic no-op, with zero changes; all four contract steps executed, `direction_layer=private_llm_inference`, and `rollback=none`. This establishes that the observed behavior on this already-qualified input was to refuse modification.

### run_b

Five terminology drifts and five AI-tell sentences were injected and processed before v2.0. P3 treated `glossary_terms` as an immutable-set violation and rolled back all attempted terminology repairs, so the terminology repair rate was 0/5. AI-tell findings fell from 10 to 4. The five non-terminology immutable categories had zero collateral damage. Both rollbacks were triggered by gates and reported.

### run_c

The same injected input was processed after v2.0.1. P3 was applied with `change_count=5`, and the terminology repair rate was 5/5. `V3(CLEAN,output)` reported `replacement_count=0`; all six `V1(CLEAN,output)` categories were zero; and every `V2(CLEAN,output)` result was zero. AI-tell findings fell from 10 to 4, while an R12 sentence was retained because claim-strength correctly blocked its removal.

The line-by-line output differed from the author's original text on two lines. One was the correctly retained R12 sentence. The other arose from a glossary specification error: P3 followed the glossary and deleted a modifier. That deletion did not violate the existing mechanical contract. This release adds the build-time `deletion_risk` lint to reject that structural glossary pattern when the explicit fail flag is enabled.
