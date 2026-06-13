# NOMOS First Use Prompt

NOMOS is only an external project that calls HElicon. It is not part of HElicon core memory.

```text
$HElicon

我现在用 HElicon 修改 NOMOS。请注意：NOMOS 是外部项目，不是 HElicon skill 本身。
请先不要润色句子，也不要把 NOMOS 的项目事实写入 HElicon 核心记忆。

任务：NOMOS 首轮写作诊断
目标：先诊断题目、摘要、文章逻辑叙述、文章定位、故事线、技术 framing、术语自然性。
输出语言：中文解释 + 英文论文表达建议。

请输出：
1. NOMOS 当前的一句话故事线；
2. NOMOS 更像哪类论文：FHE algorithm optimization / FHE systems / private inference / encrypted search-kNN / hybrid；
3. 面向 USENIX Security、NDSS、ACM CCS、IEEE S&P 的定位差异；
4. title 的 framing 问题；
5. abstract 的逻辑问题；
6. introduction 的段落顺序问题；
7. 技术贡献是否被准确表达；
8. 术语表：recommended / avoid；
9. claim-evidence-risk table；
10. 下一轮修改优先级。

我的中文说明：
<粘贴>

当前 title/abstract/introduction：
<粘贴>

已有实验、参数、baseline、结果：
<粘贴>
```
