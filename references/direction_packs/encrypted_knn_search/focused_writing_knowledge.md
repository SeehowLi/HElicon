# Encrypted kNN Search Focused Writing Knowledge

## 1. When to use this direction pack

当论文涉及 encrypted kNN、secure k-NN classification、oblivious top-k、encrypted ranking、homomorphic sorting、order statistics、encrypted database retrieval、private vector search 或 RAG-style private retrieval 时加载本方向包。

当前方向 core evidence 较少，因此使用时要把它当作 retrieval-writing scaffold，而不是完整 survey。若论文核心是 comparison/sorting primitive，应组合 `fhe_algorithm_optimization`；若论文面向安全顶会系统，应组合 `security_top_conference_writing`。

## 2. Core problem framing

常见框架是：`privacy-preserving retrieval requires ranking -> ranking requires comparison/top-k/sorting -> encrypted domain makes ordering the hard part`。

不要把 kNN 写成只有 distance computation。真正的论文故事通常是 distance representation、comparison、selection、synchronization、top-k output 和 leakage boundary 的组合。好 framing 会先说明明文 retrieval pipeline 的自然步骤，再指出哪一步在 encrypted state 中失去简单性、泄漏控制或可扩展性。

## 3. Security/privacy motivation

常见隐私动机包括保护 query、database records、distance values、rank order、top-k membership 或 classification result。安全动机要写 leakage surface：server 不应看到 query，client 不应获得超过授权的 database 信息，protocol 不应通过 access pattern、rank order 或 top-k selection 泄漏额外信息。

## 4. Technical bottleneck framing

技术瓶颈通常不是 distance formula，而是 ordering primitive：

- encrypted distances 需要比较才能变成 ranking。
- top-k selection 需要在不泄漏 order/access pattern 的情况下执行。
- sorting networks、comparison approximation 或 order statistics 可能支配成本。
- real-valued encrypted data 会引入 ordering precision 和 tie/duplicate handling 问题。

常用语言：`encrypted ranking`, `oblivious top-k`, `homomorphic comparison`, `order statistics`, `sorting network`, `distance comparison`, `access-pattern leakage`, `ranking leakage`, `top-k correctness`。

## 5. Core insight framing

核心 insight 应围绕 retrieval pipeline，而不是孤立算子。

Reusable English templates:

- `The key observation is that secure retrieval is bottlenecked by ordering, not by distance computation alone.`
- `We separate distance evaluation from rank selection to control both cost and leakage.`
- `The protocol changes the top-k selection path so that ranking information is not exposed beyond the intended output.`
- `The comparison primitive is designed around retrieval correctness, not only local approximation error.`

## 6. Contribution framing

常见结构：

1. Define secure retrieval / kNN setting and leakage boundary.
2. Identify the ordering or top-k bottleneck.
3. Introduce encrypted comparison / selection / sorting mechanism.
4. Integrate it into kNN classification or retrieval protocol.
5. Evaluate correctness, leakage, runtime, communication, and scale.

Reusable English templates:

- `We formulate <retrieval task> as an encrypted ranking problem under <leakage model>.`
- `We introduce <selection/comparison mechanism> that reduces <cost/leakage> in the top-k stage.`
- `We integrate the primitive into an end-to-end secure kNN pipeline.`
- `We evaluate both ranking correctness and protocol cost.`

## 7. Title patterns

Recommended:

- `Secure kNN for <deployment setting> using <crypto primitive>`
- `Revisiting Oblivious Top-k Selection with Applications to <task>`
- `Efficient Ranking, Order Statistics, and Sorting under <HE scheme>`
- `Optimized Rank Sort for Encrypted Real Numbers`

Avoid:

- `Encrypted Search` without saying ranking/top-k/kNN.
- Titles that imply distance-only contribution when the bottleneck is ordering.
- Claims of secure retrieval without leakage boundary.

## 8. Abstract patterns

Sentence function order:

1. State privacy-preserving retrieval or classification need.
2. Explain why ranking/top-k is the hard encrypted step.
3. Identify prior cost or leakage limitation.
4. Introduce selection/ranking/comparison mechanism.
5. State retrieval-level consequence.
6. Report query size, runtime, top-k correctness, precision, communication, or leakage boundary.

## 9. Introduction arc

Recommended paragraph arc:

1. Retrieval/kNN is useful but query/database privacy matters.
2. Distance computation can be encrypted, but ranking and top-k remain hard.
3. Prior methods trade off interaction, sorting cost, precision, or leakage.
4. The paper isolates ordering as the central bottleneck.
5. The proposed method changes ranking/selection cost or leakage.
6. End-to-end retrieval or classification evidence.

## 10. Evaluation narrative

Evaluation should prove retrieval-specific claims:

- database size
- query dimension
- k value
- distance metric
- top-k correctness / classification accuracy
- runtime and communication
- leakage or security boundary
- tie/duplicate behavior if relevant
- whether comparison/sorting dominates end-to-end cost

## 11. Related-work positioning

Group related work by pipeline stage:

- secure retrieval protocols
- encrypted distance computation
- homomorphic comparison / sign approximation
- oblivious top-k / selection
- sorting networks / order statistics
- encrypted database or vector search systems

Technical contrast should say exactly which pipeline stage is improved and what leakage or cost remains.

## 12. Terminology

- Recommended English: `encrypted kNN`, `secure k-NN classification`, `oblivious top-k`, `encrypted ranking`, `order statistics`, `homomorphic sorting`, `comparison primitive`, `distance comparison`, `access-pattern leakage`, `ranking leakage`, `top-k correctness`, `tie handling`.
- Avoid: distance-only framing, ignoring top-k leakage, omitting k/dimension/database size, treating comparison improvement as automatic retrieval improvement, over-claiming from low evidence.
- Chinese explanation: 这些术语用于把 retrieval task 拆成可评审的 operator chain，并明确每个阶段的 leakage 和 cost。

## 13. Reviewer-risk checklist

- Ranking 是否泄漏超出预期的信息？
- k、dimension、database size 是否现实？
- Distance precision 是否影响 ordering correctness？
- Ties / duplicates 是否处理？
- Comparison/sorting 是否真是 end-to-end bottleneck？
- Primitive improvement 是否真的改善 retrieval task？
- Leakage model 是否清楚？

## 14. How HElicon should use this pack

当未来论文涉及 encrypted search、secure kNN、top-k、ranking、order statistics 或 private retrieval 时加载本包。HElicon 应用本包来强制写出 retrieval pipeline 和 leakage boundary。若贡献偏底层 comparison/sorting，组合 `fhe_algorithm_optimization`；若贡献偏系统或安全顶会，组合 `security_top_conference_writing`。
