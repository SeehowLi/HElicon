# HElicon v1.1 Installation and Workflow

This document describes how to install HElicon, build its long-term knowledge, and use it on external paper projects.

## 0. Important concept

HElicon is not a fine-tuned model. It improves through a controlled loop:

```text
selected papers / own drafts / advisor feedback / project drafts
  -> distillation
  -> structured memory files
  -> better future prompts and revisions
```

The skill does not silently learn. After each meaningful session, ask it to produce a `HElicon Memory Patch`, then manually write stable lessons back into the correct files.

## 1. Install HElicon

### Option A: user-level install

Use this if you want HElicon available in all Codex projects.

```bash
cd ~/Downloads
unzip HElicon-v1.0-adjusted.zip
mkdir -p ~/.agents/skills
cp -R HElicon ~/.agents/skills/HElicon
```

### Option B: repo-level install

Use this if you want a paper repository to carry HElicon with it.

```bash
cd /path/to/your-paper-repo
mkdir -p .agents/skills
cp -R ~/Downloads/HElicon .agents/skills/HElicon
```

### Check

```bash
python ~/.agents/skills/HElicon/scripts/check_skill_integrity.py ~/.agents/skills/HElicon
```

In Codex:

```text
/skills
```

Then call:

```text
$HElicon
请说明你会如何帮助我修改安全顶会论文。
```

## 2. Create an external HElicon workspace

Do not put raw PDFs, unpublished drafts, or project-specific facts directly into the skill core.

Recommended global workspace:

```bash
mkdir -p ~/HElicon_workspace/{corpus,distilled,direction_packs,projects,logs}
mkdir -p ~/HElicon_workspace/corpus/{selected_papers,own_drafts,advisor_edits}
mkdir -p ~/HElicon_workspace/distilled/{paper_cards,unified_patterns,style_cards}
```

The core skill stays stable. The workspace grows over time.

## 3. Build unified paper patterns first

The user expects many papers of the same type to share similar writing logic. Therefore, do not only create one summary per paper. Use a two-stage distillation:

### Stage 1: individual high-value cards

Use this for papers that are especially strong or unusual.

```text
$HElicon
请把这篇论文蒸馏成 paper pattern card。不要复制原文句子。
重点学习：problem、bottleneck、title/abstract、introduction、contribution、evaluation narrative、related-work contrast、术语。

论文内容或笔记：
<粘贴>
```

Save outputs under:

```text
~/HElicon_workspace/distilled/paper_cards/
```

### Stage 2: unified pattern cards

After 5-10 similar papers, ask HElicon to collapse them:

```text
$HElicon
下面是同一类型论文的多个 paper pattern cards。请不要逐篇总结，而是蒸馏出统一模式。
输出 unified pattern card，重点包括：
1. invariant problem framing;
2. common bottleneck language;
3. title/abstract moves;
4. introduction arc;
5. contribution structures;
6. evaluation expectations;
7. terminology to prefer;
8. expressions to avoid;
9. reviewer expectations.

cards:
<粘贴多个 cards>
```

Write stable results into:

```text
HElicon/references/unified_paper_patterns.md
```

or a direction pack if it is narrower.

## 4. Build direction packs

For a direction such as private LLM inference or encrypted kNN:

```bash
mkdir -p ~/HElicon_workspace/direction_packs/private_llm_inference
mkdir -p ~/HElicon_workspace/direction_packs/encrypted_knn_search
mkdir -p ~/HElicon_workspace/direction_packs/fhe_algorithm_optimization
```

Use:

```text
HElicon/templates/direction_pack_template.md
```

Direction packs should contain focused paper patterns, local terminology, baselines, threat models, and evaluation playbooks. They are reusable across future papers in the same direction.

## 5. Build personal style memory

Use your own accepted papers, drafts, rejected/revised versions, and advisor edits.

```text
$HElicon
请从下面这些我自己的英文论文段落和修改记录中，蒸馏我的个人写作风格。
不要复制完整句子。请输出可以写入 references/personal_style_profile.md 的规则：
1. opening moves;
2. bottleneck phrasing;
3. contribution style;
4. related-work contrast;
5. evaluation-result phrasing;
6. expressions I like;
7. expressions I reject;
8. recurring weaknesses.

材料：
<粘贴>
```

Write stable lessons into:

```text
HElicon/references/personal_style_profile.md
HElicon/references/mentor_memory.md
```

## 6. Start a new project pack

For any paper project:

```bash
python ~/.agents/skills/HElicon/scripts/bootstrap_project_pack.py ~/HElicon_workspace/projects <project_name>
```

This creates:

```text
~/HElicon_workspace/projects/<project_name>/
├── project_brief.yaml
├── storyline.md
├── evidence_map.csv
├── local_glossary.md
├── focused_references.md
├── experiment_notes.md
├── draft_status.md
├── reviewer_risks.md
├── accepted_phrasing.md
└── memory_patch_log.md
```

Project-specific facts stay here, not in HElicon core.

## 7. Use HElicon on an external project

```text
$HElicon

我现在用 HElicon 修改一个外部论文项目。请注意：该项目不是 HElicon skill 本身。
请先不要润色句子。

请基于下面材料诊断：
1. title;
2. abstract;
3. paper story;
4. positioning;
5. technical framing;
6. terminology;
7. claim-evidence-risk;
8. target-venue fit.

我的中文说明：
<粘贴>

当前英文草稿：
<粘贴>

已有证据：
<粘贴>
```

Then update the project pack:

```text
~/HElicon_workspace/projects/<project_name>/storyline.md
~/HElicon_workspace/projects/<project_name>/evidence_map.csv
~/HElicon_workspace/projects/<project_name>/local_glossary.md
```

Only general lessons should be promoted into the core skill.

## 8. Revision order for any project

Recommended order:

1. project onboarding;
2. direction-pack selection;
3. one-sentence story;
4. paper positioning;
5. title candidates;
6. abstract skeleton;
7. abstract draft;
8. introduction outline;
9. introduction prose;
10. contributions;
11. related-work positioning;
12. evaluation narrative;
13. reviewer simulation;
14. final language polish;
15. memory patch.

## 9. Memory patch loop

At the end of a useful session:

```text
$HElicon
请把这次修改中形成的稳定经验整理成 HElicon Memory Patch。
请区分：
1. 应写入核心 skill 的长期经验；
2. 应写入 direction pack 的方向知识；
3. 只属于当前项目的事实；
4. 不应该写回的临时想法。
```

This is how HElicon becomes more aligned with the user over time.
