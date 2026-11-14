# Impetus Home 1.2.0 on the TV — 65NANO756PR — 2026-11-14

The TV session of `prototypes/impetus-home/TV-SESSION.md`, with the owner at
the TV and the remote for every step. Each line below says how it is known:
**seen** (the owner saw it on the screen), **read** (read back from the TV
over SSH) or **not checked**. No serial, nduid, MAC or address is recorded
here and there are no photos. Nothing was flashed, no system partition was
written and no script restarted the TV.

## Run

| Item | Value |
| --- | --- |
| When | 2026-11-14, daytime, Atlantic/Reykjavik |
| TV | LG 65NANO756PR, webOS 6.5.3, reached over SSH with a key (no password prompt) |
| Build | branch `type-saira`, app at `b4ba68c`; IPK SHA256 `e882ef56f1e9bb5a1c56e1d69001efbad0eb437aeced6a7d761bddf7d4d46152`, hash-matched on the TV before install |
| Boot file | `boot/impetus-home` at `97ff3ac`, SHA256 `ef507e05dbe341b441489abb1ca30d85f9b8e9923f722abce16b6018db48fe7a`, hash-matched on the TV |
| Install | Homebrew `appInstallService/dev/install` from `/tmp` |

## What the TV did

| Step | Result | How known |
| --- | --- | --- |
| 1. Shell | busybox; all six one-liners of step 1 item 5 behave as the helper assumes | read |
| 2. Probe | all ten lines `1` (exec, capture, picture, screenoff, sleep, volume, shield, count, log, temp) | read |
| 3. Page | Saira type, the 0.9 figure, the five apps: "looks right" | seen |
| 4. Live still | `kind=live age=0` with HDMI 2 in front and with Impetus in front | read |
| 5. Picture | values belong to the app in front. WIND DOWN took HDMI 2's backlight 40 to 25, `scene off` put 40 back; the saved line was removed | read |
| 5. Picture, by eye | daylight in the room: the owner saw no difference | seen |
| 6. Sleep timer | set by WIND DOWN, cleared by `scene off`. A run to zero (standby) was not done | read / not checked |
| 6. Volume cap | volume was 0 to 2, below the cap of 12: not exercised | not checked |
| 6. Screen off | MUSIC turned the screen off and a key brought it back; the TV logs `Active`, `Screen Off`, `Active` | seen, read |
| 7. Engine room | opens and shows its panels; whether any id shows on the screen was not checked | seen / not checked |
| 8. Shield | turned on by the owner in the engine room: 45 of 45 names blocked, two markers, written in place inside Homebrew's own `/tmp/hosts` mount over `/etc/hosts`. `restore` took it off cleanly | read |
| 9. Boot file | installed with the owner's yes. Home on the remote brings Impetus back | seen |
| 9. Way back | `restore`, the pause file, the boot file removed: LG's Home came up and stayed. Then installed again | seen |
| 9. Across a real restart | not done: see "Sleep, not restart" | not checked |
| 10. APPLE TV door, apps | open what they name | seen |
| 10. YouTube shortcuts | not reported by the owner | not checked |
| 10. `launch: "last"` | the keeper writes the app in front to `/tmp/impetus/front` and the one before to `/tmp/impetus/last` | read |
| 10. Relaunch, FILM NIGHT's colour sign | not done | not checked |

## Sleep, not restart

The remote's power button, short press or held for ten seconds, puts this TV
to sleep. It does not restart it: the same processes are there afterwards and
`/proc/uptime` only stops counting while it sleeps. The TV's log
(`/var/log/messages`) showed, for one off and on:

```
tvpowerd NL_POWER_STATE {"old":"Active","new":"Suspend","PowerOffReason":"remoteKey"}
tvpowerd NL_POWER_STATE {"old":"Suspend","new":"Active","PowerOnReason":"remoteKey"}
SAM NL_APP_LAUNCH_BEGIN {"app_id":"com.webos.app.hdmi2","caller_id":"com.webos.bootManager"}
```

On wake the TV's boot manager reopens the last input and stock Home never
comes to the front, so the boot file's Home watcher has no cue. The owner saw
exactly that twice: the Apple TV showed after an off and on, and Home on the
remote then brought Impetus back.

The owner chose "Impetus first" for a power-on. The boot file therefore got a
second loop (`97ff3ac`): it follows
`luna://com.webos.service.tvpower/power/getPowerState` with a subscription and
opens Impetus after a sleep state followed by `Active`, when the log's last
power line names `remoteKey` as the reason or names none. A wake by another
device leaves that device in front.

**That loop is host-tested only.** Two things about the TV are assumed, not
seen:

1. that the subscription prints a line with `"state":"Suspend"` (or
   `Active Standby`) and later one with `"state":"Active"`. Only the first
   line is known: `{ "subscribed": true, "returnValue": true, "state": "Active" }`.
2. that the log's last `NL_POWER_STATE` line already carries `PowerOnReason`
   three seconds after the wake.

At the end of the session `/var/log/messages` was not there (rotated, or the
TV moved it). With no log the reason reads as empty and Impetus is opened on
every wake, the other device's included.

A cold start (power cord) is the only real restart, and the boot file's own
start, 25 s after the system is up, has not been seen on this TV.

## Changed because of the TV

- One typeface, Saira (`2a8a920`): the first face read as crooked on the panel.
- The apps list is five: YouTube, Spotify, Berliner Philharmoniker, Homebrew
  Channel, MUBI. Seven others are hidden (`fdeb022`, `b4ba68c`).
- The wake loop in the boot file and its four host checks (`97ff3ac`).

## Left on the TV

- Impetus Home 1.2.0, and the boot file at
  `/var/lib/webosbrew/init.d/impetus-home` (the one file outside `/tmp` and
  the app folder). Its watcher and wake loop are running.
- The shield is on (45 names). FILM NIGHT is on, turned on by the owner from
  the control room; it ends by itself at sunrise, and `impetus-ctl restore`
  ends it at once.
- In `/tmp`, gone at the next cold start: the session's helper scripts
  (`tv-*.sh`), the IPK, and two recorders that write down what the power
  subscription and the app-in-front subscription print (`rec-power.log`,
  `rec-front.log`, pids in `rec-power.pid` and `rec-front.pid`). They are
  there so the next off and on shows what assumption 1 needs.

## Still open

1. One off and on with the Apple TV in front: does Impetus come up, and what
   did `rec-power.log` record. Fix the wake loop from that.
2. Where the power lines go when `/var/log/messages` is absent.
3. A cold start: the boot file's own start, and the way back across it.
4. YouTube shortcuts, a sleep timer run to zero, the volume cap with the
   volume above 12, FILM NIGHT's colour sign, relaunch, ids in the engine
   room's log.
