# FHE Systems Focused Writing Knowledge

## 1. When to use this direction pack

当论文是 FHE library、compiler、runtime、scheme-switching infrastructure、hardware/backend abstraction、encrypted database framework、cross-scheme pipeline、deployment-oriented FHE system 或 artifact paper 时加载本方向包。

当前方向 core evidence 较少，因此本包强调 systems writing moves。若论文核心是算法 kernel，应组合 `fhe_algorithm_optimization`；若目标是安全顶会叙事，应组合 `security_top_conference_writing`。

## 2. Core problem framing

常见框架是：`FHE primitives are powerful but hard to compose/deploy -> users need abstraction, automation, interoperability, or performance portability -> system architecture removes repeated expert burden`。

问题不是“我们做了一个工具”，而是 FHE workflow 在 scheme support、parameter management、hardware backend、compiler lowering、format conversion、operator integration 或 query execution 上存在系统性 friction。好 framing 会说明 friction 影响谁：application developer、compiler writer、cryptography expert、hardware backend maintainer 或 data-query user。

## 3. Security/privacy motivation

隐私动机来自让 FHE 安全能力可被真实应用调用。系统论文要说明降低的是哪类安全计算摩擦：非专家误用参数、难以组合 operators、无法切换 scheme、硬件加速不可移植、query/operator 不兼容、client/server deployment burden。

## 4. Technical bottleneck framing

系统方向的 bottleneck 通常是 composition bottleneck：

- primitives 存在，但不易组合到完整 workflow。
- 自动化和 expert control 之间有 tradeoff。
- backend-specific optimization 阻碍 portability。
- compiler lowering 或 scheme switching 破坏 operator compatibility。
- key-switching / memory bandwidth / hardware abstraction 影响 system performance。

常用语言：`usability-efficiency tradeoff`, `backend portability`, `hardware abstraction`, `compiler-friendly mode`, `automatic parameter selection`, `scheme switching`, `operator compatibility`, `performance portability`, `workflow friction`。

## 5. Core insight framing

核心 insight 通常是 architecture principle，而不是单个 algorithm。

Reusable English templates:

- `The key insight is to expose the right abstraction boundary between cryptographic operations and application workflows.`
- `The system separates user-facing automation from compiler- or expert-facing control.`
- `The architecture makes backend-specific optimization compatible with a shared cryptographic interface.`
- `The framework turns a set of primitives into a composable workflow.`

## 6. Contribution framing

常见结构：

1. Present artifact and system boundary.
2. Define architecture or abstraction layers.
3. Explain automation / compiler / backend / operator support.
4. Show application or workflow coverage.
5. Evaluate usability, performance, portability, or capability coverage.
6. State release, documentation, or limitations if relevant.

Reusable English templates:

- `We present <artifact>, a <library/compiler/runtime/framework> for <FHE workflow>.`
- `We identify <workflow friction> as the main barrier to practical use.`
- `We design <abstraction/layer/interface> to separate <concerns>.`
- `We evaluate the system on <workloads/capabilities> to show <usability/performance/coverage>.`

## 7. Title patterns

Recommended:

- `<Artifact>: <unified representation/framework/library> for <FHE task>`
- `Open-Source <capability> Library`
- `<System>: <precision/scale/deployment capability> via <technical principle>`
- `<Compiler/Runtime>: <automation or portability claim> for FHE`

Avoid:

- Tool names without system boundary.
- `A framework for FHE` without capability.
- Titles that imply algorithm novelty when contribution is architecture or integration.

## 8. Abstract patterns

Sentence function order:

1. State FHE promise and deployment/composition difficulty.
2. Identify fragmentation or usability/performance tradeoff in prior tools.
3. Introduce the artifact and architecture principle.
4. List key layers or public capabilities.
5. Support with benchmark, case study, capability coverage, availability, or design requirements.

## 9. Introduction arc

Recommended paragraph arc:

1. FHE primitives/libraries/compilers have matured.
2. Real workflows still require expert hand-tuning, manual parameter choices, backend-specific optimization, or operator integration.
3. A concrete workflow exposes the friction.
4. The paper proposes an abstraction or architecture.
5. Contributions are previewed by layer and capability.
6. Evaluation or artifact availability establishes utility.

## 10. Evaluation narrative

Evaluation should match system claim:

- Benchmark systems: end-to-end workload, operator microbenchmarks, latency, throughput, memory, backend comparison.
- Library/design systems: capability coverage, automation behavior, compiler integration, hardware integration, documented use cases.
- Compiler/runtime systems: compile time, memory usage, generated program performance, supported operations.
- Database/query systems: query classes, row scale, precision, communication, end-to-end latency.

## 11. Related-work positioning

Group by system category:

- FHE libraries.
- FHE compilers.
- Hardware accelerators / backend systems.
- Encrypted databases or vector search frameworks.
- Scheme-switching or runtime frameworks.
- Application-specific FHE systems.

Technical contrast should identify abstraction, portability, capability coverage, workflow support, or end-to-end deployment difference.

## 12. Terminology

- Recommended English: `FHE library`, `compiler-friendly mode`, `user-friendly mode`, `Hardware Abstraction Layer`, `backend-aware implementation`, `scheme switching`, `cross-scheme compilation`, `operator compatibility`, `automatic parameter generation`, `performance portability`, `workflow friction`, `end-to-end system`.
- Avoid: API-list writing, scheme-list writing, kernel speedup as whole-system contribution, `usable` without user workflow, architecture claims without evaluation.
- Chinese explanation: 这些术语用于把系统贡献写成 abstraction、automation、composition 和 deployment，而不是工程功能堆叠。

## 13. Reviewer-risk checklist

- 新意是否超过 engineering integration？
- System boundary 是否清楚？
- Abstraction 是否隐藏了必要 expert choices？
- Performance portability 是否测量？
- 是否支持 realistic workflow？
- API / interface 是否真的有用？
- Evaluation 是否覆盖 composition，而非只测单个 kernel？
- Borrowed dependencies 与本文贡献是否区分清楚？

## 14. How HElicon should use this pack

当未来论文是 FHE artifact、library、compiler、runtime、framework、encrypted database 或 cross-scheme system 时加载本包。HElicon 应用本包来检查：是否写清 workflow friction、system boundary、architecture principle、public capability 和 evaluation claim。若系统面向安全顶会，组合 `security_top_conference_writing`。
