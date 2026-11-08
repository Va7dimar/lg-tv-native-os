#!/bin/sh
# Native launcher for org.va7dimar.waylandhello.
#
# webOS OSE "Developing Built-in Native Apps" says SAM passes its launch
# document as argv[1]. The lifecycle event in that document is "launch",
# and values from the launch method's params arrive under "parameters".
# The same tutorial reads the target display from the DISPLAY_ID environment
# variable, defaulting to "0" when it is unset.
# https://www.webosose.org/docs/guides/development/configuration/developing-built-in-native-apps/
#
# On this TV, SAM-launched services have APPID=<id>. That value is the app
# id passed to the client. If APPID is unset, appId inside argv[1] is used.
# The id in appinfo.json is the last fallback.
# The client is plain wl_shell --demo. A SAM-launched webOS shell was not
# shown. XDG_RUNTIME_DIR and WAYLAND_DISPLAY are set only when unset, to
# /tmp/xdg and wayland-0. Stock processes on this TV use XDG_DIR=/tmp/xdg;
# this client reads XDG_RUNTIME_DIR.

LOG=/tmp/wh6.log
FALLBACK_ID=org.va7dimar.waylandhello
APP_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd) || exit 1

json_string_field() {
	printf '%s\n' "$1" | sed -n "s/.*\"$2\" *: *\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

ENV_APPID=${APPID-}
ARG1=${1-}
APPINFO=
if [ -f "$APP_DIR/appinfo.json" ]; then
	APPINFO=$(cat "$APP_DIR/appinfo.json")
fi
APPID_VALUE=
APPID_SOURCE=

if [ -n "$ENV_APPID" ]; then
	APPID_VALUE=$ENV_APPID
	APPID_SOURCE=APPID
fi
if [ -z "$APPID_VALUE" ]; then
	FROM_ARG=$(json_string_field "$ARG1" appId)
	if [ -n "$FROM_ARG" ]; then
		APPID_VALUE=$FROM_ARG
		APPID_SOURCE=argv1.appId
	fi
fi
if [ -z "$APPID_VALUE" ]; then
	FROM_INFO=$(json_string_field "$APPINFO" id)
	if [ -n "$FROM_INFO" ]; then
		APPID_VALUE=$FROM_INFO
		APPID_SOURCE=appinfo.json
	fi
fi
if [ -z "$APPID_VALUE" ]; then
	APPID_VALUE=$FALLBACK_ID
	APPID_SOURCE=fallback
fi

XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/xdg}
WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
export XDG_RUNTIME_DIR WAYLAND_DISPLAY

{
	echo "----- wayland-hello launcher -----"
	if command -v date >/dev/null 2>&1; then
		date -u '+utc=%Y-%m-%dT%H:%M:%SZ'
	fi
	echo "app_dir=$APP_DIR"
	echo "app_id=$APPID_VALUE"
	echo "app_id_source=$APPID_SOURCE"
	echo "xdg_runtime_dir=$XDG_RUNTIME_DIR"
	echo "wayland_display=$WAYLAND_DISPLAY"
	echo "argv_count=$#"
	n=0
	echo "argv_0=$0"
	for arg in "$@"; do
		n=$((n + 1))
		echo "argv_$n=$arg"
	done
	echo "----- environment -----"
	if command -v env >/dev/null 2>&1; then
		env | sort
	else
		set
	fi
	echo "----- client -----"
} >>"$LOG" 2>&1

exec "$APP_DIR/wayland-hello" \
	--demo \
	--app-id "$APPID_VALUE" \
	>>"$LOG" 2>&1
