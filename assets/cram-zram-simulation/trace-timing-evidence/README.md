# 第二轮 trace 函数耗时可视化

从原正式机制矩阵提取现有 function_graph 耗时，未增加实验、未修改原始 trace。使用四组单页匿名页用例，绘制进入、首次读、直接首次写、读后首次写四幅 CRAM / zram 对照图。

parse.py 检查每个 CPU 调用栈闭合，提取函数 inclusive 时间与调用次序；plot.py 画调用耗时条形图。无绝对时间戳，所以不是连续时间线，不构造函数开始时刻。每幅图共用 µs 横轴；嵌套函数时间不相加，无监控函数调用不作为零访问耗时。CRAM 两次 fault 的 root 调用分别显示。

全部数据来自第二轮开启 tracing 的单次记录，不拼接第三轮9000个关闭tracing样本，不用于真实设备速度排名。进入图从 cram_migrate_to / __swap_writepage 开始，不是完整 move_pages / MADV_PAGEOUT 准备时间；第六轮完整入口归因另保留。

读后首次写的 handle_mm_fault 两次为64.127 / 8.738 µs，cram_handle_fault57.159、migrate_pages49.448、页分配3.721、try_to_migrate17.291、页复制1.380 µs。该trace显示提升包含分配、映射迁移和其他管理动作，复制并非全部成本。zram 此阶段已恢复普通页，无新的监控fault调用。

公开 trace 副本仅去除十六进制地址；解析时间不受影响。parse.py 可独立生成 CSV 与 JSON，绘图依赖 matplotlib 与中文字体（附件默认 macOS STHeiti，可改为自己的中文字体）。
