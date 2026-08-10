# HElicon

HElicon is a long-term research-writing mentor skill for English security and systems papers in fully homomorphic encryption (FHE/HE), privacy-preserving computation, private inference, encrypted search/kNN, and related algorithmic or systems work.

This repository contains the HElicon skill core only. It does not contain project facts, raw PDFs, paper drafts, extracted paper text, or private project workspaces.

Current snapshot: `HElicon v1.2`.

## What HElicon Does

- Converts Chinese research intent into natural English paper prose.
- Diagnoses paper story, positioning, title, abstract, introduction, related work, contribution framing, and evaluation narrative.
- Enforces FHE/security terminology discipline and claim-evidence consistency.
- Distills selected papers into reusable writing patterns without copying source sentences.
- Maintains a controlled memory-patch loop for stable writing preferences and reusable lessons.
- Separates reusable writing knowledge from direction-specific knowledge and project-specific facts.
- Supports project-aware `H-*` short commands for discussion, positioning, drafting, decision logging, patching, sync, repair, and reopening.
- Keeps project memory compact through overwrite-style `H-SYNC`, where stale decisions, risks, and revision tasks are deleted or archived instead of appended forever.
- Provides scripts for PDF text extraction, personal style pack preparation, FHE/HE corpus collection, and core contamination checks.

## Knowledge Layers

HElicon uses three layers:

1. `references/`: stable core memory for long-term writing principles, terminology, venue expectations, FHE framing, reviewer-risk checks, and cross-paper patterns.
2. Direction packs: focused external writing knowledge for areas such as private LLM inference, encrypted kNN/search, FHE systems, and FHE algorithm optimization.
3. Project packs: external project-specific facts for a single paper or project.

Project facts must stay in project packs. Direction-specific details should stay in direction packs unless they become stable cross-direction writing rules.

## Distilled Source Bibliography

The papers used as sources for HElicon distilled writing patterns are listed in [`provenance/distilled_sources.bib`](provenance/distilled_sources.bib).

This BibTeX file is provenance only: it identifies which papers informed the reviewed distilled cards. It does not contain raw paper text, paper-card content, project facts, or extracted PDF text.

## Paper Pipeline

Use this closed loop for normal paper work:

```text
H-DISCUSS -> H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC
```

Use `H-DISCUSS` for idea pressure-testing. Use `H-POSITION` for story, venue fit, contribution hierarchy, and claim boundaries. Use `H-DRAFT` for local prose candidates. Use `H-PATCH` only after the target text is confirmed. Use `H-SYNC` after decisions or patches so the project state stays compact.

For revision or rebuttal, repeat the same loop with reviewer evidence:

```text
H-REVIEW -> H-REOPEN if needed -> H-DISCUSS/H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC
```

## Evidence-Driven Revision System

Project packs should include:

- `claim_ledger.md`
- `evidence_matrix.csv`
- `revision_queue.csv`
- `reviewer_risk_log.md`

`H-REVIEW` generates reviewer risks and revision-queue candidates. `H-DECIDE` locks claim/evidence state after confirmation. `H-SYNC` rewrites those files into current-state summaries and removes stale items.

## Install

User-level install:

```bash
mkdir -p ~/.agents/skills
cp -R HElicon ~/.agents/skills/HElicon
```

Repo-level install:

```bash
mkdir -p .agents/skills
cp -R HElicon .agents/skills/HElicon
```

Check integrity:

```bash
python ~/.agents/skills/HElicon/scripts/check_skill_integrity.py ~/.agents/skills/HElicon
python ~/.agents/skills/HElicon/scripts/check_core_contamination.py ~/.agents/skills/HElicon
```

Invoke in Codex:

```text
$HElicon
Please diagnose this paper's story and positioning before polishing sentences.
```

## Recommended External Workspace

Keep private materials outside the skill repository:

```text
HElicon_workspace/
|-- corpus/
|   |-- selected_papers/
|   |-- own_drafts/
|   `-- advisor_edits/
|-- distilled/
|   |-- paper_cards/
|   |-- unified_patterns/
|   |-- style_cards/
|   |-- fhe_2023_2026/
|   `-- batch_logs/
|-- personal_style_packs/
|   `-- user_papers/
|-- direction_packs/
|   |-- private_llm_inference/
|   |-- encrypted_knn_search/
|   |-- fhe_algorithm_optimization/
|   |-- fhe_systems/
|   `-- security_top_conference_writing/
`-- projects/
    `-- <project_name>/
```

Use `scripts/bootstrap_project_pack.py` to create a new project pack.

## How To Distill New Papers

1. Put the PDF into `HElicon_workspace/corpus/by_venue_year/<venue>/<year>/`.
2. Extract text with `scripts/extract_pdf_text.py` if needed.
3. Distill one paper card at a time into `HElicon_workspace/distilled/paper_cards_reviewed/` when the paper adds a distinct lesson.
4. After 5-10 similar papers, ask for a unified pattern card and write only the abstract reusable rule into `references/unified_paper_patterns.md`.
5. Keep project facts, raw text, ePrint IDs, and experiment numbers out of core memory.
6. Regenerate `provenance/distilled_sources.bib` from the reviewed registry when the batch changes.
7. Run `scripts/check_skill_integrity.py .` and `scripts/check_core_contamination.py .` before treating the update as stable.

## Safety Boundaries

Do not write these into HElicon core memory:

- project-specific facts from any external paper;
- raw PDF text or copied paper sentences;
- single-paper cards as if they were general rules;
- ePrint IDs, experimental numbers, or one-off benchmark claims;
- personal style updates unless they come from the user's own writing, accepted revisions, advisor edits, or explicit preferences.

## Version History

See `VERSION.md` and `CHANGELOG.md`.
