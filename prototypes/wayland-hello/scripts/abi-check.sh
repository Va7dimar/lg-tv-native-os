#!/bin/sh
# Usage: scripts/abi-check.sh BINARY REPORT
# Writes file/readelf -h/-A/-l/-d and objdump -T output, then enforces:
#   ELF32, ARM, EABI5 + soft-float e_flags (0x05000200), no Tag_ABI_VFP_args (VFP regs),
#   max GLIBC symbol version <= 2.28, NEEDED subset of {libc.so.6, libdl.so.2, librt.so.1},
#   interpreter /lib/ld-linux.so.3, no libwayland link-time dependency.
# This describes OUR binary only. It says nothing about the TV compositor's
# build attributes (readelf -A was never captured on the unit).
set -eu
BIN=$1; OUT=$2
RE=${READELF:-readelf}; OD=${OBJDUMP:-objdump}
{
  echo "== file";        file "$BIN" || true
  echo "== sha256";      sha256sum "$BIN"
  echo "== readelf -h";  $RE -h "$BIN"
  echo "== readelf -A";  $RE -A "$BIN"
  echo "== readelf -l";  $RE -l "$BIN"
  echo "== readelf -d";  $RE -d "$BIN"
  echo "== objdump -T";  $OD -T "$BIN"
} > "$OUT" 2>&1

fail=0
$RE -h "$BIN" | grep -q 'Class:.*ELF32' || { echo "FAIL: not ELF32"; fail=1; }
$RE -h "$BIN" | grep -q 'Machine:.*ARM' || { echo "FAIL: not ARM"; fail=1; }
$RE -h "$BIN" | grep -q 'Flags:.*0x5000200' || { echo "FAIL: e_flags != 0x05000200"; $RE -h "$BIN" | grep Flags; fail=1; }
if $RE -A "$BIN" | grep -q 'Tag_ABI_VFP_args: VFP registers'; then echo "FAIL: hard-float VFP args"; fail=1; fi
maxv=$($OD -T "$BIN" | grep -o 'GLIBC_[0-9.]*' | sed 's/GLIBC_//' | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)
echo "max GLIBC version: $maxv" | tee -a "$OUT"
awk -v v="$maxv" 'BEGIN{split(v,a,"."); exit !((a[1]<2)||(a[1]==2&&a[2]<=28))}' || { echo "FAIL: GLIBC_$maxv > 2.28"; fail=1; }
needed=$($RE -d "$BIN" | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p')
echo "NEEDED: $needed" | tee -a "$OUT"
# librt.so.1: glibc 2.12 (openlgtv SDK) still exports clock_gettime from librt.
# The symbol version on that SDK is GLIBC_2.4. The TV's glibc 2.28 provides librt.
for n in $needed; do case $n in libc.so.6|libdl.so.2|librt.so.1) ;; *) echo "FAIL: unexpected NEEDED $n"; fail=1;; esac; done
$RE -l "$BIN" | grep -q '/lib/ld-linux.so.3' || { echo "FAIL: interpreter not /lib/ld-linux.so.3"; fail=1; }
if $OD -T "$BIN" | grep -q 'wl_'; then echo "FAIL: link-time wl_ symbols present"; fail=1; fi
[ $fail = 0 ] && echo "ABI CHECK PASS" | tee -a "$OUT" || { echo "ABI CHECK FAIL" | tee -a "$OUT"; exit 1; }
