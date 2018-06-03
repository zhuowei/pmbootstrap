#!/bin/sh
# usage: boot.sh kernel_path initrd_path cmdline
# https://github.com/fail0verflow/shofel2/blob/master/usb_loader
# but dynamically generated with specified paths and size
set -e
kernel="${1}"
initrd="${2}"
bootargs="${3}"
initrdsize=$(printf "0x%x" $(stat -c %s "${initrd}"))
# generate the U-Boot script
rm -r /tmp/nx-boot || true
mkdir /tmp/nx-boot
cd /tmp/nx-boot
cat >switch.scr <<EOF
echo "unzipping kernel..."
unzip 0x83000000 0x85000000
setenv bootargs '${bootargs}'
echo "resetting usb..."
usb reset
echo "booting..."
booti 0x85000000 0x8f000000:${initrdsize} 0x8d000000
EOF
mkimage -A arm64 -T script -C none -n "boot.scr" -d switch.scr switch.scr.img
cat >switch.conf <<EOF
switch
hid,1024,0x80000000,0x80000000,2G
${kernel}:load 0x83000000
${initrd}:load 0x8f000000
/mnt/rootfs_nintendo-nx/usr/share/dtb/nvidia/tegra210-nintendo-switch.dtb:load 0x8d000000
switch.scr.img:load 0x8e000000,jump_direct 0x8e000000
EOF
cat >imx_usb.conf <<EOF
0x0955:0x701a, switch.conf
EOF
imx_usb -c .
