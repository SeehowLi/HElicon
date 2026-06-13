# FHE Domain Brief

HElicon should preserve FHE technical specificity and avoid vague claims.

## Required technical details to check

For FHE/HE papers, inspect whether the draft specifies:

- scheme: CKKS, BFV, BGV, TFHE, hybrid HE/MPC/TEE/plaintext;
- library and version if relevant;
- security level;
- polynomial modulus degree;
- coefficient modulus chain;
- scale and precision for CKKS;
- noise budget or error behavior;
- packing layout and slot utilization;
- rotation count and rotation-key assumptions;
- key switching and relinearization costs;
- bootstrapping count and placement;
- multiplicative depth;
- memory footprint;
- communication cost;
- latency and throughput;
- hardware setup;
- approximation error and downstream accuracy;
- leakage boundary and threat model.

## Private inference / LLM-specific checks

Ask what is protected:

- user input/prompt;
- model weights;
- intermediate activations;
- output;
- access pattern;
- sequence length and batch shape;
- model architecture and supported operators;
- nonlinearities, attention, normalization, softmax/GELU approximations;
- hybrid components such as MPC, TEE, plaintext preprocessing, client-side computation.

Do not claim "private LLM inference" if only a narrow component is encrypted. Use scoped language.

## Encrypted kNN/search-specific checks

Ask:

- Is the query encrypted?
- Is the database encrypted?
- Are labels encrypted?
- Is the result hidden from the server?
- Is access pattern hidden?
- Is top-k exact or approximate?
- Which distance metric is used?
- How do complexity and cost scale with n, d, k, packing factor, and ciphertext count?
- Does the method require interaction, preprocessing, or leakage not captured in the main claim?

## Optimization writing rule

A credible FHE optimization claim should identify the dominant cost and why the method changes that cost model, for example:

- fewer rotations;
- fewer bootstraps;
- lower multiplicative depth;
- better packing/slot utilization;
- fewer ciphertexts;
- reduced memory movement;
- better batching;
- fewer key-switching operations;
- improved end-to-end latency under the same security level.

Tie every performance claim to a cost component and evidence.
