# Changelog

## v1.2

- Distilled a new security-venue FHE systems batch in the external workspace.
- Added an abstract `Security-Venue FHE Systems Paper` pattern to core without importing raw PDF text, single-paper claims, experiment numbers, or project facts.
- Regenerated distilled-source provenance BibTeX from the reviewed registry.
- Added Evidence-Driven Revision System project-pack files and command responsibilities.
- Standardized the paper pipeline as `H-DISCUSS -> H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC`, with revision/rebuttal repeating the same loop through `H-REVIEW` and `H-REOPEN` when needed.

## v1.1

- Promoted the project-aware short-command workflow to the official v1.1 snapshot.
- Changed `H-SYNC` into a compact global synchronization command that rewrites current project state and deletes or archives stale, contradicted, superseded, or duplicated memory.
- Bound confirmed `H-DECIDE` writes to a scoped `H-SYNC` plan so decision logs and trackers do not grow as append-only transcripts.
- Kept `H-LOG` as a compatibility command name while making it execute scoped `H-SYNC` semantics instead of independent long-form logging.
- Added compact project-memory structures for current decisions, open decisions, draft status, and sync archives.
- Added personal-paper anti-overfitting rules so the user's papers can teach abstract style without importing paper-specific terminology, method names, experiment numbers, datasets, or title logic into core.
- Added scripts for PDF text extraction, FHE/HE paper metadata and open-PDF collection, and core contamination checks.
- Preserved the v1.0.1 boundary that project facts, raw paper text, single-paper details, ePrint IDs, and experiment numbers must not enter core memory.

## v1.1-rc1

- Added project-aware `H-*` short-command dispatch to `SKILL.md`.
- Added `references/command_registry.md` with command contracts for `H-HELP`, `H-LOAD`, `H-ONBOARD`, `H-DISCUSS`, `H-DECIDE`, `H-TITLE-ITERATE`, `H-ABSTRACT-ITERATE`, `H-SECTION-ITERATE`, `H-REVIEW`, `H-PATCH`, `H-LOG`, `H-SYNC`, `H-SYNC-REPAIR`, and `H-REOPEN`.
- Generalized the short-command workflow from an external paper guide without copying project facts into HElicon core.
- Distinguished discussion, iteration, decision, patching, logging, synchronization, repair, and reopening responsibilities.
- Preserved the v1.0.1 boundary that project facts, raw paper text, single-paper details, ePrint IDs, and experiment numbers must not enter core memory.

## v1.0.1

- Wrote confirmed cross-direction paper-writing guidance into core references.
- Added metric-bound HE/FHE framing, claim-evidence review checks, and security top-conference story rules.
- Updated title, abstract, introduction, contribution, and technical-framing guidance from reviewed unified patterns.
- Updated direction-pack indexing while keeping focused direction knowledge outside the core skill.
- Kept project-specific facts, paper details, and personal style memory out of this update.

## v1.0-adjusted

- Reframed HElicon as a long-term personal research-writing mentor.
- Removed single-project facts from core memory.
- Added external project-pack and direction-pack workflow.
- Added unified paper-pattern distillation workflow.
- Added bilingual continuity and terminology-control policy.
- Added mentor-memory and memory-patch loop.

## v1.0-initial

- Initial FHE/security writing skill skeleton.
