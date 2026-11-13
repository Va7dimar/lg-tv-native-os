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
#
# Lifecycle 2 (--luna-register) also installs an LS2 role + client-permission
# + manifest into a writable luna-service2 tree (never /usr, /etc, /var/palm)
# and asks ls-hubd to rescan, matching Homebrew Channel's elevate-service
# pattern. The role exeName is the ELF this script execs, not this script.

LOG=/tmp/wh6.log
FALLBACK_ID=org.va7dimar.waylandhello
APP_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd) || exit 1
LS2_ID=$FALLBACK_ID
LS2_ROLE_SRC=$APP_DIR/sysbus/$LS2_ID.role.json
LS2_PERM_SRC=$APP_DIR/sysbus/$LS2_ID.perm.json
LS2_MANIFEST_SRC=$APP_DIR/sysbus/$LS2_ID.manifest.json

json_string_field() {
	printf '%s\n' "$1" | sed -n "s/.*\"$2\" *: *\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

# Absolute path of conservative tokens (app dir, /tmp test dirs). No JSON/sed metacharacters.
ls2_path_ok() {
	nl='
'
	[ -n "$1" ] || return 1
	case $1 in
	/*) ;;
	*) return 1 ;;
	esac
	case $1 in
	*$nl*) return 1 ;;
	esac
	printf '%s' "$1" | grep -Eq '^[A-Za-z0-9._/+:@=-]+$'
}

# System/RO trees we never write. /var/luna-service2(-dev) is not in this list.
ls2_forbidden() {
	case $1 in
	/usr|/usr/*|/etc|/etc/*|/lib|/lib/*|/lib32|/lib32/*|/bin|/bin/*|/sbin|/sbin/*|/boot|/boot/*|/overlay|/overlay/*|/var/palm|/var/palm/*|/proc|/proc/*|/sys|/sys/*|/dev|/dev/*)
		return 0 ;;
	esac
	return 1
}

ls2_pick_root() {
	if [ -n "${WAYLAND_HELLO_LS2_ROOT-}" ]; then
		printf '%s\n' "$WAYLAND_HELLO_LS2_ROOT"
		return 0
	fi
	if [ -d /var/luna-service2-dev ]; then
		printf '%s\n' /var/luna-service2-dev
		return 0
	fi
	if [ -d /var/luna-service2 ]; then
		printf '%s\n' /var/luna-service2
		return 0
	fi
	return 1
}

ls2_find_control() {
	# Test hook: set to a command path, or empty to simulate a missing binary.
	if [ "${WAYLAND_HELLO_LS_CONTROL+set}" = set ]; then
		if [ -z "$WAYLAND_HELLO_LS_CONTROL" ]; then
			return 1
		fi
		printf '%s\n' "$WAYLAND_HELLO_LS_CONTROL"
		return 0
	fi
	if command -v ls-control >/dev/null 2>&1; then
		command -v ls-control
		return 0
	fi
	if [ -x /usr/sbin/ls-control ]; then
		printf '%s\n' /usr/sbin/ls-control
		return 0
	fi
	return 1
}

ls2_write_file() {
	src=$1
	dest=$2
	from=$3
	to=$4
	tmp=$dest.tmp
	if [ -n "$from" ]; then
		sed "s|$from|$to|g" "$src" >"$tmp" || return 1
	else
		cat "$src" >"$tmp" || return 1
	fi
	if [ -f "$dest" ] && cmp -s "$tmp" "$dest"; then
		rm -f "$tmp"
		return 2
	fi
	mv -f "$tmp" "$dest" || { rm -f "$tmp"; return 1; }
	return 0
}

# Install role/perm/manifest into a writable LS2 tree. Echoes status lines.
# Returns 0 on success (including already-installed), 1 on fail-closed.
install_ls2_identity() {
	exe=$APP_DIR/wayland-hello
	if command -v readlink >/dev/null 2>&1; then
		canon=$(readlink -f "$exe" 2>/dev/null) || canon=
		if [ -n "$canon" ]; then
			exe=$canon
		fi
	fi
	echo "ls2: exe=$exe"

	if [ ! -f "$LS2_ROLE_SRC" ] || [ ! -f "$LS2_PERM_SRC" ] || [ ! -f "$LS2_MANIFEST_SRC" ]; then
		echo "ls2: packaged role/perm/manifest missing under $APP_DIR/sysbus. Failing closed."
		return 1
	fi
	if [ ! -f "$exe" ]; then
		echo "ls2: ELF not found at $exe. Failing closed."
		return 1
	fi
	if ! ls2_path_ok "$exe"; then
		echo "ls2: exe path is not a usable token. Failing closed."
		return 1
	fi

	root=$(ls2_pick_root) || {
		echo "ls2: no writable luna-service2 root (/var/luna-service2-dev or /var/luna-service2). Failing closed."
		return 1
	}
	if ! ls2_path_ok "$root"; then
		echo "ls2: luna root is not a usable path: $root. Failing closed."
		return 1
	fi
	if ls2_forbidden "$root"; then
		echo "ls2: refusing to write system path $root. Failing closed."
		return 1
	fi
	if [ ! -d "$root" ]; then
		echo "ls2: luna root does not exist: $root. Failing closed."
		return 1
	fi
	echo "ls2: root=$root"

	role_dest=$root/roles.d/$LS2_ID.app.json
	perm_dest=$root/client-permissions.d/$LS2_ID.app.json
	manifest_dest=$root/manifests.d/$LS2_ID.json
	if ! mkdir -p "$root/roles.d" "$root/client-permissions.d" "$root/manifests.d"; then
		echo "ls2: cannot create .d dirs under $root. Failing closed."
		return 1
	fi

	changed=0
	ls2_write_file "$LS2_ROLE_SRC" "$role_dest" __EXE_NAME__ "$exe"
	st=$?
	if [ "$st" -eq 1 ]; then
		echo "ls2: failed to write $role_dest. Failing closed."
		return 1
	fi
	if [ "$st" -eq 0 ]; then
		changed=1
		echo "ls2: wrote $role_dest"
	else
		echo "ls2: unchanged $role_dest"
	fi

	ls2_write_file "$LS2_PERM_SRC" "$perm_dest" "" ""
	st=$?
	if [ "$st" -eq 1 ]; then
		echo "ls2: failed to write $perm_dest. Failing closed."
		return 1
	fi
	if [ "$st" -eq 0 ]; then
		changed=1
		echo "ls2: wrote $perm_dest"
	else
		echo "ls2: unchanged $perm_dest"
	fi

	ls2_write_file "$LS2_MANIFEST_SRC" "$manifest_dest" __LUNA_ROOT__ "$root"
	st=$?
	if [ "$st" -eq 1 ]; then
		echo "ls2: failed to write $manifest_dest. Failing closed."
		return 1
	fi
	if [ "$st" -eq 0 ]; then
		changed=1
		echo "ls2: wrote $manifest_dest"
	else
		echo "ls2: unchanged $manifest_dest"
	fi

	if [ "$changed" -eq 0 ]; then
		echo "ls2: already installed, no rescan"
		return 0
	fi

	ctl=$(ls2_find_control) || {
		echo "ls2: ls-control not found. Failing closed."
		return 1
	}
	echo "ls2: scan via $ctl"
	if "$ctl" scan-services; then
		echo "ls2: scan-services ok"
		return 0
	fi
	echo "ls2: scan-services failed, trying scan-volatile-dirs"
	if "$ctl" scan-volatile-dirs; then
		echo "ls2: scan-volatile-dirs ok"
		return 0
	fi
	echo "ls2: hub rescan failed. Failing closed."
	return 1
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

# nativeLifeCycleInterfaceVersion is a number. 2 means SAM's registerApp path.
LIFE=$(printf '%s\n' "$APPINFO" | sed -n 's/.*"nativeLifeCycleInterfaceVersion" *: *\([0-9][0-9]*\).*/\1/p' | head -n 1)
HB=
if [ -f "$APP_DIR/heartbeat-ms" ]; then
	HB=$(tr -cd '0-9' < "$APP_DIR/heartbeat-ms" | head -c 6)
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
	echo "lifecycle=${LIFE:-omit}"
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
	if [ "$LIFE" = "2" ]; then
		echo "----- ls2 -----"
		if ! install_ls2_identity; then
			echo "ls2: could not grant LS2 identity. Failing closed."
			exit 10
		fi
	fi
	echo "----- client -----"
} >>"$LOG" 2>&1

set -- --demo
if [ "$LIFE" = "2" ]; then
	set -- "$@" --luna-register
fi
if [ -n "$HB" ]; then
	set -- "$@" --heartbeat-ms "$HB"
fi
set -- "$@" --app-id "$APPID_VALUE"
exec "$APP_DIR/wayland-hello" "$@" >>"$LOG" 2>&1
