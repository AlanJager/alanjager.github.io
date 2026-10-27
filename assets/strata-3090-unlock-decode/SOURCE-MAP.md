# 计时与计算路径核对

固定提交：`7695859aa13afb248bdb4d36f9b2e95707db079d`。以下路径相对 Strata 源码根目录。

| 问题 | 源码位置 | 本次怎样核对 |
|---|---|---|
| 浮点矩阵乘用什么精度 | `src/prefill/gemm.cu` 的 `Gemm::bf16/f16` | cuBLAS FP16/BF16 输入、FP32 累加；与独立浮点 GEMM 基准对应 |
| CUDA 构建是否包含 MMQ/fused | `CMakeLists.txt:1360-1396` | 实际 `build.ninja` 中 prefill 编译有 `STRATA_PREFILL_MMQ=1` 与 `STRATA_PREFILL_FUSED=1`；CMakeCache 的同名选项针对 HIP，CUDA 编译以 build.ninja 中的实际定义为准 |
| MMQ 关闭会切什么 | `src/prefill/prefill.cpp:989-1013,3733-3810` | `STRATA_PREFILL_MMQ=0` 使专家先反量化到 FP16，再调用逐专家 f16 GEMM；默认 MMQ 维持量化分组产品 |
| fused 能用于哪些输入 | `src/prefill/prefill.cpp:2945-2995` | 检查编译、量化格式、stream_all、是否 peer、环境开关；以运行日志核实是否进入，不能只登记变量已设置 |
| prefill 分项各代表什么 | `src/prefill/prefill.cpp:1953-1994,4100-4130` | CUDA event 连续间隔；等待归入前一标记。`dequant` 在 MMQ 路径里包含 gather/格式整理，`gemm gate/up` 也包含激活等相关操作 |
| 复制等待在哪里 | `src/prefill/prefill.cpp:3660-3730` | 锁页直传或 stager 缓冲后 H2D；计算流等待 copied，复制复用槽位等待 used |
| decode 总时间怎么拆 | `src/program/generate.cpp:11935-12048` | verify、commit/emit、draft 是部分窗口计时；打印的总 ms/window 还有循环内其他成本，三项之和不强行凑齐总数 |
| decode GPU 分项是否改变路径 | `src/core/verify.cpp:711,847-871,1424,1599-1649,1801-1830` | `STRATA_VERIFY_PROFILE` 开启 GPU stamps，并关闭部分融合/并发优化，因此单独采集，结果用于定位而非速度成绩 |
| 专家缓存与环形槽如何争显存 | `src/prefill/prefill.cpp:220-307` | ring_cap、ring_bytes、ring_slots；结合实际 loan/归还日志，分别登记 prefill 临时占用和 decode 常驻容量 |

运行采样为 `/proc/<engine pid>/io/stat`、内存/磁盘计数、`nvidia-smi` 的功耗/时钟/显存，以及 `nvidia-smi dmon -s t -d 1 -o DT` 的 PCIe RX/TX。PCIe 的秒级平均与某次 H2D 复制有效带宽分开解释。
