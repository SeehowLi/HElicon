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

When the author supplies an English paragraph with no other instruction, select P3, then P4, then P5. First check P3 for an exact frozen-glossary mismatch and run the deterministic P4/P5 preservation preflight. If the preflight returns `preserve` and P3 found no mismatch, return the supplied paragraph byte-for-byte and report `0处`; selecting a pass does not require manufacturing an edit. Otherwise, apply only the triggered pass responsibilities. Do not change structure, claim scope, numbers, citations, or other frozen content.

When the intent is ambiguous, choose the least destructive route and proceed. If sentence editing and structural editing are both plausible, edit sentences only and state in the trailer that the author can request the deeper route. A language-level mismatch is easy to correct; a silent structural rewrite is not.

Direct action means returning revised text, not writing a file. Router output never patches a source file. File writes still require `H-PATCH` or another command contract with an explicit confirmed write target.

### Required context for language passes

The default P3 → P4 → P5 route names these references and project files; the context-budget rule must not omit them:

- P3: `language_polish.md`, `bilingual_glossary.md`, `fhe_lexicon_freeze.md`, and the active project's `.helicon/local_glossary.md` when present.
- P4 or P5: `pass_pipeline.md`, `language_polish.md`, `target_profile_policy.md`, and the results of `scripts/resolve_target_profile.py` plus `scripts/revision_preflight.py` for the active project and pass sequence. If the resolver returns `none`, the preflight applies rule-backed checks without a private target.
- P6: the same target resolver plus `personal_style_profile.md` and `style_baseline_policy.md`; baseline state remains independent of target state.

Run the resolver and preservation preflight before editing, not after composing the trailer. The resolver's `resolved_status` determines `target:<ok|partial|none>`; the preflight's `preserve|revise` decision determines whether P4/P5 may change the selection. A model-authored trailer alone is not evidence that either check ran. Do not load `target_screening.json`, revision-direction reports, hold-out ground truth, or exemplar prose unless the explicit command contract requires them.

### Upstream findings

If the default route notices an unsupported strong claim, a misplaced paragraph, or a `REWORK` draft-map verdict, finish the requested language work. Add a nonblocking upstream count to the trailer. Show the same warning only once per section in one session.

When several commands are required, sequence them automatically and report each attributable stage. Do not ask the author to invoke each command separately.

### Destructive boundary

The router never initiates an actual P1 claim rewrite or P2 structural rewrite. It may recommend P1 or P2 and wait for explicit approval, or execute them when the author invokes the corresponding command. This is the concrete boundary of least-destructive routing.

## Fixed trailer

Every routed result ends with exactly one scannable line:

```text
[HElicon] <项目名> §<节号> · <pass序列> · <改动处数> · frozen:<0变化|N处告警> · baseline:<ok|thin(n=N)|none> · target:<ok|partial|none>[ · sample:too-short][ · ⬆<N> upstream]
```

Keep pass identifiers in the trailer; do not replace them with a vague phrase such as "language optimized." Copy the target state from the resolver: `ok` means every eligible dimension owned by the requested passes came from a qualified exemplar for the active venue; `partial` means at least one eligible dimension uses `source: rule`, the venue differs, or the active venue is unknown; `none` means no valid target profile was resolved. For unrecognized projects, use a neutral project and section marker, `baseline:none`, and `target:none`.

Render multi-pass sequences with spaces around the arrow, for example `P3 → P4 → P5`. Evaluators also accept the historical compact form `P3→P4→P5` and normalize both to the same pass sequence.

For a one-sentence sample, append `· sample:too-short` before any upstream marker. This records that paragraph-level rhythm was not evaluated.

## Representative routes

`L1` means sentence-level language work. `L2` means a structural or claim-level diagnosis that may recommend P1 or P2 but cannot execute it silently. `Default` is the zero-friction P3 → P4 → P5 route.

| Input wording | Depth | Pass sequence or route | Explicitly excluded |
|---|---|---|---|
| Bare English paragraph | Default | P3 → P4 → P5; return revision and trailer | No claim or paragraph-order change |
| `这段读起来别扭` | L1, default | P3 → P4 → P5 | No structural rewrite |
| `这段有点绕` | L1, default | P3 → P4 → P5 | No paragraph reordering or claim strengthening |
| `这段说不清楚在干什么` | L2 | Diagnose the missing paragraph function; recommend P2 | Do not silently restructure |
| `这段的重点没出来` | L2 | Diagnose emphasis and recommend P2 | Do not invent or promote a contribution |
| `这个结论有点强` | L1 plus upstream claim finding | Preserve qualifiers during P3 → P4 → P5; recommend P1 | No claim-strength rewrite |
| `这么说会不会被challenge` | L1 plus upstream claim finding | Preserve hedging during P3 → P4 → P5; recommend P1 | No unsupported defense or stronger evidence label |
| `帮我把这段改得更像顶会的写法` | Default plus venue register | P3 → P4 → P5 with venue-register notes | No structural or novelty rewrite |
| `这里的术语统一一下` | L1, narrow | P3 only | No rhythm, deletion, or voice changes |
| `顺一下不要动意思` | L1, narrow | P4 only | No P5 deletion and no terminology substitution |
| `太啰嗦了删短点` | L1, compression | Audit P4 rhythm, then run P5 as primary; warn if deletion flattens sentence-length variance | No claim, evidence, or logical-connector deletion |
| One sentence, shorter than a paragraph | L1, short sample | Sentence-internal P3 → P4 → P5; mark `sample:too-short` | No paragraph-rhythm reconstruction |
| Chinese paragraph with a request for English prose | Translation plus writing | Translate research intent, then apply P3 → P4 → P5 to the English result | Do not treat Chinese surface form as an English polish target |
| Whole draft pasted or supplied by path | Intake | Recommend `H-INTAKE` before editing | Do not begin a whole-draft rewrite |
| Whole draft, author explicitly insists on immediate editing | Staged default | Start with the first section and proceed section by section through P3 → P4 → P5 | No simultaneous full-draft rewrite |
| `The logic here does not work` | L2 | Diagnose and recommend P2 | Do not silently reorder |
| `Can this conclusion stand?` | L2 | Diagnose evidence strength and recommend P1 | Preserve the original claim until approved |
| Reviewer comment or `Reviewer #` block | Rebuttal | Rebuttal triage, then the `H-REBUT` contract | No invented evidence or infeasible promise |
| Page overflow near deadline | Compression | `H-DEADLINE` contract | Freeze threat model and claim scope |
| Citation, BibTeX, or attribution question | Verification | `H-CITE` contract | Never verify from model memory |
| Ready-to-submit or pre-submission request | Gate | `H-GATE` contract | Audit only; do not patch files |
| Request to write a new paragraph without source prose | Generation | Draft from confirmed claim/evidence context, then P3 → P5 | Do not fabricate project facts or results |
