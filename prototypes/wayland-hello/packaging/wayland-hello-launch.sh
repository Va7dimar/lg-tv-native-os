#!/bin/sh
# Optional helper. Not SAM's main.
#
# On this TV, com.webos.appInstallService/dev/install generates the LS2 role
# at /var/palm/ls2-dev/roles/{pub,prv}/<id>.json from appinfo.json "main".
# ls-hubd keys that role by /proc/self/exe. appinfo.json main is therefore
# the ELF (wayland-hello), not this script. A SAM-launched process cannot
# see /var/luna-service2* and must not try to write LS2 files
# (tvs/lg-65nano756pr/evidence/ls2-roles-retest-2026-11-13.md,
# tvs/lg-65nano756pr/evidence/ls2-register-proof-2026-11-13.md).
#
# This script only dumps env to /tmp/wh6.log and execs the ELF with the
# same argv. The ELF itself recognises a SAM launch JSON document as argv[1].

LOG=/tmp/wh6.log
APP_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd) || exit 1

{
	echo "----- wayland-hello launcher (not main) -----"
	if command -v date >/dev/null 2>&1; then
		date -u '+utc=%Y-%m-%dT%H:%M:%SZ'
	fi
	echo "app_dir=$APP_DIR"
	echo "argv_count=$#"
	echo "argv_0=$0"
	n=0
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

exec "$APP_DIR/wayland-hello" "$@" >>"$LOG" 2>&1
