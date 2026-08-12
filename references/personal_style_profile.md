# Personal Style Profile

This file should gradually become the user's writing profile. It starts sparse by design.

## Current defaults

- The user prefers rigorous, structured diagnosis over excessive praise.
- The user wants Chinese discussion but English paper prose.
- The user values paper story, positioning, title, abstract, technical framing, and precise terminology.
- The user dislikes strange literal translations and generic AI academic prose.
- The user wants HElicon to behave like a long-term mentor who understands their research direction and feedback over time.

## To learn from future interactions

Append stable observations under these headings:

### Preferred introduction moves

- Prefer introductions that first make the reviewer understand the deployment or evaluation obstacle, then introduce the technical mechanism as a response to that obstacle.
- Avoid opening with a dense primitive description before the paper-level problem and bottleneck are visible.

### Preferred contribution style

- Prefer contribution lists that bind each contribution to a bottleneck, a measurable consequence, and a bounded claim.
- Contributions should avoid sounding like an implementation inventory; they should explain why each technical step matters to the paper story.

### Preferred title/abstract style

- Prefer titles and abstracts that expose the task, technical setting, and main capability without relying on an acronym alone.
- Abstracts should be incremental and evidence-aware: preserve working logic when revising, and mark claims that still need support.

### Preferred related-work style

- Prefer related-work contrast organized by assumptions, functionality, leakage/threat model, and evaluation regime rather than by paper-by-paper summary.

### Preferred evaluation narrative style

- Prefer evaluation narratives that state the question being answered before presenting numbers, and that connect each metric to the claim it validates.

### Expressions the user likes

- Leave empty until `extract_revision_direction.py` finds an expression unchanged across all declared stages and the author explicitly confirms it.
- For each confirmed unchanged candidate, record the expression, acceptable rhetorical context, and exclusions.
- This is the only profile field that permits positive lexical imitation; all other fields are descriptive or restrictive.

### Expressions the user rejects

- Generic AI academic filler.
- Literal translations that sound unnatural in English security papers.
- Broad claims such as "practical", "large-scale", "end-to-end", or "secure" when the exact scope is not stated.

### Recurring weaknesses to check

- Check whether a strong claim is ahead of the available evidence.
- Check whether a local technical improvement has been promoted into a paper-level contribution without an end-to-end or workload consequence.
- Check whether terminology from one project is being reused too rigidly in another project.

### Advisor-style reminders

- First decide the story and evidence boundary; then polish sentences.
- Keep personal-paper style lessons abstract. Do not import project-specific terminology, method names, datasets, experiment numbers, or title logic into core memory.

### Quantitative baseline

- Store the local fingerprint at `<paper_dir>/.helicon/style/fingerprint.json`; never commit it to this skill repository.
- Generate it with `scripts/style_fingerprint.py baseline` from the eligible section classes in `style_baseline_policy.md`; assign revisions of the same manuscript the same `paper_id`.
- P4 reads the resolved target's sentence-length, multi-paragraph length, and paragraph-opening fields; unestimable fields are excluded rather than forced.
- P5 reads the resolved target's connective and hedging fields plus punctuation density and terminology-variation candidates as warnings rather than rewrite instructions.
- P6 reads the resolved target's section-normalized active/passive and first-person fields; it reads section-matched baseline deviations only for drift detection.
- A thin baseline is descriptive only: it cannot produce a drift warning, refuse a pass, or define a revision target.

### Prescriptive target

- Store screened target values and filled exemplar cards only under `<paper_dir>/.helicon/style/`.
- Follow `target_profile_policy.md`: target values guide P4/P5/P6, while the baseline remains a separate drift detector.
- Never use a reviewer-driven stage pair as an author-preference signal unless the author explicitly reclassifies it.
