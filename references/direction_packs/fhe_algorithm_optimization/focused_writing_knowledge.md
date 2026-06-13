# FHE Algorithm Optimization Focused Writing Knowledge

## 1. When to use this direction pack

当论文目标是优化 FHE/CKKS/BGV/BFV 中某个 encrypted computation critical path 时加载本方向包。典型对象包括 bootstrapping、modular reduction、EvalMod/EvalRound、CoeffToSlot/SlotToCoeff、homomorphic comparison、sorting/ranking、packing conversion、linear algebra kernel、precision/error control、RNS scale management。

不要在完整系统论文中单独加载它作为主包，除非论文贡献核心确实是算法路径、参数成本或底层算子。如果算法只是系统中的 supporting kernel，应与 `fhe_systems` 或 `security_top_conference_writing` 组合使用。

## 2. Core problem framing

常见框架是：`FHE enables encrypted computation -> practical use is blocked by one dominant subroutine -> this subroutine consumes a named resource -> changing its computation path unlocks downstream workloads`。

写作时不要说 “FHE is slow”。要把慢拆成具体资源：multiplicative depth、rotations、key-switching、ciphertext modulus bits、scale alignment、approximation error、slot layout、memory movement、bootstrapping latency。问题描述应让 reviewer 看到瓶颈是 scheme/workload 结构导致的，不是代码优化不足。

## 3. Security/privacy motivation

隐私动机来自 enabling computation without decryption。应用背景可以短，但必须落到 encrypted operator gap：为了让 private inference、encrypted ranking、secure database 或 encrypted ML 成为可能，系统必须在 ciphertext 上执行某个本来明文很简单的 operation。

强写法：说明为什么不能回到明文监控、明文 clipping、明文 sorting、interactive workaround 或解密后处理。这样隐私动机会自然转成算法瓶颈。

## 4. Technical bottleneck framing

把瓶颈写成 cost dimension，而不是 function name。常用表达：

- `the dominant cost is not homomorphic multiplication itself, but the rotations and key-switching needed to realize the transform`
- `the bottleneck is the approximation interval required by encrypted evaluation, not the target function alone`
- `the current route spends the modulus budget on scale alignment before the useful computation begins`
- `prior bootstrapping pipelines are dominated by one linear transform / modular reduction step`

## 5. Core insight framing

核心 insight 应写成因果链：`observation -> representation/protocol/function change -> cost metric improvement -> workload consequence`。

可复用表达：

- `The key observation is that the target operation does not need to be evaluated in its original representation.`
- `Instead of reducing the whole circuit depth, we isolate the subroutine that dominates the modulus budget.`
- `The method changes where approximation error is introduced and how it is propagated.`
- `This turns a depth-heavy path into a sequence of cheaper transforms with controlled precision loss.`

## 6. Contribution framing

常见结构：

1. Identify the bottlenecked operator or subroutine.
2. Propose a new algorithm / approximation / representation / transform.
3. Prove or analyze the relevant complexity, precision, or correctness property.
4. Implement the method under comparable security parameters.
5. Demonstrate downstream consequence on the intended workload.

Reusable English templates:

- `We identify <subroutine> as the dominant source of <cost metric> in <setting>.`
- `We introduce <method>, which replaces <prior route> with <new route>.`
- `We show that this reduces <depth/rotations/error/modulus/latency> while preserving <precision/security/functionality>.`
- `We implement the method in <scheme/library setting> and evaluate it under comparable parameters.`

## 7. Title patterns

Recommended:

- `<Primitive> for <specific HE setting>`
- `Efficient/Faster <homomorphic operation> with <specific metric>`
- `<Named method>: <bottleneck relief> for CKKS/FHE`
- `<Approximation method> for <encrypted primitive>`

Avoid:

- `Efficient <something>` with no metric.
- Titles that hide whether the contribution is depth, precision, rotations, latency, or throughput.
- Acronyms that replace the actual primitive.

## 8. Abstract patterns

Sentence function order:

1. State the FHE/CKKS capability and the target operation.
2. Identify the specific bottleneck in prior methods.
3. Present the key observation or representation change.
4. State the main technical contribution.
5. Quantify the improvement in the same metric used for the bottleneck.
6. Give implementation or benchmark evidence.

## 9. Introduction arc

Recommended paragraph arc:

1. FHE promise and relevant application class.
2. Target operation is necessary for that application.
3. Existing FHE route makes one subroutine expensive.
4. Prior work improved part of the story but leaves a next bottleneck.
5. New observation changes the cost structure.
6. Contributions and evaluation claims.

## 10. Evaluation narrative

Evaluation should prove the claimed bottleneck relief:

- depth claim -> depth, modulus chain, remaining levels, security feasibility.
- precision claim -> error bits, model utility, approximation error, correctness rate.
- transform/packing claim -> rotations, key-switching, memory movement, throughput.
- bootstrapping claim -> latency, precision after bootstrap, remaining budget.
- comparison/sorting claim -> amortized runtime, failure rate, security parameter.

## 11. Related-work positioning

Position by technical route, not chronology:

- bootstrapping subroutines
- approximation families
- RNS/scale-management variants
- comparison/sign approximation methods
- packing and linear transform methods
- scheme/format conversion methods

Reusable contrast: `Prior work optimizes <route>, but still pays <cost metric> when <workload/parameter condition>. Our method changes <representation/path>, so the limiting cost becomes <new smaller cost>.`

## 12. Terminology

- Recommended English: `multiplicative depth`, `modulus budget`, `scale management`, `approximation error`, `precision bits`, `bootstrapping critical path`, `EvalMod`, `EvalRound`, `CoeffToSlot`, `SlotToCoeff`, `homomorphic comparison`, `sign-function approximation`, `key-switching`, `rotation`, `slot layout`, `bootstrappable ciphertext`, `amortized throughput`.
- Avoid: `FHE is slow`, `efficient` without metric, `implementation optimization` as the whole contribution, confusing `noise` with `approximation error`, runtime without security parameters.
- Chinese explanation: 这些术语用于把数学细节翻译成 reviewer 可比较的资源消耗。每次使用时都要绑定 workload consequence。

## 13. Reviewer-risk checklist

- Metric 是否与 claim 一致？
- Security parameters 是否公平？
- Precision loss 是否被隐藏？
- 是否只是把成本转移到 precomputation、memory 或 keys？
- 是否支持 realistic workload，而不是 toy benchmark？
- 是否说明了该 primitive 为什么值得一篇论文？

## 14. How HElicon should use this pack

当未来论文的核心是 FHE 算子、CKKS bootstrapping、comparison、packing、precision 或 depth 时，优先加载本包。HElicon 应用本包来强制写作者先命名 critical path，再写 method 和 metric。若论文同时面向安全顶会或应用系统，应组合 `security_top_conference_writing` 或 `fhe_systems`。
