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

## Immutable set

The immutable set contains:

- numbers together with adjacent units;
- keys inside `\cite*`, `\ref`, `\autoref`, `\eqref`, `\cref`, and `\label` commands;
- inline mathematics and the contents of mathematics environments;
- terms frozen by the project glossary and `fhe_lexicon_freeze.md`;
- figure and table labels, plus caption keys.

P1 may change only the wording that scopes a numeric claim, never the number. P7 may move a citation to its supported clause, never change its key. Any other immutable-set difference is a failed pass: report it, restore the prior text, and use `scripts/latex_guard.py` to identify the violation. A model's claim that it preserved the set is not evidence.

Threat-model qualifiers, security semantics, and claim-scope terms become immutable during compression; see `deadline_compression.md`.

## Execution contracts

`H-PASS` runs exactly one pass and reports its single target. `H-POLISH` is an orchestrator and may run P3, P4, P5, and P6 in order, but it must emit a separate result and change count for every pass. Do not collapse the report into one attribution-free rewrite.

Before each pass:

1. load the smallest required references;
2. snapshot the immutable set;
3. state the target and exclusions;
4. apply the pass;
5. compare the immutable set and report any rollback.

## Anti-drift rule

threshold: if the target section's style metrics are already inside the personal baseline band of plus or minus 1.5 standard deviations, P5 and P6 refuse to run. Report: `already within baseline; further editing would create drift rather than improvement`.

This refusal is active only when the baseline contains at least the minimum document count defined in `style_baseline_policy.md`. With a thin baseline, use the fingerprint only as directional context, do not issue drift warnings, and do not refuse P5 or P6.
