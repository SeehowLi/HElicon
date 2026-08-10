# Draft Intake

Draft intake is a one-time triage for an existing manuscript. Its output is cached as `draft_map.md` so later local edits do not repeat a whole-paper diagnosis.

**Diagnosis is one-time, cached, and skippable; but skipping must leave a trace.**

## Inputs

- manuscript source and include graph;
- project glossary and evidence map, if present;
- target venue and current page state, if known;
- existing project memory under `.helicon/`.

Missing inputs stay `UNKNOWN`. Intake does not invent project facts or silently infer evidence.

## Per-section record

For every section, write:

1. **Structural verdict:** `STABLE`, `REWORK`, or `DELETE-CANDIDATE`, followed by one sentence of reasoning.
2. **Claim inventory:** each material claim with one existing evidence label: `SUPPORTED`, `PARTIAL`, `MISSING`, `RISKY`, `UNKNOWN`, `MISSING_EVIDENCE`, or `OVERCLAIM_RISK`.
3. **Terminology drift:** competing names for one construct and the proposed canonical form. Do not approve the form until checked against the glossary.
4. **Polish eligibility:** `YES`, `CONDITIONAL`, or `NO`, with the blocking upstream pass when applicable.
5. **Recommended pass sequence:** the smallest ordered subset of P1 through P7 that addresses the diagnosis.

## Intake procedure

1. Map source files to rendered sections without rewriting them.
2. Identify each section's rhetorical job and compare it with the actual content.
3. Register claims and evidence status before evaluating prose quality.
4. Record terminology variants without performing synonym replacement.
5. Assign polish eligibility and a pass sequence.
6. Save the result to the project-local path defined in `project_memory.md`.

Intake is diagnostic. It does not patch manuscript files.

## Cache and skip behavior

Reuse a draft map while its manuscript fingerprint still matches. When the source fingerprint changes materially, mark only affected sections stale rather than repeating the whole intake.

If the author skips intake, create the minimal `draft_map.md` entry with the timestamp, source fingerprint when available, and status `[no intake]`. Commands must continue to work, but reports include the marker until intake is completed.

## Output boundary

The draft map stores section-level decisions and identifiers, not a second copy of unpublished prose. It may quote only the minimum phrase needed to identify a claim or terminology conflict. All writes require the normal project-memory or `H-PATCH` authorization boundary.
