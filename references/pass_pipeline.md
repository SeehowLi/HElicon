# Seven-Pass Revision Pipeline

Use this file to select, order, and audit revision passes. A pass has one primary responsibility; later passes may not reopen earlier decisions silently.

## Ordered passes

| Pass | Responsibility | Must follow | Must not change |
|---|---|---|---|
| P1 claim | Align claim scope, qualification strength, and evidence labels | — | Numbers, citations, structure |
| P2 structure | Repair paragraph order, topic sentences, section boundaries, and cross-section transitions | P1 | Claims, numbers, terms |
| P3 term | Normalize terminology against the glossary | P2 | Claims, structure |
| P4 rhythm | Reshape sentence-length variation, clause structure, and long-short alternation | P3 | Terms, claims, numbers |
| P5 diction | Remove AI tells, inflated wording, connective stacking, dummy subjects, and nominalization overload | P4 | Terms, claims, numbers |
| P6 voice | Align prose with the author's measured style fingerprint | P5 | Terms, claims, numbers |
| P7 surface | Repair LaTeX hygiene, citation placement, and punctuation | P6 | All semantic content |

## Why this order is fixed

1. **P1 comes first.** Polishing a claim whose scope is about to change wastes work and can make an incorrect statement sound more credible.
2. **P2 precedes every language pass.** Do not polish a paragraph that may be moved or deleted.
3. **P3 precedes P4, P5, and P6.** Style editing rewards variation, but cryptographic terminology cannot be varied freely. Without a locked glossary, an editor may treat `ciphertext`, `encrypted value`, and `encoded input` as interchangeable even when they name different objects.
4. **P4 precedes P5.** P5 mostly removes material. Uniform deletion shortens sentences by similar amounts, lowers sentence-length variance, and weakens long-short alternation. Running P5 first leaves P4 less structure to reshape. In addition, deleting ornamental adverbs without concurrent syntactic restructuring can make detector-oriented rhythm measures worse. The smoke test records the observed variance change rather than treating this as intuition.
5. **P6 is the final language pass.** Voice alignment is fine calibration. General rhythm or diction edits performed afterward would erase it.
6. **P7 is last.** It is mechanical and may not revise meaning.

For P4, load at most three qualified exemplar cards matching the section type and rhythm-related rule context. For P5, load at most three cards matching the section type and triggered rule IDs. For P6, load at most three non-reviewer-driven cards matching the section type; use them as form anchors only, never as content sources.

## Pass references and target-field ownership

For every route containing P4, P5, or P6, run `scripts/resolve_target_profile.py` against the active paper directory before editing. The resolver validates the private profile, selects the active venue, returns only fields owned by the requested passes, and computes the trailer target state. If an authorized evaluation needs a durable audit record, use its privacy-safe `--trace-output`; a trace proves resolution, not causal influence on generated prose.

| Pass | Required context | Target fields owned | Permitted use | Explicit exclusions |
|---|---|---|---|---|
| P3 | project `local_glossary.md`; `bilingual_glossary.md`; `fhe_lexicon_freeze.md`; `language_polish.md` | none | normalize only against frozen terms | no synonym variation for style |
| P4 | `language_polish.md`; resolved target | `sentence_length`, `paragraph_length`, `opening_structure` | use sentence range and variance as a direction; vary clauses only at real reasoning boundaries; use paragraph metrics only on a multi-paragraph sample or when paragraph restructuring was explicitly authorized | do not add/delete claims; do not split/merge paragraphs merely to hit a number |
| P5 | `language_polish.md`; resolved target | `connectives`, `hedging` | remove documented tells; reduce connective density only above an explicit upper bound while preserving the relation; preserve evidence-bound hedges even when density differs | no point-density quota; no deletion of scope, mechanism, evidence, or required uncertainty |
| P6 | `personal_style_profile.md`; resolved target; qualified baseline when present | `active_passive_by_section`, `first_person` | align voice for the normalized section type; use baseline only for drift detection | no mechanical passive-to-active conversion and no invented first-person actor |
| P2/upstream | structural review | `claim_position`, `contribution_limitation_moves` | surface as a structural recommendation or execute only in P2 | never apply silently inside the bare P3 → P4 → P5 route |

For `source: exemplar`, treat the typed value as a correction direction, not a quota. For `source: rule`, ignore exemplar statistics and apply the policy value plus `language_polish.md`. If the sample cannot estimate a field—one paragraph for paragraph distributions, one sentence for rhythm, or a missing section type—exclude that field and report the limitation rather than forcing a change. The immutable set and evidence-bound hedging always outrank target convergence.

## Preservation preflight

For every route containing P4 or P5, run `scripts/revision_preflight.py` after target resolution and before generating prose. It measures only fields estimable from the supplied selection and runs the numbered P5 audit. A target value defines an acceptable band or a correction direction, not a quota and not a request for lexical variation.

- `preserve`: no eligible P4 boundary is violated and no P5 rule is triggered. P4 and P5 make no edit. On a bare P3 → P4 → P5 route, if P3 also finds no exact glossary mismatch, return the original selection verbatim and report zero changes. An orchestrated P6 remains a separate decision.
- `revise`: change only the pass responsibilities named by the preflight trigger IDs. A trigger authorizes a repair, not a general rewrite.
- Insufficient samples are excluded rather than treated as failures. In particular, a single paragraph cannot trigger paragraph-length or paragraph-opening edits.

The preflight JSON is a privacy-safe decision record: it may contain field IDs, rule IDs, counts, target status, and profile hashes, but never manuscript prose or private target values. It proves deterministic admission to editing; the immutable-set comparison still decides whether the resulting edit is safe.

## Immutable set

The immutable set contains:

- numbers together with adjacent units;
- keys inside `\cite*`, `\ref`, `\autoref`, `\eqref`, `\cref`, and `\label` commands;
- inline mathematics and the contents of mathematics environments;
- terms frozen by the project glossary and `fhe_lexicon_freeze.md`;
- figure and table labels, plus caption keys;
- negation, modality, quantifier scope, comparison direction, and claim-strength markers during P3-P7.

P1 may change claim-scope markers only when that change is the explicit pass target, and may change only the wording that scopes a numeric claim, never the number. P7 may move a citation to its supported clause, never change its key. Any unapproved immutable-set difference is a failed pass: report it, restore the prior text, and use `scripts/latex_guard.py` to identify the violation. The guard aligns markers only across sufficiently similar content-bearing scopes; an ambiguous match or radical paraphrase is conservatively unverifiable and therefore fails rather than guessing semantic equivalence. A model's claim that it preserved the set is not evidence.

Threat-model qualifiers, security semantics, and claim-scope terms become immutable during compression; see `deadline_compression.md`.

## Execution contracts

`H-PASS` runs exactly one pass and reports its single target. `H-POLISH` is an orchestrator and may run P3, P4, P5, and P6 in order, but it must emit a separate result and change count for every pass. Do not collapse the report into one attribution-free rewrite.

Before each pass:

1. load the smallest required references from the ownership table, resolve the target before P4/P5/P6, and run the preservation preflight before P4/P5;
2. snapshot the immutable set;
3. state the target and exclusions;
4. apply only a triggered pass, or record a deterministic no-op;
5. compare the immutable set and report any rollback.

### Mechanical verification contract

For every rewriting pass from P3 through P7, generate a candidate and run these checks in order before delivery:

1. Run `python -B scripts/check_immutable_set.py <BEFORE> <AFTER> --glossary <MERGED>`. Exit 0 continues; exit 1 is an immutable-set violation, so roll back the pass under Iron Rule 6 and report the categories and violation count in the trailer; exit 2 is an input or configuration error and must stop with a report rather than count as passing.
2. Run `python -B scripts/check_claim_strength.py <BEFORE> <AFTER>`. A positive `upward_move_count` or non-empty `crypto_upward_moves` rolls back the pass because claim-scope markers and claim strength are immutable outside an explicit P1 request. Report `crypto_downward_moves`, `crypto_relocations`, `crypto_upward_candidates`, and claim-scope relocation warnings in the trailer without blocking. During P1 only, an author-approved claim-scope adjustment may exempt an upward move from rollback, but every exempted move must be listed in the trailer; this exemption never applies to steps 1 or 3.
3. Run `python -B scripts/check_terminology_freeze.py <BEFORE> <AFTER> --glossary <MERGED>`. A blocking replacement rolls back P3 as a P3 failure or P4-P7 as downstream contamination and must be reported. A result containing only `case_inconsistency` findings is warning-only; its known capitalization boundary is recorded in `CHANGELOG.md`.
4. Run `python -B scripts/check_ai_tells.py --json <AFTER>`. Report density without blocking, preserving the existing P5 semantics.

Build `<MERGED>` with `python -B scripts/glossary_build.py --direction <DIRECTION> [--project <PACK>/local_glossary.md] -o <TMP>`. Resolve `<DIRECTION>` from `project.yaml`; when it is missing, omit `--direction` and use L0 only. When `local_glossary.md` is absent, omit `--project`, allowing `project_layer=absent`. Store `<TMP>` only in a temporary directory and delete it after delivery; never write it into the repository or project pack.

## Anti-drift rule

threshold: when no qualified target profile exists, if the target section's style metrics are already inside the personal baseline band of plus or minus 1.5 standard deviations, P5 and P6 refuse to run. Report: `already within baseline; further editing would create drift rather than improvement`.

This refusal is active only when the baseline contains at least the minimum document count defined in `style_baseline_policy.md`. With a thin baseline, do not issue drift warnings or refuse P5/P6. When a qualified target exists, movement toward that screened target is convergence rather than drift; the baseline may flag movement that approaches neither target nor baseline, but it cannot override the target direction. A target profile never activates anti-drift refusal by itself.
