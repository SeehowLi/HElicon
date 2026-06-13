# Reviewer Simulation Prompt

```text
$HElicon

请模拟 USENIX Security、NDSS、ACM CCS、IEEE S&P 的严格审稿人。
不要只润色；优先判断是否会被拒。

项目：<project>
方向知识库：<direction pack>
材料：title + abstract + introduction + contributions + evaluation summary

请输出：
1. 每个会议最可能的拒稿理由；
2. 严重程度；
3. 对应证据缺口；
4. 必须补的实验/论证；
5. 可以通过写作收紧解决的问题；
6. 不能只靠写作解决的问题；
7. 下一轮修改优先级。
```
