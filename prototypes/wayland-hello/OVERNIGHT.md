# Overnight ledger (wayland-hello)

Authority: owner, 2026-11-09 01:01 Atlantic/Reykjavik: "use agents to continue working on the repo even if we cant access the tv right now ... testing can be done later. work via agents trough the night". Window ends 2026-11-09 08:00 Atlantic/Reykjavik. No TV access. No merges.

| Item | State |
| --- | --- |
| Tested SHA before this patch | `133aba1` (box rebuild matched binary `3e608448…`, default IPK `ea3a5c14…`, lifecycle-2 IPK `40264851…`). No `registerApp` reply. v0.6 remove succeeded; v0.7 install overlapped and failed `-5 duplicate command`. TV then unreachable. Evidence: `tvs/lg-65nano756pr/evidence/luna-register-test-2026-11-08.md` on main `3138def`. |
| Review of `b113f77` | Approve-with-nits, host-only. Not evidence the ~31 s reclaim is fixed. |
| This patch | F1–F3 and F7 on that review: reject logs `exiting (luna-reject)` and returns 10; luna error code/message logged; dry-run and startup `close` do not commit a surface; summary has `luna_replies` and `no registerApp reply after`. Fixture covers silent bus, late reject, hub error, unregister order. Still does not claim the 31 s Home relaunch is fixed. |
| Pending live gates | TV reachable. Wait for `NL_APP_REMOVED` before `dev/install` of the lifecycle-2 IPK of the head after this patch. Launch once. Read `/tmp/wh6.log` (`scripts/classify_wh6_log.py` is host-side only). Close with `applicationmanager/close`, not `closeByAppId` via `luna-send-pub`. |
| Owner | repo owner (GitHub `Va7dimar`) |
| Next action | Review this host patch before any lifecycle-2 install. Do not reinstall `133aba1` or `b113f77`. |
