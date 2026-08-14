# HElicon

HElicon is a long-term research-writing mentor skill for English security and systems papers in fully homomorphic encryption, privacy-preserving computation, private inference, encrypted search, and related algorithmic or systems work.

This repository contains the reusable skill core only. It contains no paper draft, project fact, unpublished style corpus, or derived personal fingerprint.

Current snapshot: `HElicon v1.3.1`.

## What changed in v1.3.1

- AI-tell rules 1–14 now have executable, contract-checked coverage, including scoped exemptions for qualified performance language.
- Same-paper versions group automatically by normalized title or parent directory, so five versions remain `thin(n=1)` rather than masquerading as five papers.
- A screened target profile gives P4/P5/P6 a prescriptive destination while the descriptive baseline remains isolated to drift detection.
- Revision-direction reports keep author/advisor changes separate from reviewer-driven changes and surface invariant expressions for author confirmation.
- Private before/after exemplar cards provide section- and rule-matched form anchors without becoming content sources.
- Hold-out evaluation measures structural convergence, AI tells, frozen LaTeX, alignment, and the actual router trailer against an approved final version.

## Choose by situation

| Situation | Start with | What happens |
|---|---|---|
| I have an existing full or partial draft | `H-INTAKE [path]` | One-time cached triage creates section verdicts and pass sequences. |
| I am starting from zero | `H-NEW <name>` | HElicon proposes a project pack and onboarding state before writing. |
| I want one controlled revision stage | `H-PASS <Pn> [--section X]` | Exactly one P1–P7 pass runs without patching the source. |
| I want a small local edit | `H-SPOT <selection>` | The least destructive local surgery is returned directly. |
| I want normal language polishing | `H-POLISH` | P3→P4→P5→P6 runs with a separate report per pass. |
| I am over the page limit | `H-DEADLINE --pages N` | Redundancy is removed before any sentence-level compression. |
| I have reviewer comments | `H-REBUT` | Comments are triaged and answered under evidence and feasibility constraints. |
| I need citation verification | `H-CITE` | Attribution is checked against an authorized real library, never model memory. |
| I have staged versions of one paper | `H-STYLE target <dir>` | The final version is screened before a private target profile and exemplar candidates are previewed. |
| I want to inspect my revision habits | `H-STYLE direction <dir>` | Version pairs are aligned; reviewer-driven edits stay separate from author-preference signals. |
| I want a measurable hold-out test | `H-STYLE eval <before> <target>` | A held-out HElicon output is compared with the approved target and frozen source. |
| I want a submission audit | `H-GATE` | Blocking findings, warnings, optional improvements, and machine checks are listed. |
| I need outside strategic advice | `H-EXPORT mode=advice` | A self-contained, sensitivity-labeled handoff is produced for review. |

All v1.2 commands remain available. See `references/command_registry.md` for complete contracts and compatibility aliases.

## No-command editing

Paste an English paragraph with no instruction and HElicon defaults to P3→P4→P5: terminology, rhythm, and diction. Before editing, a deterministic preflight checks whether any eligible P4/P5 boundary or numbered rule is actually triggered; clean text returns unchanged with `0处`. It does not change structure, claim scope, numbers, citations, or frozen terms. Ambiguous requests take the least destructive useful route instead of stopping for a workflow question.

Router output is returned in chat. It does not write a file; accepted text still requires `H-PATCH`. Every routed response ends with:

```text
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none> · target:<ok|partial|none>[ · sample:too-short][ · ⬆<N> upstream]
```

The router may recommend P1 or P2 but never executes claim or structural rewrites without explicit approval.

## Revision passes

| Pass | Scope |
|---|---|
| P1 | Claim scope and evidence strength |
| P2 | Section and paragraph structure |
| P3 | Terminology normalization |
| P4 | Sentence rhythm and clause structure |
| P5 | Diction, inflation, filler, and AI tells |
| P6 | Qualified personal style alignment |
| P7 | Semantic-free LaTeX, citation placement, and punctuation cleanup |

The fixed order and immutable-set contract are in `references/pass_pipeline.md`.

## Project-local memory

Each paper keeps private state beside its LaTeX source:

```text
<paper_dir>/
├── main.tex, sections/, figures/ ...
└── .helicon/
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

The global `~/.helicon/registry.json` stores only the paper path and fingerprint. Legacy v1.2 packs under `~/HElicon_workspace/projects/<name>/` remain readable, with paper-local memory taking priority.

Create a local pack:

```bash
python scripts/bootstrap_project_pack.py --paper-dir /path/to/paper --name MyPaper
```

## Install

Preview all destinations before installation:

```powershell
.\scripts\install.ps1 --target codex --dry-run
```

```bash
sh scripts/install.sh --target codex --dry-run
```

Supported targets are `codex`, `claude-code`, `both`, and `repo-local`. Remove `--dry-run` to install. Existing destinations are moved to `.bak.<timestamp>`, files are copied rather than symlinked, and package integrity runs after the copy.

Codex user install:

```powershell
.\scripts\install.ps1 --target codex
```

Claude Code user install:

```bash
sh scripts/install.sh --target claude-code
```

## Validate

```bash
python scripts/selftest_checks.py
python scripts/check_skill_integrity.py .
python scripts/check_core_contamination.py .
python scripts/check_contract_sync.py .
python scripts/style_fingerprint.py --help
python scripts/latex_guard.py --help
python scripts/check_ai_tells.py --help
python scripts/build_target_profile.py --help
python scripts/resolve_target_profile.py --help
python scripts/revision_preflight.py --help
python scripts/extract_revision_direction.py --help
python scripts/target_eval.py --help
```

Use `scripts/latex_guard.py` on before/after LaTeX files and all style scripts only with local or private corpus paths. Personal prose, fingerprints, target-profile values, screening and direction reports, evaluations, and filled exemplar cards never belong in this repository.

## Target exemplars from staged versions

Prepare ordered `.tex`, `.md`, or `.txt` versions of the same paper in one private directory. If the available stages are PDFs, first run the existing `scripts/extract_pdf_text.py` once per PDF into a separate private text directory; its optional `pdftotext`/`PyPDF2` fallback remains unchanged. The final version must be author-approved, version pairs must be labeled as author/advisor or reviewer-driven, and some start-version paragraphs must be reserved as hold-out data before target construction. `H-STYLE target <dir>` first screens the final version; it never treats an AI-assisted final draft as an unconditional target. Clean dimensions use `source: exemplar`, while rejected dimensions use `source: rule`. When the stage directory is separate from the paper directory, every write uses explicit `--profile-output` and `--screening-output` paths under the active paper's `.helicon/style/`.

Run `H-STYLE direction <dir>` to inspect what changed, the observed editing order, and what remained invariant. Reviewer-driven pairs are listed separately and excluded from author-preference signals by default. After confirming target artifacts and exemplar candidates, keep them under the paper's `.helicon/style/`; load at most three cards matched by section type and rule ID. Normal P4/P5/P6 routes call `resolve_target_profile.py` before editing; P4/P5 then call `revision_preflight.py`, and a `preserve` result forbids cosmetic churn. Finally, process content-stable reserved start-version paragraphs through the normal router and use `H-STYLE eval <before> <target>` to compare that output with the approved target. A functionally corresponding paragraph with changed facts is diagnostic-only, not a style-efficacy ground truth.

## Knowledge layers

HElicon keeps three layers separate:

1. `references/`: stable reusable writing and review logic.
2. Direction packs: focused knowledge for one research direction.
3. Paper-local or legacy project packs: unpublished project facts and state.

Selected paper provenance is listed in `provenance/distilled_sources.bib`. External writing-skill influences and license checks are recorded separately in `provenance/external_influences.md`; HElicon distills concepts and does not copy instruction passages.

## Safety boundaries

- Do not put paper drafts, project facts, experiment results, ePrint identifiers, reviewer text, or personal style derivatives into core references.
- Do not strengthen claims or silently change security semantics.
- Do not verify citation truth from model memory.
- Gates warn and continue; only immutable-set damage causes rollback.
- A thin personal baseline is descriptive and cannot emit a drift warning; the target profile supplies direction but never activates drift detection.

See `VERSION.md`, `CHANGELOG.md`, and `INSTALL_AND_WORKFLOW.md` for release and workflow details.

## Quick start

1. `powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 --target codex`
2. `python -B scripts/bootstrap_project_pack.py --paper-dir "<PAPER_DIR>" --direction private_llm_inference`
3. `notepad "<PAPER_DIR>\.helicon\local_glossary.md"; python -B scripts/glossary_md_to_json.py "<PAPER_DIR>\.helicon\local_glossary.md" -o "$env:TEMP\helicon-local-glossary.json" --fail-on-deletion-risk`
4. `python -B scripts/glossary_build.py --direction private_llm_inference --project "<PAPER_DIR>\.helicon\local_glossary.md" -o "$env:TEMP\helicon-merged-glossary.json" --fail-on-deletion-risk`
5. `H-POLISH`
