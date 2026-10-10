# CRAM 第二篇：实验附件

这是 2026-10-10 的实验源文件、数据和脱敏后的运行脚本。正文数值已经测完；附件不是预期结果列表。

## 目录与数据

- `fbatch/`：完整 01–26 回移及 CRAM 适配的合并 patch、共同 free 修正、probe、guest-init、样本与分析。`source-complete-with-common-fix.patch` 已包含共同修正，不要再重复应用。
- `flushcpu/`：第一次迁移发送 CPU 的 patch、6000 样本/组的独立 A/B。
- `releasecpu/`：发送/归还三组对照；正式样本、独立宿主与 guest trace 汇总、release patch、运行和分析脚本。
- `lineage/`：256 轮逐页实验，PFN/代次分析、完整性统计、两个实际示例及对应 trace 摘录。
- `mmio/`：510 次 MMIO 的宿主阶段分析。
- `kernel.config`：本轮 A/B 使用的配置；未启用 MGLRU/NUMA balancing，开启 DEBUG_VM。
- `guest-tail-selected.trace.txt`：16.183 ms 长尾的选定 trace，包含调度栈和后台函数入口/出口。
- `figures.json`、`plot.py`、`pfn-lineage.mmd`：正文图的数据和生成代码。
- `public-provenance.json`：源文件与脱敏附件的 SHA256；修改启动脚本的路径不会改变已测数据。

CSV 时间单位是 ns。正式 CPU 样本只使用 `mode=nop`。fbatch P99 使用 floor(p×(n−1))，CPU P99 使用 nearest-rank。guest/host 详细 tracing 不混入无详细 tracing 分布。不同目录的轮次、镜像和负载长度分开。

大型完整 host trace、内核/QEMU 二进制未打入附件；保存了原实验构建信息、hash 与选定 trace。部分分析脚本读取 `results/` 或 `host-results/` 原始日志，重采后才有这些文件；现有 CSV/JSON 可直接查看。

## 固定源码与补丁顺序

Linux：`https://github.com/gourryinverse/linux.git`，commit `9fa5ffee4fd4726e31f05deebb938cccfa0b460f`。
QEMU：`https://github.com/gourryinverse/qemu.git`，commit `a078aaedd382eedd121a037ffa992bb9db964acb`。

在独立 Linux checkout 的基础 commit 上构建最终 CPU 对照内核：

```sh
git apply /path/to/kit/fbatch/source-complete-with-common-fix.patch
git apply /path/to/kit/flushcpu/flush-cpu.patch
git apply /path/to/kit/releasecpu/release-cpu.patch
mkdir -p build
cp /path/to/kit/kernel.config build/.config
make O=build olddefconfig
make O=build -j"$(nproc)" bzImage
```

fbatch 原版 A 只应用 `common-cram-free-fix.patch`，B 应用完整合并 patch；配置相同。最终 CPU 对照的三个参数组合用同一个镜像启动。编译环境改变会影响二进制 hash，guest kprobe 偏移与 QEMU uprobe 偏移必须按新二进制反汇编重新核对。

配置中启用的 `CONFIG_CXL_REGION_INVALIDATION_TEST=y` 是模拟 guest 的测试设置，沿用第一篇环境。

## 构建 guest 与启动

在 Linux x86_64 上使用静态 gcc、静态 busybox、cpio 和 gzip；确认 `/usr/bin/busybox` 不依赖 guest 中不存在的动态库。

```sh
cd releasecpu
bash build-initramfs.sh
export QEMU_BIN=/absolute/path/to/fixed-qemu-system-x86_64
export BIOS_DIR=/absolute/path/to/qemu/pc-bios
export KERNEL_IMAGE=/absolute/path/to/split-capable-bzImage
bash run-guest.sh local nop local-export.gz > local.log
bash run-guest.sh remote nop remote-export.gz > remote.log
bash run-guest.sh split nop split-export.gz > split.log
```

每个命令都是一个新 guest；`run-guest.sh` 保留原 q35/CXL/CT3/内存/2vCPU 配置和全部命令参数。`nop` 不开详细 tracing。实验 probe 需要 guest root，以调用迁移与 trace 接口。位置、读后内容、局部写后内容和提升位置都通过才出现 `MIGRATE_CONTENT_POSITION_PASS`。

正式三组顺序与 vCPU 绑核由 `releasecpu/run-matrix.py` 控制；脚本选宿主 affinity 允许集合的最后两个 CPU，应确认这两个 CPU 适合实验。每个 guest 1000 轮，各组 6 次，不并发压测。

`lineage/` 使用单独的 256 轮 probe 和 guest-init，构建方法相同，不能复用正式计时 guest-init。其 trace buffer 较大，会改变时间分布。

## 宿主诊断脚本

宿主 trace runner 需要 root 访问 tracefs，QEMU 在普通实验用户下运行。设置 `LAB_USER`。脱敏脚本保留原实验选择宿主 CPU 6/7、UID 1000 及相应 tracing mask 的代码：运行前按可用 CPU、用户 UID 调整 `run-host.py` 的 affinity、`tracing_cpumask` 和 chown。这些诊断 runner 是采集方法参考，不是通用一键部署工具。

动态 probe 偏移只适用于元数据里的内核/QEMU 二进制。页身份关联用 `struct page` 指针转 PFN，并将宿主 GPA>>12 对上 guest PFN；新内核需要核对 vmemmap、struct page 大小、寄存器与反汇编。每次采集都验证 trace hash、丢事件统计和目标事件数量守恒。

模拟设备由 RAM 后备，不能用这些数据推算真实设备压缩率或端到端硬件延迟。
