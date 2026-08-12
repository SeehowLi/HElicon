# HElicon Round 4 Taskbook — Independent Evidence Closure

This repository-safe taskbook is self-contained. It binds inherited Round 3
items to the committed source record at
`a52366983621b6481284f0c9a09f9fe3a866f2d8:handoff/round_3.json` and never
copies private manuscript text, reviewer wording, target values, or local
paths into the repository.

## 1. Starting point and current authorization

Round 4 starts as `partial`.

Fixed Round 3 repository identities:

- implementation commit: `230dc4ddbedccb8fe263b4180d0b110dc6961bcf`;
- handoff and externally audited checkout commit:
  `a52366983621b6481284f0c9a09f9fe3a866f2d8`;
- checkout parent: `230dc4ddbedccb8fe263b4180d0b110dc6961bcf`;
- public origin: `https://github.com/SeehowLi/HElicon.git`.

The author currently authorizes only R4-0 and R4-1 as one public-repository
bundle. Complete both, report the stop point, and wait. This authorization
does not permit:

- reading any private manuscript, private `.helicon/` pack, private target,
  private evaluator output, or reviewer material;
- reading or updating the live installed skill;
- installation, restore drills, merge, tag, push, or publication;
- entering R4-2 or any later stage.

Round 3 history is immutable. New evidence may close or supersede a claim but
must not be backfilled as proof of an unrecoverable historical event.

## 2. Evidence model

Round 4 uses `helicon-handoff-v2`. Every command-bearing evidence record has:

- globally unique `id`;
- `command`, actual `exit_code`, `executed_utc`, and sanitized `key_output`;
- `input_manifest_sha256` and captured `output_summary_sha256`;
- `data_provenance`;
- `execution_provenance`;
- `target_provenance`;
- `human_review`;
- `claim_domain` and `claim_scope`.

The top-level `evidence_hash_policy` binds every evidence ID exactly once to
one of: captured combined stdout/stderr, recomputable sanitized key output, or
an external-audit attestation. `generated_utc` must not precede any contained
execution, attestation-record, or decision time. A source that did not report
its execution time is recorded as `executed_utc:null` plus
`execution_time_status:not-reported-by-source`; no time is invented.

An external audit attestation additionally records the exact reported command
list, per-command exit codes, the time at which the attestation was captured,
and a hash of its sanitized key output. It remains an attestation rather than
raw retained logs.

The axes are independent. In particular, `independent-session` describes only
who executed a check; it never upgrades synthetic data to real data or an
AI-assisted target to independent ground truth.

Allowed data provenance:

- `synthetic`;
- `private-real-data`;
- `repository-metadata`.

Allowed execution provenance:

- `builder-session`;
- `independent-session`.

Allowed target provenance:

- `none`;
- `qualified-original`;
- `author-approved-ai-assisted`;
- `synthetic-oracle`.

Allowed human review:

- `none`;
- `author-attested`;
- `independent-human-reviewed`.

Allowed claim domains:

- `repository`;
- `corpus`;
- `target`;
- `evaluation`;
- `privacy`;
- `install`.

Allowed claim scopes:

- `repository-integrity`;
- `corpus-qc`;
- `authority-approval`;
- `revision-attribution`;
- `privacy-review`;
- `pipeline-only`;
- `evaluator-only`;
- `preservation`;
- `rule-direction`;
- `structural`;
- `fixture-provenance`;
- `install-rollback`.

A `done` task requires evidence that directly matches its claim domain and
scope. Field presence alone is not evidence truth.

## 3. Canonical Git-blob digest

Repository digests use committed Git blob bytes, not checkout bytes affected
by `core.autocrlf`.

For a named commit and subtree:

1. enumerate tracked blobs at that commit;
2. use subtree-relative POSIX paths encoded as UTF-8;
3. sort by raw path bytes;
4. compute SHA-256 over each raw blob;
5. append `<lowercase-sha256>  <relative-path>\n` for each path;
6. SHA-256 the UTF-8/LF manifest.

The manifest file itself is excluded when a later stage creates a fixture
manifest, avoiding self-reference. Record commit, file count, blob byte count,
manifest byte count, and digest.

## 4. R4-0 — Public repository baseline

Fresh-clone the GitHub origin without local-object reuse. Record Git and Python
versions, origin, branch, checkout commit, parent, remote `main`, and the
canonical Git-blob input manifest.

Required checks:

1. checkout and `origin/main` resolve to the audited checkout commit;
2. it has the declared sole parent;
3. parent-to-checkout changes are limited to five `handoff/` files;
4. no local Git object alternate is present;
5. no `.helicon/` pack is present;
6. run all Round 3 public reproduce commands and record every exit code;
7. confirm the checkout remains clean and has no Python cache artifacts;
8. remove the temporary clone after evidence capture.

R4-0 evidence produced by the current builder remains `builder-session`.
Round 3 U08 is closed by the author-supplied external independent audit and is
corroborated, not independently recreated, by R4-0.

Synthetic regression output must retain:

- `pipeline_runnable: true`;
- `capability_validated: false`;
- `claim_scope: pipeline-only` or `evaluator-only`.

The target-to-output copy in the synthetic evaluator case is recorded as
`target_provenance: synthetic-oracle` and
`generation_path_exercised: false`. It validates the evaluator and guards, not
HElicon's ability to generate improved prose.

## 5. R4-1 — Handoff schema and policy validator

Add stable IDs:

- inherited claims: `R3-U01` through `R3-U10`;
- inherited questions: `R3-OQ01` through `R3-OQ03`;
- Round 4 tasks: `R4-*`;
- evidence: `R4-E*`;
- decisions: `R4-D*`;
- new unverified claims: `R4-U*`;
- new questions: `R4-OQ*`.

Every one of the 13 inherited items receives exactly one disposition. The
committed Round 3 JSON blob is hash-pinned, and `source_index` binds each stable
ID to its exact array entry under the `array-order-v1` rule:

- `closed`;
- `carried-forward`;
- `retired-known-gap`;
- `blocked`;
- `reframed-and-tested`.

All evidence and decision references must resolve. Evidence must match the
item's claim domain and scope and have exit code zero. A closed or
reframed-and-tested factual claim must cite direct evidence; a closed question
must cite an explicit author decision. Decision-only closure is not allowed for
a factual claim.

The validator must reject:

1. synthetic-only evidence attached to a capability claim;
2. `capability_validated: true` derived from repository fixtures;
3. synthetic-oracle evaluator evidence represented as generation evidence;
4. a structural headline unless eligible observations are at least 6,
   scorable observations are at least 5, coverage is at least 80%, zero
   denominator cases are zero, and aggregate is non-null;
5. duplicate or dangling IDs;
6. a missing or duplicated inherited disposition;
7. ambiguous `head_commit` semantics in v2;
8. malformed, missing, non-ancestral, or incorrectly parented commit objects;
9. a worktree-EOL hash represented as a canonical Git-blob digest;
10. a `done` capability task without matching private-real-data and
    independent-session evidence for every declared capability scope;
11. malformed task, evidence, or decision IDs;
12. evidence or decisions later than `generated_utc`;
13. a shrunken policy-bundle path set or a Git-blob manifest not anchored to
    the audited checkout;
14. an inherited disposition supported by evidence from an unrelated domain
    or scope.

Validator output separates:

- `schema_valid`;
- `policy_consistent`;
- `repository_metadata_verified`;
- `evidence_truth_verified`, which remains `false` because a repository
  validator cannot prove human judgments or semantic truth.

Add standard-library negative selftests for capability-scope escalation,
unsupported structural positive claims, insufficient coverage, unrelated
disposition evidence, missing independent U08 support, malformed IDs/commits,
future-dated evidence, shrunken candidate manifests, checkout drift, and source
index drift. Preserve Round 3 validation; do not rewrite Round 3 JSON or
Markdown.

Round 3 Iteration Protocol task status was too broad: an index existed, but
most private claims had not been behavior-tested. Record it in Round 4 as
`superseded-partial`; do not edit the historical record.

## 6. Inherited-item decisions

Round 4 binds the exact inherited statements through the committed Round 3
JSON and its recorded blob SHA-256.

Required dispositions:

- U01: carry forward for dated Round 4 visual-QC confirmation;
- U02: carry forward and reframe as approval under declared criteria;
- U03: carry forward as aggregate `confirmed|changed|unknown` adjudication;
- U04: retire the unrecoverable historical-order claim and create a forward
  manifest-before-computation successor;
- U05: carry forward as bounded human privacy/content review;
- U06: retire the unsupported historical summary-field claim and create a new
  command-bearing process-evidence successor;
- U07: block until preregistered structural coverage is sufficient;
- U08: close using the author-supplied external audit plus repository
  corroboration;
- U09: carry forward as a bounded fixture-provenance review;
- U10: block pending separately authorized disposable install/restore work.

The three inherited questions are closed by explicit author decisions:

- add sanitized Stage 1 and Stage 2 summaries;
- expand structural evaluation only under preregistered admission and coverage
  gates;
- keep reviewer-pattern candidates private throughout Round 4.

## 7. R4-2 — Stage 1 sanitized evidence

Requires new authorization and private access. Reconfirm, rather than backfill,
the extraction QC and authority decision. Record hashes, command exit codes,
dimension verdicts, reviewer role, timestamp, and author decision without any
manuscript excerpt or private identifier. Stop for author confirmation.

## 8. R4-3 — Stage 2 chronology, attribution, and privacy

Requires new authorization and private access. Freeze the complete hold-out
manifest before any isolated rebuild; compare outputs; adjudicate venue and
page-budget attribution with stable private IDs; keep unknown signals out of
preferences; perform bounded reviewer-pattern privacy review. Never infer
historical chronology from current mtimes. Stop for author confirmation.

## 9. R4-4 — Independent Stage 3 replay

Requires a new independent task and explicit authorization. Before generation,
the task must not inspect blind targets or evaluator internals. An outer
wrapper persists command, actual OS exit code, evaluator/input/target/summary
hashes, and timestamp. Retire the old historical-exit-code claim rather than
rewriting it. Stop for author confirmation.

## 10. Optional structural-evidence track

Requires separate authorization. Freeze the candidate universe, admissions,
exclusions, metrics, and coverage before output selection. Minimum gate:

- eligible observations at least 6;
- scorable observations at least 5;
- coverage at least 80%;
- zero zero-denominator cases.

Failure keeps `status: insufficient-coverage`, aggregate `null`, and no
structural capability headline. Never shrink hold-outs or relax immutable
guards to manufacture coverage. Stop for author confirmation.

## 11. R4-5 — Fixture provenance and canonical hashing

Requires separate authorization. Create a Git-blob canonical fixture inventory
with deterministic-generation description or author attestation, independent
review metadata, and bounded authorized-corpus overlap results. Continue to
state that 5/5 proves regression runnability only. Stop for author confirmation.

## 12. R4-6 — Disposable installed-payload restore drill

Requires separate explicit authorization. Do not touch the live skill. Install
only into disposable targets, establish manifest parity, create a current
backup, damage only the disposable target, restore it, and recheck full parity
and public tests. Confirm `.helicon/`, caches, `evals/`, and `handoff/` remain
excluded. Stop for author confirmation.

## 13. Required Round 4 handoff artifacts

- `handoff/HELICON_ROUND4_TASKBOOK.md`;
- `handoff/round_4.json`, the machine-readable source of truth;
- `handoff/ROUND_4_HANDOFF.md`;
- updated `handoff/INDEX.md`;
- upgraded `handoff/validate.py`.

The Round 4 containing commit is `null` until publication. It cannot embed its
own hash; after publication, an external audit resolves it from checkout
`HEAD`. Keep `implementation_commit`, `handoff_commit`, and
`audited_checkout_commit` explicit.

## 14. Stop-point format

At each stop report:

- task status and all provenance axes;
- command, exit code, input and output hashes;
- inherited dispositions changed in the stage;
- new unverified claims, deviations, and open questions;
- cleanup performed and retained artifacts;
- whether entering the next stage is authorized and safe.

R4-0 and R4-1 may run consecutively under the current authorization. Stop
after R4-1. Every later stage requires a separate confirmation.

## 15. Red lines

1. Never treat synthetic regression as capability validation.
2. Never infer historical ordering from a new rebuild or filesystem time.
3. Never infer process exit code from `run_completed`.
4. Never treat independent execution as real-data provenance.
5. Never use raw third-version prose as style-only ground truth.
6. Never relax immutable, hold-out, privacy, or structural coverage gates.
7. Never put manuscript text, reviewer wording, profile values, targets, or
   private identifiers in the repository.
8. Never promote reviewer-pattern candidates in Round 4.
9. Never test installation or rollback against the live skill.
10. Never enter a private stage without the author confirming that stop point.
11. Scripts remain standard-library only; existing optional fallbacks remain.
