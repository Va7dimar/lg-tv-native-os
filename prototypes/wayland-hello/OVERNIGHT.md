# Overnight ledger (wayland-hello)

Authority: owner, 2026-11-09 01:01 Atlantic/Reykjavik: "use agents to continue working on the repo even if we cant access the tv right now ... testing can be done later. work via agents trough the night". Follow-up 01:21: research the ~30 s `last_input_handler` relaunch from public sources. Window ends 2026-11-09 08:00 Atlantic/Reykjavik. No TV access. No merges.

| Item | State |
| --- | --- |
| Live SHA | Root-side proof 2026-11-13: `registerApp` works once the LS2 role `exeName` names the ELF (`t=197 luna: event=registered returnValue true`). Registration does **not** stop the ~31 s Home reclaim (`keyboard leave` t=31639 ms). `tvs/lg-65nano756pr/evidence/ls2-register-proof-2026-11-13.md`. The jailed SAM process cannot see `/var/luna-service2*` (`ls2-roles-retest-2026-11-13.md`). Do not reinstall `888e96b0…` or `0452e5e3…`. |
| Host head, unmerged | This branch, 0.8. appinfo `main` is the ELF so `dev/install` should generate a matching role. Lifecycle-2 SAM launch uses `wl_webos_shell` overlay + relaunch restore + 90 s cap. SDK binary `ef27b70fcdca93f4a71e92c530d2fefd803d5c8f8a62f078919a45c30ff00f2b`, default IPK `1f774ab06df06fe5b31b712fa63fbb5c377f95e11e14c9afd5df06a3ac61d054`, lifecycle-2 IPK `e940723ab82be2cebcd1e02639abdcf1317afba960524ebe4dd2a8069fef39dc`. Overlay persist is **hypothesis**. |
| This research | `tvs/lg-65nano756pr/evidence/persist-past-31s-2026-11-13.md`. OSE `RunningApp::sendEvent` does not require a client ack. nativeqt `showFullScreen()` on `relaunch`. Overlay is the LSM type that sits above CARD. `last_input_handler` is the verified 31 s cause. |
| Pending live gates | TV reachable. Wait for `NL_APP_REMOVED` before `dev/install` of lifecycle-2 IPK `e940723ab82be2cebcd1e02639abdcf1317afba960524ebe4dd2a8069fef39dc`. One launch. Keep `/tmp/wh6.log`. Confirm `luna: exe=` ends in `/wayland-hello`, `luna: event=registered`, overlay properties, then `persist: alive t=` **> 31000**. Close is the 90 s cap. |
| Owner | repo owner (GitHub `Va7dimar`) |
| Next action | Install the 0.8 lifecycle-2 IPK `e940723a…` and grep `/tmp/wh6.log` for a `persist: alive` tick past 31 s. Do not root-edit `/var` for the role. |
