# Strata 分层观测方法与已有记录

本文重新整理10月13日和14日已有采样，没有新增负载测试。入口：`bottleneck-observations.json` / `.csv`，及两轮独立证据包中的 `recordings/`。

## 先统一请求时间

`run_matrix.py` 的 `request()` 在发出 HTTP 前保存墙钟时间和进程计数，逐条保存 SSE 事件的相对时间，在收到 DONE 后再次读取计数。TTFT计到第一个非空content。`resources.jsonl` 的time是Unix秒，每2秒读取一次资源；截取同一请求开始至结束的采样。模型启动、预热分开记录。示例字段和计算方法如下：

| 层 | 采集位置 | 本次计算与使用方式 |
|---|---|---|
| 请求阶段 | SSE usage/timings、engine.log 的 prompt/generated 行 | prompt_ms为引擎prompt时间，predicted_ms为decode时间；TTFT是客户端等待，检查cached_tokens/reused是否为0 |
| CPU | /proc/PID/stat 的 utime、stime | 两次差值 / CLK_TCK；本机100 ticks/s。所有线程累计CPU秒，含prefill和decode |
| 主缺页 | /proc/PID/stat 的 majflt | 请求前后差值；一次major fault与一次块请求不是一一对应关系 |
| 实际读盘 | /proc/PID/io 的 read_bytes | 请求前后差值 / 1e6；文件路径与每次I/O延迟未包含在这个计数中 |
| RAM | /proc/meminfo 的 MemAvailable、Cached、Mlocked | 本机无swap；记录可用内存及锁页空间，不把全部page cache都当作额外空闲内存 |
| GPU | nvidia-smi GPU util、memory.used、power.draw、temperature.gpu、clocks.sm、clocks.mem | 每2秒采样，按请求区间关联；GPU util描述采样窗口中的活动，不直接给出SM占用率或计算吞吐饱和度 |
| PCIe | engine.log 的 PCIe probe；反序组的 dmon rxpci/txpci | 前者是启动校准，后者是请求期间低频活动采样；本次未记录每个H2D副本的字节量、耗时与等待事件 |
| 显存专家缓存 | 启动cache slots/borrows日志、每请求decode cache hit与resident RAM日志 | 分别看容量、prefill临时借用、decode命中和专家文件读取；命中率本身不包含其他数据文件的读取 |
| MTP | SSE timings 的 draft_n、draft_n_accepted | 按同一组请求求和后相除，并同时比较decode时间、生成量、I/O和正确性 |
| 输出质量 | SSE finish_reason、content/reasoning、冻结功能测试 | 先检查完整结束，再做字段/代码验收；length请求保留为失败，后加边界测试单列 |

完整采集代码在两份证据包的 `run_matrix.py`，原轮汇总见 `analyze.py`，本页摘录由 `extract_observations.py` 从已有汇总与原始日志生成。

## 本次使用的 GPU 采样命令

```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used,power.draw,temperature.gpu,clocks.sm,clocks.mem,pcie.link.gen.current,pcie.link.width.current --format=csv,noheader,nounits
```

10月14日首轮完成后，给全部反序区块追加：

```bash
nvidia-smi dmon -s t -d 1 -o DT
```

请求时间为Unix秒；dmon文本时间采用测试机UTC+08:00。保持统一时间轴后再对照。本文的PCIe采样用于观察活动，未积分为搬运总字节数。

## 记录在哪里

- 原轮证据包 `recordings/confirm-candidate-off/r2--code_retry_fix.json`：77.53秒，533.02MB、4382次major fault；截断。
- 同目录 `r2--code_log.json`：61.29秒，366.20MB、3009次major fault；10/10测试通过。
- `recordings/off-a/code_merge.json` 与 `off-b/code_merge.json`：相同输出SHA，66.29→2.75秒，344.78→1.96MB，major fault 2800→16。
- `recordings/sweep-p2048-w7-s4/sweep-0-mtp07-code_merge.json`：149.7 token/s的原始请求，含输出与67项测试结果。
- 独立分块证据包 `recordings/01-p256-auto/` 至 `08-p256-auto/`：四配置正反序；每进程2次完整预热、3次正式请求。
- 每组 `engine.log` 保存cache规划、CPU/后台亲和、启动PCIe校准；每组 `resources.jsonl` 保存同时间轴资源采样。

## 下一步怎样把等待定位到具体操作

已有数据回答了“哪个请求慢、同期是否读盘、改哪个设置能改善”。以下是尚未执行的细化观测：

- 用逐文件缺页/块I/O追踪关联文件、偏移、提交和完成时间，分清PLE等文件的读取，并给出块I/O延迟分布。
- 用CPU调度trace或逐线程运行/等待统计，区分专家计算、stager数据准备和主线程调度等待。
- 用CUDA trace同时记录H2D memcpy、kernel与event wait，检查复制与计算重叠，以及等待是否落在同一条关键路径。
- 固定块长、只改变流式阈值，把batch收益和流式调度收益进一步分开。

这些trace按独立诊断轮采集；性能数字仍以低干扰计时轮为主。当前没有上述trace，因此保留“PCIe是否饱和、SM是否饱和、某次GPU等待发生在哪个事件”的待定位状态。

## 重新生成本文摘录

解压主证据包后，将其中的 `prefill-ablation-evidence.zip` 解压到同级 `prefill-ablation/` 目录，再执行 `python3 tools/extract_observations.py`。脚本从已有汇总和原日志生成 JSON/CSV，不连接测试机。
