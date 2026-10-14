# 事先固定的任务验收条件

所有任务：HTTP200、SSE DONE、finish_reason=stop、无错误；length视为未完成。评分分开报告格式与事实，不用回答相似度代替质量。

- dialogue_capacity：首个2秒，最后20秒，平均11秒；解释单请求token/s与队列等待的区别；不编造GPU吞吐。人工逐项4分。
- dialogue_followup：两个实例最后10秒，平均6秒；指出至少两项真实部署条件（负载/请求长度不同、共享资源竞争、分配不均、固定开销等）；延续上下文且不声称保证翻倍。人工4分。
- incident_extract：合法JSON、精确字段；start_time包含14:05、recovered_time包含14:17、impact_minutes=12；cause表明未证实，不能断言数据库故障；confirmed保留80→20及恢复80事实；next_actions包含等待时间与相同流量复测。人工逐项7分。
- code_merge：67个固定与seed=7301随机测试；覆盖空、相接/不相接、重复、嵌套、负数、错误输入、输入不变。任务全通过才记1。
- code_retry：14项；覆盖bool/非整数、负数、零参数、base>cap、attempts10000，避免指数转float溢出。任务全通过才记1。
- code_log：10项；非法行/非法字段、bool、边界状态码、nearest-rank 1/2/19/20/21/40、额外字段、迭代器。任务全通过才记1。
- long_read：JSON精确提取R017、林青、容量评估未通过、R089、错误率超过2%。任务全通过才记1。

质量结果仅适用于这些工作样本；同策略重复也可能受CPU/GPU浮点归约与适应策略影响，保留重复间变化。动态对话第二轮的输入包含该组第一轮真实输出，不作为完全相同输入的微基准。
