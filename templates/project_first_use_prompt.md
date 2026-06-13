# Project First Use Prompt

Use this when a new external paper project first calls HElicon.

```text
$HElicon

I am using HElicon for an external paper project. The project is not part of HElicon core memory.
Please do not polish sentences first, and do not write project facts into HElicon core.

Task: first-round writing diagnosis.
Goal: diagnose the title, abstract, introduction logic, positioning, storyline, technical framing, and terminology before drafting.
Output language: Chinese explanation plus English paper-writing suggestions.

Please output:
1. current one-sentence story;
2. likely paper type: FHE algorithm optimization / FHE systems / private inference / encrypted search-kNN / hybrid;
3. venue-positioning differences for USENIX Security, NDSS, ACM CCS, and IEEE S&P;
4. title framing issues;
5. abstract logic issues;
6. introduction paragraph-order issues;
7. whether the technical contribution is expressed accurately;
8. terminology table: recommended / avoid;
9. claim-evidence-risk table;
10. next revision priority.

My Chinese project description:
<paste>

Current title / abstract / introduction:
<paste>

Existing experiments, parameters, baselines, and results:
<paste>
```
