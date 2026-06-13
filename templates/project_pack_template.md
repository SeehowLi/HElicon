# Project Pack Template

Create one folder per paper/project outside the skill:

`HElicon_workspace/projects/<project_name>/`

Recommended files:

```text
project_brief.yaml
storyline.md
evidence_map.csv
local_glossary.md
focused_references.md
experiment_notes.md
draft_status.md
reviewer_risks.md
accepted_phrasing.md
decision_log.md
sync_archive.md
memory_patch_log.md
```

## project_brief.yaml

Copy `templates/paper_brief.yaml` and fill project-specific facts.

## storyline.md

```markdown
# <Project> Storyline

## One-sentence story

## Problem framing

## Existing gap

## FHE-specific bottleneck

## Key insight

## Design summary

## Contribution hierarchy

## Target-venue positioning

## Claims to avoid
```

## local_glossary.md

Only project-specific terms and naming decisions.

## focused_references.md

Papers that should be emphasized for this project, separate from the global pattern bank.

## accepted_phrasing.md

English sentences or phrases accepted for this project. Keep short excerpts only.

## decision_log.md

Keep this compact. Do not append indefinitely.

```markdown
# Decision Log

## Current Locked Decisions

- Decision:
  - Scope:
  - Evidence status:
  - Active risks:
  - Last synced:

## Open Decisions

- Question:
  - Current options:
  - Missing evidence:
  - Next command:

## Recently Superseded

- Old decision:
  - Superseded by:
  - Keep in archive: YES / NO
```

## draft_status.md

Use this as the compact project tracker. It should contain only current, confirmed state.

```markdown
# Draft Status

## Current State

## Locked Story / Scope

## Active Claims

## Section Status

## Open Issues

## Last Sync
```

## sync_archive.md

Archive only material that prevents future confusion. Do not store full transcripts.

```markdown
# Sync Archive

## YYYY-MM-DD - <short reason>

- Archived item:
- Why not current:
- Replacement:
```
