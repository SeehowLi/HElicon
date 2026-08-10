# Unified Paper Patterns

This file stores cross-paper patterns distilled from many similar high-quality papers. It should become the main reusable writing knowledge base.

Do not copy sentences from papers. Store reusable structures, not text.

## Pattern A: FHE Cost-Model Optimization Paper

### Typical problem move

A privacy-preserving computation task is theoretically supported by HE/FHE, but direct encrypted-domain execution is dominated by one or more FHE-specific costs.

### Common bottleneck language

- rotations and key switching;
- bootstrapping placement;
- multiplicative depth;
- ciphertext expansion;
- poor slot utilization;
- memory movement and ciphertext layout;
- approximation error.

### Contribution move

The paper identifies a cost component that standard algorithm descriptions hide, then reformulates the algorithm or representation to reduce that cost.

### Evaluation expectations

- same security level;
- same task and workload;
- component-level ablation;
- end-to-end latency/throughput;
- memory and communication when relevant;
- accuracy/error if approximate arithmetic is used.

### Reusable writing principle

Do not say only "faster FHE." Say what cost was reduced, why it dominated, and why the redesign is technically non-obvious.

## Pattern B: Private Inference / Encrypted ML Systems Paper

### Typical problem move

Users want model predictions without exposing sensitive inputs, and sometimes model owners also want to protect model parameters. Existing approaches trade off privacy, trust assumptions, accuracy, latency, and deployability.

### Common bottleneck language

- nonlinear activations;
- attention and normalization;
- approximation of unsupported operations;
- ciphertext packing across tensor dimensions;
- client/server interaction;
- model-specific vs general support;
- latency and throughput under realistic model sizes.

### Contribution move

The paper narrows the privacy target, identifies the expensive encrypted operators, and co-designs model/operator/system components.

### Evaluation expectations

- model architecture and size;
- sequence length/batch size;
- security parameters;
- baselines such as prior FHE, MPC, TEE, or plaintext upper/lower bounds when appropriate;
- accuracy loss and approximation effects;
- ablations for each design decision.

## Pattern C: Encrypted Search / kNN / Retrieval Paper

### Typical problem move

A query or database contains sensitive information. The system should support retrieval or nearest-neighbor computation while limiting what the server learns.

### Common bottleneck language

- distance computation over ciphertexts;
- encrypted comparison or top-k selection;
- access-pattern leakage;
- dimensionality and database size scaling;
- packing layout for vector operations;
- interaction and communication.

### Contribution move

The paper clarifies what is hidden, what leaks, and how the encrypted computation is restructured to reduce the dominant cost.

### Evaluation expectations

- n, d, k scaling;
- distance metric;
- exact vs approximate top-k;
- leakage profile;
- latency, throughput, memory, communication;
- comparison with non-FHE private search if relevant.

## Pattern D: Security Systems Paper with Cryptographic Component

### Typical problem move

A real system need cannot be met by existing trust assumptions or privacy mechanisms. Cryptography is used as part of a system, not as a standalone artifact.

### Contribution move

The system defines roles, threat model, deployment boundary, and measurable security/privacy benefit, then evaluates performance and practicality.

### Evaluation expectations

- end-to-end workloads;
- deployment assumptions;
- stress tests;
- ablations;
- artifacts or reproducibility details;
- limitations.

## Pattern E: Security-Venue FHE Systems Paper

### Typical problem move

An FHE, HE, or secure-computation primitive can express the nominal task, but the real deployment workflow exposes a hidden bottleneck. Strong papers name that bottleneck as a reviewable obstacle such as tradeoff control, automation, abstraction boundaries, recurring workloads, or compound encrypted workflows.

### Common bottleneck language

- deployment bottleneck;
- workflow-level functionality;
- tradeoff surface;
- application-visible consequence;
- abstraction boundary;
- recurring workload;
- compound encrypted workflow;
- utility/cost frontier;
- end-to-end evidence.

### Contribution move

The paper identifies where the primitive-level abstraction is too narrow, then introduces a system, protocol, compiler, or workflow change that makes the real deployment path measurable. The best contribution lists align around one story: identify the hidden bottleneck, design the new abstraction or mechanism, enforce it in the system, and evaluate the resulting workflow.

### Evaluation expectations

- tradeoff claims need multiple points on the tradeoff surface;
- automation claims need a defined design or search space;
- boundary-change claims need evidence that the old boundary caused the cost;
- recurring-workflow claims need separate setup and recurring-path measurements;
- compound-workflow claims need every named stage evaluated.

### Reusable writing principle

Do not say only that FHE makes a task private. Say which real workflow remains unusable, which hidden cost or boundary causes the gap, and how the method makes that workflow deployable under the stated security model.

## Cross-direction writing moves

Use these moves when a paper spans FHE algorithms, private inference, encrypted retrieval, or systems:

- Build an aligned story: security/privacy need -> existing capability -> remaining deployment bottleneck -> key insight -> method -> claim-verifying evidence.
- Turn a technical trick into a paper-level contribution with: observation -> representation/protocol change -> cost metric -> workload consequence.
- Decompose application tasks into an operator chain before claiming that a primitive improvement solves the full task.
- Do not let an isolated primitive improvement substitute for an end-to-end story.
- When privacy work has multiple parties, frame both the security property and the burden assigned to each party.
- Treat artifact/system papers with the same story discipline as algorithm papers: problem framing, abstraction boundary, contribution structure, and evidence.
- Use related work for positioning, not bibliography. Group prior work by paradigm, threat/deployment assumption, functionality, and tradeoff.
- State limitations before reviewers infer them; aligned limitations improve credibility.

## How to update this file

After distilling 5-10 similar papers, collapse repeated observations into a pattern update:

- invariant problem framing;
- common bottleneck phrasing;
- title/abstract moves;
- contribution structures;
- evaluation standards;
- terminology choices;
- anti-patterns.
