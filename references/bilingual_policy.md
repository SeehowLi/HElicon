# Bilingual Policy: Chinese Control, English Paper Prose

The user often thinks and instructs in Chinese while writing English research papers. HElicon should bridge this gap.

## Language roles

- Chinese: discussion, diagnosis, explanation, decision trade-offs, feedback.
- English: paper title, abstract, introduction, contributions, related work, evaluation narrative, rebuttal prose.

## Translation principle

Translate **research intent**, not surface wording.

Bad: literal translation of Chinese research phrases.
Good: natural English used in security, applied cryptography, systems, and FHE papers.

Examples:

| Chinese intent | Prefer | Avoid |
|---|---|---|
| 技术包装 | technical framing; contribution framing; positioning; paper narrative | technical packaging |
| 故事线 | paper story; narrative arc; argument flow | story line in a casual sense |
| 落实到文字 | render the idea in paper prose; turn the idea into a concrete argument | implement into words |
| 同态实现 kNN | FHE-based kNN; encrypted k-nearest-neighbor search; homomorphic kNN evaluation | homomorphic realization of kNN |
| 大模型隐私推理 | privacy-preserving LLM inference; encrypted LLM inference; private inference for large language models | large model privacy inference |

## Continuity

If the user corrects a term, treat the correction as stronger than the default glossary. Propose a glossary patch at the end of the task.

## Output format

When revising English paper prose from Chinese instructions:

1. briefly state the Chinese diagnosis;
2. provide English paper text;
3. explain key wording choices in Chinese;
4. list terminology risks if any.
