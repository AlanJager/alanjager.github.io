# 在另一张显卡或公共 API 上复测

复用本目录的 cases.json，不修改题目、请求顺序或4096-token上限。164题、每题一次、串行请求；不要将失败后的修复答案混入pass@1。

## 生成

使用支持OpenAI Chat Completions流式协议的端点。建议在同一客户端机器运行，记录公共服务的网络路径、准确模型版本与日期。密钥通过BENCH_API_KEY环境变量读取，脚本不把它写进结果。

```sh
python3 replay_api.py --cases cases.json --base-url https://YOUR-ENDPOINT/v1 --model EXACT-MODEL-ID --output run-provider
```

默认temperature0、top_p0.95、seed20261015、reasoning_effort none、max_tokens4096。提供`--max-completion-tokens`可换用对应字段；`--omit-seed`与`--omit-reasoning`用于不支持这两个参数的服务。所有实际参数保存在请求记录与run-config.json中，比较时明确差异。仅支持temperature1的模型需要另建相应协议，不能把默认请求失败后悄悄重试为另一套参数。

脚本不自动重试失败请求；传输失败会保存错误并停止。重新运行必须使用新输出目录。比较质量保留一题一次；重复整套评测时把每轮分开。

## 官方后处理与评分

使用与本次相同的EvalPlus源码提交`26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`、数据`HumanEvalPlus-v0.1.10.jsonl.gz`。数据SHA256见dataset-manifest.json。生成的代码仅在隔离容器中执行；可以沿用score-container.sh的无网络、非root、只读输入和资源限制。

prepare_samples.py只使用官方sanitize提取程序，不修改算法或修复答案。以下步骤在相同依赖环境中运行；evaluate在隔离环境中运行：

```sh
python3 prepare_samples.py --cases cases.json --records run-provider --output provider-samples.jsonl
HUMANEVAL_OVERRIDE_PATH=/path/to/HumanEvalPlus-v0.1.10.jsonl.gz python3 -m evalplus.evaluate --dataset humaneval --samples provider-samples.jsonl --parallel 2 --test-details --output-file provider-eval-results.json
python3 summarize_api.py --cases cases.json --records run-provider --evaluation provider-eval-results.json --output provider-summary.json
```

每次重建评分环境先用参考实现跑自检，Base与Plus均应164/164。该检查不调用模型，参考实现和隐藏测试不进入模型请求。Python版本、EvalPlus源码、依赖清单、资源限制都应保留。

## 对比表怎么填

comparison.csv已填本机数据，另外两行留给候选硬件和公共API。核心列为HumanEval+ pass@1、164题生成总时间、每题E2E均值/中位数/P95、TTFT、截断数与真实费用。正式生成时间从首题发出到末题结束，加载/预热/评分单列。

本机基线的请求经loopback访问，公共API会计入网络和排队等待。相同题目在不同模型上token数可能不同；固定题目完成时间适合比较使用体验，token/s用于解释各自生成过程。任务为Python函数实现，公共榜单须核对数据版本、提示形式、n、推理模式和输出预算；本次实测不补造其他服务的时间或费用。
