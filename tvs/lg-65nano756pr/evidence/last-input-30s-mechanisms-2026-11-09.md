# Why Home returns after a SAM-launched native surface

Public sources checked 2026-11-09, off the TV. OSE SAM is
[webosose/sam `96161d3`](https://github.com/webosose/sam/commit/96161d3e50670fb21daccfb12a75c35fe406ce0e)
(2025-01-20). That tree has no `last_input_handler`, no `on_foreground_null`,
and no `idleApp`. Those names are from LG TV logs, not from this OSE snapshot.

Two different events are already on this set:

- Unlaunched client, 2026-11-08 21:19:49Z
  (`focus-loss-log-2026-11-08.md`): LSM `app_id ""` CARD becomes visible,
  and about 1.5 s later
  `NL_APP_LAUNCH_BEGIN {"app_id":"com.webos.app.home","caller_app_id":"last_input_handler","mode":"last_input"}`.
- SAM-launched plain `wl_shell`, 21:44:23Z
  (`sam-launch-success-2026-11-08.md`): LSM `app_id` stays `""` for the whole
  30 s the process chose to run. Home's `last_input_handler` line is at
  21:44:55Z, when that process exited. The surface was hidden at 21:44:54Z.
- SAM-launched interactive demo, 21:52Z
  (`interactive-demo-2026-11-08.md`): focus at t=586 ms, last key about 9 s
  before t=31.67 s, then `last_input_handler` launches Home while the
  process keeps running. No `registerApp` reply was captured. No later
  v0.7 lifecycle-2 run completed.

Nothing below says registration will stop the 31 s hide.

## Candidates

### 1. LSM `app_id` is empty, so SAM never treats the surface as foreground

**OSE, confirmed.** `LSM::onGetForegroundAppInfo` looks up each LSM
foreground entry with `getByAppId`. A miss is skipped
([`LSM.cpp` 112–116](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/LSM.cpp#L112-L116)).
Only a fullscreen `windowType` updates the full-window app id
([119–120](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/LSM.cpp#L119-L120)),
and a match is what sets `FOREGROUND`
([134](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/LSM.cpp#L134)).
OSE's fullscreen list is `_WEBOS_WINDOW_TYPE_CARD` and
`_WEBOS_WINDOW_TYPE_RESTRICTED`
([`sam-conf.json.in` 36–39](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/files/conf/sam-conf.json.in#L36-L39)).

**This TV.** The 30 s SAM-launched run still logged LSM `app_id ""` while
the picture stayed up. Empty `app_id` alone does not explain a 31 s delay:
the unlaunched client was reclaimed in about 1.5 s.

**One check.** During the first 20 s, one shot:

`luna-send-pub -n 1 -f luna://com.webos.service.applicationmanager/getForegroundAppInfo '{}' </dev/null`

If `appId` is absent or not `org.va7dimar.waylandhello` while
`NL_VSC {"app_id":"","visible":true,"window_type":"_WEBOS_WINDOW_TYPE_CARD"}`
is current, SAM is not using that surface as its foreground app.

### 2. Foreground empty, so TV SAM's last-input path launches Home

**OSE.** Not in this SAM snapshot.

**LG TV, confirmed for the empty-foreground case, not for a 31 s delay.**
Homebrew Channel's Home Chooser records the stock profile on webOS 6–9:
when the foreground becomes empty, sam logs
`LAUNCH_LASTAPP {"status":"run_to_launch_last_app"} on_foreground_null`
and then
`NL_APP_LAUNCH_BEGIN {"app_id":"com.webos.app.home","caller_app_id":"last_input_handler","mode":"last_input"}`
within about 2 s. `getPreloadPolicy` staying `isEnabled:false` is how they
separated it from preload
([`settings-app.md` 534–540](https://github.com/webosbrew/home-chooser/blob/1123add757aafdf6922ce2b630e3bc192c408c38/docs/settings-app.md#L534-L540)).
That matches the 1.5 s unlaunched-client log. It also matches Home
returning at 21:44:55Z, because the process had just exited. It does not,
by itself, explain a hide at 31 s while the process is still alive.

**One check.** The sam line immediately before `caller_app_id":"last_input_handler"`:

`LAUNCH_LASTAPP {"status":"run_to_launch_last_app"} on_foreground_null`

Present: this is the idle/last-input relaunch. Absent: something else
called `launch` with that caller id.

### 3. Launch or transition timer (10 s in OSE, ~30 s on this TV)

**OSE, confirmed and it does not match 31 s.** A native launch is set to
`LAUNCHING` and left there
([`NativeContainer.cpp` 208](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/NativeContainer.cpp#L208);
the comment at
[97–98](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/NativeContainer.cpp#L97-L98)
says `FOREGROUND` arrives later from LSM). The killing timer is 10 s for a
transition and 1 s for close
([`RunningApp.h` 310–311](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/RunningApp.h#L310-L311)).
`LAUNCHING` does not start it
([`RunningApp.cpp` 248–249](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/RunningApp.cpp#L248-L249)).
The timeout log is `Transition is timeout`
([274](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/RunningApp.cpp#L274)).
No 30 s constant showed up in this SAM tree.

**LG TV, hypothesis.** A firmware timer near 30 s from launch, not the OSE
10 s transition kill. The demo's process was still running after the hide,
which a kill would have ended.

**One check.** In the sam log at the hide:

`Transition is timeout`

If that line is absent and the wayland-hello pid is still alive, it is not
this OSE timer.

### 4. Input idle

**OSE.** No input-idle timer in this SAM snapshot.

**LG TV, hypothesis, weaker than a launch timer.** The demo's last key was
about 9 s before the hide, and the hide was about 31.5 s after launch. A
30 s idle measured from the last key would have landed near 53 s. A 10 s
idle measured from the last key is only roughly "about 9 s".

**One check.** Press one arrow at about t=25 s and no other key. Read the
`keycode raw=` line in `/tmp/wh6.log` and the `last_input_handler` line.

- Hide still ~31 s after launch: not idle-from-last-key.
- Hide ~10 s or ~30 s after that key: idle timer of that length.

### 5. `registerApp` never completed

**OSE, confirmed as a lifecycle fact, not as a 30 s clock.** Missing
`nativeLifeCycleInterfaceVersion` means version 1
([`AppDescription.h` 186–188](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/base/AppDescription.h#L186-L188)).
`registerApp` and `registerNativeApp` are the same handler. The bus name it
looks up is `LS2_NAME`, which OSE sets to `<appId>-<n>`
([`NativeContainer.cpp` 199–202](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/NativeContainer.cpp#L199-L202)).
OSE's argv JSON also carries `event`, `reason`, `appId`, and `nid`
([115–120](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/bus/client/NativeContainer.cpp#L115-L120)).
This TV's successful launch argv was only
`{"@system_native_app":true,"nid":"org.va7dimar.waylandhello"}`.
A `close` event is sent only when the running app is already registered
([`PolicyManager.cpp` 89–98](https://github.com/webosose/sam/blob/96161d3e50670fb21daccfb12a75c35fe406ce0e/src/manager/PolicyManager.cpp#L89-L98)).

**LG TV, hypothesis for the 31 s hide.** No completed lifecycle-2 run exists.
The v0.5/v0.6 packages did not call `registerApp`.

**One check.** In `/tmp/wh6.log` for a lifecycle-2 launch, one of:

- `luna: event=registered` and the surface still dies at ~31 s: registration
  was not sufficient.
- `luna: event=close` in the same second as `last_input_handler`: SAM closed
  the registered app.
- `luna: no registerApp reply after`: the bus never answered. That is not
  proof the timer is the missing call.

`python3 -I prototypes/wayland-hello/scripts/classify_wh6_log.py /tmp/wh6.log`
prints `replies`, `reply`, `exit`, and `marker`. It does not judge the screen.

### 6. Window type

**OSE.** CARD and RESTRICTED count as fullscreen, as cited above. Overlay
does not, unless it is in the TV's own `FullscreenWindowType` list.

**This TV.** Plain `wl_shell` was logged as
`_WEBOS_WINDOW_TYPE_CARD` with `app_id ""`. `--webos-shell` with OVERLAY or
CARD produced no `NL_VSC` visible line
(`sam-launch-success-2026-11-08.md`). Switching the Wayland window type is
not a useful next change. `defaultWindowType` in appinfo is a separate
field and was not what LSM printed.

**One check.** The `window_type` value on the last `NL_VSC` line for our
surface before `last_input_handler`. CARD means the compositor's type was
already the OSE fullscreen type.

## What not to add

No new client flag comes out of this. `registerApp` is already the opt-in
`--luna-register` path on PR #8, and lifecycle 2 is the package that passes
it. Another appinfo field or a different Wayland window type would be a
guess. The next live run should be that existing lifecycle-2 package, after
`NL_APP_REMOVED`, with the checks above.
