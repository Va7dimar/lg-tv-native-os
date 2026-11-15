#!/bin/sh
# probe_phone.sh: what the TV offers the phone remote (issue #21). Reads only:
# it starts no server, opens no port, writes nothing, changes no setting.
# Run it as root on the TV (Homebrew Channel shell or ssh) and paste the
# output into the issue. It prints addresses as "private" or "other" only,
# never the address itself (public repo).
#
#   sh probe_phone.sh
#
# Answers: does busybox carry httpd (and is it CGI-capable), is there nc or
# node as a fallback, which of the ports 8090-8093 are free, can /tmp run a
# CGI script, and are the small tools impetus-ctl leans on there.

PORTS="8090 8091 8092 8093"

say() { echo "$1=$2"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "@shell"
say user "$(id -u 2>/dev/null)"
say busybox "$(busybox 2>&1 | head -n 1 | tr -cd 'A-Za-z0-9 ._()-' | cut -c1-60)"

echo "@server"
applets=$(busybox --list 2>/dev/null)
for a in httpd nc netcat inetd tcpsvd; do
  if echo "$applets" | grep -qx "$a"; then say "applet.$a" 1; else say "applet.$a" 0; fi
done
# httpd answers --help with its usage; -c (conf file) and the CGI word mark a
# build with CGI support compiled in.
hu=$(busybox httpd --help 2>&1)
if echo "$hu" | grep -q 'Usage: httpd'; then
  say httpd.usage 1
  if echo "$hu" | grep -q -- '-c'; then say httpd.conf 1; else say httpd.conf 0; fi
else
  say httpd.usage 0
fi
bb=$(command -v busybox 2>/dev/null)
if [ -n "$bb" ] && grep -q 'cgi-bin' "$bb" 2>/dev/null; then say httpd.cgi 1; else say httpd.cgi 0; fi
if have httpd; then say path.httpd "$(command -v httpd)"; else say path.httpd none; fi
nu=$(busybox nc --help 2>&1)
if echo "$nu" | grep -q -- '-l'; then say nc.listen 1; else say nc.listen 0; fi
if have node; then say node "$(node -v 2>/dev/null)"; else say node none; fi
for t in wget curl; do if have "$t"; then say "tool.$t" 1; else say "tool.$t" 0; fi; done

echo "@tools"
for t in od base64 dd awk tr cut netstat ip ifconfig luna-send; do
  if have "$t"; then say "tool.$t" 1; else say "tool.$t" 0; fi
done
if printf 'b2s=' | base64 -d >/dev/null 2>&1; then say base64.decode 1; else say base64.decode 0; fi
if [ -r /dev/urandom ]; then say urandom 1; else say urandom 0; fi
if od -An -N3 -tu1 /dev/urandom >/dev/null 2>&1; then say od.urandom 1; else say od.urandom 0; fi

echo "@ports"
listen=$(netstat -ltn 2>/dev/null)
for p in $PORTS; do
  if echo "$listen" | grep -q ":$p "; then say "port.$p" busy; else say "port.$p" free; fi
done
say listeners "$(echo "$listen" | grep -c LISTEN)"

echo "@mounts"
# The CGI wrapper lives in /tmp/impetus/www/cgi-bin: a noexec /tmp would stop
# httpd running it.
for m in /tmp /media/developer /media/cryptofs; do
  opts=$(awk -v m="$m" '$2 == m { print $4 }' /proc/mounts 2>/dev/null | head -n 1)
  if [ -z "$opts" ]; then say "mount.$m" none
  elif echo ",$opts," | grep -q ',noexec,'; then say "mount.$m" noexec
  else say "mount.$m" exec; fi
done
if [ -f /etc/httpd.conf ]; then say etc.httpdconf 1; else say etc.httpdconf 0; fi

echo "@network"
# Kind of address only: private (home network) or other.
addrs=$(ip -4 -o addr 2>/dev/null | awk '{ print $2, $4 }')
if [ -z "$addrs" ]; then addrs=$(ifconfig 2>/dev/null | awk '/^[a-z]/ { i = $1 } /inet addr:/ { sub("addr:", "", $2); print i, $2 }'); fi
echo "$addrs" | while read -r ifc a; do
  [ -n "$ifc" ] || continue
  a=${a%%/*}
  case "$a" in
    127.*) kind=loop ;;
    10.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[01].*) kind=private ;;
    *) kind=other ;;
  esac
  say "if.$ifc" "$kind"
done
if have iptables; then say iptables.input "$(iptables -S INPUT 2>/dev/null | head -n 1 | cut -c1-40)"; else say iptables none; fi
