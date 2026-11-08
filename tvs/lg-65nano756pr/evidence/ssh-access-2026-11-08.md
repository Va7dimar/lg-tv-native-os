# Post-root SSH/Telnet access — LG 65NANO756PR

Recorded 2026-11-08 ~17:53 Atlantic/Reykjavik. Unit is rooted (SlopBro, owner-run) with
Homebrew Channel present and Root status "ok".

## Homebrew Channel root configuration (as set by owner)
- Telnet: ON
- SSH Server: ON
- Block system updates: ON (keep on; Auto Update also OFF in LG settings)
- Failsafe mode: OFF
- webosbrew version: 0.7.3
- Repositories: https://repo.webosbrew.org (Default) + Extra non-free software

## How to connect (from owner's PC on the same LAN)
- TV LAN IP (DHCP, may change): 192.168.0.2
- Command: `ssh root@192.168.0.2`
- Host key: ED25519, already added to PC known_hosts on first connect.
- Login: user `root`. Default-password login is in effect (webosbrew warns the system
  is using a default password). Prompt lands at `root@LGwebOSTV:~#`.
- Telnet also available on the TV as a fallback.

## Hardening note (not yet done)
webosbrew warns: insert an SSH public key into `/home/root/.ssh/authorized_keys` and
reboot to remove the default-password warning. Optional; do only if we want key-only auth.

## HARD SAFETY RULE (from the TV's own banner)
NEVER overwrite system partitions (kernel, rootfs, tvservice) or the TV is bricked,
guaranteed. All current work is READ-ONLY inventory. No writes to system regions,
no flashing, until a verified boot route + independent recovery exist and owner decides.

## Secrets
TV serial / MAC / any keys stay OUT of this repo. IP above is a private-LAN DHCP
address only.
