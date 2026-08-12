# HElicon Round 3 Handoff

本文件是 `handoff/round_3.json` 的人读版；JSON 为机器审计真源。

## Round identity

| Field | Value |
|---|---|
| Round | 3 |
| Status | `partial` |
| Branch | `main` |
| Base commit | `f26388dc027bc9eda019892db358530306e8d8b9` |
| Audited implementation commit | `230dc4ddbedccb8fe263b4180d0b110dc6961bcf` |
| Taskbook | `handoff/HELICON_ROUND3_TASKBOOK.md`，仓库内脱敏复本 |

`head_commit` 锚定已经审计、提交并推送的实现与 `evals/`。包含本 handoff 的下一笔提交仅修改 `handoff/`；其自身哈希不能写入自身，审计者应从 checkout 的 `HEAD` 解析该哈希，并核对相对实现锚点没有 `handoff/` 之外的变化。总体状态仍为 `partial`，因为 Stage 1–3 仍有明确未验证边界。

## Task status

| Taskbook section | Status | Evidence class | Result |
|---|---|---|---|
| Stage 0 / §2 | `done` | `self-authored-fixture` + `independent-session` | 110 项仓库自测满足；R02/R10 与契约同步受行为测试保护；目标分支已进入 v1.3.1 发布提交；已安装副本完整性检查成功。 |
| Stage 1 / §3 | `partial` | `real-data` | 六个私有语料/QC 产物存在；三份受保护源文件哈希一致。人眼 QC 与权威版本判断尚无独立的脱敏机器摘要。 |
| Stage 2 / §4 | `partial` | `real-data` | 目标画像 schema v3、筛查 schema v2；9 个字段中 5 个来自范本、4 个来自规则；6 个目标 hold-out。顺序和人工归因仍缺可重放的脱敏摘要。 |
| Stage 3 / §5 | `partial` | `independent-session` | Preservation 3/3；规则方向 3/3，L1 距离 6→1，收敛 83.3333%。结构方向为 `insufficient-coverage`，不得形成结构能力结论。 |
| Stage 4 / §6 | `done` | `self-authored-fixture` + `independent-session` | 5/5 回归组断言满足，`pipeline_runnable=true`、`capability_validated=false`；已从 GitHub origin fresh clone 精确 checkout 实现锚点并复跑成功。 |
| Stage 5 / §7 | `done` | `independent-session` | JSON、人读版、索引与污染检查就位。 |
| Iteration protocol / §8 | `done` | `independent-session` | `INDEX.md` 记录遗留项；下一轮必须逐条回应本轮问题与未验证声明。 |

## Evidence summary

公开仓库可复现命令：

```text
python -B scripts/selftest_checks.py
python -B scripts/check_contract_sync.py
python -B scripts/check_skill_integrity.py .
python -B scripts/check_core_contamination.py .
python -B evals/run_all.py
python -m json.tool handoff/round_3.json
```

当前结果：

- repository selftests：110
- contract rules：14
- synthetic regression groups：5/5 assertions satisfied
- `evals/`：12 files，25,899 bytes，portable POSIX-path tree SHA-256 `814f9f42d0b52e56a4d8f12e30e45cde8507a82164f66f78ee20ec4116c1edd4`
- synthetic fixtures：只证明管道可运行，不证明真实能力
- protected sources：3/3 hashes unchanged
- Stage 3C preservation：3/3
- Stage 3D rule-direction：3/3，L1 `6→1`，83.3333%
- Stage 3D structural direction：`insufficient-coverage`，6 eligible / 2 scorable，aggregate `null`
- installed skill：integrity check satisfied；exact current source parity 与 rollback drill 尚未形成 command-bearing evidence

私有 evidence 命令运行前，由审计者在本机设置以下环境变量；仓库不保存其真实值：

- `HELICON_SKILL_ROOT` → installed skill root
- `HELICON_PRIVATE_ROOT` → private Stage 1–2 root
- `HELICON_STAGE3_ROOT` → private Stage 3 workspace
- `HELICON_CLEAN_CLONE` → ephemeral GitHub-origin clean clone

## Unverified claims

本轮主动申报 10 项：

1. Stage 1 全部抽取质量维度已由作者人眼确认。
2. PDF 派生中间版本是正确的内容权威版本。
3. venue-confounded 与 page-budget-driven 分类没有归因错误。
4. 所有 hold-out 均在画像与方向计算之前排除。
5. 审稿模式抽象既完整又不存在语义隐私泄漏。
6. 历史 Stage 3C/3D 的进程退出码已写入各自 summary；当前 summary 只保存 `run_completed`。
7. 目标层能改善真实论文的段落结构。
8. 包含本 handoff 的 metadata-only 提交可由远端 clone，并且相对实现锚点只修改 `handoff/`。
9. 六个仓库 fixture 的合成来源可被机器证明。
10. 已安装副本的备份能完整恢复当前开发状态。

每项的原因和验证方式见 `round_3.json`。

## Deviations

本轮记录 10 项偏差：

- 仓库在 `handoff/HELICON_ROUND3_TASKBOOK.md` 保存脱敏任务书复本，原始发起任务文本因包含私有路径未直接写入。
- 真实语料采用“第一版摘要 / PDF 派生 Markdown 中间版 / 文本第三版”，替代最初三版统一 TeX 的假设。
- Stage 3 拆成 do-no-harm 与 rule-direction 两轨。
- Directional targets 是作者批准的 AI-assisted style-only targets，不是 raw third-version ground truth。
- Stage 3D 首次运行因 SHA-256 表示形式不一致在评估前停止；只修 harness 比较，冻结输出未重生成。
- 结构证据不足，因此没有结构 headline 或聚合收敛率。
- 早期一次性 synthetic fixture 已在 Stage 4 前删除，无法逐字恢复；本轮重建的是当前契约回归。
- `evals/` 与 `handoff/` 为 repository-only，不进入 installed skill payload。
- `head_commit` 有意锚定实现提交；包含本 handoff 的 metadata-only child 哈希由 checkout `HEAD` 外部解析，以避免 Git 提交哈希自引用。
- Stage 4 停点报告使用 Windows 反斜杠路径清单哈希；handoff 改用跨平台 POSIX 路径清单哈希，文件集合和文件内容未变化。

## Open questions

1. 是否补建不含原文的 Stage 1/2 summary JSON？推荐是。
2. 是否增加满足 immutable gate、结构分母非零的 style-only targets？推荐在有合格样本时进行，不放宽门禁。
3. 是否把私有 reviewer-pattern candidates 写入 core？推荐继续保持私有，另开审阅轮。

## Privacy

- 原始源文件保持在作者指定的原位置且未进入仓库；所有评估派生物、targets、outputs、画像值、范例卡和修订方向报告只存在于私有 `.helicon/`。
- 仓库只记录路径别名、计数、schema、哈希、退出码与脱敏指标。
- 未记录稿件句子、审稿措辞、系统名称、实验数值、参数或投稿标识。
- `python -B scripts/check_core_contamination.py .` 是提交前必跑门禁。

## Next round priorities

1. 从发布后的 `origin/main` clone metadata-only child，独立复跑 `reproduce[]` 并验证相对实现锚点只含 `handoff/`。
2. 为 Stage 1/2 增加 command-bearing sanitized summaries。
3. 未来 private summary 固定记录 command、exit_code 与 summary hash。
4. 扩大结构方向有效覆盖。
5. 单独审阅 reviewer-pattern candidates。
6. 发布后重新同步 installed skill，并做 payload 对比与回滚演练。
