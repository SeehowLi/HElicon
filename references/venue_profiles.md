# Venue Profiles for Security Top Conferences

Target venues: USENIX Security, NDSS, ACM CCS, IEEE S&P.

These are writing and positioning heuristics, not hard rules.

## USENIX Security

Useful framing:

- security/privacy problem with real deployment implications;
- strong systems design and end-to-end evaluation;
- convincing workloads, baselines, ablations, and artifact-like concreteness;
- practical constraints such as latency, throughput, memory, communication, and engineering trade-offs.

Risks:

- paper reads like a narrow algorithmic micro-optimization;
- evaluation is only toy benchmarks;
- security/privacy relevance is asserted but not operationalized.

## NDSS

Useful framing:

- networked or deployed setting;
- clear protocol roles and threat model;
- leakage, communication, latency, and deployment constraints;
- system behavior under realistic settings.

Risks:

- cryptographic computation is described without deployment boundary;
- access-pattern or metadata leakage is ignored;
- roles such as client, server, database owner, model owner, and querier are unclear.

## ACM CCS

Useful framing:

- broad enough for applied cryptography, privacy systems, secure computation, and systems security;
- clear novelty in either cryptographic cost model, system design, or privacy application;
- strong related-work positioning across neighboring communities.

Risks:

- contribution appears incremental or only implementation-level;
- FHE is treated as a black-box tool;
- paper does not explain why the work belongs in security rather than only ML/systems.

## IEEE S&P

Useful framing:

- rigorous threat model and security/privacy claim boundary;
- precise novelty and conceptual contribution;
- careful argumentation and limitation awareness;
- strong evidence that claims do not exceed experiments.

Risks:

- vague "privacy-preserving" language;
- unsupported practicality claims;
- missing security analysis or leakage boundary.

## Cross-venue writing rule

A strong HE/FHE paper for security venues should not merely say "we make encrypted computation faster." It should connect:

privacy/security need -> infeasibility or bottleneck in encrypted computation -> technical insight -> system/algorithm design -> evidence -> carefully scoped implication.

For top security venues, generalize HE/FHE/privacy work into an aligned story:

- credible threat or deployment model;
- deployment-relevant bottleneck;
- method that directly targets that bottleneck;
- fair baselines and realistic scale;
- end-to-end evidence tied to the claim;
- explicit limitations and leakage boundary;
- related work grouped by paradigm, threat model, interaction model, functionality, precision/scale, and deployment assumption.

Avoid algorithm流水账. Convert low-level technique into a security/deployment obstacle and a claim-verifying evaluation.
