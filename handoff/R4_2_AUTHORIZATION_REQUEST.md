# HElicon R4-2 Authorization Request

本文件只提出下一阶段授权建议，不授予授权。本轮没有读取任何私有稿件、私有 `.helicon/`、私有评估结果或 live skill，也没有执行 Stage 1 至 Stage 3 的计算。

机器可核验标记：

```text
request_status=proposal-only-not-authorized
holdout_before_profile_required=true
holdout_precondition_status=declared-not-executed
failure_mode=fail-closed
structural_status=insufficient-coverage
eligible_observations=6
scorable_observations=2
zero_denominator_cases=1
aggregate_convergence_percent=null
R4-ITERATION=partial
authorized_closure_claims=R4-U01,R4-U02
deferred_claims=R4-U03,R4-U04,R4-U05,R4-U06,R4-U07,R4-U08,R4-U09
conditional_source_read_requires_stop=true
stage1_summary_create_once=true
holdout_receipt_creation_authorized=false
profile_screening_target_direction_authorized=false
private_paths_are_aliases=true
structural_option_A_expands_private_paths=false
structural_option_B_expands_private_paths=false
structural_option_C_expands_private_paths=true
```

## 1. 建议授权结论

建议下一次只授权 `R4-2`，目标是对 Stage 1 的抽取质检与中间版本 authority 做有时间戳的重新确认。该阶段是 `capability_claim=false` 的事实确认，不评价 HElicon 的论文改写能力。

R4-2 预计只能关闭：

- `R4-U01`：作者重新确认全部 Stage 1 抽取质检维度；
- `R4-U02`：作者按预先声明的逐节准则批准中间版本 authority。

`R4-U03` 至 `R4-U09` 均不得在 R4-2 中顺带关闭。

## 2. 最小私有访问申请

下列路径均为公开别名。实际路径由作者在获授权的私有执行会话中带外提供，不写入仓库。所有现有文件均为只读，禁止移动、改名、覆盖或修改原始 TeX/PDF。

| Access | Alias path | Type | Purpose / claim |
|---|---|---|---|
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/extraction_qc.md` | 私有 Markdown 抽取-QC报告 | `R4-U01` |
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v1.txt` | 私有派生文本 | `R4-U01` 的逐阶段人眼抽查 |
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v2.md` | 私有 PDF 派生 Markdown | `R4-U01` 与 `R4-U02` |
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/stages/v3.txt` | 私有派生文本 | `R4-U01` 的逐阶段人眼抽查 |
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/v2_authority.md` | 私有 Markdown authority 比较报告 | `R4-U02` |
| READ | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/versions.yaml` | 私有版本身份、venue 与 authority 元数据 | `R4-U01` / `R4-U02` 的身份绑定 |
| CONDITIONAL READ | `<PRIVATE_SOURCE_ROOT>/version-2.tex` | 受保护的中间版本 TeX | 仅当既有 authority 报告缺少逐节来源绑定或 hash 时，用于 `R4-U02`；触发前必须停下并取得精确扩权 |
| CREATE-ONCE | `<PRIVATE_PAPER_ROOT>/.helicon/corpus/stage1_summary.json` | 私有、脱敏、command-bearing JSON | 保存 U01/U02 的命令、真实退出码、时间、输入/输出 hash、逐维度 verdict 与 author decision |

若任一 `CREATE-ONCE` 目标已经存在，执行者必须停下，不得覆盖；是否改用 versioned 输出需另行授权。

R4-2 明确不授权访问：

- `target_profile.json`、`target_screening.json`、`revision_direction.json`；
- `holdout_manifest.md` 与 `holdout_freeze_receipt.json`；它们属于未来 R4-3 的前置门，本次只声明门禁、不读取或创建；
- `reviewer_patterns.md`、任何范例卡或任何 Stage 3 target/output/report；
- live skill 或其备份；
- 未在上表列出的原始论文、审稿意见或私有目录。

## 3. U01 / U02 的关闭判据

Round 4 v2 将旧的单轴 `evidence_class` 拆为正交字段。本文所说的 real-data 对应 `data_provenance=private-real-data`，独立执行对应 `execution_provenance=independent-session`，人工确认由 `human_review` 单独记录。

### R4-U01 — Stage 1 extraction QC

必须同时满足：

1. `data_provenance=private-real-data`、`target_provenance=none`、`claim_domain=corpus`、`claim_scope=corpus-qc`；
2. 机器证据记录完整命令、真实 OS `exit_code`、`executed_utc`、输入 manifest SHA-256 与脱敏 summary SHA-256；
3. 对 section / paragraph / sentence / word counts、断词残留、孤立排版行、宏残留、图注混入、异常句长、数学残留逐项给出 `confirmed | rejected | unknown`；
4. 断词残留、宏残留、图注混入为 0；其他异常率低于预先写死的阈值；
5. `human_review=author-attested`，含 reviewer role、时间和明确的视觉确认结论。

任一维度 verdict 为 `rejected` 或 `unknown` 时，`R4-U01` 必须保持 carried-forward，不得关闭。

这是有边界的真实语料事实确认，不是能力 claim；`builder-session` 可以支撑机器记录，`independent-session` 不是关闭 U01 的必要条件，也不能替代作者人眼确认。

### R4-U02 — Middle-version authority approval

必须同时满足：

1. `data_provenance=private-real-data`、`target_provenance=none`、`claim_domain=corpus`、`claim_scope=authority-approval`；
2. 在比较前声明逐节判据，并记录每条判据的脱敏 verdict；
3. authority 报告、保留的 PDF 派生文本、版本元数据及必要时的 TeX comparator 由 hash 绑定；
4. 明确记录 `human_review=author-attested`、作者角色、时间与批准/拒绝结果；
5. 结论只能写成“按声明的准则获作者批准”，不得表述为客观、无条件正确或独立 ground truth。

只有明确的 `approve` author decision 才可关闭 `R4-U02`；`reject` 或 `unknown` 必须保持 carried-forward。

这同样不是能力 claim；`builder-session` 可关闭有边界的前向事实，独立执行不必强加，也不能代替作者决策。

## 4. 剩余 9 条的阶段与证据要求

| Claim | 最早可关闭阶段 | 必需证据组合 | R4-2 结论 |
|---|---|---|---|
| R4-U01 | R4-2 | `private-real-data + author-attested`；完整命令/退出码/时间/hash；target `none` | 可关闭 |
| R4-U02 | R4-2 | `private-real-data + author-attested`；逐节准则与 author decision；target `none` | 可关闭 |
| R4-U03 | R4-3 | `private-real-data + author-attested`；只公开 confirmed/changed/unknown 聚合数 | 不可关闭 |
| R4-U04 | R4-3 | `private-real-data` 的前向 manifest-before-computation 命令链；建议 independent-session 复核 | 只能建立前置 receipt，不能关闭 |
| R4-U05 | R4-3 | `private-real-data + human_review != none`；最低为 `author-attested`，只有另行授权独立审阅者读取候选时才可用 `independent-human-reviewed`；候选始终私有 | 不可关闭 |
| R4-U06 | R4-4 | `private-real-data + independent-session`；外层 wrapper 持久化实际 OS 退出码；preservation target=`qualified-original`，directional target=`author-approved-ai-assisted` | 不可关闭 |
| R4-U07 | 独立 structural track | `private-real-data + independent-session + author-approved-ai-assisted + author-attested`，并通过全部结构 coverage gate | 当前 blocked |
| R4-U08 | R4-5 | fixture 的 synthetic/repository provenance，加私有 corpus overlap 检查与 independent-human-reviewed；只允许声称 no detected overlap | 不可关闭 |
| R4-U09 | R4-6 | disposable target 上的 repository-metadata install/restore 命令证据；human review 非必需；严禁 live skill | 不可关闭 |

## 5. Hold-out 必须先于画像：授权前置门

这不是执行时的提醒，而是 R4-2 及后续授权成立的 fail-closed 前置条件：

该门禁在本轮仅被声明，状态为 `declared-not-executed`。R4-2 不读取 hold-out、不生成 receipt；未来 R4-3 必须先单独获权，才能执行以下步骤：

1. 在任何新 profile、screening、target 或 direction 命令之前，先生成 `<PRIVATE_PAPER_ROOT>/.helicon/corpus/holdout_freeze_receipt.json`；
2. receipt 必须记录 stable private-ID 集合的 canonical hash、生成命令、真实 OS 退出码与 `executed_utc`；
3. R4-2 禁止运行或更新 profile、screening、target、direction 和 Stage 3 产物；
4. 未来 R4-3 wrapper 必须显式接收 receipt hash，并逐项核对 exclusions；缺失、hash 变化或集合不一致时必须非零退出；
5. 后续证据必须呈现 `freeze receipt -> computation command -> output hash` 的前向顺序；
6. 现有 mtime、事后一致性或事后重建不得用来证明历史先后。

因此，R4-2 只把这条要求固化为未来授权的机器 admission contract，不产生 receipt，也不能提前关闭 U04。

## 6. R4-U07 结构证据的可评分扩展方案

当前状态固定为 6 eligible / 2 scorable、coverage 33.3333%、1 个 zero-denominator、aggregate `null`，所以 `structural_status=insufficient-coverage`，禁止结构改善 headline。

### 方案 A — 修复现有 cohort 的可评分性

在现有 6 个观测内，预注册并由作者批准至少 3 个额外或替代的 multi-sentence、immutable-compatible、non-zero-denominator style-only targets，必须覆盖当前 zero-denominator case。目标至少为 5/6 scorable、coverage 83.3333%、zero-denominator 0。

- 是否扩大私有语料路径：否；
- 是否扩大授权：是，扩大 target 生成与作者审批范围；
- 风险控制：完整候选 universe、选择规则和全部失败尝试必须在生成 output 前冻结，不能看结果挑 target。

### 方案 B — 现有语料内扩大预注册 cohort

先修复至少 2 个现有不可评分观测（其中必须包含 zero-denominator case），再从同一三阶段语料预注册至少 4 个全可评分观测，可达到 8/10 = 80%。旧 6 个继续单列，不能删除困难样本。

- 是否扩大私有语料路径：否；
- 是否扩大授权：是，扩大现有三阶段语料内的可读 paragraph universe 与 target 审批范围；
- 前置条件：新版 hold-out 必须在任何画像/target/direction 计算前冻结，且不得按已见结果挑样本。

### 方案 C — 新增独立私有稿件或版本对

若既有语料不足，引入额外可比稿件/版本对，按 venue 分层形成独立 confirmatory cohort。原 6 个仍保留；不同 venue 不得混合制造单一 aggregate。

- 是否扩大私有语料路径：是，必须单独列出新路径并再次授权；
- 是否扩大授权：是，扩大 corpus、hold-out、target 审批与独立评估范围；
- 风险控制：先冻结候选 universe、排除理由、hold-out、指标与最低 coverage，再生成任何画像或输出。

三个方案均属于后续 structural track，不包含在 R4-2 授权中。

## 7. 建议授权文字

若作者决定进入 R4-2，建议使用以下精确授权；在明确发送之前，R4-2 仍未获授权：

> 确认授权 R4-2，仅允许读取 `R4_2_AUTHORIZATION_REQUEST.md` 第 2 节列出的非条件私有材料，并在私有 `.helicon/corpus/` 中 create-once 写入 `stage1_summary.json`。本阶段不得读取 `holdout_manifest.md` 或创建 `holdout_freeze_receipt.json`；后者保留为未来 R4-3 在任何画像计算前必须先执行的 fail-closed admission gate。不得读取条件路径，除非先停下取得精确扩权；不得运行 profile、screening、target、direction 或 Stage 3 计算；不得修改原始 TeX/PDF、live skill 或公开仓库中的 scripts/references/evals/SKILL.md。完成 U01/U02 证据后停下等待作者确认。
