# HElicon Round 3 Taskbook — Sanitized Repository Copy

This file is the repository-safe equivalent of the taskbook supplied in the originating task. Private paths are replaced with aliases, and no manuscript text, reviewer wording, system name, experimental value, target-profile value, or submission identifier is retained.

## 1. Objective and evidence policy

Round 3 must replace self-authored end-to-end proof with real-corpus and independent-session evidence, then preserve every reusable synthetic regression.

Evidence classes are fixed:

- `self-authored-fixture`: proves only that a pipeline is runnable;
- `real-data`: uses the author's private corpus;
- `independent-session`: runs in a task that did not build the evaluated feature.

Every reported conclusion needs a command, exit code, sanitized key output, and evidence class. Anything else must be listed under `unverified_claims`.

Private aliases:

- `<PRIVATE_PAPER_ROOT>`: private corpus and Stage 1–2 project pack;
- `<PRIVATE_STAGE3_ROOT>`: isolated Stage 3 workspace;
- `<INSTALLED_SKILL_ROOT>`: local installed skill;
- `<REPOSITORY_ROOT>`: HElicon development checkout.

## 2. Stage 0 — Close audited micro-bugs

1. Exempt R10 when the trailing clause contains a measured value, citation/reference command, or explicit mechanism; retain a hollow-clause positive case.
2. Make every Rule 2 keyword declared in `language_polish.md` behaviorally trigger R02 where applicable.
3. Upgrade contract synchronization from rule-number registration to executable keyword behavior checks, with explicit context-dependent positive and exempt samples.
4. Document the conservative adjacent-sentence support window for R02.
5. Merge the target-layer branch, tag v1.3.1, install the skill, and retain a backup.

Stage 0 acceptance requires selftests, contract sync, integrity, contamination, tag/ancestry evidence, and installed-skill integrity.

## 3. Stage 1 — Prepare the real corpus

All outputs remain under `<PRIVATE_PAPER_ROOT>/.helicon/`.

1. Determine the authority of the middle version by comparing PDF-derived Markdown with source-derived text section by section.
2. Extract content-focused text for three stages without modifying or moving any source file.
3. Remove preamble, macros, floats, formulas, citations, bibliography, comments, and appendix unless explicitly retained; preserve headings and paragraph boundaries.
4. Produce extraction QC covering section/paragraph/sentence/word counts, broken hyphenation, isolated layout lines, macro residue, caption leakage, abnormal sentence lengths, and mathematical residue.
5. Do not enter Stage 2 until broken hyphenation, macro residue, and caption leakage are zero and other anomaly rates are below the declared threshold.
6. Require one author visual confirmation after the machine QC gate.
7. Record stage, venue, template, page limit, author-supplied diff source, and authority in private version metadata.

Approved corpus amendment:

- first stage: abstract-only content extract;
- middle stage: PDF-derived Markdown authority;
- third stage: content text extract.

## 4. Stage 2 — Build target and direction evidence

All numerical profile values, exemplar prose, direction reports, and reviewer-pattern candidates remain private.

1. Add venue to the target-profile schema and make cross-venue use degrade to `target:partial`.
2. Select hold-outs before screening, target building, or direction analysis.
3. Run B1 screening on the real third-stage content. Every target field records `source: exemplar|rule`; an unclean exemplar dimension must fall back to the rule source.
4. Use only the author/advisor-driven first-to-middle pair for author-preference signals.
5. Mark venue-confounded signals as confirmed, possible, or unknown; do not write them into personal expressions without author approval.
6. Keep the reviewer-driven middle-to-third pair outside author preference. Abstract it only into private reviewer-pattern candidates and separate likely page-budget deletion.
7. Never copy reviewer wording, manuscript claims, experimental values, parameter values, or system names into core.
8. Keep target profiles separate from descriptive baselines; target values cannot trigger drift alerts.

Stage 2 acceptance requires venue-aware profile/schema evidence, screened source counts, hold-out exclusion evidence, private direction/reviewer-pattern artifacts, and contamination checks.

## 5. Stage 3 — Independent real-data evaluation

Stage 3 must run from `<PRIVATE_STAGE3_ROOT>` in an independent task using the installed skill. It may not inspect blind targets or evaluator internals before output generation.

### 5.1 Preservation track

Use already-qualified third-stage fragments as do-no-harm hold-outs. Preflight `preserve` plus no exact glossary mismatch requires byte-identical output, zero changes, immutable-set preservation, exact trailer semantics, and target-resolution consistency.

Preservation mode does not report directional or aggregate convergence.

### 5.2 Directional track amendment

Raw cross-version pairs were found to change facts and claim scope. Therefore:

1. HElicon proposes style-only targets.
2. The author approves each target individually.
3. Approved targets are recorded as `author-approved-ai-assisted`, never as raw third-stage ground truth.
4. Rule-direction distance is reported only for rules actually changed by the approved target.
5. New AI-tell regressions, immutable changes, trailer mismatch, provenance mismatch, or target-resolution mismatch fail the gate.
6. Structural metrics with zero or insufficient denominators remain diagnostic only; no structural headline is allowed.

Stage 3 acceptance requires independent-session evidence for preservation, rule direction, immutable guards, trailer semantics, target resolution, and explicit structural-coverage status.

## 6. Stage 4 — Persist the regression suite

Repository structure:

```text
evals/
  fixtures/
  cases/
  run_all.py
```

Requirements:

1. Synthetic fixtures contain no real manuscript text.
2. Every case declares input, expected result, assertion method, synthetic provenance, and `evidence_class: self-authored-fixture`.
3. `run_all.py` uses only the standard library and system temporary storage.
4. It must run from any working directory and must not require network access, an installed skill, private `.helicon/`, or external binaries.
5. Exit codes are `0` for all assertions satisfied, `1` for a regression failure, and `2` for a harness/schema failure.
6. Output must state `pipeline_runnable:true` and `capability_validated:false`.
7. Real-data artifacts and metrics do not enter fixtures.
8. The suite must run in a clean Git clone after the implementation is committed.
9. Installers exclude `.helicon/`, caches, `evals/`, and `handoff/` from runtime skill payloads.

## 7. Stage 5 — Produce the handoff

Required repository artifacts:

- `handoff/ROUND_3_HANDOFF.md` — human-readable report;
- `handoff/round_3.json` — machine-readable source of truth;
- `handoff/INDEX.md` — round index.

Required JSON fields:

```text
round
branch / head_commit / base_commit
taskbook
tasks[]
  id
  status: done | partial | blocked | skipped
  evidence[]
    command
    exit_code
    key_output
    evidence_class
  note
unverified_claims[]
  claim
  why_unverified
  how_to_verify
deviations[]
  what / why / impact
open_questions[]
  question / options / recommendation
metrics{}
privacy{}
  files_read[]
  private_outputs[]
  repo_contamination_check
reproduce[]
next_round_candidates[]
  item / reason / priority
```

JSON and Markdown must agree; JSON controls. A `done` task requires at least one evidence record. Sanitized handoff content may contain counts, schemas, rule IDs, hashes, exit codes, paths represented by aliases, and distance values. It may not contain manuscript excerpts, reviewer wording, system names, experimental values, parameter values, target-profile values, or submission identifiers.

## 8. Iteration protocol

1. Round 3 produces `handoff/round_3.json`.
2. An external auditor clones the committed revision and executes `reproduce[]`.
3. The auditor behavior-tests every `unverified_claim`.
4. The next taskbook must answer every open question and unverified claim, or explicitly carry it forward.
5. `handoff/INDEX.md` records round, taskbook, commit, status, and outstanding-item counts.

## 9. Stop-point report

At the end of each stage report:

- task status and evidence class;
- newly added unverified claims;
- deviations and open questions;
- whether the next stage is safe and why.

Stop for author confirmation before entering the next stage.

## 10. Red lines

1. Never place manuscript text, reviewer text, profile values, exemplar cards, or direction reports in the repository.
2. Do not modify or move any original source file.
3. Do not enter Stage 2 before extraction QC and author confirmation.
4. Hold-outs are selected before target construction and never reduced to manufacture coverage.
5. Stage 3 uses an independent task.
6. Self-authored fixtures never count as capability validation.
7. Source attribution labels supplied by the author are not inferred or changed.
8. Page-budget changes are not counted as reviewer or author preference without evidence.
9. Reviewer-pattern candidates require a separate author-approved promotion round.
10. Synthetic fixtures and harnesses remain in `evals/` once committed.
11. Every unsupported conclusion enters `unverified_claims`.
12. Scripts remain standard-library only; optional legacy fallbacks are preserved.
