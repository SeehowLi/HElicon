# Private LLM Inference Focused Writing Knowledge

## 1. When to use this direction pack

当论文目标是 private inference、secure transformer inference、privacy-preserving LLM serving、non-interactive STFI、encrypted neural network inference，或涉及 FHE/MPC/hybrid protocol 与 model architecture co-design 时加载本方向包。

如果论文重点是底层 FHE 算子，例如 bootstrapping、softmax approximation、linear transform 或 packing，应同时加载 `fhe_algorithm_optimization`。如果论文目标是安全顶会系统故事，应同时加载 `security_top_conference_writing`。

## 2. Core problem framing

常见问题框架是：`modern model serving creates privacy demand -> secure inference exists -> deployment remains blocked by interaction, communication, client burden, nonlinear layers, or model architecture mismatch`。

不要把问题写成 “Transformer inference is slow”。要把模型结构拆成 linear layers、attention/softmax、activation、normalization、packing/format conversion、bootstrapping、client/server workload，然后说明哪一层把安全可行变成部署不可行。

## 3. Security/privacy motivation

本方向常见安全动机是双边的：client input privacy 和 server model confidentiality。更强的写法会继续说明 deployment burden：如果用户需要多轮交互、大量预处理、巨大通信、存储辅助材料或修改模型结构，即使协议安全也不够 usable。

安全动机要具体到 parties、assets 和 protocol stage。不要只说 “prompts are sensitive”。要说明谁持有什么，谁不能看到什么，哪一步会泄漏或增加用户负担。

## 4. Technical bottleneck framing

把瓶颈写成 model-protocol mismatch：

- Transformer 结构中的 nonlinear operators 很难直接同态计算。
- Linear layers 可批量化，但 packing format 会影响后续 nonlinear evaluation。
- Non-interactivity 可能把成本转移到 offline artifacts、client storage 或 server bootstrapping。
- Communication rounds 和 client-side work 可能比 raw server latency 更决定部署可行性。

常用语言：`non-interactivity`, `offline-online paradigm`, `client-side burden`, `communication bottleneck`, `Transformer operator mismatch`, `homomorphic softmax`, `activation approximation`, `model utility`, `server-side latency`。

## 5. Core insight framing

核心 insight 通常是 co-design：cryptographic primitive、packing format、approximation method、model layer 和 protocol schedule 互相配合。

Reusable English templates:

- `The key insight is to align the cryptographic representation with the layer structure of the model.`
- `Rather than optimizing each layer independently, the protocol preserves a format that makes the next layer cheaper.`
- `The offline phase is designed to remove online interaction without increasing the client's active workload.`
- `The approximation is chosen for end-to-end model utility, not only for local polynomial error.`

## 6. Contribution framing

常见结构：

1. Define the threat/deployment model.
2. Identify the Transformer-specific bottleneck.
3. Propose model/protocol/operator co-design.
4. Explain non-interactivity, communication, or user-burden improvement.
5. Evaluate accuracy, latency, communication, and client-side cost.

Reusable English templates:

- `We present <system>, a secure inference framework for <model class> under <threat model>.`
- `We identify <operator/protocol stage> as the main barrier to <deployment property>.`
- `We co-design <packing/protocol/model component> to reduce <rounds/communication/client work> while preserving <utility/security>.`
- `We evaluate end-to-end inference rather than isolated cryptographic kernels.`

## 7. Title patterns

Recommended:

- `<System>: Efficient and <deployment property> Secure Transformer Inference`
- `Secure Transformer Inference Made <property>`
- `<Architecture>: <module-level optimization> for Non-Interactive Secure Inference`
- `Privacy-Preserving <model class> with Homomorphic Encryption`

Avoid:

- Vague `Private LLM Inference` without workload or deployment property.
- Acronym-only titles.
- Titles that do not reveal whether the key property is non-interactivity, accuracy, communication, or user burden.

## 8. Abstract patterns

Sentence function order:

1. State LLM/Transformer serving and privacy threat.
2. Explain prior secure inference limitation.
3. Identify the specific deployment bottleneck.
4. Introduce named system or co-design principle.
5. List two or three aligned techniques.
6. Report accuracy, latency, communication, rounds, and client-side cost.

## 9. Introduction arc

Recommended paragraph arc:

1. LLM/Transformer services create input/model privacy risks.
2. Secure inference provides a path but remains hard to deploy.
3. The workload has specific structure: linear layers, attention, nonlinear layers, packing constraints.
4. Prior protocols fail on interaction, communication, utility, or user-side burden.
5. The paper's key observation aligns model structure with cryptographic representation.
6. Contributions and end-to-end evaluation.

## 10. Evaluation narrative

Evaluation should prove both security-serving and model-serving claims:

- Accuracy / model utility.
- End-to-end latency.
- Communication size.
- Number of rounds / non-interactivity.
- Client-side computation and storage.
- Server-side throughput.
- Comparison under the same model scale and threat model.

## 11. Related-work positioning

Group related work by paradigm:

- MPC-heavy secure inference.
- FHE-heavy secure inference.
- Hybrid FHE/MPC protocols.
- Non-interactive protocols.
- Model architecture optimization.
- Operator approximation.

Technical contrast should focus on deployment gap, not just speed: interaction, client work, communication, utility, model confidentiality, or supported model class.

## 12. Terminology

- Recommended English: `secure transformer inference`, `private inference`, `model confidentiality`, `input privacy`, `non-interactive`, `offline-online paradigm`, `client-side burden`, `communication rounds`, `packing format`, `homomorphic softmax`, `activation approximation`, `end-to-end inference`, `utility preservation`.
- Avoid: vague `private LLM inference`, runtime-only claims, `user-friendly` without client-side measurements, treating all Transformer layers as identical, hiding model architecture changes that affect utility, project-specific language in a direction-level pattern.
- Chinese explanation: 这些术语用于把安全协议、模型结构和部署成本连成一个故事。每个术语都应服务 threat model 或 deployment claim。

## 13. Reviewer-risk checklist

- Threat model 是否同时覆盖 input privacy 和 model confidentiality？
- Non-interactivity 是否真实，还是把交互藏到 setup？
- Offline cost 是否转移给 client？
- Accuracy 是否与明文或 prior secure inference 可比？
- Communication / client storage 是否实际可部署？
- 评估模型规模是否足够可信？
- Architecture changes 是否影响 utility？

## 14. How HElicon should use this pack

当未来论文涉及 secure inference、Transformer/LLM privacy、client/server burden、non-interactivity 或 model-protocol co-design 时加载本包。HElicon 应用本包来强制检查四类证据：security property、model utility、communication/rounds、client-side burden。若论文同时包含底层 FHE 算法贡献，组合 `fhe_algorithm_optimization`。
