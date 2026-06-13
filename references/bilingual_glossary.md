# Bilingual Glossary

This glossary stores stable Chinese-to-English research terms for the user's papers. Update it continuously based on user feedback and selected papers.

| Chinese | Recommended English | Acceptable alternatives | Avoid | Notes |
|---|---|---|---|---|
| 全同态加密 | fully homomorphic encryption (FHE) | homomorphic encryption (HE), when leveled HE is intended | full homomorphic encryption | Use FHE when arbitrary-depth computation or common FHE framing is intended; use HE if the exact scheme is not fully homomorphic. |
| 同态计算 | homomorphic computation | encrypted computation, computation over encrypted data | homomorphic calculation | Use when emphasizing operations over ciphertexts. |
| 密文计算 | computation over ciphertexts | encrypted-domain computation | ciphertext calculation | Useful for systems narrative. |
| 同态实现 kNN | FHE-based kNN; encrypted k-nearest-neighbor search; homomorphic kNN evaluation | private kNN over encrypted data | homomorphic realization of kNN | Choose based on threat model and what is encrypted. |
| 大模型隐私推理 | privacy-preserving LLM inference | encrypted LLM inference; private inference for large language models | large model privacy inference | Be precise about whether model, input, output, or activations are protected. |
| 技术包装 | technical framing | contribution framing; positioning; narrative framing | technical packaging | Use only in meta discussion, not paper prose. |
| 文章定位 | paper positioning | positioning; venue positioning; problem framing | article positioning | Use for strategic diagnosis. |
| 故事线 | paper story | narrative arc; argument flow; storyline | story line | In paper comments, prefer narrative arc or argument flow. |
| 核心洞察 | key insight | central observation; core insight | core inspiration | Use sparingly and support with technical detail. |
| 威胁模型 | threat model | adversarial model, security model | threat-modeling | Be explicit about parties, assets, capabilities, leakage; state it before evaluation claims. |
| 泄露边界 | leakage boundary | leakage profile; leakage surface | privacy boundary only | Use when discussing what remains visible. |
| 访问模式泄露 | access-pattern leakage | leakage of access patterns | access leakage | Common for encrypted search/retrieval. |
| 泄漏面 | leakage surface | observable leakage surface | vague privacy risk | Use for outputs, access patterns, rankings, timings, interaction, or setup artifacts visible to an adversary. |
| 部署瓶颈 | deployment bottleneck | practical deployment barrier | implementation difficulty only | Use when a technical obstacle prevents a secure method from being practical in the claimed setting. |
| 端到端评估 | end-to-end evaluation | full-system evaluation; workload-level evaluation | overall experiment | Evidence should validate the paper-level claim under realistic workload assumptions, not only a kernel. |
| 通信开销 | communication overhead | communication cost; bandwidth overhead | communication burden if vague | Specify bytes, rounds, or network cost introduced by the protocol. |
| 客户端负担 | client-side burden | client-side cost; user-side burden | user-friendly without evidence | Include computation, storage, setup, preprocessing, or online interaction required from the client. |
| 算子表达能力 | operator expressiveness | supported encrypted operators | function support if vague | Clarifies which operations are supported without breaking the threat model or workload. |
| 查询表达能力 | query expressiveness | supported query classes | query flexibility if vague | Use for encrypted database/search settings and state the supported query classes. |
| 规模化精度 | precision at scale | large-scale precision; accuracy at scale | precision generally | Use when numerical precision, correctness, or utility must survive realistic sizes. |
| 打包 | packing | ciphertext packing; SIMD packing | package | For FHE slot layout. |
| 旋转 | rotation | slot rotation; ciphertext rotation | rotate operation | Include count and key-switching cost when relevant. |
| 重线性化 | relinearization | relinearization step | re-linearization if inconsistent | Follow library terminology. |
| 密钥切换 | key switching | key-switching operation | key change | Often tied to rotation/relinearization cost. |
| 模数链 | modulus chain | coefficient-modulus chain | modulo chain | CKKS/BFV/BGV context. |
| 模数预算 | modulus budget | available modulus budget | modulo budget | Use when explaining feasible circuits, remaining levels, or bootstrapping need. |
| 尺度管理 | scale management | scale alignment; scale control | scale processing | CKKS-style approximate arithmetic; do not conflate with generic noise control. |
| 近似误差 | approximation error | numerical approximation error | approximate noise | Distinguish from encryption noise and model utility loss. |
| 精度位数 | precision bits | usable precision bits | bit precision if unclear | Use for numerical precision after encrypted or approximate computation. |
| 乘法深度 | multiplicative depth | circuit depth | multiplication depth | Use multiplicative depth in FHE writing. |
| 自举 | bootstrapping | bootstrapping operation | bootstrap casually | Count bootstraps and cost if central. |
| 模型机密性 | model confidentiality | model privacy | model secrecy if informal | Protection of model weights, architecture-sensitive parameters, or proprietary model information. |
| 输入隐私 | input privacy | user-input privacy | input confidentiality if too narrow | Protection of user input or query content during inference, search, or computation. |
| 非交互式 | non-interactive | no online interaction; single-round online protocol | interaction-free if unscoped | State whether interaction is absent online or merely shifted into setup/offline phases. |
| 离线-在线范式 | offline-online paradigm | offline/online split | precomputation trick if vague | Always report whether cost is shifted to client, server, storage, or setup. |
| 工作流摩擦 | workflow friction | workflow burden; integration friction | usability issue only | Recurring expert burden, manual tuning, integration difficulty, or portability barrier. |
| 性能可移植性 | performance portability | backend performance portability | portability only | Whether performance survives across hardware backends, schemes, workloads, or compiler targets. |
| 端到端延迟 | end-to-end latency | overall latency | total time, if too vague | Scope workload and hardware. |
| 吞吐量 | throughput | query throughput; inference throughput | handling capacity | Define batch size. |
| 消融实验 | ablation study | ablation experiment | ablation analysis only | Tie to insight. |
| 基线 | baseline | comparison baseline | base line | Baselines must be fair and comparable. |

## Update rule

When the user accepts or rejects a phrase, append it here with context. Do not add project-specific proper names unless they are expected to recur across papers.
