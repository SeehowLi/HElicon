# Local Style Baseline

This directory stores unpublished source samples and derived fingerprints. Neither belongs in the HElicon skill repository.

## Evidence currently available

- No advisor-edited before/after pairs are assumed. The baseline describes current author habits, not an advisor-approved ideal.
- Multiple drafts of the same paper may form self-edit pairs. Give them the same `Paper ID` and register the later item as `Version: revised` in `templates/style_sample_card.md`.
- Keep corpus files and `fingerprint.json` local to this paper.

## Eligible sampling

Use completed-draft prose from Introduction, Contributions, Related Work, and Evaluation narrative. Do not sample Methods or Construction, whose conventions mask personal style.

## Build and use

Run `scripts/style_fingerprint.py baseline` with an explicit local output path and `--paper-id` metadata. One `--paper-id` applies to all selected files; otherwise repeat it once per resolved input file. Compare section types with the same section type. Sentence rhythm informs P4, diction-adjacent structural measures inform P5, and qualified baseline deviations inform P6.

A quantitative baseline needs the minimum distinct-paper count declared in `references/style_baseline_policy.md`. Versions sharing a `paper_id` are averaged and count once. Below that minimum, mark it `thin(n=N)`, use it only directionally, disable drift alerts and anti-drift refusal, and show the thin status in the trailer.

## Positive imitation boundary

Only author-supplied, explicitly approved entries in `Expressions the user likes` permit positive lexical imitation. Do not infer expressions from these unpublished samples.
