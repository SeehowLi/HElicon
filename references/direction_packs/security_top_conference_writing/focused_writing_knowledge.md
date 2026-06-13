# Security Top Conference Writing Focused Writing Knowledge

## 1. When to use this direction pack

当目标是把 FHE/privacy 技术写成 security top conference paper 时加载本方向包。适用对象包括 secure inference、encrypted database、FHE compiler、ranking/order statistics、bootstrapping precision、homomorphic softmax/activation、secure transformer systems、privacy-preserving retrieval。

它不是单一技术方向，而是写作方向：帮助把复杂 HE 技术写成 reviewer 能评审的 security/system story。

## 2. Core problem framing

常见框架是：`security/privacy need is real -> prior cryptographic capability exists -> deployment or systems bottleneck prevents adoption -> paper isolates one bottleneck that matters at scale`。

强写法会把技术细节压成可评审的 obstacle：non-interactivity、user burden、query expressiveness、precision at scale、compiler usability、operator compatibility、model utility、communication overhead。

## 3. Security/privacy motivation

安全动机必须具体到 parties、assets、leakage 和 deployment。不要只说 sensitive data。要说明：谁持有什么，谁不能看到什么，现有方案保护了什么但仍不好用，本文消除了哪类 deployment bottleneck。

典型 assets：client input、model weights、database records、query intent、ranking information、intermediate activations、program logic。

## 4. Technical bottleneck framing

把底层 HE/FHE/MPC 细节翻译成 paper-level obstacle：

- interaction barrier
- communication overhead
- client-side burden
- operator expressiveness
- precision bottleneck
- functional completeness
- hybrid query support
- model utility
- compiler abstraction
- end-to-end latency

Reviewer 应该能在不追公式的情况下理解瓶颈为什么阻碍 deployment。

## 5. Core insight framing

核心 insight 应把技术和 story 对齐：

- `The key observation is that the deployment bottleneck comes from <specific stage>, not from secure computation in general.`
- `The system aligns <cryptographic primitive> with <workload structure>.`
- `The abstraction separates <hard technical concern> from <user-facing workflow>.`
- `The protocol removes <interaction/communication/client burden> while preserving <security/utility>.`

## 6. Contribution framing

常见结构：

1. Identify a deployment-relevant security bottleneck.
2. Design a system/protocol/operator/abstraction.
3. Implement it in a realistic setting.
4. Evaluate end-to-end against fair baselines.
5. State limitations, availability, or artifact details.

Reusable English templates:

- `We identify <deployment bottleneck> as the main barrier to practical <secure task>.`
- `We design <system/protocol> that combines <technique A> and <technique B> to address this bottleneck.`
- `We implement <artifact> and evaluate it on <realistic workload>.`
- `Our evaluation shows improvements in <metric set> while preserving <security/utility>.`

## 7. Title patterns

Recommended:

- `<System>: <capability> Secure <workload> with <deployment property>`
- `<Artifact>: A Unified Representation for <cross-boundary task>`
- `<System>: <precision/scale capability> <secure system class> via <technical principle>`
- `<Primitive> under <HE scheme>` when the paper is algorithmic but venue-facing.

Avoid:

- Acronym-only titles.
- Titles that hide threat model or workload.
- Titles that sound like a narrow implementation note.

## 8. Abstract patterns

Sentence function order:

1. Give application/security setting.
2. State prior limitation.
3. Identify deployment bottleneck.
4. Introduce named system or method.
5. List aligned techniques.
6. Give end-to-end evidence.
7. Mention artifact availability if relevant.

## 9. Introduction arc

Recommended paragraph arc:

1. Application or threat scenario.
2. Prior secure computation / FHE progress.
3. Remaining deployment bottleneck.
4. Motivating example, table, or bottleneck diagram.
5. Key observation.
6. System/method overview.
7. Contributions and evaluation.

## 10. Evaluation narrative

Evaluation must verify the claim, not merely show speed:

- secure inference: accuracy, latency, communication, rounds, client burden.
- encrypted DB/retrieval: query classes, scale, precision, communication, leakage boundary.
- compiler/system: microbenchmarks, end-to-end programs, compile time, memory, functionality.
- FHE algorithm in top venue: security parameters, precision, runtime, downstream consequence.

Also explain limitations before reviewers infer them.

## 11. Related-work positioning

Related work is positioning, not bibliography. Group by paradigm, threat model, interaction model, functionality coverage, precision/scale, and deployment assumptions. Use tables when capability contrast matters.

Reusable contrast: `Unlike work that optimizes <narrow metric>, this paper targets <deployment bottleneck> under <threat/workload setting>.`

## 12. Terminology

- Recommended English: `threat model`, `deployment bottleneck`, `end-to-end evaluation`, `usability-efficiency dilemma`, `non-interactive`, `communication overhead`, `client-side burden`, `operator expressiveness`, `query expressiveness`, `model utility`, `precision at scale`, `functional completeness`, `artifact availability`.
- Avoid: algorithm流水账, microbenchmark-only evaluation, missing threat model, unfair baselines, early notation overload, acronym as contribution, hidden limitations, project-specific overfitting.
- Chinese explanation: 这些术语用于把安全动机、系统瓶颈、技术方案和评估证据对齐成同一条 story。

## 13. Reviewer-risk checklist

- Threat/deployment model 是否可信？
- Baselines 是否公平？
- Metrics 是否匹配 claims？
- Scale 是否现实？
- Utility/security tradeoff 是否明确？
- 是否只是 engineering integration？
- 是否有 end-to-end evidence？
- Limitations 是否主动说明？

## 14. How HElicon should use this pack

当论文目标是安全顶会、系统安全、隐私推理、加密数据库、FHE compiler 或 deployable HE/FHE contribution 时加载本包。HElicon 应用本包来检查 story alignment：problem framing、abstract、contribution、evaluation 和 related work 是否都服务同一个 reviewer-visible bottleneck。
