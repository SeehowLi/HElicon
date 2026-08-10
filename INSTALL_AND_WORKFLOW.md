# HElicon v1.3 Installation and Workflow

This guide installs HElicon, separates private paper state from skill core, and selects a workflow from the author's actual starting point.

## 0. Important concept

HElicon is not a fine-tuned model and does not learn silently. It improves through controlled distillation and explicit memory patches:

```text
selected papers / own drafts / revision feedback / project state
  -> distillation
  -> scoped core, direction, or project memory
  -> better future diagnosis and revision
```

Project facts and unpublished prose stay outside the skill repository.

## 1. Install HElicon

First preview the selected destination.

Windows PowerShell:

```powershell
.\scripts\install.ps1 --target codex --dry-run
.\scripts\install.ps1 --target claude-code --dry-run
```

POSIX shell:

```bash
sh scripts/install.sh --target codex --dry-run
sh scripts/install.sh --target claude-code --dry-run
```

Targets are `codex`, `claude-code`, `both`, and `repo-local`. Remove `--dry-run` to install. The installer backs up an existing destination as `.bak.<timestamp>`, copies files without symlinks, and runs `check_skill_integrity.py` after installation.

Validate a checkout or installed copy:

```bash
python scripts/selftest_checks.py
python scripts/check_skill_integrity.py .
python scripts/check_core_contamination.py .
```

## 2. Keep optional shared knowledge outside core

An optional private workspace may hold corpus notes, distilled cards, and direction packs:

```text
HElicon_workspace/
├── corpus/
├── distilled/
├── direction_packs/
└── projects/        # legacy v1.2 packs remain readable
```

Do not put raw PDFs, unpublished drafts, reviewer text, or project facts into `references/`.

## 3. Build unified paper patterns

Use two stages:

1. Distill a high-value paper into a paper pattern card without copying source prose.
2. After several comparable cards, distill only their stable shared structure into a unified pattern or direction pack.

Promote a lesson to core only when it is reusable across papers and carries no source-specific fact, sentence, identifier, or result.

## 4. Build direction packs

Use `templates/direction_pack_template.md` for focused knowledge such as private LLM inference, encrypted search, FHE algorithm optimization, or FHE systems. Direction packs may record recurring threat models, comparison dimensions, terminology, and evaluation expectations, but not one paper's private state.

## 5. Build personal style memory

All available author papers are treated as unpublished. Corpus text and derived `fingerprint.json` stay in a paper-local `.helicon/style/` directory or another private workspace, never in the skill repository.

There are no assumed advisor-edited pairs. Revisions of the same paper may be registered as self-edit pairs with `Version: revised`. Sample only Introduction, Contributions, Related Work, and Evaluation narrative; exclude Methods and Construction.

Build a local baseline with an explicit output path:

```bash
python scripts/style_fingerprint.py baseline /private/style/paper-a-versions --paper-id paper-a --output /path/to/paper/.helicon/style/fingerprint.json
```

`n` is the number of distinct `paper_id` values, not the number of version files. Below the minimum distinct-paper count, the baseline is `thin(n=N)`: use it directionally and disable drift warnings.

## 6. Create paper-local project memory

For an existing or new LaTeX paper folder:

```bash
python scripts/bootstrap_project_pack.py --paper-dir /path/to/paper --name MyPaper
```

This creates:

```text
<paper_dir>/.helicon/
├── project.yaml
├── draft_map.md
├── claim_ledger.md
├── evidence_matrix.csv
├── revision_queue.csv
├── reviewer_risk_log.md
├── pass_log.md
├── polish_ledger.csv
├── local_glossary.md
├── decisions.md
└── style/
```

The global `~/.helicon/registry.json` stores only path and fingerprint. To preserve v1.2 workflows, the legacy positional form still creates or reads a centralized pack:

```bash
python scripts/bootstrap_project_pack.py ~/HElicon_workspace/projects MyPaper
```

Paper-local `.helicon/` has priority when both layouts exist.

## 7. Use HElicon on an external paper

The shortest safe paths are:

```text
$HElicon
H-INTAKE /path/to/paper
```

or simply paste a paragraph and ask for a revision. Diagnosis and revisions are returned in chat. Manuscript files change only through an explicit `H-PATCH` target.

Keep current project facts in `.helicon/`; promote only stable general lessons through an explicit memory patch.

## 8. Revision order by entry mode

There is no single mandatory workflow for every situation.

### A. Start a new paper from zero

Retain the original full sequence:

1. project onboarding;
2. direction-pack selection;
3. one-sentence story;
4. paper positioning;
5. title candidates;
6. abstract skeleton;
7. abstract draft;
8. introduction outline;
9. introduction prose;
10. contributions;
11. related-work positioning;
12. evaluation narrative;
13. reviewer simulation;
14. final language polish;
15. memory patch.

Use `H-NEW`, then the existing discussion, positioning, drafting, patch, and sync contracts.

### B. Revise an existing complete draft

```text
H-INTAKE -> section-by-section H-PASS from draft_map -> H-REVIEW -> H-DEADLINE -> H-PATCH -> H-SYNC
```

Intake is one-time, cached, and skippable. A skipped intake leaves `[no intake]` but does not block local work.

### C. Perform local surgery

```text
paste text and use intent routing, or H-SPOT -> H-PATCH
```

Use this path for a paragraph or several sentences. A gate may warn about an upstream issue but still performs the chosen local work.

### D. Prepare a rebuttal

```text
H-REVIEW -> H-REBUT
```

Do not add unverified experimental results or infeasible camera-ready promises.

## 9. What happens without a command

HElicon first identifies project context using the paper-local pack or the path-only registry. If exactly one project matches, it continues directly. If none matches, it works without a project and suggests intake once. Multiple project matches are the only bootstrap ambiguity that stops for selection.

A bare English paragraph routes to P3→P4→P5. Ambiguous language requests take the least destructive route. The router never auto-runs P1 or P2 and never writes a file.

Every routed response ends with:

```text
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none>[ · ⬆<N> upstream]
```

Pass identifiers make the action visible and teach the sequence without a workflow lecture.

## 10. Memory patch loop

At the end of a substantial task, ask HElicon to separate:

1. stable core lessons;
2. direction-pack knowledge;
3. current-project facts for `.helicon/`;
4. temporary ideas that should not be written back.

No layer updates itself silently. `H-PATCH`, `H-DECIDE`, `H-SYNC`, and `H-INGEST` retain their explicit authorization boundaries.
