#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
gcc -static -O2 -g -Wall -Wextra -Werror -o stress stress.c
mkdir -p rootfs/{bin,sbin,proc,sys,dev,tmp}
cp /usr/bin/busybox rootfs/bin/busybox
for app in sh mount mkdir cat sleep uname poweroff mkswap swapon swapoff; do ln -sf busybox "rootfs/bin/$app"; done
cp stress rootfs/bin/
cp guest-init rootfs/init
chmod +x rootfs/init
(cd rootfs && find . -print0 | cpio --null -o --format=newc) | gzip -1 > initramfs.cpio.gz
sha256sum stress.c stress initramfs.cpio.gz > guest-hashes.txt
