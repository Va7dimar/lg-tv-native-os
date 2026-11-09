# Overnight ledger (wayland-hello)

Authority: owner, 2026-11-09 01:01 Atlantic/Reykjavik: "use agents to continue working on the repo even if we cant access the tv right now ... testing can be done later. work via agents trough the night". Window ends 2026-11-09 08:00 Atlantic/Reykjavik. No TV access. No merges.

| Item | State |
| --- | --- |
| Tested SHA before this patch | `133aba1` (box rebuild matched binary `3e608448…`, default IPK `ea3a5c14…`, lifecycle-2 IPK `40264851…`). No `registerApp` reply. v0.6 remove succeeded; v0.7 install overlapped and failed `-5 duplicate command`. TV then unreachable. Evidence: `tvs/lg-65nano756pr/evidence/luna-register-test-2026-11-08.md` on main `3138def`. |
| This patch | Host-only. Rejected `registerApp` replies, `LSRegister`/`LSCall` failure, missing `LSGmainAttach`, relaunch vs close, poll `g_main_context_iteration(NULL, 0)`, and `LSUnregister` after close. Does not claim the 31 s Home relaunch is fixed. |
| Pending live gates | TV reachable. Wait for `NL_APP_REMOVED` before `dev/install`. Launch lifecycle-2. Read `/tmp/wh6.log` for `registerApp` replies past 31 s. Close with `applicationmanager/close`, not `closeByAppId` via `luna-send-pub`. |
| Owner | repo owner (GitHub `Va7dimar`) |
| Next action | Review this host patch. Do not reinstall `133aba1`. |
