# Language Polish for FHE and Security Papers

This reference distills general academic editing patterns into HElicon's domain rules. It does not reproduce any external skill text. Apply it only after claims, structure, and terminology are stable.

## Hard preservation rules

- Terminology consistency outranks lexical variety. Resolve terms through `bilingual_glossary.md` and `fhe_lexicon_freeze.md`.
- Preserve evidence-bound hedging such as `suggests`, `is consistent with`, `we conjecture`, and `appears to`. Replacing it with `shows` or `proves` can create an overclaim.
- Passive voice is normal in Construction, Protocol, and Methods prose when the actor is irrelevant.
- First-person plural `we` is standard academic usage; do not remove it mechanically.
- Preserve theorem, lemma, definition, security statement, and reduction wording verbatim unless the user explicitly requests a formal correction.
- Preserve logical connectors and reasoning markers. Never delete one without restoring the relation through a replacement connector, a backward reference, or syntactic restructuring.
- Preserve negation, modality, quantifier scope, comparison direction, and claim-strength markers during P3-P7. Only an explicit P1 target may authorize a scoped change, which must then be passed deliberately to `latex_guard.py --allow`.
- Do not add opinions, anecdotes, emotional color, personal experience, or a separate "humanity" pass. Security papers require precise scholarly voice, not manufactured personality.

threshold: use no more than 3 em dashes per 1000 words, and never use an em dash as a substitute for a colon or semicolon.

## P4: Rhythm

P4 changes syntax and cadence, not terminology or meaning.

Before P4, use `resolve_target_profile.py` and `revision_preflight.py` as required by `pass_pipeline.md`. Consume only `sentence_length`, `paragraph_length`, and `opening_structure`. Paragraph length and paragraph-opening distributions are not estimable from a one-paragraph selection; do not restructure a paragraph merely to manufacture those measurements. If no eligible P4 field violates its accepted band, P4 is a no-op.

- Measure sentence lengths before editing. Low variance alone is descriptive; it authorizes P4 only when paired with a repeated opening pattern, while a mean outside the public or screened range may trigger directly.
- Alternate compact claim sentences with longer explanatory or qualifying sentences when the logic supports it.
- Move a condition to the front, combine closely dependent clauses, or split a clause stack at a genuine reasoning boundary.
- Vary openings among subjects, conditions, contrasts, and scoped transitions. Do not vary a defined technical term merely to vary the opening.
- After restructuring, check that each pronoun and discourse marker still has an unambiguous antecedent.

## P5: Numbered audit rules

These identifiers are the source of truth for `scripts/check_ai_tells.py`. A match is a warning for contextual review, not permission to rewrite blindly.

Before P5, consume only the resolver's `connectives` and `hedging` fields and the numbered rule hits emitted by `revision_preflight.py`. A target density is a ceiling/direction, never a quota and never permission to add or delete a logical relation or an evidence-required hedge. With no numbered-rule hit and no field above its allowed boundary, P5 is a no-op; do not substitute synonyms merely to sound polished.

Rule 12's correlative `not only ... but also ...` is rhetorical, not semantic negation. `latex_guard.py` excludes that exact frame from its negation and quantifier-scope signatures so a meaning-preserving direct conjunction remains possible; other negation or `only` changes stay frozen.

1. **Inflated importance.** Flag unsupported `groundbreaking`, `transformative`, `pivotal`, `remarkable`, and broad claims of significance.
2. **Unscoped performance adjectives.** Flag `significantly`, `dramatically`, `practical`, `scalable`, `efficient`, and `secure and efficient` unless the same or adjacent sentence states the metric, workload, hardware, or threat model that earns the term. This same-or-adjacent-sentence exemption is deliberately conservative: number-dense Evaluation prose may suppress many rule 2 findings because nearby measurements provide scope. Treat that behavior as a precision choice, and use claim-evidence review rather than assuming rule 2 remains sensitive in such passages.
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

Rules 1 through 3 own their vocabulary in `check_ai_tells.py`. `check_style_rules.py` retains only non-numbered Chinese-literal and sentence-level overclaim patterns and must not maintain competing rule 1/2/3 terms.

## P6: Voice

Use the already resolved target profile and, separately, the structural baseline when available. P6 owns active/passive balance and first-person usage. Sentence rhythm belongs to P4, diction and hedging to P5, while claim position and contribution/limitation moves remain P2/upstream unless the author explicitly requests structural revision.

The target profile supplies direction for P4, P5, and P6. The baseline supplies drift detection only; a thin baseline emits no warning and cannot refuse a pass. A field marked `source: rule` follows this reference rather than the exemplar. Use target values as a correction vector, not a prose generator. Positive lexical imitation remains limited to author-confirmed `Expressions the user likes` candidates from the revision-direction workflow.

## Pass report

For P4, P5, or P6, report the pass identifier, locations changed, rule identifiers involved, immutable-set result, and any upstream issue noticed but not repaired. `H-POLISH` reports these separately for attribution.
