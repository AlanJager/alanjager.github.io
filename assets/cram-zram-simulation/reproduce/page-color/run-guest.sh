#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec timeout 180 build-qemu/qemu-system-x86_64 \
    -L qemu/pc-bios \
    -machine q35,cxl=on -accel kvm -cpu host \
    -m 512M,maxmem=2G,slots=8 -smp 2 \
    -object memory-backend-ram,id=ram0,size=512M \
    -numa node,nodeid=0,memdev=ram0 -numa node,nodeid=1 \
    -kernel build-linux/arch/x86/boot/bzImage -initrd initramfs.cpio.gz \
    -append 'console=ttyS0 earlyprintk=serial nokaslr panic=-1' \
    -display none -serial stdio -monitor none -no-reboot -nic none \
     -object memory-backend-ram,id=cxl-mem0,size=512M,share=on \
    -object memory-backend-ram,id=cxl-lsa0,size=1M,share=on \
    -device pxb-cxl,bus_nr=12,bus=pcie.0,id=cxl.1 \
    -device cxl-rp,port=0,bus=cxl.1,id=root_port0,chassis=0,slot=2 \
    -device cxl-ct3,bus=root_port0,volatile-memdev=cxl-mem0,lsa=cxl-lsa0,id=cxl-ct3-0 \
    -M cxl-fmw.0.targets.0=cxl.1,cxl-fmw.0.size=1G,cxl-fmw.0.interleave-granularity=8k
