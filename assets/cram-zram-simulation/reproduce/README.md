# CRAM / zram 模拟测试复现附件

这份附件整理自六轮已完成实验的脚本。公开副本把开发机绝对路径替换为脚本所在目录；未包含开发机地址、账号、凭据、内核/QEMU 二进制或源附件。原始实验记录另行保留。

## 准备运行环境

使用支持 KVM 的 x86_64 Linux 测试机，运行用户能访问 `/dev/kvm`。需要 GCC 与静态 libc、make、内核构建依赖、QEMU 构建依赖、Python 3、cpio、gzip、GNU timeout 和静态 BusyBox。原脚本使用 `/usr/bin/busybox`；必须是静态版本，动态版本的共享库未放入 initramfs。可通过 `file /usr/bin/busybox` 检查，或把构建脚本中的该路径替换为自己的静态 BusyBox。

固定源码：

- Linux：https://github.com/gourryinverse/linux ，commit `9fa5ffee4fd4726e31f05deebb938cccfa0b460f`
- QEMU：https://github.com/gourryinverse/qemu ，commit `a078aaedd382eedd121a037ffa992bb9db964acb`

从 `reproduce` 目录准备源码、构建目录：

```bash
git clone https://github.com/gourryinverse/linux.git linux
git -C linux checkout 9fa5ffee4fd4726e31f05deebb938cccfa0b460f
git clone https://github.com/gourryinverse/qemu.git qemu
git -C qemu checkout a078aaedd382eedd121a037ffa992bb9db964acb
mkdir -p build-linux build-qemu
cp kernel.config build-linux/.config
make -C linux O="$PWD/build-linux" olddefconfig
make -C linux O="$PWD/build-linux" -j2 bzImage
```

`kernel.config` 是实验内核最终配置，优先用它复现。另附 `build-kernel.sh` 记录当时启用配置项的过程。配置包括 CRAM、CXL_COMPRESSION、zram、LZ4、function graph、内存迁移以及实验用 CXL_REGION_INVALIDATION_TEST；本配置的 NUMA_BALANCING 未启用。

QEMU 可在 `build-qemu` 中用该固定源码的 `configure` 配置 x86_64-softmmu 与 KVM，再构建 `qemu-system-x86_64`。按源码的构建说明准备依赖；这份附件不包含当时 QEMU configure 命令的完整记录。不要用发行版 QEMU 直接代替，此实验使用该分支的 `cxl-ct3` 设备和 QMP 水位注入接口。

每个用例目录需要三个链接。下面示例在 `reproduce` 内执行；`pressure/oom` 因嵌套一层使用 `../../`：

```bash
for case_dir in matrix latency pressure page-color prepare-profile; do
    ln -s ../build-linux "$case_dir/build-linux"
    ln -s ../build-qemu "$case_dir/build-qemu"
    ln -s ../qemu "$case_dir/qemu"
done
ln -s ../../build-linux pressure/oom/build-linux
ln -s ../../build-qemu pressure/oom/build-qemu
ln -s ../../qemu pressure/oom/qemu
```

全部用例为 RAM 后备 CT3 模型；不实现真实硬件压缩。每个 run-guest.sh 保留对应轮次的实际 QEMU 参数。普通内存 512 MiB，额外 RAM 后备设备 512 MiB；zram 逻辑设备大小 256 MiB，不能合并计算为相同物理预算。

## 第二轮：六组机制路径

```bash
cd matrix
bash build-initramfs.sh
bash run-guest.sh > guest-boot.log 2>&1
printf '%s\n' "$?" > guest-exit-status.txt
python3 analyze.py guest-boot.log
```

guest-init 自动运行 CRAM / zram 的 direct、readwrite、readrepeat，并导出 trace。analyze.py 按阶段 marker 拆分 trace，核对 fault、恢复/提升函数、页状态及校验输出。

## 第三轮：访问计时

```bash
cd latency
bash build-initramfs.sh
bash run-guest.sh > guest-boot.log 2>&1
printf '%s\n' "$?" > guest-exit-status.txt
python3 analyze.py guest-boot.log
```

DRAM / CRAM / zram 三种后端、三种模式，各 1000 个成功样本。输出 samples.csv、clock.csv、failures.csv、results.json。prepare_ns 包含对应后端的准备过程，load/store 使用独立计时区间；zram 先核对 swapped 状态。详细 tracing 关闭。

## 第四轮：压力、回退与恢复

```bash
cd pressure
mkdir -p logs
bash build-initramfs.sh
python3 orchestrate.py
python3 analyze.py logs/guest-boot.log
```

orchestrate.py 启动 guest，根据 guest marker 经本地 Unix socket 注入 lthresh / hthresh，保存 qmp-events.json、guest-exit-status.txt 和 logs/guest-boot.log。guest 依次运行 demotion 关闭、开启、阻止迁入条件。此用例必须通过 orchestrate.py 启动，注入时机是测试步骤的一部分。

无 swap 的 OOM 边界单独运行：

```bash
cd pressure/oom
mkdir -p logs
bash build-initramfs.sh
python3 orchestrate.py
python3 analyze.py logs/guest-boot.log > results.json
```

该用例的预期结果是 stress 被 OOM 终止、init 存活、恢复迁入后探针通过；不是要求 stress 完成工作集校验。

## 第五轮：逐页着色与观察器控制

```bash
cd page-color
sed 's/OBSERVER_MODE/1/' guest-init-template > guest-init
bash build-initramfs.sh
bash run-guest.sh > observed-guest.log 2>&1
printf '%s\n' "$?" > observed-qemu-exit.txt
cp guest-hashes.txt observed-hashes.txt
sed 's/OBSERVER_MODE/0/' guest-init-template > guest-init
bash build-initramfs.sh
bash run-guest.sh > control-guest.log 2>&1
printf '%s\n' "$?" > control-qemu-exit.txt
cp guest-hashes.txt control-hashes.txt
python3 analyze.py
```

480 MiB 工作集，每 64 页采样一个固定逻辑页。先写前 64 MiB，再分段写完整工作集三轮。两组各用新 guest；观察组连续采样，控制组保留相同缓存结构而关闭连续采样。程序以无损 RLE 导出状态，解析输出 timeline.csv、page-transitions.csv、writes.csv 和 results.json。

## 第六轮：单页迁入准备阶段归因

```bash
cd prepare-profile
bash build-initramfs.sh
bash run-guest.sh > guest-boot.log 2>&1
printf '%s\n' "$?" > guest-exit-status.txt
python3 extract-trace.py
python3 analyze.py
```

固定 CPU 0，每次初始化一个新 4 KiB 页；200 个 tracer=nop 样本，随后 40 个 function_graph 样本。计时为单页 move_pages 系统调用，成功后局部写 8 字节并校验整页。trace 根为 __x64_sys_move_pages，启用 sleep-time。完整 trace 通过 gzip/base64 从串口导出，extract-trace.py 还原为 move.trace。

输出 samples.csv、functions.csv、results.json。functions.csv 的时间单位 µs，包含子调用和等待；嵌套函数时间不相加。每个样本的串口 printf 在计时区间外；不同批次的运行时序仍可能影响时间分布。

## 附件检查与验收

附件公开副本做过 Shell/Python 语法检查、文件链接和路径脱敏检查；C 程序内容与原实验一致，原实验已编译并执行通过；路径适配后的整套脚本未在新机器重新运行。正文数据来自原开发机的正式实验。

判断一次复现成功，应同时检查 guest 退出码、日志完成标记、各阶段程序返回值、页状态、内容校验和分析器结果；不能只看 QEMU 进程退出。首次读等非常短的时间受计时开销与 cache 状态影响。输入源码与附件校验值见 SHA256SUMS。

上述示例分别从 reproduce 目录进入用例；不要在上一段所在子目录直接执行下一段的 cd。运行后如修改了源码或配置，保留自己的版本、构建哈希和日志，另记一轮实验。
