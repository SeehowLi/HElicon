# Abstract and Title Framework

## Title principles

A good title should communicate one or two of:

- problem setting;
- technical insight;
- security/privacy goal;
- system or algorithmic object;
- method scope.

Avoid titles that rely on unsupported adjectives:

- practical;
- scalable;
- efficient;
- secure;
- robust;
- fast;
- generic.

These words can be used only when the rest of the title scopes the claim.

## Domain-specific title rules

- HE/FHE algorithm titles should expose the primitive and setting, such as `<Primitive> for <specific HE setting>`.
- Security/systems titles should expose workload, capability, and deployment property, not only an acronym.
- Private inference titles should reveal whether the key property is non-interactivity, communication, user burden, accuracy, or model class.
- Encrypted retrieval titles should name ranking, top-k, kNN, or search when that is the real bottleneck.
- Systems titles should name the artifact class and boundary: library, compiler, runtime, framework, or system.
- Avoid acronym-only titles when the acronym hides threat model, workload, or contribution type.

## Title categories to generate

When asked for titles, group candidates:

1. security/systems framing;
2. FHE technical-insight framing;
3. application/privacy framing;
4. concise top-conference style;
5. conservative/precise version.

For each candidate, explain in Chinese:

- what it emphasizes;
- what it hides;
- which venue it fits;
- risk of overclaim or vagueness.

## Abstract skeleton

A default abstract should contain:

1. Problem and privacy/security motivation.
2. Gap in existing approaches.
3. Concrete HE/FHE bottleneck.
4. Key insight or design principle.
5. System/algorithm contribution.
6. Evidence: metrics, workloads, baselines, parameters.
7. Scoped implication.

## Domain-specific abstract orders

Use these as sentence-function orders, not fixed prose.

- FHE algorithm: capability/operation -> specific prior bottleneck -> key observation -> technical contribution -> metric improvement -> comparable implementation evidence.
- Private inference: serving privacy threat -> prior secure inference limitation -> deployment bottleneck -> co-design principle -> techniques -> accuracy/latency/communication/rounds/client-cost evidence.
- Encrypted retrieval: privacy-preserving retrieval need -> ranking/top-k hardness -> prior cost/leakage limitation -> comparison/selection mechanism -> retrieval-level consequence -> scale/correctness/communication/leakage evidence.
- Systems paper: FHE promise plus composition difficulty -> fragmentation or usability/performance tradeoff -> artifact and architecture principle -> key layers/capabilities -> coverage/performance/availability evidence.
- Security top-venue paper: application/security setting -> prior limitation -> deployment bottleneck -> method/system -> aligned techniques -> end-to-end evidence -> artifact/availability if relevant.

## Abstract revision output

For abstract tasks, output:

- six- or seven-sentence logic skeleton;
- English abstract;
- sentence role table;
- claim-evidence-risk table;
- terminology warnings;
- alternative version for a different venue if useful.
