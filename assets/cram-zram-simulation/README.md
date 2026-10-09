# CRAM / zram 模拟文章数据附件

- summary.csv：126 条汇总指标，单位见 unit 列；采样分布不是压缩率。
- samples.csv：9000 个成功样本的原始计时；时间字段单位 ns。数值 0 可能表示该组未执行对应操作，node 字段 -999 是未观测哨兵。
- plot.py：从 summary.csv 生成两张图；Python + matplotlib，macOS 使用本地 Heiti 字体，其他系统需配置中文字体。
- latency.png：首次访问分位数，对数轴。
- pressure.png：1920 点抽样分布、单批升温墙钟时间。

固定 Linux commit：9fa5ffee4fd4726e31f05deebb938cccfa0b460f。
固定 QEMU commit：a078aaedd382eedd121a037ffa992bb9db964acb。
设备 RAM 后备，不支持真实硬件性能或压缩容量结论。

## 数据校验

- summary.csv SHA-256: `673f85bf1c84b8fc0b9b00603ccc394578fc0bdc838d4239da9163c833829005`
- samples.csv SHA-256: `b036077f7d3aca6e21410f02292c83e5d310d8c8213225aa29b28f263c7987b8`

## 作者原图

cram-access-architecture-author-slide7.png 提取自 Gregory Price（Meta）的 LPC 2026《A Compressed RAM Service》第 7 页 “Write Control”，未修改图像。
官方来源：https://lpc.events/event/20/contributions/2424/
演讲附件：https://lpc.events/event/20/contributions/2424/attachments/2052/4705/A%20Compressed%20RAM%20Service%20%281%29.pptx
原图为作者作品，本目录自绘图的归属不适用于该图片。

## 页状态对照图

page-lifecycle.png / page-lifecycle.svg 为依据固定版本匿名页实验绘制的对照图，不是作者原图。page-lifecycle.py 保留绘图代码。展示进入、首次读与随后首次写；直接首次写的分支在图下注明。

## 第五轮页着色补测

- page-color.png / svg：固定逻辑页的颜色时间线，原升温和完整反复写入分别显示。
- timeline.csv：快照起止时间（ns）及 D/C/S/U 状态序列，固定 1920 个采样页。
- page-transitions.csv：逻辑页编号、MiB 偏移、快照结束时间与观测状态转换。
- writes.csv：两组的写入时段与耗时。
- page-color-results.json：统计、校验与输入哈希；独立于前四轮 summary.csv。
- page-color.c：页编号、位置采样和内容校验程序，Linux 上 gcc -static -O2 -pthread 编译。
- page-color-plot.py：从时间线及结果生成着色图，需要 numpy 和 matplotlib。

观察器会改变耗时；颜色变化不是全量迁移事件。模拟设备、短间隔漏采和非原子快照的限制见正文末注。

## 第六轮准备阶段归因

- prepare-profile-summary.csv：40 个完整 move_pages function graph 样本的函数 inclusive 耗时，单位 µs；嵌套时间不相加。
- prepare-profile-samples.csv：200 个关闭详细 tracing 和 40 个开启 function graph 的迁入墙钟样本，wall_ns 为 ns。
- 新批次与原 samples.csv 的 9000 个访问计时样本分开，不作为原第三轮 96.789 ms 极值的路径证据。

## 图源与复现附件

- page-paths.mmd：CRAM / zram 双泳道 Mermaid 流程图，分别表达首次读、直接首次写、读后首次写。
- reproduce/README.md：构建前提、固定版本、各轮操作顺序与验收。
- cram-zram-reproduce.zip：37 个文件，含各轮测试 C 程序、guest 初始化、QEMU 启动、QMP 注入、分析脚本、固定内核配置与 SHA256SUMS。使用相对目录定位，未包含构建二进制。公开脚本路径适配后只做语法检查，未在新机器重跑。
