# 复现与数据口径

本目录记录固定 Strata 0.1.43 / Qwen IQ2_XS / RTX 3090 的运行时调优。完整原版/解锁72请求对照保留在相邻 `strata-gpu-unlock-20261026`，本目录的原始数据位于 `remote/`。

## 请求与配置

- `replay/cases.json` 保存六类完整请求及输出预算，修复A/B使用各自冻结的完整对话历史。
- `replay/tune.py` 定义第一阶段单变量；`extra.py`、`extra2.py`、`extra3.py`、`memorycap.py` 保存按观测新增的候选。
- `replay/confirm.py` 保存独立启动确认；`select_confirm.py` 保存32768上限候选的初选条件。
- 每个 `remote/<组>/config.json` 是实际传入服务的配置，`fingerprint.json` 保存环境变量、二进制/初始画像哈希、启动参数；`environment.json` 保存loaded时的内存状态。
- 专家初始画像在每次启动前恢复；同一启动按两轮相同题序运行。请求无前缀和对话缓存；加载、预热另计。保留首轮和第二轮，比较时使用中位数与实际范围。

## 指标

- TTFT：发出HTTP请求到首个非空 content；E2E：到SSE完整结束。
- prefill/decode token/s：引擎返回的 `timings`，连同prompt/生成token数保存。
- 无插桩速度组与诊断组分开。`STRATA_PREFILL_TIMING` 为计算流连续event分段，包含等待；`STRATA_VERIFY_PROFILE` 会改变部分融合/并发路径，专供定位。
- `resources.jsonl`每2秒记录GPU与进程计数；`pcie-dmon.txt`每1秒记录RX/TX。进程读盘不等同于整盘吞吐或某一文件的读盘。

## 质量

代码以相同的无网络、非root测试器验收，CPU上限5秒，地址空间384MiB。抽取题以五字段字典精确匹配。`finish_reason=length`、代码语法错误、边界错误和超出资源预算均保留，HTTP200/SSE完整不代替质量验收。

`half8192/r2--repair_b` 资源上限复评保留在 `resource-grade-audit.json`；评分输出和原始请求均未覆盖。`unlocked-confirm-*` 专门确认大上限配置；`prefill18432` 用于对比RAM余量，勿把两者合并为同一配置。

## 重新执行

仅在已安装相同模型的专用测试环境执行。先检查服务空闲并保留日常配置，再修改脚本中的 `REPO` 和冻结画像路径以匹配安装目录。脚本会停止已识别的日常服务，串行运行实验，最后恢复启动器。每组目录要求不存在，避免覆盖原记录。独立工具可直接复算：

```sh
python3 analyze.py
python3 audit.py
python3 plot.py
python3 timeline.py
python3 build_html.py
```

绘图与HTML需要matplotlib、markdown，字体脚本使用本机PingFang，其他系统可换成已安装的中文字体。GPU解锁采用独立的单次启动项，状态核对包括引导参数、日志与GEMM吞吐。

## 归档后的复现修订

日常配置已改为18432。公开重放脚本改为读取随包冻结的 `base-config.json` 和 `frozen-expert-profile.bin`，使baseline保持原2048；执行时的脚本另存 `replay/archive/`。这两处仅改变复现文件查找位置，原始请求和计时不变。

默认启动项的复核显示GPU仍处于解锁吞吐（8192³ FP16约122.35TFLOPS），虚拟机重启没有恢复初始硬件状态。脚本增加实际GEMM状态门槛，避免把仅删除启动参数的状态登记为stock。新的同配置未解锁组需要宿主机层面恢复初始卡状态后再执行。
