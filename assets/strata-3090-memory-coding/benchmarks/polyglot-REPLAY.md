# 复测 Aider Polyglot：固定编码工作流再比较配置

本目录记录一次 225 题、六语言的 Aider 文件编辑评测。任务要求修改已有源文件，通过测试；首次失败后提供一次测试反馈。五题接入预检单独保存，正式分数使用全部 225 题。

## 头文件解析修正

本轮发现默认lint把.h当成C，26个正确C++参考头文件均误报。后续完整对比使用`run_suite_fixed.py`与`run_experiment_fixed.py`；它们仅把.h语法判定改为C++。旧`run_suite.py`保留原始轮次，26题专项见CPP-CONTROL-PLAN.md。复测需在新目录运行，保留所有失败和退步。

## 固定输入

| 项目 | 本轮协议 |
| --- | --- |
| Aider | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot 题库 | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| 题目及顺序 | `order.json` 的 formal 数组；225 题全部保留 |
| 编辑方式 | `whole`，完整文件输出；无 repo map |
| 测试机会 | 首次 + 一次测试反馈，最多两次测试尝试 |
| Aider 行为 | 保留默认 lint、格式修正、摘要；它们可能产生额外模型调用 |
| 摘要阈值与模型 | Aider max_chat_history_tokens=2048；摘要使用同一个本地模型 |
| 摘要调度 | `summarize_start` 后立即 `summarize_end`，等待并提交摘要，所有请求串行 |
| 推理参数 | temperature=0、top_p=0.95、seed=20261015、reasoning_effort=none |
| 预算 | 总上下文 32768、单次输出预留 8192，因此输入最多24576；每题 600 秒、每次测试 180 秒 |
| 环境 | Python 3.10.12、Go 1.21.5、Node 20.19.0、Rust 1.90.0、JDK 21.0.12.1、Gradle 8.7、GCC 11.4.0 |
| 测试限制 | Docker 无网络、非 root、无 GPU，4 CPU / 6GiB / 256 PID |

完整请求、响应、测试日志和结果均按题保存。Aider 的默认 lint / 格式修正可能在第一次运行测试前请求模型多次，因此这里的“首次通过”指第一次测试尝试通过。最终通过率指允许一次测试反馈后的完成率。

## 换硬件

在相同工具链、依赖锁和 Docker 限制下运行。先用官方参考程序完成 225/225 自检，保存版本和输入哈希。保持模型文件、量化、上下文、MTP、尾部跳过和采样参数一致，另列硬件相关的专家缓存、CPU/PCIe 分工等配置。启动后等待 loaded，再执行同一条预热；正式题库从第一题开始。

当前 `run_experiment_fixed.py` 是修正头文件解析后的本机服务编排脚本，包含本机路径和服务恢复步骤。异机先调整编排及监控路径，保留 `run_suite_fixed.py` 的提示、评分与摘要调度协议。每次使用新实验目录，保存脚本差异；不覆盖已有结果。对实际使用的文件名生成输入哈希清单，并与 phase/runtime.json 核对。旧 `launch.py` 的清单用于初轮，应按新文件名调整，不能直接当成修正版的校验清单。

## 换公共 API

复用相同 Aider 提示、题目顺序、whole 编辑格式、测试反馈、工具链、输出预算与同步摘要。把模型注册名、端点和模型元数据改为服务实际配置，并显式保持 Aider 历史摘要阈值为2048、摘要使用同一被测模型，关闭本机引擎的 proc/log 采样。API 密钥从环境变量读取，不写入请求记录；调用前另行确认费用预算。

服务不支持 seed、temperature=0、reasoning_effort=none 或 8192 输出上限时，单列实际参数差异。API 网络、排队时间计入调用时间。公共榜单先核对编辑方式、Aider 版本、模型、推理模式和预算；本轮使用同步摘要、whole 格式和本机工具链，直接对比应复用这些条件。

## 填表与计时

每个配置填首次通过数、最终通过数、完整 225 题墙钟时间、每题 E2E 中位数/P95、模型 API 总时间、测试总时间、截断数、超时数、失败清单和实际费用。

任务 E2E 包含编辑、摘要、测试、反馈与清理；API 时间包含编辑、格式修正及摘要调用；测试时间包含容器启动、编译与测试。模型加载、预热、参考自检和依赖安装单列。Aider 原有 duration 仅包围 coder.run，本轮同步摘要也在该区间中。非流式调用没有客户端 TTFT 数据。

保留全部失败题。更改提示、预算或参数后的重试另建实验轮次。依赖缓存已按题库预热，测试时禁网；生成代码若引入未提供的新依赖，需把相应构建失败单独说明。专家缓存随固定题序自然变化；比较时采用相同启动流程和顺序。重复整轮有助于评估运行波动，单轮分数只代表该次输出。

## 原始项目

- [Aider benchmark](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/benchmark/benchmark.py)
- [Polyglot 题库](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f)
- [Aider 榜单和评测说明](https://aider.chat/docs/leaderboards/)

## 汇总本轮记录

完整结果同步到remote/后，依次运行`python3 analyze.py`、`python3 audit_tests.py`、`python3 validate.py`、`python3 report.py`。分析脚本要求225题齐全，核对逐题时间、模型调用串行性和实际加载的脚本哈希。`plot.py`依赖matplotlib并使用本机PingFang字体；`build_html.py`使用Markdown3.9生成静态页面。代码轨迹说明保存在FAILURES.md，原始记录与汇总表相互对应。

C++专项结束后，运行`python3 audit_tests.py --cpp-control`和`python3 analyze_cpp.py`。远端`closeout.py`核验日常服务恢复、健康和空闲状态；同步其closeout.json后，运行`final_report.py`、`plot_cpp.py`、`build_html.py`和`package.py`生成最终材料。修正后的功能汇总取199道初轮非C++和全部26道复测C++，完整轮次墙钟分别保留。

额外参考lint审计保存在reference-lint-all.json：修正.h映射后，254份参考源文件中还有C++预处理宏、Rust生命周期两处解析提示；两份参考实现均通过编译验收。本轮其他默认lint未改动，后续比较需保持同一版本和检查行为。
