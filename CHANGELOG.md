# Changelog

## v1.6

- 新增一份公共 FHE 核心词表与五份互不重叠的方向词表，采用 `helicon-lexicon-v1` 结构，并保持项目词表与真实稿件内容在仓库外。
- 新增确定性的分层词表构建器，按 L2、L1、L0 优先级合并同名词项并记录覆盖冲突；未提供方向时可独立输出核心层，未提供项目词表时明确标记项目层缺席。
- 新增两种 Markdown 表格布局到 L2 JSON 的转换器；`Avoid` 进入禁用同义词，空格与连字符形式机械派生为禁用变体，acceptable alternatives 被明确忽略且不会自动派生复数。
- 修复术语冻结对句首首字母大写的误报，同时继续拒绝句中大小写漂移、全大写与单词型驼峰形式。
- 将方向包知识文件和六份词表接入可达图，并用新增的合成用例覆盖分层冲突、缺省层行为、Markdown 转换和大小写边界。
- 本轮合成证据仅说明词表构建、转换、机械检查和回归管道可运行；不构成论文质量、评审结果、录用概率或真实稿件能力的验证。

## v1.4

- 新增六项只读、单 JSON 输出的可验证性检查：不可变集合、claim strength、术语冻结、R1–R14 AI-tell 密度、reference/template 可达性与 H-* 命令覆盖矩阵。它们尚未接入 pass pipeline；本轮只建立可独立调用的检验器与未来调用契约。
- 不可变集合报告分别覆盖带单位数字、LaTeX key、规范化数学、figure/table label 与 caption 编号引用、glossary 词项，以及对齐后的否定/模态/量词/比较/断言强度标记；任何变化返回 1，配置错误返回 2。
- claim-strength 检查加入可扩展强度阶梯，检测否定或模态删除、比较方向翻转和作用域限定删除；术语检查读取合成 JSON glossary 并报告禁用同义词、大小写、缩写/全称和复数/连字符漂移的位置。
- `check_ai_tells.py` 在既有 R1–R14 行为基础上新增逐规则命中数、位置、每千词密度、总密度和 `--max-density` 门限；零命中 synthetic fixture 被固定为零密度回归。
- eval 套件新增 19 个 `helicon-eval-case-v1` 合成用例，所有文本均显式标记 `provenance=synthetic` 与 `contains_real_manuscript_text=false`。这些用例只证明检验器和拒绝分支可运行，输出继续保持 `capability_validated=false`。
- 修复 Round 6+ target-semantics 自指门禁：contract sync 逐字符绑定 `imitation-fidelity-to-author-approved-ai-assisted-target`，handoff 负向 fixture 不再引用被测常量，并固定“常量被改写即失败”的回归。
- 版本状态保持 verifiability candidate；真实论文质量、评审结果、录用概率和结构改善均不由本轮 synthetic 证据支持。

## v1.3.1

- 修复规则 10 对证据型 `-ing` 收尾从句的误报：从句内含数字加单位、引用/交叉引用或明确机制动词短语时不再建议删除；空洞的伪深度从句仍会命中。
- 将规则 2 的声明词表纳入逐词行为契约，覆盖 `dramatically` 等全部点名词；契约检查现在会实际调用检测器，并通过上下文正反例验证作用域豁免，不再只核对规则编号。
- 明确记录规则 2 的保守豁免窗口：同句或相邻句的度量、负载、硬件或威胁模型限定会抑制告警，因此数字密集的 Evaluation 段落需要配合 claim-evidence 审查。
- 修复 `language_polish.md` 与 `check_ai_tells.py` 的规则 1/2/3 契约断裂：此前脚本仅实现规则 4–14，规则 1/2/3 的部分词表滞留在 `check_style_rules.py`，而 `groundbreaking`、`transformative`、`pivotal`、`remarkable` 等规则 1 核心词在两个脚本中都缺失。现由 `check_ai_tells.py` 统一实现 1–14；规则 2 复用相邻句作用域证据进行豁免；事实性错误规则 3 为 block；`check_style_rules.py` 只保留中式直译与 overclaim 句式。
- 修复 `style_fingerprint.py` 的默认 `paper_id` 与政策相反的问题：旧逻辑把每个版本文件当作独立论文，可能把同源三至五个版本误计为 `n=3/5` 并错误启用漂移告警。新逻辑优先按归一化标题、其次按父目录自动分组，显式 `--paper-id` 仍可覆盖；输出会报告 `N files -> M papers` 和分组文件。
- 新增常设契约同步检查，自动核对语言规则号、description 中的 H-* 命令与 registry、以及基线最小论文数阈值，避免文档与代码再次静默分裂。
- 引入目标范例层。原设计的量化基线和禁止性规则只能让输出更干净，不能让输出趋向作者已经认可的成品形态；现在可从同一论文的分阶段版本建立 `target_profile`、修订方向与成对范例卡，并用 hold-out 收敛率进行端到端验收。
- `target_profile` 与 `baseline` 保持分家：baseline 描述作者当前习惯并需要至少 5 篇不同论文来估方差，只用于 P6 漂移检测；target 规定收敛方向，单篇合格范本即可用于 P4/P5/P6，但永不触发漂移告警。
- 目标范本采用“先量后用”。最终版本即使由作者认可，也可能经 AI 辅助而残留连接词堆叠、平坦句长或夸大词；`H-STYLE target` 必须先运行 AI-tell 与结构指标筛查，合格维度标 `source: exemplar`，不合格维度退回 `source: rule`，不得无条件照搬范本。
- 扩展 `H-STYLE target|direction|eval`：按版本对分别保留 author/advisor 与 reviewer-driven 来源；审稿驱动版本对默认不计入作者偏好；范例卡只作为结构形态参照，每轮最多加载 3 张；hold-out 验收报告结构收敛、AI-tell 三方对比、LaTeX 冻结项和固定 trailer。
- 所有目标画像数值、筛查报告、修订方向报告和已填范例卡只允许写入项目私有 `.helicon/style/`；仓库只保存 schema、生成方法、空模板和加载协议，污染检查会阻止私有派生物进入 core。

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
- 作者论文均处于投稿中；个人风格语料及其派生 `fingerprint.json` 一律保存在论文本地或私有 workspace，不进入本仓库。样本不足时标记 `thin(n=N)`，关闭 drift 告警和 anti-drift 拒绝；从 v1.3.1 起，修订方向仅由筛查后的 target 层提供。

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
