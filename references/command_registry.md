# HElicon Command Registry

Treat an `H-*` token as an executable workflow contract. Commands are project-aware but project-agnostic: project facts, manuscript text, review content, experiment results, paper identifiers, and local paths never enter HElicon core.

## Contents

- [Choose by situation](#choose-by-situation)
- [Entry modes](#entry-modes)
- [Functional commands and aliases](#functional-commands-and-aliases)
- [Global rules](#global-rules)
- [Gates](#gates)
- [Output footer](#output-footer)
- [Command contracts](#command-contracts)
- [Legacy v1.2 contracts](#legacy-v12-contracts)

## Choose by situation

`H-HELP` presents this situation-first view rather than an alphabetical inventory.

| I am in this situation | Start with | Likely next |
|---|---|---|
| I have a completed or partial draft to revise | `H-INTAKE [path]` | `H-PASS` or `H-SPOT` |
| I am starting a paper from zero | `H-NEW <name>` | `H-POSITION`, then `H-DRAFT` |
| I want one controlled revision stage | `H-PASS <Pn>` | the next numbered pass |
| I want a small local edit now | `H-SPOT <selection>` | `H-PATCH` if accepted |
| I want normal end-to-end language polishing | `H-POLISH` | `H-GATE` or `H-PATCH` |
| I am over the page limit or near a deadline | `H-DEADLINE --pages N` | `H-GATE` |
| I have reviewer comments | `H-REBUT` | `H-DRAFT`, then `H-PATCH` |
| I doubt a citation | `H-CITE` | fix the evidence map or claim |
| I want to build or inspect my style baseline | `H-STYLE` | `H-PASS P6` |
| I want a submission-readiness audit | `H-GATE` | resolve blocking findings |
| I need outside strategic advice | `H-EXPORT mode=advice` | external advisor, then `H-INGEST` |
| I need to pressure-test an idea or claim | `H-DISCUSS` | `H-DECIDE` or gather evidence |
| I need to lock story, venue, or contribution hierarchy | `H-POSITION` | `H-DECIDE` or `H-DRAFT` |
| I have accepted text to write into a file | `H-PATCH` | `H-SYNC` |
| Project memory is stale or incomplete | `H-SYNC` or `H-SYNC-REPAIR` | confirmation |

## Entry modes

Entry modes name the author's situation rather than an internal operation.

| Command | Situation | Writes by default |
|---|---|---|
| `H-NEW <name>` | Start a paper from zero; wraps `H-ONBOARD`. | After confirmation |
| `H-INTAKE [path]` | Triage an existing draft once. | After confirmation, writes `draft_map.md` |
| `H-PASS <Pn> [--section X]` | Run one revision pass. | No |
| `H-SPOT <selection>` | Perform the smallest local surgery. | No |
| `H-DEADLINE --pages N` | Compress under a page or time constraint. | No |
| `H-REBUT` | Triage and answer reviewer feedback. | No |

## Functional commands and aliases

| Command | Function | Writes by default |
|---|---|---|
| `H-CITE` | Verify citation existence and attribution against an authorized external library. | No |
| `H-STYLE` | Report, build, compare, or inspect drift for a local style fingerprint. | Only after a confirmed baseline target |
| `H-GATE` | Run the pre-submission review gate and available machine checks. | No |
| `H-EXPORT mode=<mode>` | Build a self-contained external-advisor handoff. | No |
| `H-INGEST` | Compare returned advice with current state and propose a scoped patch plan. | No |

Compatibility aliases:

- `H-POLISH` orchestrates P3 → P4 → P5 → P6. It applies gates, never auto-runs P2 for a `STABLE` section, and reports every pass separately.
- `H-COMPRESS` is `H-DEADLINE`.
- `H-VOICE` is `H-STYLE`.
- `H-TRIAGE` is `H-INTAKE`.

The sixteen v1.2 commands remain valid with unchanged semantics: `H-HELP`, `H-LOAD`, `H-ONBOARD`, `H-DISCUSS`, `H-POSITION`, `H-DRAFT`, `H-DECIDE`, `H-TITLE-ITERATE`, `H-ABSTRACT-ITERATE`, `H-SECTION-ITERATE`, `H-REVIEW`, `H-PATCH`, `H-LOG`, `H-SYNC`, `H-SYNC-REPAIR`, and `H-REOPEN`.

## Global rules

1. Chinese is the control language; English is the default paper-facing language.
2. Discussion, diagnosis, and iteration commands do not patch manuscripts.
3. `H-PATCH` requires an explicit file, exact location, and confirmed text or version.
4. Recommend `H-SYNC` after a successful patch and after a confirmed decision.
5. Recommend `H-DECIDE` after stable consensus.
6. Track material claims with `SUPPORTED`, `PARTIAL`, `MISSING`, `RISKY`, `UNKNOWN`, `MISSING_EVIDENCE`, or `OVERCLAIM_RISK`, and citations with `CITATION_UNVERIFIED` or `CITATION_MISATTRIBUTED` when applicable.
7. Prefer scoped or conditional wording when evidence is incomplete.
8. Trackers contain confirmed current state, not temporary ideas.
9. Decision logs retain scoped current decisions, evidence state, risk, and follow-up; stale decisions are deleted or archived.
10. Workbenches may keep reversible candidates; synchronization removes candidates superseded by confirmed state.
11. HElicon core is never updated automatically.
12. Project facts, unpublished prose, paper-specific results, reviews, and identifiers never enter HElicon core.
13. Use `H-DISCUSS` for brainstorming; there is no separate brainstorm command.
14. Use `H-POSITION` for story and positioning; there is no separate storyline command.
15. Use `H-DRAFT` for general section iteration; specialized v1.2 entry points remain available.
16. `H-PASS` runs one pass with one target. `H-POLISH` may orchestrate several passes but reports them separately.
17. The immutable set outranks every style suggestion.
18. Gate notices appear at most once per section per session.
19. Without an explicit command, use `intent_router.md`.
20. At session start, follow the bootstrap and context budget in `project_memory.md`.

The project loop remains:

```text
H-DISCUSS -> H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC
H-REVIEW -> H-REOPEN if needed -> H-DISCUSS/H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC
```

Project memory is a compact live-state cache, not an append-only transcript. Prefer rewriting current state to appending discussion history.

## Gates

Before `H-SPOT` or `H-PASS`, inspect `draft_map.md` when present.

- `STABLE`: execute silently.
- `REWORK` or `DELETE-CANDIDATE`: emit exactly one line, once per section per session, then honor the author's command:

```text
[GATE] §<id> marked <verdict> by intake (<reason>). Local polish here is likely to be discarded. Continue anyway, or run H-PASS P2 --section <id>.
```

- A target claim tagged `MISSING_EVIDENCE`, `OVERCLAIM_RISK`, or `CITATION_UNVERIFIED`: emit one concise notice and preserve every qualifier and scope term by default.
- No `draft_map.md`: continue normally and emit this once per session:

```text
[no intake] running ungated. H-INTAKE gives you section-level gating.
```

Gates warn; they do not block. No command may refuse work merely because an upstream step is unfinished. Only an immutable-set violation may stop or roll back execution.

## Output footer

Discussion and iteration commands end with the existing compact footer:

```markdown
Round consensus:
- ...

Open issues:
- ...

Next recommended HElicon commands:
1. `...` - ...
2. `...` - ...
3. `...` - ...
```

Use Chinese labels in a Chinese conversation. Recommendations are pass-aware: after P4, recommend P5 before P6 or P7. Routed revisions also use the fixed trailer from `intent_router.md`.

## Command contracts

### H-NEW

Purpose: start a paper from zero by invoking the existing `H-ONBOARD` contract.

Before writing, output the proposed project-local `.helicon/` path, files, direction-pack suggestions, known facts, missing facts, and a confirmation request. After confirmation, bootstrap the pack; do not create manuscript claims or evidence.

### H-INTAKE

Purpose: perform the cached, skippable triage in `draft_intake.md`.

Read the draft, source map, glossary, and available evidence state. Produce per-section structural verdicts, claim labels, terminology drift, polish eligibility, and pass sequence using `templates/draft_map.md`. Show the proposed `draft_map.md` first; write only after confirmation. If skipped, record `[no intake]` through the authorized memory path.

### H-PASS

Purpose: run exactly one P1–P7 pass on the named section or selection.

Required behavior:

- load only the pass reference and target context;
- state one target and excluded changes;
- snapshot and verify the immutable set;
- apply the draft-map gate without blocking;
- return revised text, change locations, rollback findings, and the next pass;
- use `templates/pass_log.md` and `templates/polish_ledger.csv` only for a later authorized state update.

Reject only an invalid pass name or an immutable-set violation. Do not write source files.

### H-SPOT

Purpose: make the smallest useful local revision with minimal ceremony.

Infer the least destructive language pass from the selection, apply the gate, preserve upstream decisions, and return the revision directly. If no intake exists, show the single `[no intake]` line. Do not write a file; use `H-PATCH` for accepted text.

### H-DEADLINE

Purpose: reduce length using `deadline_compression.md` while freezing threat-model and claim-scope language.

Output:

```markdown
Compression target:
- Current/target pages or time:

Candidates:
- Delete / merge / appendix / rewrite:
- Claim-integrity risk:

Compressed candidate:
- ...

Frozen-set result:
- PASS / warning and rollback:
```

Follow the fixed action order. If the target is unsafe, report the remaining delta rather than deleting scope.

### H-REBUT

Purpose: use `rebuttal_playbook.md` after an `H-REVIEW` state check.

Classify each comment as factual error, misreading, fixable real defect, or unfixable real defect. Return a direct response, evidence pointer, feasible manuscript promise, and unresolved risk using `templates/rebuttal_response.md`. Never introduce an unverified experimental result or an infeasible camera-ready promise.

### H-CITE

Purpose: verify citation existence and support using `citation_discipline.md`.

Require an authorized Zotero library, project bibliography, or source PDF. Never use model memory as the verifier. Return the claim, citation, external source checked, `VERIFIED`, `CITATION_UNVERIFIED`, or `CITATION_MISATTRIBUTED`, the misattribution class, and a safe next action. Do not invent a replacement citation.

### H-STYLE

Purpose: run style `report`, `baseline`, `compare`, or `drift` through `style_fingerprint.py`.

Keep corpus and fingerprint outputs outside the skill repository and follow `templates/style_baseline_readme.md`. A baseline write requires an explicit local target and `paper_id` grouping; revisions of one paper count once. Report distinct-paper count, source-file count, `ok`, `thin(n=N)`, or `none`, metrics used, comparison result, and whether drift alerts were disabled. `H-VOICE` invokes the same contract.

### H-GATE

Purpose: audit submission readiness without patching files, using `templates/submission_gate_checklist.md` for the three result levels.

Read `review_gate.md`, current claim/citation state, and the applicable venue and FHE references. Run all available repository machine checks plus immutable-set consistency. Missing tools are reported as `NOT_RUN`, not silently treated as passing.

Output:

```markdown
Blocking findings:
- ...

Warnings:
- ...

Optional improvements:
- ...

Machine checks:
- command: PASS / FAIL / NOT_RUN

Submission state:
- READY / NOT_READY / UNKNOWN
```

The labels prioritize work; they do not prevent another command from running.

### H-EXPORT

Purpose: create one machine-oriented, self-contained external-advisor bundle using `external_advisor_protocol.md` and `templates/advisor_brief.md` for advice mode.

Modes:

- `mode=dossier`: skill state, project state, manuscript summary, claim ledger, and open issues.
- `mode=advice`: dossier plus the question, attempted approaches, failure reasons, desired correct state, constraints, and immutable items. Instruct the flagship model to provide top-level diagnosis or design and return a Codex execution prompt, not to perform the file changes itself.
- `mode=skill-upgrade`: HElicon's current design, observed failure, compatibility obligations, requested upgrade, and validation state.

The entire export is one code block. Put constraints first, use labeled fields, and remove pleasantries. Include a sensitivity inventory naming unpublished data, experimental results, and verbatim reviewer text present in the bundle. Never delete sensitive material silently; the author decides what to remove before upload.

### H-INGEST

Purpose: ingest returned flagship advice without applying it.

Output a current-versus-proposed diff, destination layer (`core`, `direction pack`, `project pack`, or `do not write back`), scoped patch plan, conflicts with Iron Rules or locked state, required verification, and unresolved questions. Application requires a later confirmed patch action.

### H-POLISH

Purpose: orchestrate P3, P4, P5, and P6 in order.

Apply the gate once, snapshot immutable content, and emit four pass-labeled sections with target, changes, skipped items, and frozen-set status. The single-pass restriction belongs to `H-PASS`, not this orchestrator. Respect qualified anti-drift refusal for P5/P6; thin baselines do not refuse or warn for drift.

## Legacy v1.2 contracts

### H-HELP

Show the situation table, choose the most likely command for current context, and give two or three next commands. For an unknown `H-*` token, map the author's situation rather than listing commands alphabetically.

### H-LOAD

Load project and direction context without writing. Follow `project_memory.md`: bootstrap with `project.yaml`, draft-map verdict lines, and the pass-log tail; load briefs, trackers, decisions, workbenches, claim/evidence files, risk logs, glossary, direction packs, and core references only when the active task requires them.

Report active project, direction packs, files read, estimated context occupancy, locked and open decisions, missing or stale files, and the next command. Never lock an inferred fact.

### H-ONBOARD

Start or repair a project pack. Read the project templates, evidence templates, claim ledger, revision queue, reviewer risk log, and direction map. Before writing, show the proposed path, files, direction packs, missing author facts, and confirmation request. Write only after confirmation.

### H-DISCUSS

Pressure-test an idea, claim, experiment, story move, term, or reviewer risk. Do not patch or agree by default. Test project evidence, direction and venue expectations, and reviewer risk.

```markdown
Agreement: agree / partly agree / disagree / UNKNOWN; reason
Evidence: status; source; gap; citation status
Reviewer concern: ...
Venue fit: strong / medium / weak / UNKNOWN; reason
Overclaim risk: ...
Safer framing: Chinese positioning; English paper-safe phrasing
Next questions: ...
```

### H-POSITION

Define or revise story, venue, contribution hierarchy, novelty angle, and claim boundary without drafting full prose unless requested. Separate problem, bottleneck, insight, contributions, and evaluation promise. Mark claim-ledger candidates for later `H-DECIDE`.

Return current diagnosis, one-sentence story, bottleneck, insight, contribution hierarchy, evidence promise, safe/risky/forbidden claims, evidence gaps, reviewer risks, and the next command.

### H-DRAFT

Draft a section, paragraph, abstract, title rationale, related-work contrast, evaluation narrative, rebuttal, or response candidate without patching. Identify the target and upstream position, preserve claims, and emit claim/evidence/risk updates for later synchronization.

Return target, local keep/change/delete-or-move plan, candidate prose, claim-evidence-risk state, and `READY` or `NOT_READY` patch readiness.

### H-DECIDE

Turn consensus into a scoped project decision. First show the decision, applies/does-not-apply scope, evidence state, reviewer concerns, risks, affected memory files, stale decisions to remove or archive, and `Need confirmation: YES`. Write only after confirmation and then perform or propose scoped synchronization. Do not patch manuscript text.

Claim changes update the claim ledger and evidence matrix; resolved reviewer or revision items are removed or archived through synchronization.

### H-TITLE-ITERATE

Generate title candidates from the locked story, direction, and evidence state without changing files. Return the current title state, several candidates with claim/evidence/venue/risk analysis, directions to avoid, and feedback choices. Broad terms require explicit scope and evidence.

### H-ABSTRACT-ITERATE

Revise an abstract incrementally without patching. Preserve sound logic, prefer reversible local edits unless structure is broken, and label each strong claim's evidence gap. Return diagnosis, keep/revise/delete/move analysis, claim-evidence-risk table, candidate abstract, and feedback choices.

### H-SECTION-ITERATE

Compatibility alias for `H-DRAFT` with a section target. Diagnose locally, plan before prose, preserve structure unless a structural issue is identified, and check positioning before revising Introduction, Contributions, Related Work, Evaluation, or Threat Model. Do not patch.

### H-REVIEW

Simulate reviewer objections or audit venue fit, evidence gaps, and claim risk using `review_gate.md`, venue and direction references, FHE checks, and project evidence. Return ranked objections, affected claims/sections, missing evidence, safer boundaries, actions, reviewer-risk candidates, and revision-queue candidates. Write those files only through confirmed synchronization.

### H-PATCH

Apply confirmed text to an explicit file and exact location. Modify only that location; preserve citations, labels, references, mathematics, figures, tables, algorithms, comments, and formatting unless instructed otherwise. Use the smallest patch, show a diff summary, and run relevant validation. If the target is ambiguous, ask one concise clarification.

```markdown
Patch target: file; location
Pre-patch check: immutable items; ambiguity
Applied changes: ...
Diff summary: ...
Verification: command; PASS / FAIL / NOT_RUN; first actionable error
```

### H-LOG

Compatibility alias for a scoped `H-SYNC`. Translate the requested item into a compact synchronization plan; classify it as temporary discussion, project fact, confirmed decision, or reusable lesson; identify target and stale content; request confirmation unless target and content were explicitly authorized. Never append blindly or write project facts to core.

### H-SYNC

Synchronize current project state after patching, deciding, or iterating. Do not patch manuscript text. Read only affected scope, detect unrecorded consensus and patches, classify progress, workbench, discussion, stale deletion, archive, claim, evidence, reviewer-risk, and revision-queue changes, then propose compact replacements. Delete or archive stale, contradicted, superseded, completed, or duplicated state. Write only after confirmation.

### H-SYNC-REPAIR

Repair missed synchronization after long discussion, context loss, or unsynchronized patches. Compare available manuscript scope and project memory, separate confirmed state from plausible inference, list patched-but-unrecorded content, undecided consensus, stale items, classification, and write plan. Wait for confirmation; never modify manuscript text.

### H-REOPEN

Reopen a title, abstract, section, claim, or decision after new evidence, contradiction, reviewer risk, or scope change. Do not patch. Return the target, reason, old conclusion, still-valid parts, needed changes, risk of leaving it closed, and the recommended discussion, decision, or iteration command.
