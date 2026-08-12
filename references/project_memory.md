# Project Memory

Each paper has a stable local directory containing its LaTeX source. HElicon stores its project pack beside that source so the open directory identifies the paper and machine checks can compare real files.

## Project-local layout

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
    ├── local_glossary.md
    ├── decisions.md
    └── style/
        ├── fingerprint.json
        ├── target_profile.json
        ├── target_screening.json
        ├── target_traces/
        └── exemplars/
```

`project.yaml` contains the project fingerprint. `draft_map.md` caches intake. `pass_log.md` stores one attributable record per pass. The style directory contains derivatives of unpublished material and never enters the skill repository. `target_profile.json` is the only prescriptive target read by P4, P5, or P6; `target_screening.json` remains construction evidence and is not normal revision context.

The adjacent LaTeX source lets `latex_guard.py` compare frozen items against real text instead of relying on a model assertion.

## Legacy compatibility

Continue to read v1.2 packs found under `~/HElicon_workspace/projects/<name>/`. Do not require migration. When both layouts exist, the paper-local `.helicon/` pack has priority over the centralized workspace.

## Fingerprint and registry

The `project.yaml` fingerprint includes:

- title, target venue, creation time, and last-action time;
- top-N key terms from `local_glossary.md`;
- ordered section headings and per-section word counts;
- one content hash.

The global index is `~/.helicon/registry.json`. It stores only a project path and fingerprint, never manuscript text, extracted sentences, evidence content, or experiment results.

## Session bootstrap protocol

1. Inspect the current directory and up to three parent directories for `.helicon/`.
2. If none is found, fingerprint-match the message against `registry.json`.
3. For one match, print `识别为 <项目名>（<N> 节 / 上次 <pass> §<节号> / <日期>）` before the trailer, then continue without waiting for confirmation.
4. For no match, continue in no-project mode, use `baseline:none`, and mention `H-INTAKE` once as an optional setup action.
5. For multiple matches, list the candidates and stop for selection. This is the only bootstrap ambiguity that may block, because editing the wrong paper is costly.

Bootstrap identification does not authorize source-file writes. It only selects read context.

## Context budget

At session start, read only:

- `project.yaml`;
- verdict lines from `draft_map.md`;
- the final five lines of `pass_log.md`.

Load every other project file only when the active routing node names it. A route containing P3 names `local_glossary.md`; a route containing P4, P5, or P6 names `style/target_profile.json` and must resolve it through `scripts/resolve_target_profile.py` before editing. A P4/P5 route then runs `scripts/revision_preflight.py` on only the supplied selection and returns a privacy-safe `preserve|revise` decision. The resolver reads no manuscript prose, and neither script writes unless an authorized trace path under `style/target_traces/` is supplied. `H-LOAD` reports both the files read and estimated context occupancy.

threshold: when estimated context occupancy exceeds 50%, load only files explicitly named by the current routing node. <!-- helicon:allow-numeric -->

This budget is a hard rule. A convenient whole-pack load is not a reason to consume the window needed for revision.

## Memory boundaries

Project facts remain in `.helicon/`; reusable writing rules remain in HElicon core; direction-specific abstractions remain in direction packs. A memory patch must name its destination and must never promote unpublished prose or project identifiers into the core.
