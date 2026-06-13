# Technical Framing

Technical framing is the art of making the contribution legible without exaggerating it.

## From implementation detail to contribution

Weak:
- We reduce the number of rotations.
- We optimize kNN under FHE.
- We implement private inference.

Stronger:
- Identify the dominant encrypted-domain cost.
- Explain why existing formulations incur it.
- State the structural insight that changes the cost.
- Connect the design to a measurable improvement.
- State the scope and remaining leakage.

## Framing template

Use this pattern when enough evidence exists:

1. In `<setting>`, the dominant cost is not only `<surface operation>` but `<FHE-specific cost>`.
2. Existing approaches inherit this cost because `<structural reason>`.
3. The key observation is that `<property>` allows `<reformulation>`.
4. Based on this observation, the system/algorithm `<design action>`.
5. This reduces `<cost component>` while preserving `<security/privacy boundary>` under `<parameters/threat model>`.

Never invent the placeholders. Mark missing parts explicitly.

## Metric-bound framing checks

- Replace generic "FHE is slow" with named resources: depth, rotations, key switching, modulus budget, precision bits, memory movement, bootstrapping latency, communication, or client-side burden.
- Bind `efficient` to a metric and setting: latency, throughput, depth, rotations, modulus, precision, memory, communication, rounds, or client cost.
- Distinguish encryption noise, approximation error, scale-management error, and model-utility loss.
- Runtime claims need security parameters and comparable settings.
- Privacy motivation should identify the leakage surface: output, access pattern, ranking/order, timing, interaction, or setup artifacts.
- Deployment claims should account for latency, communication, interaction rounds, accuracy/utility, client-side computation, and client-side storage.
- Systems contributions should be framed as abstraction, automation, composition, portability, or deployment evidence, not as an API list.
- A system boundary must distinguish the paper's contribution from bundled dependencies and existing libraries.
- Evaluation must verify the claim using metrics that correspond to the stated bottleneck.
- If a cost is shifted to preprocessing, memory, keys, storage, setup, or client work, say so explicitly.

## Safe contribution verbs

Prefer:

- identifies;
- reformulates;
- restructures;
- decomposes;
- co-designs;
- amortizes;
- reduces;
- avoids;
- preserves;
- exposes;
- quantifies;
- demonstrates.

Avoid unless strongly supported:

- solves;
- eliminates;
- guarantees;
- fully protects;
- scales to arbitrary;
- makes FHE practical generally;
- first, unless verified.

## Packaging vs framing

The user's Chinese phrase "技术包装" should usually be rendered as:

- technical framing;
- contribution framing;
- positioning;
- narrative framing;
- making the technical insight legible.

Do not use "technical packaging" in paper prose.
