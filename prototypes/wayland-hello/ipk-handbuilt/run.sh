#!/bin/sh
D=$(dirname "$0")
L=/tmp/wh6.log
{ echo "launch $(date -u +%T) args: $*"; env | sort | grep -vE "KEY|TOKEN|SECRET|PASS"; } > $L
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/xdg} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
AID=${APPID:-org.va7dimar.waylandhello}
exec "$D/wayland-hello" --input --duration 30 --app-id "$AID" >> $L 2>&1
