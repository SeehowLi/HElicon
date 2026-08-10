# HElicon v1.3.1 Installation and Workflow

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

## 5. Build personal style memory and target exemplars

All available author papers are treated as unpublished. Corpus text and all derived style artifacts stay in a paper-local `.helicon/style/` directory or another private workspace, never in the skill repository.

The baseline and target profile are deliberately different. A baseline describes current habits, needs at least five distinct papers to estimate variance, and is used only for drift detection. A target profile prescribes the direction of P4/P5/P6, may use one screened author-approved exemplar, and never emits a drift alert.

Build a local baseline with an explicit output path. Same-title versions group automatically; `--paper-id` is only an explicit override:

```bash
python scripts/style_fingerprint.py baseline /private/style/author-papers --output /path/to/paper/.helicon/style/fingerprint.json
python scripts/style_fingerprint.py baseline /private/style/paper-a-versions --paper-id paper-a --output /path/to/paper/.helicon/style/fingerprint.json
```

`n` is the number of distinct `paper_id` values, not the number of version files. Below the minimum distinct-paper count, the baseline is `thin(n=N)`: retain it as descriptive context only and disable drift warnings. Direction comes from a screened target profile, not a thin baseline.

### Prepare a three-stage target set

Put ordered `.tex`, `.md`, or `.txt` versions of the same paper in one private directory and record the provenance of every adjacent version pair. A common layout is v1→v2 author/advisor discussion and v2→v3 reviewer-driven revision. Mark reviewer-driven pairs explicitly: they remain visible in the report but are excluded from author-preference signals by default. The final version must be author-approved even if AI-assisted.

PDF stages are not parsed directly by the new stdlib-only target scripts. Extract each PDF into a separate private text directory first; the existing extractor keeps its optional `pdftotext`/`PyPDF2` fallback:

```bash
python scripts/extract_pdf_text.py /private/Paper-v1.pdf /private/stages/version1.txt
python scripts/extract_pdf_text.py /private/Paper-v2.pdf /private/stages/version2.txt
python scripts/extract_pdf_text.py /private/Paper-v3.pdf /private/stages/version3.txt
```

Before building the target, reserve several v1 paragraphs as hold-out data and exclude their corresponding v3 paragraphs from target construction. Then preview the mandatory screening and outputs:

```bash
python scripts/build_target_profile.py /private/stages --holdout 2 --holdout 7 --author-advisor-pair 1:2 --review-driven-pair 2:3
python scripts/extract_revision_direction.py /private/stages --author-advisor-pair 1:2 --review-driven-pair 2:3
```

The target builder runs AI-tell and structural checks first. Each profile field records `source: exemplar|rule` and `confidence`; a rejected dimension falls back to the rule policy. Inspect the preview before using `--write`, which is restricted to `.helicon/style/`. Filled exemplar cards remain under `.helicon/style/exemplars/`; load at most three cards matched by section type and rule ID, never copy their prose as content.

After HElicon processes the held-out v1 text through the normal router, evaluate it against the corresponding approved target:

```bash
python scripts/target_eval.py /private/holdout/before.tex /private/holdout/output.tex /private/holdout/target.tex --screening /path/to/paper/.helicon/style/target_screening.json --target-paragraph 2 --trailer-file /private/holdout/trailer.txt --output-report /path/to/paper/.helicon/style/target_eval.json --write
```

This reports structural convergence relative to the original v1→v3 distance, AI-tell counts for v1/output/v3, frozen-set changes from `latex_guard.py`, paragraph alignment, unconverged dimensions, and fixed-trailer compliance.

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
    ├── fingerprint.json
    ├── target_profile.json
    ├── target_screening.json
    ├── revision_direction.json
    ├── target_eval.json
    └── exemplars/
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
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none> · target:<ok|partial|none>[ · sample:too-short][ · ⬆<N> upstream]
```

Pass identifiers make the action visible and teach the sequence without a workflow lecture.

## 10. Memory patch loop

At the end of a substantial task, ask HElicon to separate:

1. stable core lessons;
2. direction-pack knowledge;
3. current-project facts for `.helicon/`;
4. temporary ideas that should not be written back.

No layer updates itself silently. `H-PATCH`, `H-DECIDE`, `H-SYNC`, and `H-INGEST` retain their explicit authorization boundaries.
