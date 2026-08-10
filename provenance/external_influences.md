# External Influences

This file records design influence, not copied text. HElicon's rules were independently rewritten for FHE and security papers.

## Sources checked

| Repository | License verified from repository | Influence adopted | Influence rejected or changed |
|---|---|---|---|
| [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic) | MIT; official `LICENSE` checked | Academic sentence-rhythm diagnosis, terminology consistency, and preservation of logical cohesion informed `language_polish.md`. | Rejected detector-score optimization as a product goal and replaced zero-tolerance em-dash removal with a scoped density rule. |
| [blader/humanizer](https://github.com/blader/humanizer) | MIT; official `LICENSE` checked | General warning categories such as inflated importance, filler, repetition, and formulaic syntax informed the P5 audit taxonomy. | Rejected casual voice injection, synonym cycling, blanket passive-voice removal, and prose rules not suited to formal security writing. |
| [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) | MIT; official `LICENSE` checked | Claim-evidence discipline, scholarly-convention preservation, and audit-before-rewrite influenced `language_polish.md` and `citation_discipline.md`. | Rejected any rule that could strengthen claims, alter citations without external verification, or treat one group's voice as universal. |

## Distillation boundary

No external examples or instruction passages are stored here. HElicon uses its own FHE examples, immutable-set contract, pass ordering, glossary, and security-semantics rules. External projects remain attribution sources, not runtime dependencies.
