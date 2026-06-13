# Review Gate

Use this before finalizing major writing.

## General paper risks

- The paper lacks a clear security/privacy problem.
- The main contribution sounds like engineering cleanup.
- The story jumps from application motivation to method details.
- Title and abstract overpromise.
- Introduction does not explain why existing approaches fail.
- Related work is a list instead of contrast.
- Evaluation does not support the strongest claims.
- Limitations are hidden or vague.

## FHE-specific risks

- Scheme and parameters are unclear.
- Security level is missing.
- Packing layout is underspecified.
- Rotation/key-switching/bootstrapping costs are not isolated.
- Claims mix microbenchmark and end-to-end results.
- Baselines are unfair or outdated.
- Approximation error or accuracy loss is ignored.
- Leakage boundary is vague.

## Security venue reviewer questions

- What is the threat model?
- What privacy claim is actually achieved?
- What leaks?
- Why is the contribution not incremental?
- Which cost dominates and how is it reduced?
- Are the baselines fair?
- Are workloads realistic?
- Can the result generalize beyond a toy setting?
- Are limitations explicit?

## Cross-direction reviewer checks

- Is the threat/deployment model credible and stated before evaluation?
- Do metrics match the paper's strongest claims?
- Are baselines fair, comparable, and clearly scoped?
- Is the scale realistic for the claimed deployment?
- Are utility/security tradeoffs explicit?
- Does the paper provide end-to-end evidence instead of microbenchmarks only?
- Are limitations stated before reviewers infer them?
- Are security parameters, modulus choices, precision, and benchmark settings comparable?
- Does the claimed primitive matter outside a toy benchmark?
- Is precision loss hidden or conflated with another error source?
- Does the method shift cost to precomputation, memory, keys, setup, or another party?
- Does the threat model cover input privacy, model confidentiality, or both when both are relevant?
- Is non-interactivity genuine, or is interaction hidden in setup/offline phases?
- Are communication, client storage, client compute, and model utility measured when deployment is claimed?
- Does ranking, top-k, or access behavior reveal more than the intended leakage?
- Is systems novelty more than engineering integration?
- Is usability or portability measured, not only claimed?

## Output format for review simulation

Use:

| Concern | Severity | Evidence in draft | Why reviewer cares | Revision action |
|---|---:|---|---|---|
