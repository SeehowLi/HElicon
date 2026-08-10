# External Advisor Protocol

This protocol defines the handoff loop among HElicon, prompt-counselor, a flagship model, and Codex. It protects scope and provenance when a writing or skill-design problem needs outside strategic reasoning.

## Four-party loop

1. **HElicon** identifies the research-writing state, locked claims, unresolved problem, project boundary, and sensitivity inventory. `H-EXPORT` packages this state.
2. **prompt-counselor**, when explicitly invoked, clarifies the rescue need and produces its design-brief handoff. HElicon does not impersonate this clarification workflow.
3. **Flagship model** performs high-level diagnosis or design and returns both its rationale and an execution instruction for Codex. It receives no file-write authority.
4. **Codex** uses `H-INGEST` to compare the advice with current state, expose conflicts, and propose a scoped implementation. It edits only after the normal authorization boundary.

After implementation, HElicon updates project state through the appropriate confirmed synchronization path. The loop may repeat with verification evidence.

## Outbound handoff fields

An external-advisor bundle contains:

- bundle type and requested outcome;
- current HElicon version and relevant feature state;
- project state and manuscript summary when in scope;
- claim ledger and evidence/citation status;
- precise open problem;
- attempted approaches and observed failure reasons;
- desired correct state;
- constraints, immutable set, compatibility obligations, and prohibited changes;
- available artifacts and verification already run;
- requested return format;
- sensitivity inventory.

Put constraints before optional background. Use labeled, machine-oriented fields and one enclosing code block.

## Return contract

Ask the flagship model to return:

- assumptions and uncertainty;
- root-cause or design diagnosis;
- recommended decision and rejected alternatives;
- compatibility and risk analysis;
- a scoped Codex execution instruction with exact files or components;
- required tests and acceptance criteria;
- unresolved questions.

For `mode=advice`, the flagship model designs or diagnoses; it does not claim to have edited local files.

## Ingest contract

`H-INGEST` separates advice into `core`, `direction pack`, `project pack`, and `do not write back`. It reports current-versus-proposed differences, conflicts with Iron Rules or locked decisions, required evidence, scoped patches, and validation. It never auto-applies the returned plan.

## Boundaries

- HElicon owns research-writing diagnosis and state packaging, not prompt-counselor's clarification role.
- prompt-counselor clarifies and packages; it does not implement or repair files.
- the flagship model advises; it cannot verify unseen local state or authorize writes.
- Codex implements only the approved scope and reports real verification.
- Sensitive content is named, not silently removed. The author decides what leaves the local machine.
