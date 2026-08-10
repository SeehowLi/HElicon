# Citation Discipline

Evidence labels answer whether a claim has support. Citation labels answer whether the cited work exists and supports the specific attributed claim. Both are required.

## Citation labels

- `CITATION_UNVERIFIED`: the cited item or its support relation has not been checked against an external library.
- `CITATION_MISATTRIBUTED`: external verification found that the citation does not support the attributed statement at the required strength.

These labels join the existing evidence labels in `H-DISCUSS` and `H-REVIEW` outputs. They do not replace `MISSING_EVIDENCE` or `OVERCLAIM_RISK`.

## Authority boundary

Verify citations only against a real external collection supplied or authorized by the author: a Zotero library, bibliography files under project `provenance/`, or source PDFs held by the author. Never decide that a citation is real or correctly attributed from model memory. That would use an unverified recollection to validate another possible hallucination.

## Misattribution classes

1. **Nonexistent citation:** the bibliographic item cannot be found in the available external collection.
2. **Unsupported attribution:** the work exists but does not support the associated claim.
3. **Strength escalation:** the work is relevant but is cited for a stronger guarantee, scope, comparison, or causal statement than it establishes.

## Verification record

For each material claim, `evidence_map.csv` carries `citation_status` beside the evidence status. Use `VERIFIED`, `CITATION_UNVERIFIED`, `CITATION_MISATTRIBUTED`, or `NOT_APPLICABLE`; add a short source pointer in `source_or_file`.

Do not invent a replacement citation. If no authorized library is available, leave the label unverified and tell the author what source is needed.
