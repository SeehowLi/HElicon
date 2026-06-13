# HElicon Command Registry

This file defines HElicon short commands. Treat these commands as executable workflow contracts when the user starts a message with `H-*`.

The command system is project-aware but project-agnostic. It was generalized from an external paper workflow. Do not copy project facts, manuscript details, review text, experiment numbers, paper names, ePrint IDs, or local file paths from any project into HElicon core memory.

## Command Families

### Project Setup And Context

| Command | Responsibility | Writes files by default |
|---|---|---|
| `H-HELP` | Show available commands and choose the right next command. | No |
| `H-LOAD` | Load the relevant project pack, direction pack, tracker, decision log, and workbench files for the current task. | No |
| `H-ONBOARD` | Start or repair a project pack for a new paper. | Only after confirmation |

### Interactive Revision

| Command | Responsibility | Writes manuscript by default |
|---|---|---|
| `H-DISCUSS` | Pressure-test an idea, claim, experiment, framing choice, or reviewer risk. | No |
| `H-TITLE-ITERATE` | Generate or revise title candidates without changing the manuscript. | No |
| `H-ABSTRACT-ITERATE` | Incrementally revise an abstract candidate without patching the manuscript. | No |
| `H-SECTION-ITERATE` | Plan and draft local section revisions without patching the manuscript. | No |
| `H-REVIEW` | Simulate reviewers or audit a draft section against venue and evidence expectations. | No |

### State, Decisions, And Patching

| Command | Responsibility | Writes files by default |
|---|---|---|
| `H-DECIDE` | Convert a discussion consensus into a scoped project decision. | Only after confirmation |
| `H-PATCH` | Apply a confirmed version to an exact file location. | Yes, only specified target |
| `H-LOG` | Record temporary discussion, confirmed decisions, or project state in the appropriate project file. | Only after confirmation |
| `H-SYNC` | Synchronize manuscript, workbenches, decision log, tracker, and open issues after work. | Only after confirmation |
| `H-SYNC-REPAIR` | Repair missed syncs after long conversations or unsynchronized patches. | Only after confirmation |
| `H-REOPEN` | Reopen an earlier title, abstract, section, claim, or decision when evidence or scope changes. | No |

## Global Command Rules

1. Chinese is the control language for discussion and diagnosis. English is for paper-facing prose.
2. Discussion commands do not patch manuscripts.
3. `H-PATCH` must have an explicit target file, exact location, and confirmed text or version.
4. After a successful `H-PATCH`, recommend `H-SYNC`.
5. After stable consensus, recommend `H-DECIDE`.
6. Track every strong claim with `SUPPORTED`, `PARTIAL`, `MISSING`, `RISKY`, `UNKNOWN`, `MISSING_EVIDENCE`, or `OVERCLAIM_RISK`.
7. If evidence is incomplete, prefer scoped or conditional language over optimistic agreement.
8. Project trackers should contain only confirmed and current project state, not temporary ideas.
9. Decision logs should contain scoped decisions, evidence status, risks, and follow-up.
10. Workbenches may store iterative candidates and reversible draft versions.
11. HElicon core is never updated automatically.
12. Never write project facts, raw paper text, paper-specific numbers, review details, or single-paper card content into HElicon core.

## Standard Output Footer

For discussion and iteration commands, end with:

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

Use Chinese labels if the conversation is in Chinese.

## Command Contracts

### H-HELP

Purpose: show the command menu and recommend the right next command.

Use when:
- the user asks what command to use;
- the project state is unclear;
- the user invokes an unknown `H-*` command.

Output:
- command categories;
- the most likely command for the current situation;
- 2-3 next command suggestions.

### H-LOAD

Purpose: load the current project and direction context without changing files.

Read as available:
- project brief;
- progress tracker;
- decision log;
- iteration log;
- claim/evidence matrix;
- title, abstract, or section workbench;
- local glossary;
- selected direction packs;
- relevant HElicon core references.

Output:
- active project;
- active direction packs;
- files read;
- locked decisions;
- open decisions;
- stale or missing files;
- recommended next command.

Do not:
- infer project facts as locked if files are missing;
- write any file.

### H-ONBOARD

Purpose: start a new project pack or repair an incomplete project pack.

Read:
- `templates/project_pack_template.md`;
- `templates/project_onboarding_prompt.md`;
- `templates/evidence_map.csv`;
- direction map if direction selection is needed.

Output before writing:
- proposed project pack path;
- project-specific files to create;
- initial direction-pack recommendation;
- missing facts the user must supply;
- confirmation request.

Write only after confirmation.

### H-DISCUSS

Purpose: pressure-test a new idea, claim, experiment, storyline move, terminology choice, or reviewer risk.

Required behavior:
- do not patch files;
- do not write final prose unless explicitly requested as a candidate;
- test against project evidence, direction-pack expectations, venue expectations, and reviewer risks;
- do not agree by default.

Output:

```markdown
Agreement:
- agree / partly agree / disagree / UNKNOWN
- Reason: ...

Evidence status:
- SUPPORTED / PARTIAL / MISSING / RISKY / UNKNOWN
- Evidence: ...
- Gap: ...

Reviewer concern:
- ...

Venue fit:
- strong / medium / weak / UNKNOWN
- Reason: ...

Overclaim risk:
- OVERCLAIM_RISK: ...
- Unsafe wording: ...

Safer framing:
- Chinese positioning: ...
- English paper-safe phrasing: ...

Next questions:
1. ...
2. ...
3. ...
```

### H-DECIDE

Purpose: convert a discussion consensus into a project decision.

Required behavior:
- first output a write-in plan;
- wait for explicit user confirmation before editing decision logs or trackers;
- scope what the decision applies to and does not apply to;
- do not patch manuscript files.

Output before writing:

```markdown
Decision draft:
- ...

Scope:
- Applies to: ...
- Does not apply to: ...

Evidence status:
- SUPPORTED / PARTIAL / MISSING / RISKY / UNKNOWN

Reviewer concerns addressed:
- ...

Risks / conditions:
- ...

Sync needed:
- YES / NO / LATER

Need confirmation:
- YES
```

### H-TITLE-ITERATE

Purpose: generate or revise title candidates.

Required behavior:
- base candidates on locked story, active project direction, and evidence state;
- do not modify title files or LaTeX;
- do not assume the story is frozen unless the project memory says so;
- avoid broad words such as `practical`, `large-scale`, `general`, `universal`, `end-to-end`, and `secure` unless scope and evidence support them.

Output:
- current title or title state if available;
- 3-6 title candidates;
- each candidate's claim, evidence status, venue fit, risk, and best-fit storyline;
- title directions to avoid;
- specific feedback choices for the next round.

### H-ABSTRACT-ITERATE

Purpose: revise an abstract interactively and incrementally.

Required behavior:
- start from the current abstract logic when available;
- prefer local, reversible changes unless the abstract structure is fundamentally wrong;
- do not patch manuscript files;
- label evidence gaps for every strong claim.

Output:
- current-version diagnosis;
- old logic to preserve;
- sentence-level keep/revise/delete/move analysis when text is available;
- claim-evidence-risk table;
- revised abstract candidate;
- next feedback choices.

### H-SECTION-ITERATE

Purpose: revise a manuscript section interactively.

Required behavior:
- identify the target section;
- provide a local modification plan before prose;
- preserve structure unless a structural problem is identified;
- do not patch files;
- check positioning before rewriting introduction, contribution, related work, evaluation, or threat model sections.

Output:
- target section;
- local problem diagnosis;
- local revision plan;
- content to keep;
- content to move or delete;
- claim-evidence-risk table;
- candidate outline or prose if appropriate;
- whether user confirmation is needed before a patch.

### H-REVIEW

Purpose: simulate reviewer objections or audit draft text for venue fit, evidence gaps, and claim risk.

Read:
- `references/review_gate.md`;
- `references/venue_profiles.md`;
- direction packs relevant to the paper;
- project evidence map if available.

Output:
- likely reviewer objections ranked by severity;
- affected claims or sections;
- missing evidence;
- safer claim boundaries;
- concrete revision actions.

### H-PATCH

Purpose: apply a confirmed version to an exact file location.

Required behavior:
- require file path, exact location, and confirmed version;
- modify only the specified location;
- preserve citations, labels, refs, math, figures, tables, algorithms, comments, and formatting unless instructed otherwise;
- use the smallest patch that satisfies the request;
- show the changed target and a diff summary;
- run the relevant validation if available.

If the target is ambiguous, stop and ask one concise clarification.

Output:

```markdown
Patch target:
- File: ...
- Location: ...

Pre-patch check:
- Preserved commands/citations/labels: YES / issue
- Ambiguity: none / ...

Applied changes:
- ...

Diff summary:
```diff
...
```

Verification:
- Command: ...
- Status: PASS / FAIL / NOT_RUN
- First actionable error if any: ...
```

### H-LOG

Purpose: record discussion, decisions, or project state in the correct project memory layer.

Required behavior:
- distinguish temporary discussion, project fact, decision, and long-term reusable lesson;
- do not write temporary ideas into the progress tracker;
- do not write project facts into HElicon core;
- ask for confirmation before writing unless the user explicitly instructs a target and content.

Output before writing:

```markdown
Log target:
- iteration_log / decision_log / progress_tracker / project_pack / none

Layer:
- temporary discussion / project fact / confirmed decision / long-term lesson

Write plan:
- ...

Need confirmation:
- YES / NO
```

### H-SYNC

Purpose: synchronize current project state after patching, deciding, or iterating.

Required behavior:
- do not patch manuscript text;
- read current manuscript state only for the affected scope;
- read project memory files when available;
- identify unrecorded consensus, unrecorded patches, stale tracker items, and open decisions;
- classify sync candidates.

Classification:
- A. locked project status for progress tracker;
- B. workbench iteration records;
- C. temporary ideas for iteration log only;
- D. stale or obsolete ideas that should not be preserved.

Output before writing:

```markdown
Sync scope:
- ...

Files read:
- ...

Detected current state:
- ...

Unrecorded consensus:
- ...

Unrecorded patches:
- ...

Stale tracker items:
- ...

Sync classification:
- A. Progress tracker candidates: ...
- B. Workbench candidates: ...
- C. Discussion log candidates: ...
- D. Do-not-save stale ideas: ...

Write plan:
- Target files: ...
- Changes: ...

Need confirmation:
- YES
```

### H-SYNC-REPAIR

Purpose: repair missed synchronization after long conversations, context loss, or unsynchronized patches.

Required behavior:
- do not modify manuscript text;
- compare current manuscript, workbenches, decision log, iteration log, claim matrix, and tracker when available;
- distinguish confirmed decisions from plausible but unconfirmed inferences;
- classify repair candidates using the same A/B/C/D scheme as `H-SYNC`;
- wait for confirmation before writing.

Output:
- repair scope;
- files read;
- patched-but-unrecorded content;
- discussed-but-undecided consensus;
- stale tracker items;
- repair classification;
- write plan;
- confirmation request.

### H-REOPEN

Purpose: reopen an earlier title, abstract, section, claim, or decision when new evidence, contradiction, reviewer risk, or scope change invalidates part of it.

Required behavior:
- do not patch files;
- identify what remains valid and what must change;
- propose the next command.

Output:

```markdown
Reopen target:
- ...

Why reopen:
- New evidence / contradiction / reviewer risk / scope change / UNKNOWN

Old conclusion:
- ...

Still valid:
- ...

Needs change:
- ...

Risk if not reopened:
- ...

Recommended next command:
- H-DISCUSS / H-DECIDE / H-TITLE-ITERATE / H-ABSTRACT-ITERATE / H-SECTION-ITERATE
```

## Quick Command Selection

| Situation | Use | Next |
|---|---|---|
| New idea or uncertain claim | `H-DISCUSS` | `H-DECIDE` or gather evidence |
| Consensus should become a decision | `H-DECIDE` | `H-SYNC` |
| Need title options | `H-TITLE-ITERATE` | `H-DECIDE` or `H-PATCH` |
| Need abstract revision | `H-ABSTRACT-ITERATE` | `H-PATCH` |
| Need section revision | `H-SECTION-ITERATE` | `H-PATCH` |
| Confirmed text should be written | `H-PATCH` | `H-SYNC` |
| Project memory may be stale | `H-SYNC` | confirmation |
| Previous work was not synchronized | `H-SYNC-REPAIR` | confirmation |
| A prior decision may be wrong | `H-REOPEN` | `H-DISCUSS` or `H-DECIDE` |
| Need to record without deciding | `H-LOG` | continue |
