#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p build-linux
make -C linux O="$PWD/build-linux" x86_64_defconfig
cfg=linux/scripts/config
opts=(64BIT SMP NUMA ACPI_NUMA MEMORY_HOTPLUG MEMORY_HOTREMOVE MIGRATION CRAM CXL_BUS CXL_PCI CXL_ACPI CXL_MEM CXL_PORT CXL_REGION CXL_REGION_INVALIDATION_TEST CXL_COMPRESSION DEVTMPFS DEVTMPFS_MOUNT TMPFS PROC_FS SYSFS BLK_DEV_INITRD RD_GZIP ZRAM ZRAM_BACKEND_LZ4 ZRAM_BACKEND_ZSTD SWAP FTRACE FUNCTION_TRACER FUNCTION_GRAPH_TRACER KPROBES KPROBE_EVENTS FTRACE_SYSCALLS PERF_EVENTS IKCONFIG IKCONFIG_PROC MEMCG CGROUPS)
for o in "${opts[@]}"; do "$cfg" --file build-linux/.config -e "$o"; done
for o in DRM SOUND WLAN WIRELESS USB MEDIA_SUPPORT INPUT NETDEVICES; do "$cfg" --file build-linux/.config -d "$o"; done
"$cfg" --file build-linux/.config --set-str LOCALVERSION '-cram-lab' -d LOCALVERSION_AUTO
make -C linux O="$PWD/build-linux" olddefconfig
for o in CRAM CXL_COMPRESSION CXL_ACPI NUMA FUNCTION_GRAPH_TRACER ZRAM; do grep -q "^CONFIG_${o}=y$" build-linux/.config || { echo "Missing CONFIG_$o"; exit 1; }; done
make -C linux O="$PWD/build-linux" -j2 bzImage
sha256sum build-linux/.config build-linux/arch/x86/boot/bzImage > kernel-hashes.txt
