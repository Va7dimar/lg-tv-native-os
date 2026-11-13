# Root-side proof: registerApp works; 31 s Home reclaim is separate — 2026-11-13 ~19:34Z

## Setup (owner-approved root test over SSH)
dev/install of the PR #11 IPK auto-generated the app's LS2 role at
`/var/palm/ls2-dev/roles/{pub,prv}/org.va7dimar.waylandhello.json`, but with
`exeName` = the launcher SCRIPT
(`.../wayland-hello-launch.sh`), not the ELF. ls-hubd keys roles by the
registering process's `/proc/self/exe` (the ELF), so the name claim was rejected
(`-1027 Invalid permissions`). As root I edited both role files to set
`exeName` = `.../wayland-hello` (the ELF), bypassed the launcher's jailed
self-install (`if ! true` so it no longer fails closed; backup at
`/tmp/wayland-hello-launch.sh.bak`), ran `ls-control scan-services` +
`scan-volatile-dirs`, and SAM-launched.

## Result 1 — PERMISSION FIX PROVEN ✅
LSRegister / registerApp now succeed:
```
t=13 luna: register name=org.va7dimar.waylandhello source=app-id
t=13 luna: exe=.../wayland-hello
t=20 luna: LSCall .../registerApp {"subscribe":true}
t=197 luna: reply {"event":"registered","returnValue":true}
t=197 luna: event=registered
```
No `-1027`, no "Invalid permissions". Root cause of the earlier failure: the
generated role named the wrapper script instead of the binary. The surface also
drew: 18 wayland globals, wl_shell, resized to 1920x1080, keyboard focus entered
our surface at t=645 ms.

## Result 2 — registerApp does NOT stop the ~31 s Home reclaim ❌
```
t=645    input: keyboard enter  surface=ours
t=31639  input: keyboard leave  surface=ours entered=1
```
~31 s after launch the compositor pulled keyboard focus off our surface (the
same reclaim seen in plain mode on 2026-11-08), and the process was gone by the
40 s check. Registering with SAM's native lifecycle v2 is therefore NOT the
mechanism that keeps the app foregrounded. The app registered but did not act on
any lifecycle event delivered on the subscription; whatever drives SAM's
~31 s `last_input_handler` → Home relaunch still fires.

## Takeaways
1. Shippable permission fix: the build must ship / generate the role with
   `exeName` = the ELF, or set appinfo `main` so the generated role already names
   the binary. (Manual root edit above is a test shim, not the ship path.)
2. The persistence problem is independent of registration. Next investigation:
   handle the SAM lifecycle events that now arrive on the registered
   subscription (e.g. relaunch/pause/foreground), and/or use wl_webos_shell to
   assert a persistent foreground window, to survive past 31 s.
3. No system partitions touched; edits were under /var/palm/ls2-dev and
   /media/developer (writable dev areas). The role `exeName` correction is
   itself the right fix and was left in place.
