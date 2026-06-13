# Story Logic Framework

HElicon should optimize paper logic before surface prose.

## Default argument arc

For FHE/privacy/security papers, the default story is:

1. A real privacy/security task is important.
2. Existing practical approaches leave a gap: leakage, trust, accuracy, deployment, or performance.
3. FHE/HE offers a principled path but exposes a concrete computational bottleneck.
4. Existing FHE formulations inherit the bottleneck because of a structural mismatch between the algorithm and encrypted computation.
5. The paper's key insight changes the representation, computation schedule, packing layout, protocol boundary, or cost model.
6. The design follows from the insight.
7. Experiments show the specific claimed improvement under clear parameters and workloads.
8. The paper states what remains limited.

## Common story failures

- Starting with FHE background instead of a security/privacy problem.
- Claiming "privacy-preserving" without a threat model.
- Jumping from application motivation to implementation details without a bottleneck.
- Listing contributions that sound like engineering tasks.
- Using adjectives such as efficient, practical, scalable without evidence.
- Hiding limitations until reviewers discover them.
- Using related work as a paper list rather than a set of unresolved tensions.

## Paragraph roles for introductions

A strong introduction usually includes:

1. Motivation and security/privacy need.
2. Why existing solutions are insufficient.
3. Why HE/FHE is attractive but difficult.
4. The specific bottleneck or mismatch.
5. Key insight.
6. Design summary.
7. Evaluation summary with scoped numbers.
8. Contributions.
9. Limitations or scope when necessary.

## Domain-specific introduction arcs

- FHE algorithm papers: explain why the operation matters before formulas; name the resource that blocks the workload, then introduce the representation or protocol change.
- Private inference papers: move from model-serving privacy risk to threat model, then expose the model/protocol stage that blocks deployment.
- Encrypted retrieval papers: separate distance computation from ranking, comparison, and top-k selection before presenting the method.
- Systems papers: show who experiences the friction: application developer, compiler writer, cryptography expert, backend maintainer, or end user.
- Security/privacy venue papers: turn technical detail into a reviewer-visible obstacle before presenting the mechanism.

Do not introduce dense notation, formulas, or low-level implementation details until the reader understands the problem, bottleneck, and claim boundary.

## Story diagnosis output

When diagnosing a draft, output:

- current one-sentence story;
- intended one-sentence story;
- missing bridge paragraphs;
- claim-evidence-risk table;
- recommended paragraph order;
- top three reviewer misunderstandings to prevent.
