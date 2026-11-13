# v0.7 lifecycle-2 (--luna-register) live run on 65NANO756PR — 2026-11-13

## Result (confirmed)
The PR #8 lifecycle-2 IPK (sha256 `888e96b0e705bec22c4852dd7e1d7eea2b54ea8ff2b2d4cfcbcfe6735a7cf7b1`,
binary `673dfb9b98a8d170bb1be328af426afa4e966e06393b05b6c4beeb70359f1c30`,
PR #8 head `8aa820a`) was rebuilt on the box, hash-verified, copied to the TV
(`/tmp/wh-lifecycle2.ipk`, hash matched on-device), the prior app removed
(`dev/remove` returnValue true, gone after 5 s), installed (`dev/install`
returnValue true, appinfo present after 2 s) and launched
(`applicationmanager/launch` returnValue true) at 2026-11-13 18:53:23Z.

The app did NOT draw. It exited almost immediately. `/tmp/wh6.log` shows SAM
passed the native lifecycle-2 launch document:
`argv_1={"event":"launch",...,"appId":"org.va7dimar.waylandhello","interfaceVersion":2,"interfaceMethod":"registerApp","@system_native_app":true}`
and the client then failed closed:

```
t=12 luna: register name=org.va7dimar.waylandhello source=app-id
t=16 luna: LSRegister failed code=-1027 message=Invalid permissions for org.va7dimar.waylandhello. Failing closed.
```

The process was gone afterward (ps empty). The screen never changed; the
normal picture stayed the whole time. Home was never displaced because the
surface was never created.

## Interpretation (not proof of the 31 s cause)
- A dev-installed native app cannot acquire the LS2 bus name `org.va7dimar.waylandhello`
  without a client-permissions/roles grant. `-1027 Invalid permissions` is the
  denial. The fail-closed behaviour from PR #8 is working as written.
- Because the client exits 10 on this path, the lifecycle-2 hypothesis
  ("does registerApp stop the ~31 s Home reclaim?") is still UNTESTED on this TV.
- The plain `--demo` path (no luna register, v0.5/0.6) is the one that held the
  screen 30 s and is also the one Home reclaims at ~31 s.

## Blocker to clear next
Grant the app an LS2 client identity so `LSRegister` / `registerApp` can run:
a roles/permissions file for `org.va7dimar.waylandhello` shipped with the app
(dev install path), without touching system partitions.

## Method-call note
`applicationmanager/close` via `luna-send-pub` was denied
(`-1 Denied method call "close" for category "/"`); it was moot here since the
app had already exited. A working close path still needs to be found for the
cases where the app stays up.
