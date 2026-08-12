# HElicon Round 4 Handoff

本文件是 `handoff/round_4.json` 的人读版；JSON 是机器审计真源。

## Round identity

| Field | Value |
|---|---|
| Round | 4 |
| Status | `partial` |
| 当前授权 | R4-0 / R4-1；完成后停下 |
| Round 3 implementation commit | `230dc4ddbedccb8fe263b4180d0b110dc6961bcf` |
| Round 3 handoff commit | `a52366983621b6481284f0c9a09f9fe3a866f2d8` |
| Audited checkout commit | `a52366983621b6481284f0c9a09f9fe3a866f2d8` |
| Round 4 containing commit | `a18364d535e3691b49be1c6c9ce3de1a087be14d`，已由外部 fresh-clone 审计 |
| Taskbook | `handoff/HELICON_ROUND4_TASKBOOK.md` |

本轮没有读取私有稿件、私有 `.helicon/` 或 live skill，也没有安装、merge、tag 或 push。总体继续保持 `partial`。

## Task status

| Task | Status | Capability claim | Result |
|---|---|---|---|
| R4-0 | `done` | `false` | 21 条 builder-session command evidence、1 条 external independent audit attestation、提交边界和 Git-blob 清单均已记录。 |
| R4-1 | `done` | `false` | v2 schema、Git 元数据/清单核验和 16 个负向 policy/repository selftests 已实现；validator 明确保持 `evidence_truth_verified=false`。 |
| R4-ITERATION | `partial` | `false` | 13 个继承项已有唯一 disposition，但私有 successor 尚未授权或仍被覆盖门槛阻断。 |

## R4-0 evidence

- Fresh checkout：`a52366983621b6481284f0c9a09f9fe3a866f2d8`
- Sole parent：`230dc4ddbedccb8fe263b4180d0b110dc6961bcf`
- Parent-to-checkout：仅 5 个 `handoff/` 文件
- Public builder command evidence：21/21 exit `0`
- External independent audit attestation：1 条；原审计未报告执行时间，因此机器记录明确保留 `execution_time_status=not-reported-by-source`
- Repository Git-blob manifest：107 files，652,697 blob bytes，SHA-256 `d9256cebe6f1419eadcbb8919521401a8bc183fa6aeb2e97c59377f6c8b2ff98`
- `evals/` Git-blob manifest：12 files，25,899 blob bytes，SHA-256 `814f9f42d0b52e56a4d8f12e30e45cde8507a82164f66f78ee20ec4116c1edd4`
- 5/5 synthetic groups：`pipeline_runnable=true`，`capability_validated=false`
- Synthetic evaluator oracle：`generation_path_exercised=false`
- Fresh checkout after tests：clean；没有 `.helicon`、`__pycache__` 或 `.pyc`

R4-0 是 builder-session 佐证。U08 的独立关闭依据仍是作者转交的外部独立审计，不把本轮复跑冒充独立执行。

## Evidence axes

Round 4 不再把来源与执行者混在一个 `evidence_class`：

- `data_provenance`：数据来源；
- `execution_provenance`：builder 或 independent session；
- `target_provenance`：目标来源；
- `human_review`：人工审核状态；
- `claim_domain` / `claim_scope`：证据允许支撑的结论边界。

因此 independent execution 不会把 synthetic 变成 real-data，author-approved AI target 也不会变成独立 ground truth。

## Round 3 inherited dispositions

| Item | Disposition | Round 4 treatment |
|---|---|---|
| R3-U01 | `carried-forward` | R4-2 重新做有时间戳的作者 QC 确认，不倒填历史。 |
| R3-U02 | `carried-forward` | 改写为“按明确准则获批准”。 |
| R3-U03 | `carried-forward` | 仅报告 confirmed / changed / unknown 聚合数。 |
| R3-U04 | `retired-known-gap` | 历史顺序不可恢复；建立前向 manifest-before-computation 证据。 |
| R3-U05 | `carried-forward` | 仅做有边界的人类语义隐私/有用性审阅。 |
| R3-U06 | `retired-known-gap` | 不改写历史 summary；未来 wrapper 持久化真实进程退出码。 |
| R3-U07 | `blocked` | 结构覆盖不满足门槛。 |
| R3-U08 | `closed` | 作者转交的外部审计已 fresh clone 并验证 metadata-only child。 |
| R3-U09 | `carried-forward` | 后续做 canonical fixture manifest 与有限 overlap 审阅。 |
| R3-U10 | `blocked` | live skill 不动；等待 disposable restore drill 授权。 |
| R3-OQ01 | `closed` | 后续补 Stage 1/2 脱敏 summary。 |
| R3-OQ02 | `closed` | 只在预注册 admission / coverage gate 下扩展结构轨。 |
| R3-OQ03 | `closed` | Round 4 不晋升 reviewer-pattern candidates。 |

Round 3 的 Iteration Protocol 任务曾标为 `done`，但当时多数私有 claim 尚未行为验证。Round 4 不改旧文件，而将该状态记录为 `superseded-partial`。

## Structural boundary

当前仍是：

- eligible：6
- scorable：2
- coverage：33.3333%
- zero-denominator cases：1
- aggregate：`null`
- headline：不允许
- status：`insufficient-coverage`

至少达到 6 eligible、5 scorable、80% coverage、零 zero-denominator 且 aggregate 非空，才允许结构 headline。

## Outstanding items

Round 5 已依据外部独立 fresh-clone 审计关闭原 `R4-U10`；当前保留 9 项 unverified claims，均对应尚未授权、历史不可恢复或覆盖不足的边界。该关闭只涉及仓库发布与可复现性，不产生能力证据。

本轮有 0 项开放问题：Round 3 的三个问题已经由作者明确决定，但后续私有 stage 仍需逐 stage 新授权。

## Deviations

本轮记录 4 项偏差：R4-0 仅作 builder-session 佐证；Round 3 Iteration Protocol 在新协议中被 supersede 为 partial；未发布 bundle 使用排除自引用 JSON 的 canonical-LF candidate manifest；当前授权明确排除 private/live 验证。完整 `what / why / impact` 见 JSON。

## Privacy and cleanup

- 私有数据读取：`false`
- live skill 读取或更新：`false`
- 临时 fresh clone：三次均为 135 files / 1,006,754 bytes；postflight clone 记录了机器删除证据，三条精确 TEMP 路径均已确认不存在
- 仓库未记录真实本地路径
- `python -B scripts/check_core_contamination.py .` 仍是公开污染门禁

## Stop point

R4-0 / R4-1 已完成，现已停下。不得进入 R4-2；R4-2 将首次需要私有 Stage 1 证据和作者确认。
