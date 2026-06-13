# HElicon Direction Packs

These direction packs are focused writing-knowledge modules distilled from reviewed canonical paper patterns. They are not surveys and should not be used as paper summaries.

## Available Packs

| direction | best fit |
|---|---|
| `fhe_algorithm_optimization` | FHE/CKKS algorithm papers focused on bootstrapping, modular reduction, comparison, packing, precision, depth, rotations, or homomorphic kernels. |
| `private_llm_inference` | Secure transformer inference, private LLM serving, non-interactive STFI, model-protocol co-design, client/server burden, communication and utility tradeoffs. |
| `encrypted_knn_search` | Encrypted kNN, secure retrieval, oblivious top-k, encrypted ranking, order statistics, homomorphic sorting, private vector search. |
| `fhe_systems` | FHE libraries, compilers, runtimes, hardware/backend abstraction, scheme switching, encrypted database frameworks, deployable FHE systems. |
| `security_top_conference_writing` | Security top-conference framing for HE/FHE/privacy papers: threat model, deployment bottleneck, aligned contribution story, end-to-end evaluation. |

## External Workspace Path

This README is an index. The preferred maintained source for focused pack files is external:

`~/HElicon_workspace/direction_packs/<direction>/focused_writing_knowledge.md`

If installed copies also exist under this directory, treat them as focused direction references, not HElicon core memory and not project-specific facts.

## Recommended Combinations

- FHE algorithm paper: `fhe_algorithm_optimization` + optional `security_top_conference_writing`.
- Private transformer/LLM inference paper: `private_llm_inference` + `security_top_conference_writing` + optional `fhe_algorithm_optimization` when the contribution includes FHE kernels.
- Encrypted kNN / private retrieval paper: `encrypted_knn_search` + optional `fhe_algorithm_optimization` for comparison/sorting primitives + optional `security_top_conference_writing` for top-venue framing.
- FHE library/compiler/runtime paper: `fhe_systems` + `security_top_conference_writing` + optional `fhe_algorithm_optimization` if kernel design is central.
- Encrypted database or hybrid query system: `fhe_systems` + `encrypted_knn_search` when ranking/retrieval is central + `security_top_conference_writing` for threat/evaluation framing.

## NOMOS Combination Example

NOMOS is treated here only as a conditional example, not as a source of project facts.

- If NOMOS is framed as an HE/FHE algorithm or primitive paper, prioritize `fhe_algorithm_optimization` + `security_top_conference_writing`.
- If NOMOS is framed as privacy-preserving inference or secure model serving, prioritize `private_llm_inference` + `security_top_conference_writing` + optional `fhe_algorithm_optimization`.
- If NOMOS is framed around encrypted retrieval, ranking, or top-k, prioritize `encrypted_knn_search` + `fhe_algorithm_optimization` + `security_top_conference_writing`.
- If NOMOS is framed as a system, compiler, runtime, or deployable framework, prioritize `fhe_systems` + `security_top_conference_writing`.

## Private LLM Inference Combination

For a private LLM inference paper, load these packs in order:

1. `private_llm_inference` for threat model, deployment burden, non-interactivity, model utility, and communication story.
2. `security_top_conference_writing` for top-conference framing, reviewer concerns, related-work positioning, and end-to-end evaluation logic.
3. `fhe_algorithm_optimization` if the paper depends on bootstrapping, packing, approximation, homomorphic softmax, activation, comparison, or linear transform improvements.
4. `fhe_systems` only if the paper contributes a reusable system, runtime, compiler, or framework beyond a protocol/algorithm.

## Use Rules

- Do not treat packs as surveys.
- Do not copy paper text from source papers.
- Use packs to shape problem framing, bottleneck language, contribution structure, title/abstract/introduction/evaluation moves, terminology, and reviewer-risk checks.
- If a paper spans multiple directions, combine packs but keep one primary story.
