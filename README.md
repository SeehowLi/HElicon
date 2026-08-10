# HElicon

HElicon is a long-term research-writing mentor skill for English security and systems papers in fully homomorphic encryption, privacy-preserving computation, private inference, encrypted search, and related algorithmic or systems work.

This repository contains the reusable skill core only. It contains no paper draft, project fact, unpublished style corpus, or derived personal fingerprint.

Current snapshot: `HElicon v1.3`.

## What changed in v1.3

- Natural-language intent routing handles pasted prose without requiring a command.
- Paper-local `.helicon/` memory identifies the active paper across sessions.
- Seven ordered passes separate claim, structure, terminology, rhythm, diction, voice, and surface work.
- Sentence-level FHE/security polish preserves technical terms, hedging, formal language, and immutable LaTeX content.
- Machine checks cover contamination, package integrity, style fingerprints, AI-writing tells, and LaTeX frozen sets.
- Portable installers target Codex, Claude Code, both hosts, or one repository.

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
| I want a submission audit | `H-GATE` | Blocking findings, warnings, optional improvements, and machine checks are listed. |
| I need outside strategic advice | `H-EXPORT mode=advice` | A self-contained, sensitivity-labeled handoff is produced for review. |

All v1.2 commands remain available. See `references/command_registry.md` for complete contracts and compatibility aliases.

## No-command editing

Paste an English paragraph with no instruction and HElicon defaults to P3→P4→P5: terminology, rhythm, and diction. It does not change structure, claim scope, numbers, citations, or frozen terms. Ambiguous requests take the least destructive useful route instead of stopping for a workflow question.

Router output is returned in chat. It does not write a file; accepted text still requires `H-PATCH`. Every routed response ends with:

```text
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none>[ · ⬆<N> upstream]
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
    └── style/fingerprint.json
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
python scripts/style_fingerprint.py --help
python scripts/latex_guard.py --help
python scripts/check_ai_tells.py --help
```

Use `scripts/latex_guard.py` on before/after LaTeX files and `scripts/style_fingerprint.py` only with local or private corpus paths. Personal style source and `fingerprint.json` never belong in this repository.

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
- A thin personal baseline is directional and cannot emit a drift warning.

See `VERSION.md`, `CHANGELOG.md`, and `INSTALL_AND_WORKFLOW.md` for release and workflow details.
