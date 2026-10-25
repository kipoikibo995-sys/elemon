#!/bin/bash
# gom file ACT2_*.png / CHAM*.png từ Downloads vào source rồi tối ưu sang r36s
A=$HOME/mnt/HoLua/assets; D=$HOME/mnt/Downloads
mkdir -p $A/source/tinh-linh/hanh-dong $A/source/cham-soc/_bang
cd $D
find . -maxdepth 1 -mmin +1 -name 'ACT2_*.png' -exec cp -n {} $A/source/tinh-linh/hanh-dong/ \;
for f in CHAM1_do-cham-soc.png CHAM2_canh-bao.png; do [ -f $f ] && cp -n $f $A/source/cham-soc/_bang/; done
cd $A && timeout 170 python3 toi_uu_r36s.py tinh-linh/hanh-dong cham-soc | tail -2
ls source/tinh-linh/hanh-dong | wc -l; du -sh r36s/tinh-linh/hanh-dong 2>/dev/null
