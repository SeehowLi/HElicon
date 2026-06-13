# Direction Knowledge Map

Use direction packs when a project needs focused knowledge beyond the HElicon core.

## Recommended direction packs

### fhe_algorithm_optimization

Focus:
- ciphertext arithmetic cost model;
- rotations, key switching, bootstrapping, depth;
- packing and layout;
- parameter/security trade-offs;
- algorithm reformulation.

### private_llm_inference

Focus:
- privacy-preserving inference for large language models;
- operator approximation;
- attention/normalization/nonlinear layers;
- model-owner vs user privacy;
- hybrid HE/MPC/TEE designs;
- realistic model and sequence-size claims.

### encrypted_knn_search

Focus:
- FHE-based kNN;
- encrypted vector distance;
- top-k selection;
- access-pattern leakage;
- database/query privacy;
- scaling with n, d, k.

### fhe_systems

Focus:
- systems implementation and deployment;
- compiler/runtime/scheduler choices;
- end-to-end evaluation;
- engineering trade-offs;
- artifacts.

### security_top_conference_writing

Focus:
- threat/deployment model;
- deployment bottleneck;
- aligned contribution story;
- fair baselines and end-to-end evidence;
- related-work positioning;
- reviewer-risk and limitations language.

## Direction pack location

Treat direction packs as focused references, not HElicon core memory. The preferred maintained source is outside the core skill:

`~/HElicon_workspace/direction_packs/<direction_name>/focused_writing_knowledge.md`

Current reviewed direction packs:

- `fhe_algorithm_optimization`
- `private_llm_inference`
- `encrypted_knn_search`
- `fhe_systems`
- `security_top_conference_writing`

Load direction packs as focused references when a paper needs the direction. Do not promote their full direction-specific content into HElicon core memory.

New direction packs may still be created with `templates/direction_pack_template.md`.
