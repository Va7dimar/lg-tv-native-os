# Live display/service mapping — read-only Stage 1

2026-11-08 approximately 18:18–18:20 Atlantic/Reykjavik. Unit: rooted LG 65NANO756PR. Six modest POSIX scripts (`display-map-a.sh` through `display-map-f.sh`) were written on the owner's AC-009 under `~/lgtv-root`, then piped through existing key-auth SSH into `sh -s`. **No TV filesystem writes, rendering, device opens for control, bus calls, service control, reboot, installs or changes to the screen were requested.** Script definitions that contain state-changing commands were read as text only, never executed. No visual regression test was performed. Commands themselves can cause normal process/log activity; this is not a zero-footprint forensic capture.

Serial, nduid, MAC, credentials, full environments and provisioning contents are excluded. Results below are transcribed from Shell stdout, not invented full raw logs. Run B exceeded inline output size; only visible excerpts plus narrower follow-up C–F are used. Original scripts remain on AC-009; this note records the relevant command forms and observed results. No cloud or other-model review of these findings was performed.

## Confirmed observations

### Display ownership, compositor and client stack

- PID 1 `systemd`; compositor PID 1608 `/usr/bin/surface-manager`, PPid 1, sampled VmRSS 55,640 kB.
- Its FD symlinks show `/dev/fb0`, `/dev/fb1`, `/dev/mali0`, `/dev/gdma_hal_gal0`, `/dev/rtd-logger`, `/dev/uinput` and several input event devices. Only link targets were inspected, not device contents.
- Final all-process FD scan found **no open `/dev/dri/card0`**, no `/dev/watchdog` owner and no other fb0/fb1 holder in that sampled process set. This is a point-in-time negative observation, not proof no kernel/vendor component uses these interfaces or that opening them would be safe.
- Several application processes, WebAppMgr and MaliitServer hold `/dev/mali0`; multiple existing Mali clients are observed, not yet custom-client compatibility.
- Surface-manager owns socket inode 17696; `/proc/net/unix` associates it with `/tmp/xdg/wayland-0` (listening row). Directory permissions `0770`, root/compositor group (group name displayed truncated as `composit`); socket `0660`, same ownership.
- Startup wrapper text exports `WEBOS_COMPOSITOR_PLATFORM=eglfs`, displays=1, `QT_IM_MODULE=none`, and ultimately execs surface-manager with that platform. **Wrapper was not executed.**
- Loaded mappings include Qt5Compositor **5.6.3**, Qt5Core/Gui/Network/Qml/Quick **5.12.3**, `libmali.so.0.17.0`, `libwayland-client.so.0.3.0`, `libwayland-server.so.0.1.0`, `libwayland-webos-server.so.1.0.0`, webOS compositor extension plugins, and server graphics integration `libwayland-egl.so`.
- Installed platform plugins: `libqminimal.so`, `libqoffscreen.so`, `libqstarfishegl.so`, `libqvnc.so`, `libwebos-wayland-egl.so`; shell integration `libwebos.so`.
- Installed `libEGL.so.1.4.0`, `libGLESv1_CM.so.1.1.0`, `libGLESv2.so.2.1.0`, Wayland EGL/client/server libraries and Starfish/webOS client libraries were listed. The small EGL/GLES files may be dispatch wrappers; implementation role is not established by size. No libgbm match was returned at `/usr/lib/libgbm*`; not a whole-filesystem absence finding.
- `lsmod`: mali_kbase 471040, use count 6; mali_fb 20480, use count 6; dma_buf_test_exporter 20480, use count 21 (mali_kbase dependency shown).
- Both framebuffers report `mali_venusfb`, 32 bits/pixel. fb0 virtual_size `1920,2160`; fb1 `512,4320`. These are virtual framebuffer dimensions, **not** panel native resolution or a safe modesetting specification. No connector-status lines appeared at the queried `/sys/class/drm/card0-*/status` paths.

### Audio / video / panel / HDMI investigation leads

Final all-process device FD scan:

|Process (sample PID)|Observed selected device links|
|---|---|
|surface-manager (1608)|fb0, fb1, mali0|
|avmutemanager (1487), videooutputd (2054)|video30, video31|
|audiooutputd (1526)|snd/controlC0|
|legacy-broadcas (1565; comm truncated)|snd/controlC0, video2|
|pqcontroller (2050)|video40, video50|
|panelcontroller (2287)|video40|
|extinput-integr (2449; comm truncated)|snd/controlC0, video12|
|eim (2779), arccontroller (2781)|video12|

ALSA card 0 is **Mars / Mars 1**. PCM list: playback 0–7 PCM, 8–9 ES; capture 10 PCM, 11 ES, 12 DSNOOP. Device nodes include corresponding PCM/control entries. No PCM holder in final FD filter; this does not imply audio is idle/broken or exclusively userspace ALSA-driven.

Video class also includes video2 at platform `wfm`, video20 at `vdec`, video27 at `vdogav`, video28/29 at `vdo0`/`vdo1`, video70 at `vcap`, plus virtual video10/12/30/31/40/50/60 and vbi1. Some sysfs `name` files are empty. **Exact HDMI RX/video-plane control contracts have not been identified**: names and FD ownership are leads, not proof which ioctl or service preserves protected playback.

### Supervisor, watchdog and snapshot/resume

- Surface-manager service is a oneshot wrapper requiring ls-hubd and wanting configd, starting/stopping `surface-manager-daemon.service`. Daemon: Type=notify, Restart=on-failure, OOMScoreAdjust=-1000; wrapper launch; runtime directory setup. Drop-in requires and orders after `mount-readonly-volatile.service`.
- tvpowerd: requires/after ls-hubd, Restart=on-failure, OOMScoreAdjust=-1000. videooutputd and audiooutputd require/after ls-hubd and configd, Restart=on-failure, OOMScoreAdjust=-500. Audiooutputd unit includes libsystrim preload. Definitions alone do not establish all effective runtime dependencies or safe restart behavior.
- Kernel thread `hw_watchdog` PID 3 observed; `/dev/watchdog` exists (245:0), sysfs watchdog class exists. Its directory exposed dev/power/subsystem/uevent but none of the queried identity/state/timeout/nowayout files. **Watchdog timeout/arming policy remains unknown. Never open the device to query it.**
- Legacy `/etc/init/ls-hubd_watchdog.conf` describes “watchdog to reboot if ls-hubd dies”, start on stopping ls-hubd. PID 1 is systemd: legacy definition presence **does not prove this Upstart job is active**.
- CRIU process PID 1833 observed. Systemd criu.service starts `/lib/systemd/system/scripts/criu.sh`, image directory `/tmp/checkpoint`, Restart=on-failure; script text starts `/usr/sbin/criu service`.
- Active-system definitions exist for snapshot-boot on/off/components/profile/resume/auto-reboot. Snapshot-on checks `snapshot` cmdline and exclusions, requires GPU libraries + readonly volatile mounts, starts components and calls snapshot-boot-manager with `/etc/snapshot/file_list` and readahead list. Component definition starts compositor/config/bus/app manager and launches stock inputcommon/home with snapshot parameters. These commands were **not invoked**.
- Legacy CRIU copy/remove configuration references persistent second image directory `/mnt/lg/cmn_data/checkpoint`, per-app image hashes/pgid and snapshot-related cleanup. This is separate evidence from kernel resume partition p53; **do not equate CRIU app checkpoints with system-wide p53 snapshots**.
- No process-list grep match was returned for selected compositor/audio/video/power terms in `/etc/snapshot/process_list`. No selected-term matches in the queried resume script. Negative filters do not establish inclusion/exclusion of arbitrary test processes.
- Whether a manually launched client can enter persistent checkpoints, what remote standby does on this unit, or whether cold power restores stock remains **unresolved**. No standby, power-cycle or failure testing occurred.

### ABI and current resource budget

`readelf` and `file` returned no executable path; `getconf GNU_LIBC_VERSION` returned **glibc 2.28**. Compositor maps `/lib/ld-2.28.so`, `/lib/libc-2.28.so`; `/lib/ld-linux.so.3` links to ld-2.28.so.

Read-only `od -An -tx1 -N52 /usr/bin/surface-manager` returned ELF header:

```text
7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
03 00 28 00 01 00 00 00 35 24 00 00 34 00 00 00
68 31 00 00 00 02 00 05 34 00 20 00 09 00 28 00
1d 00 1c 00
```

Interpretation: ELF32, little-endian, EM_ARM (0x28), ET_DYN, e_flags **0x05000200** = ARM EABI5 with **EF_ARM_ABI_FLOAT_SOFT** flag. Thus **do not choose generic Debian armhf/hard-float solely from ARMv7/NEON**. This flag describes calling ABI, not absence of hardware floating point. Exact build triple/attributes, dynamic dependencies and every supplied library's ABI still need off-TV inspection before compilation; no readelf attributes were captured.

Sample resource readings (KiB, transient):

|Resource|Available / free|
|---|---|
|MemAvailable|296696 KiB (~290 MiB)|
|MemFree|32520 KiB|
|SwapFree / SwapTotal|793552 / 921592 KiB|
|/home, /var, /mnt/lg/user overlay|535312 KiB available, 22% used; 40190 free inodes|
|/media and /media/developer (p59 backing)|1117484 KiB available, 47% used; 130598 free inodes|
|/tmp tmpfs|547424 KiB filesystem available; **shared RAM budget, not additional RAM**|

`df` displays overlay backing mounted on `/var` and p59 on `/mnt/lg/appstore`, despite queried paths. No allocation test was performed. Large userland copies and package installs are not yet justified by these figures.

## Method / actual limitations

Relevant read-only commands: `/proc/*/comm`, selected status fields, `ls -l /proc/PID/fd`, selected `/proc/PID/maps` library paths, `readlink /proc/PID/exe`, filtered `/proc/net/unix`, `lsmod`, passive sysfs framebuffer/device class attributes, `/proc/asound/{cards,pcm}`, selected supervisor files and startup-wrapper text, `od` of executable header, `getconf`, `df -k/-i`, selected memory fields.

Initial script A's multi-argument readlink filter returned no owners; **not used as a negative finding**. Listing FD symlinks in B/C/F corrected that method. First scripts ended with an extra PowerShell-pipeline CRLF causing a final CR token / `exit 0` parse error (A/C exit127, B exit2), after earlier reads had completed. D–F used Set-Content `-NoNewline` and a final comment; each exit0. No TV state changes were attempted to correct these transport issues. B was too verbose/truncated; final focused scans are authoritative for the selected ownership claims.

Reproduction transport on AC-009 PowerShell 5.1: store ASCII LF script with `Set-Content -Encoding ascii -NoNewline`, end script in a comment, then pipe `Get-Content -Raw` through existing SSH key auth to `sh -s` (BatchMode, ConnectTimeout=15). Do not expose private key contents or dump full command lines/environments. Sample PIDs are ephemeral: discover again, do not assume fixed IDs.

## Feasibility judgment and next bounded work

A **stock-compositor native client prototype is now a concrete off-TV engineering candidate**: a live Wayland listener, webOS Qt client integration and shared Mali client use are confirmed. This is stronger than node existence alone. It is **not yet a GO to launch**: protocol globals/roles, stock library ABI/header/toolchain compatibility, remote focus/escape, HDMI plane coexistence and snapshot restoration gates remain unresolved. No protocol connection/registry enumeration or custom rendering occurred.

Next priorities: (1) off-TV soft-float ABI/toolchain and webOS Wayland client compatibility investigation using compatible source/library metadata, (2) targeted read-only effective service/snapshot dependency clarification, (3) bounded prototype specification with timed exit and owner notice before any TV copy/launch. Do not kill compositor, modeset DRM, install hooks, adjust watchdog/OOM policy or execute downloaded SDKs. Launcher/client remains a milestone, not completed native OS replacement. Boot/recovery deployment no-go is unchanged.
