# Language Polish for FHE and Security Papers

This reference distills general academic editing patterns into HElicon's domain rules. It does not reproduce any external skill text. Apply it only after claims, structure, and terminology are stable.

## Hard preservation rules

- Terminology consistency outranks lexical variety. Resolve terms through `bilingual_glossary.md` and `fhe_lexicon_freeze.md`.
- Preserve evidence-bound hedging such as `suggests`, `is consistent with`, `we conjecture`, and `appears to`. Replacing it with `shows` or `proves` can create an overclaim.
- Passive voice is normal in Construction, Protocol, and Methods prose when the actor is irrelevant.
- First-person plural `we` is standard academic usage; do not remove it mechanically.
- Preserve theorem, lemma, definition, security statement, and reduction wording verbatim unless the user explicitly requests a formal correction.
- Preserve logical connectors and reasoning markers. Never delete one without restoring the relation through a replacement connector, a backward reference, or syntactic restructuring.
- Do not add opinions, anecdotes, emotional color, personal experience, or a separate "humanity" pass. Security papers require precise scholarly voice, not manufactured personality.

threshold: use no more than 3 em dashes per 1000 words, and never use an em dash as a substitute for a colon or semicolon.

## P4: Rhythm

P4 changes syntax and cadence, not terminology or meaning.

- Measure sentence lengths before editing. A paragraph with nearly equal lengths or repeated subject-verb openings is a candidate, not an automatic error.
- Alternate compact claim sentences with longer explanatory or qualifying sentences when the logic supports it.
- Move a condition to the front, combine closely dependent clauses, or split a clause stack at a genuine reasoning boundary.
- Vary openings among subjects, conditions, contrasts, and scoped transitions. Do not vary a defined technical term merely to vary the opening.
- After restructuring, check that each pronoun and discourse marker still has an unambiguous antecedent.

## P5: Numbered audit rules

These identifiers are the source of truth for `scripts/check_ai_tells.py`. A match is a warning for contextual review, not permission to rewrite blindly.

1. **Inflated importance.** Flag unsupported `groundbreaking`, `transformative`, `pivotal`, `remarkable`, and broad claims of significance.
2. **Unscoped performance adjectives.** Flag `significantly`, `dramatically`, `practical`, `scalable`, and `secure and efficient` unless the nearby text states the metric, workload, hardware, or threat model that earns the term.
3. **Domain-invalid phrases.** Flag `technical packaging`, `large model privacy inference`, `homomorphic realization`, and `full homomorphic encryption`; use the glossary's scoped form.
4. **Filler AI vocabulary.** Review decorative uses of `delve`, `tapestry`, `landscape`, `showcase`, `seamless`, `intricate`, `leverage`, and `underscore`. Keep a term if it has a precise technical sense.
5. **Connective stacking.** Reduce clusters such as `Moreover, furthermore, additionally` while retaining the actual logical relation.
6. **Dummy-subject framing.** Replace `It is important to note that` and similar shells with the supported claim, unless the construction carries real information structure.
7. **Nominalization overload.** Prefer an explicit actor and action when chains of abstract nouns hide who performs an operation. Do not rewrite established terms such as `key switching`.
8. **Paraphrastic repetition.** Remove a second sentence that merely restates the same claim with `in other words`, `that is`, or `essentially`; retain a formal definition or necessary disambiguation.
9. **Hedge imbalance.** Remove stacked empty hedges, but never strengthen a claim beyond its evidence label or delete uncertainty required by approximate computation.
10. **Pseudo-depth participles.** Review trailing `-ing` clauses that claim importance without mechanism, evidence, or a clear grammatical subject.
11. **Copula avoidance.** Prefer `is` or `has` over decorative `serves as`, `stands as`, or `boasts`; preserve formal role statements where the distinction matters.
12. **Negative parallelism.** Replace slogan-like `not only X but also Y` with the direct relation unless the contrast is logically necessary.
13. **Rule-of-three padding.** Keep exactly as many items as the contribution or experiment contains; do not manufacture a third item for cadence.
14. **Punctuation mannerism.** Enforce the em-dash threshold and use colons, semicolons, parentheses, or sentences according to their actual grammatical function.

Rules 1 through 3 subsume the nine phrases previously surfaced by `check_style_rules.py`; do not maintain a competing vocabulary list.

## P6: Voice

Load only the structural fingerprint relevant to the target section. Compare sentence-length distribution, paragraph-opening pattern, connective density, active/passive balance, first-person usage, and preferred contribution or limitation moves.

Use the fingerprint as a correction vector, not a prose generator. Change only metrics that materially depart from a qualified baseline. The only positive lexical imitation source is the author-supplied `Expressions the user likes` field. A thin baseline is directional only and cannot trigger a drift warning.

## Pass report

For P4, P5, or P6, report the pass identifier, locations changed, rule identifiers involved, immutable-set result, and any upstream issue noticed but not repaired. `H-POLISH` reports these separately for attribution.
