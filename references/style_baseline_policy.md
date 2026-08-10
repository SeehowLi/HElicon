# Personal Style Baseline Policy

The personal baseline records the author's current structural habits. It is not automatically an ideal style and must not be confused with advisor preference.

## Available and missing evidence

There are no advisor-edited before/after pairs. Therefore the baseline cannot encode a verified direction of improvement from an advisor. It may describe the author's present habits only.

Multiple revisions of the same manuscript are valid self-edit pairs. Register every source version with the same `Paper ID` in `templates/style_sample_card.md`; mark the later self-edited item as `Version: revised`. Such a pair may indicate how the author tends to revise, but not how an advisor would revise.

## Confidentiality boundary

All source manuscripts are unpublished. Neither corpus text nor derived fingerprint JSON enters this repository. Store both only in the project-local layout defined by `project_memory.md`.

Repository voice and style files may contain schemas, generation methods, metrics, and pass integration rules. They must contain no sentence, project term, number, or result drawn from an author's manuscript. The core contamination check enforces this boundary.

## Qualification threshold

threshold: a quantitative baseline requires at least 5 distinct papers, identified by `paper_id`.

Several versions of one paper count as one document for qualification and variance: average their metrics inside the `paper_id` group before computing cross-paper statistics. Thus five versions of one manuscript remain `thin(n=1)`, not `thin(n=5)`.

With fewer distinct papers, the fingerprint is `thin(n=N)`: use it only as directional context, disable the P5/P6 anti-drift refusal, and issue no drift warning. The trailer must show `baseline:thin(n=N)`. A qualified baseline may show `baseline:ok`; no available baseline shows `baseline:none`.

The minimum prevents ordinary variation in a narrow sample from being misreported as personal-style drift.

## Eligible sections

Sample completed drafts only from:

- Introduction;
- Contributions;
- Related Work;
- Evaluation narrative.

Exclude Methods and Construction. Their conventions constrain prose too tightly to represent personal voice reliably.

## Metrics and use

Measure sentence-length distribution, paragraph-length distribution, opening patterns, connective density, active/passive balance, first-person use, and selected punctuation. Keep section types separate; do not compare an Evaluation paragraph directly with an Introduction baseline.

P6 uses metric differences as revision guidance. It must not reconstruct source prose or copy characteristic project terminology.

## Expressions the user likes

`Expressions the user likes` is the only profile field that permits positive lexical imitation. The author must supply or explicitly approve each entry. Record the expression, acceptable context, and any exclusion. Until material is provided, leave the field empty; never infer entries from unpublished drafts. Every other profile field is descriptive or restrictive and cannot by itself make text sound like the author.
