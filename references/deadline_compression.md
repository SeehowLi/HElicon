# Deadline Compression

## Highest-risk failure

The most dangerous compression error is deleting threat-model qualifiers or claim-scope words. A manuscript can meet the page limit while becoming materially overclaimed. During compression, these qualifiers enter the immutable set. They may not be deleted. A complete detail may move to an appendix only when the main text retains an accurate pointer and enough scope to prevent misreading.

## Candidate actions

| Action | Typical target | Claim-integrity risk |
|---|---|---|
| Delete | Repeated motivation, duplicate result narration, redundant roadmap | Low when truly redundant |
| Merge | Paragraphs with the same rhetorical job or repeated setup | Medium; preserve distinct qualifications |
| Move to appendix | Derivation detail, extended ablation, secondary implementation detail | Medium to high; keep the main-text contract and pointer |
| Rewrite compactly | Clause-heavy explanation, repeated definitions, verbose transitions | High; immutable-set validation is mandatory |

Every candidate receives an action and risk label before editing. Page pressure is not evidence that a claim or threat-model statement is expendable.

## Fixed order

1. Delete redundant restatement.
2. Merge paragraphs with the same function.
3. Move supporting detail to an appendix while retaining the main-text pointer.
4. Only then compress inside sentences.

This order mirrors the revision pipeline: settle semantic scope and structure before local wording. Re-run claim and LaTeX guards after each batch, and report any text that could not be compressed without changing meaning.

## Never compress silently

- adversary capability, corruption timing, leakage boundary, and trust assumption;
- claim qualifiers such as workload, hardware, parameter regime, baseline, and measured metric;
- theorem assumptions or the distinction between proven and empirical statements;
- limitations needed to interpret evaluation results.

If the target cannot be reached safely, return the remaining page delta and the least harmful unresolved candidates. Do not make the gate look green by hiding risk.
