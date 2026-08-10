# Changelog

## v1.3

- 引入无命令意图路由与跨会话项目记忆，解决作者不记命令、只贴局部文本，以及换会话后无法可靠识别论文的问题。路由层默认执行低破坏性的 `P3 → P4 → P5`，不自行改写 claim 或结构；项目状态优先保存在论文目录的 `.helicon/`，全局 registry 只存路径与指纹。
- 引入按处境选择的入口模式和 P1–P7 revision pass 流水线，分别解决“已有整稿/局部手术缺少直接入口”和“润色任务无法分阶段归因”的问题。`H-PASS` 保持单 pass 单目标，`H-POLISH` 按 P3→P4→P5→P6 编排并逐段报告。
- 固定 P4 先于 P5：P5 以删除夸大词、连接词和填充为主，先执行会压低可供节奏重构的句长方差。合成假稿冒烟测试中，P5 前后句长标准差由 `2.6339` 降至 `2.1213`，句数均为 8。
- 修复污染检查的数值正则：原尾部 `\b` 在 `%` 这类非单词单位后无法形成 word boundary，导致 `37%`、`0.5%` 漏检；现改为 `(?![A-Za-z0-9])`，并用限定文件、策略行前缀和显式 marker 精确豁免政策阈值，不放松 blocklist、项目名或 ePrint 检查。
- 新增入口命令：`H-NEW`、`H-INTAKE`、`H-PASS`、`H-SPOT`、`H-DEADLINE`、`H-REBUT`；新增功能命令：`H-CITE`、`H-STYLE`、`H-GATE`、`H-EXPORT`、`H-INGEST`。
- 保留全部兼容别名：`H-POLISH`、`H-COMPRESS`、`H-VOICE`、`H-TRIAGE`，以及 v1.2 的 `H-SECTION-ITERATE`、`H-LOG` 兼容语义；v1.2 的 16 个命令全部继续可用。
- 新增七阶段语言/术语/引用/压缩/rebuttal references、机器执行的 LaTeX immutable-set guard、风格指纹、AI 痕迹检查、dossier 导出和跨平台安装脚本。
- 依赖红线调整为「新增脚本不得引入第三方依赖；既有脚本的可选 fallback 保留」。恢复 `extract_pdf_text.py` 的可选 `PyPDF2` fallback，避免 Windows 缺少 Poppler `pdftotext` 时发生能力回退。
- 风格基线按 `paper_id` 聚合同源版本；资格计数和跨论文方差均以不同论文为单位，五个同源版本记为 `thin(n=1)`。
- 外部 humanizer 类 skill 的影响仅以“蒸馏后重写规则”的方式吸收，没有复制其指令段落；许可证、采纳项和拒绝项见 `provenance/external_influences.md`。
- 作者论文均处于投稿中；个人风格语料及其派生 `fingerprint.json` 一律保存在论文本地或私有 workspace，不进入本仓库。样本不足时标记 `thin(n=N)`，关闭 drift 告警和 anti-drift 拒绝。

## v1.2

- Distilled a new security-venue FHE systems batch in the external workspace.
- Added an abstract `Security-Venue FHE Systems Paper` pattern to core without importing raw PDF text, single-paper claims, experiment numbers, or project facts.
- Regenerated distilled-source provenance BibTeX from the reviewed registry.
- Added Evidence-Driven Revision System project-pack files and command responsibilities.
- Standardized the paper pipeline as `H-DISCUSS -> H-POSITION -> H-DRAFT -> H-PATCH -> H-SYNC`, with revision/rebuttal repeating the same loop through `H-REVIEW` and `H-REOPEN` when needed.

## v1.1

- Promoted the project-aware short-command workflow to the official v1.1 snapshot.
- Changed `H-SYNC` into a compact global synchronization command that rewrites current project state and deletes or archives stale, contradicted, superseded, or duplicated memory.
- Bound confirmed `H-DECIDE` writes to a scoped `H-SYNC` plan so decision logs and trackers do not grow as append-only transcripts.
- Kept `H-LOG` as a compatibility command name while making it execute scoped `H-SYNC` semantics instead of independent long-form logging.
- Added compact project-memory structures for current decisions, open decisions, draft status, and sync archives.
- Added personal-paper anti-overfitting rules so the user's papers can teach abstract style without importing paper-specific terminology, method names, experiment numbers, datasets, or title logic into core.
- Added scripts for PDF text extraction, FHE/HE paper metadata and open-PDF collection, and core contamination checks.
- Preserved the v1.0.1 boundary that project facts, raw paper text, single-paper details, ePrint IDs, and experiment numbers must not enter core memory.

## v1.1-rc1

- Added project-aware `H-*` short-command dispatch to `SKILL.md`.
- Added `references/command_registry.md` with command contracts for `H-HELP`, `H-LOAD`, `H-ONBOARD`, `H-DISCUSS`, `H-DECIDE`, `H-TITLE-ITERATE`, `H-ABSTRACT-ITERATE`, `H-SECTION-ITERATE`, `H-REVIEW`, `H-PATCH`, `H-LOG`, `H-SYNC`, `H-SYNC-REPAIR`, and `H-REOPEN`.
- Generalized the short-command workflow from an external paper guide without copying project facts into HElicon core.
- Distinguished discussion, iteration, decision, patching, logging, synchronization, repair, and reopening responsibilities.
- Preserved the v1.0.1 boundary that project facts, raw paper text, single-paper details, ePrint IDs, and experiment numbers must not enter core memory.

## v1.0.1

- Wrote confirmed cross-direction paper-writing guidance into core references.
- Added metric-bound HE/FHE framing, claim-evidence review checks, and security top-conference story rules.
- Updated title, abstract, introduction, contribution, and technical-framing guidance from reviewed unified patterns.
- Updated direction-pack indexing while keeping focused direction knowledge outside the core skill.
- Kept project-specific facts, paper details, and personal style memory out of this update.

## v1.0-adjusted

- Reframed HElicon as a long-term personal research-writing mentor.
- Removed single-project facts from core memory.
- Added external project-pack and direction-pack workflow.
- Added unified paper-pattern distillation workflow.
- Added bilingual continuity and terminology-control policy.
- Added mentor-memory and memory-patch loop.

## v1.0-initial

- Initial FHE/security writing skill skeleton.
