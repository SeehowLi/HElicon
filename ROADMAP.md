# HElicon Roadmap

This file is the sole entry point for the next optimization round. Every newly discovered open item must be appended here and must not be scattered through `CHANGELOG.md`.

## P4 and P6 have never been exercised on real data

- Current state: P4 and P6 depend on a resolved target and a style profile. The current project pack has neither, so their no-op results reflect missing configuration rather than a capability judgment.
- Impact: The real-corpus runs provide no behavioral evidence for either pass.
- Verifiable acceptance criterion: Run both passes on a project pack with a target profile; `p4_trigger_count` and `p6_result` must no longer be trivial values.

## Bare numbers outside mathematics are unprotected

- Current state: `numbers_with_units` recognizes only numbers carrying known units, while the `math` category covers only mathematical regions. The measured sample contains 19 bare numbers outside both protections.
- Impact: A rewrite can alter those numbers without an immutable-set violation.
- Verifiable acceptance criterion: Add a dedicated protection category and demonstrate that it detects an injected bare-number change.

## Ordinary content words are not immutable

- Current state: A malformed glossary rule can cause P3 to delete a modifier without triggering the rewrite-time mechanical contract; this occurred at line 51 in `run_c`. This release adds a build-time `deletion_risk` lint, but rewrite-time protection remains absent.
- Impact: A glossary specification error can remove meaning-bearing words during an otherwise contract-compliant replacement.
- Verifiable acceptance criterion: Add a rewrite-time word-level protection rule and demonstrate that it detects an injected deletion of a meaning-bearing word.

## Cryptographic-ladder candidate precision is low

- Current state: A two-word anchor window removed blocking false positives. Unanchored true upgrades are now warning-only candidates, and that track also contains coincidental matches from non-cryptographic contexts.
- Impact: Candidate warnings are not yet reliable enough for automated escalation or dismissal.
- Verifiable acceptance criterion: Define a measurable precision metric for the candidate track and report its measured value on a declared evaluation set.

## Command coverage debt

- Current state: Of 31 `H-*` commands, 30 have no eval case coverage.
- Impact: Most command routing and contract surfaces lack executable regression evidence.
- Verifiable acceptance criterion: Increase the covered-command count and show the resulting coverage change in `check_command_coverage` output.

## Unreachable templates

- Current state: Seven files under `templates/` are not referenced by any route.
- Impact: They consume installed context and maintenance attention without a reachable execution path.
- Verifiable acceptance criterion: Connect them to the reachability graph or explicitly remove them, and demonstrate a lower `orphan_file_count`.

## Handoff ledger remains open

- Current state: `round_6.json` remains a local draft. `target_semantics` must be reduced to a per-evidence field, and the `human_review` value for `R6-E001` must become `run-attested-only`.
- Impact: Round 6 cannot yet serve as a complete, validator-accepted public evidence ledger.
- Verifiable acceptance criterion: Make Round 6 a complete v2 round accepted by the validator and publish it without upgrading unsupported claims.

## Real-corpus sample size is narrow

- Current state: All real-data observations come from one 805-word technical subsection and cover only the `private_llm_inference` direction.
- Impact: The observations cannot support generalization across sections or directions.
- Verifiable acceptance criterion: Repeat the declared test on at least three subsections spanning at least two directions.
