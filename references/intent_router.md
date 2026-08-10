# Intent Router

The router handles ordinary requests when the author does not use an HElicon command. Its default behavior is to return useful revised text immediately, without a workflow preface or an unnecessary question.

## Signal priority

1. If the message contains an `H-*` token, execute its command contract. The router does not reinterpret it.
2. Classify the supplied material: path, whole draft, section, paragraph, one or two sentences, or no text.
3. Read the requested depth: `改`, `润色`, `顺一下`, `读起来别扭`, polish, or awkward indicate language; `逻辑不通`, `顺序不对`, or what-is-this-saying indicate structure; `能不能站住`, `证据够不够`, or support indicate claims; write or add indicate generation; venue-fit language indicates positioning; ready-to-submit language indicates a final gate.
4. Detect task features: `Reviewer #`, `weakness`, `rebuttal`, or `R1/R2` indicates rebuttal; page overflow, deadline, or `压缩` indicates compression; citation, `bib`, or attribution questions indicate citation verification.
5. Use project context last: the previous pass and the target section's `draft_map` verdict refine, but do not override, an explicit request.

## Routing decisions

### Default zero-friction route

When the author supplies an English paragraph with no other instruction, run P3, then P4, then P5. Normalize terms, repair rhythm, and clean diction. Do not change structure, claim scope, numbers, citations, or other frozen content.

When the intent is ambiguous, choose the least destructive route and proceed. If sentence editing and structural editing are both plausible, edit sentences only and state in the trailer that the author can request the deeper route. A language-level mismatch is easy to correct; a silent structural rewrite is not.

Direct action means returning revised text, not writing a file. Router output never patches a source file. File writes still require `H-PATCH` or another command contract with an explicit confirmed write target.

### Upstream findings

If the default route notices an unsupported strong claim, a misplaced paragraph, or a `REWORK` draft-map verdict, finish the requested language work. Add a nonblocking upstream count to the trailer. Show the same warning only once per section in one session.

When several commands are required, sequence them automatically and report each attributable stage. Do not ask the author to invoke each command separately.

### Destructive boundary

The router never initiates an actual P1 claim rewrite or P2 structural rewrite. It may recommend P1 or P2 and wait for explicit approval, or execute them when the author invokes the corresponding command. This is the concrete boundary of least-destructive routing.

## Fixed trailer

Every routed result ends with exactly one scannable line:

```text
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none>[ · ⬆<N> upstream]
```

Keep pass identifiers in the trailer; do not replace them with a vague phrase such as "language optimized." For unrecognized projects, use a neutral project and section marker and `baseline:none`.

## Representative routes

| Input | Action |
|---|---|
| Bare English paragraph | P3 → P4 → P5; return revision and trailer |
| "This paragraph reads awkwardly" | P3 → P4 → P5 |
| "The logic here does not work" | Diagnose and propose P2; do not silently reorder |
| "Can this conclusion stand?" | Diagnose and propose P1; preserve the original claim until approved |
| Reviewer comment | Rebuttal triage, then the rebuttal contract |
| Page overflow near deadline | Deadline-compression contract with threat and claim scope frozen |
