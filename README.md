# HElicon

HElicon is a long-term research-writing mentor skill for English security and systems papers in fully homomorphic encryption (FHE/HE), privacy-preserving computation, private inference, encrypted search/kNN, and related algorithmic or systems work.

This repository contains the HElicon skill core only. It does not contain project facts, raw PDFs, paper drafts, extracted paper text, or private project workspaces.

Current snapshot: `HElicon v1.0.1`.

## What HElicon Does

- Converts Chinese research intent into natural English paper prose.
- Diagnoses paper story, positioning, title, abstract, introduction, related work, contribution framing, and evaluation narrative.
- Enforces FHE/security terminology discipline and claim-evidence consistency.
- Distills selected papers into reusable writing patterns without copying source sentences.
- Maintains a controlled memory-patch loop for stable writing preferences and reusable lessons.
- Separates reusable writing knowledge from direction-specific knowledge and project-specific facts.

## Knowledge Layers

HElicon uses three layers:

1. `references/`: stable core memory for long-term writing principles, terminology, venue expectations, FHE framing, reviewer-risk checks, and cross-paper patterns.
2. Direction packs: focused external writing knowledge for areas such as private LLM inference, encrypted kNN/search, FHE systems, and FHE algorithm optimization.
3. Project packs: external project-specific facts for a single paper or project.

Project facts must stay in project packs. Direction-specific details should stay in direction packs unless they become stable cross-direction writing rules.

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
|   `-- style_cards/
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

## Safety Boundaries

Do not write these into HElicon core memory:

- project-specific facts such as NOMOS details;
- raw PDF text or copied paper sentences;
- single-paper cards as if they were general rules;
- ePrint IDs, experimental numbers, or one-off benchmark claims;
- personal style updates unless they come from the user's own writing, accepted revisions, advisor edits, or explicit preferences.

## Version History

See `VERSION.md` and `CHANGELOG.md`.
