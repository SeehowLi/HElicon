# Contribution Patterns

## Strong contribution structure

A strong contribution sentence normally includes:

- task or setting;
- bottleneck or limitation;
- technical insight;
- design mechanism;
- evidence or measurable effect;
- claim boundary.

## Patterns

### Cost-model contribution

"We identify `<FHE-specific cost>` as a dominant bottleneck in `<task>` and show that `<reformulation>` reduces `<operation/cost>` under `<security/workload conditions>`."

### Representation contribution

"We introduce a `<representation/packing/layout>` that aligns `<algorithmic structure>` with ciphertext slots, reducing `<cost>` without changing `<privacy boundary>`."

### System contribution

"We design and implement `<system>` for `<privacy task>`, combining `<techniques>` to support `<scope>` under `<threat model>`."

### Measurement contribution

"We provide an evaluation of `<task>` across `<workloads>` and quantify how `<bottleneck>` affects `<latency/throughput/memory/accuracy>`."

### Deployment-bottleneck contribution

"We identify `<deployment bottleneck>` as the main barrier to practical `<secure task>` and design `<system/protocol/operator>` to address it while preserving `<security/utility/functionality>`."

### FHE algorithm contribution

Structure the contribution as:

1. identify the bottlenecked operator or subroutine;
2. introduce a new route, representation, approximation, or transform;
3. analyze the relevant complexity, precision, or correctness property;
4. implement under comparable security parameters;
5. show downstream workload consequence.

Reusable sentence:

"We show that this reduces `<depth/rotations/error/modulus/latency>` while preserving `<precision/security/functionality>`."

### Privacy inference contribution

Structure the contribution as:

1. define the threat and deployment model;
2. identify the model/protocol bottleneck;
3. co-design protocol, representation, approximation, or model component;
4. explain the interaction, communication, or user-burden improvement;
5. evaluate accuracy, latency, communication, and client-side cost.

### Retrieval pipeline contribution

Structure the contribution as:

1. define the retrieval task and leakage boundary;
2. identify the ordering, comparison, or top-k bottleneck;
3. introduce the comparison, selection, or ranking mechanism;
4. integrate it into the retrieval pipeline;
5. evaluate correctness, leakage, runtime, communication, and scale.

### Systems-layer contribution

Structure the contribution by layer:

1. artifact boundary;
2. architecture or abstraction;
3. automation, compiler, interface, or backend support;
4. workflow coverage;
5. evaluation and limitations.

## Anti-patterns

Avoid contribution lists that read like a development log:

- implemented module X;
- optimized function Y;
- evaluated on dataset Z.
- claimed "framework" without defining the abstraction boundary or verifying capability/workflow coverage.

Instead, connect each item to a claim and evidence.
