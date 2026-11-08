# Post-root plan — LG 65NANO756PR

2026-11-08, Atlantic/Reykjavik. **Planning/research only; no custom OS built or booted.**

## Goal, authority and evidence

The goal remains a custom operating environment **inside the TV**, preserving panel/backlight, HDMI **input** including normal licensed protected playback, audio, remote and power/thermal behavior. Homebrew Channel is a foothold, not completion. A fullscreen shell on stock webOS is a useful integration milestone, **not a replacement OS** and not presumed to satisfy the owner's earlier requirement that an app is insufficient. The long-term retained/replaced boundary stays explicit and subject to the owner's decision; this plan does not silently change it.

Owner requested documentation and enhanced plans with Claude, ChatGPT and Gemini. This update supersedes the pre-root sequencing in [root-plan](evidence/root-plan.md) and supplements, rather than discards, the [earlier native design](docs/plans/2026-11-08-native-bootable-os-design.md), [execution plan](docs/plans/2026-11-08-native-bootable-os.md), [boot route](evidence/boot-route.md), [recovery case](evidence/recovery-case.md), and [decision history](evidence/decision-record.md). Historical prohibitions/unknown identity fields describe their recording time; current root/read-only access is recorded in the [live inventory](evidence/live-system-inventory-2026-11-08.md).

**Current hard limits:** no writes to kernel/rootfs/tvservice/boot/system partitions, flashing, exploit reproduction, bank switches or boot-policy changes. Notice to the owner precedes every non-read-only TV action, including copying/installing software, launching UI, hook changes, stopping services or rebooting. Research authority is not boot/flash authority: those require a verified exact-target route, independent operation-specific recovery and an explicit owner decision. No physical opening is inferred. Keep serial, nduid, MAC, keys and credentials out of git.

### What changed, and what did not

|Observation from the running unit|What it supports / does not prove|
|---|---|
|Root SSH and Homebrew 0.7.3 available|Can inspect live vendor interfaces; does not unlock bootloader or establish recovery.|
|RTD2875/K7LP, ARMv7l, ARM part 0xd05 (A55 class), four cores|Use a 32-bit target ABI investigation, not an assumed arm64 userland; full sales suffix/PCB/panel assembly still need evidence.|
|Mali modules, DRM card0, fb0/fb1|Discovery leads only: no demonstrated EGL ABI, client protocol, scanout or HDMI-plane coexistence.|
|Kernel 4.4.84 built with gcc 8.2.0|Aligns with OSS/SDK findings; exact config, patches, module ABI and BSP build closure remain unproved.|
|~1.5 GB physical RAM, ~1.07 GB Linux-visible; ~7.3 GiB eMMC|Budget actual free RAM/storage, not total capacity or TV Information's app-space number.|
|p27 squashfs root, p29 BSP overlay, writable user areas, parallel p38 bank layout|Not proof p38 is valid/selectable/fallback-safe. Writable user areas can hold executable persistence and are not harmless by definition.|
|`starfish-global-secured`, `encryption_key_type: prodkey`|Production-image metadata; signature enforcement, covered stages, fuses and rejection behavior are **unknown**. Assume restrictive policy for planning, do not report it as measured.|
|No standard fw_env tools/config; negative `/etc` bank-reference search|No discovered userspace selection mechanism, NOT proof selection is absent from all userspace.|

The live note's claim of viable chroot/DRM/startup paths is a **proposal**, not a demonstrated route. Its “recovery signal” and signed-image rejection language must be read with the qualifications above. Stock updates, factory reset and parallel partitions remain insufficient independent recovery. Boot/deployment no-go is unchanged even without proven signature enforcement.

## Independent review reconciliation

Raw prompt/outcomes: [review packet](reviews/2026-11-08/README.md). These are opinions checked against the evidence, not three hardware confirmations.

|Reviewer / actual outcome|Top recommendation|Agreement / disagreement and disposition|
|---|---|---|
|Claude, requested Opus 5.5 high; substantive exit 0, internal safety-truncation caveat|Map display ownership first; retain vendor compositor/services for a fullscreen shell|Agrees with Codex on route order. Claims “preserves all four by construction,” “zero brick risk,” fully reversible hooks and chroot GO are too strong: reject those assurances; require manual bounded testing before persistence.|
|ChatGPT/Codex, CLI reported gpt-6.1-sol high; substantive exit 0|Map display owner/client ABI; manual shell milestone before hooks|Prefer its stricter reversible-test gates, memory budgeting, snapshot/restore caution and metadata/A-B qualifications. It notes a launcher does not equal complete replacement.|
|Gemini, requested Argon high; exit 0, empty response (not successful review)|No recommendation obtained|Headless command permission auto-denied. No retry/escalation. No Gemini agreement/disagreement can be inferred.|

Both substantive reviews prioritize vendor-stack coexistence over direct framebuffer takeover, chroot before kernel replacement, and boot/recovery characterization before deployment. Neither establishes the display API. Claude's suggestion to install a startup hook early is deferred; Codex's manual-first sequence is adopted. No model approved this synthesis.

## Ranked routes and gates

|Rank / route|Delivers and retained boundary|Evidence needed / current gate|Risk and reversibility|
|---|---|---|---|
|1. Fullscreen shell as a stock-compositor client|Custom home/navigation/settings/input UI inside TV; retains kernel, init, compositor, vendor TV/audio/power stack. **Milestone, not OS replacement.**|Read-only discovery GO. Need client protocol/ABI, focus/remote control, HDMI overlay behavior, supported control interfaces and escape path before any prototype launch.|Lowest relative risk, not zero: focus capture, OOM, video obstruction. Manual nonpersistent process first; no launcher disabling or hook installation. Exit/restore must be demonstrated.|
|2. Alternative Linux userland on vendor kernel|Different userland/native applications, initially clients of stock compositor; vendor hardware stack retained. Chroot alone does not provide graphics, isolation or hardware integration.|Need ELF/loader/libc/kernel compatibility, storage/headroom, graphics libraries/protocol, scoped devices and service bridge. armhf is a candidate, not an ABI guarantee. Prepare off-TV only until mapped.|Shared kernel and resource contention; mounts/persistence complicate cleanup. A directory is removable but side effects are not automatically reversible. Direct DRM/fbdev is separately gated, not implied by chroot success.|
|3. Custom compositor / selective vendor userspace replacement|More independent interface/window/input stack, while enumerated vendor HDMI/audio/power dependencies remain.|Current takeover NO-GO. Need buffer ABI, HDMI/video-plane integration, supervisor/respawn/watchdog dependencies and independently demonstrated stock restoration with screen unavailable.|Black screen, lost input/audio/power functions, restart loops. Stock reboot restoration is a hypothesis until snapshot/resume and hook order are characterized. Do not stop services to discover dependencies.|
|4. Alternate init/kernel/boot|Actual replacement boundary; retain only explicitly justified hardware components, subject to owner selection.|Deployment NO-GO. Need exact running config/board mapping, complete build/packaging/BSP inputs, legitimate boot acceptance, independent tested recovery and preservation/non-impact coverage plus owner decision.|Potential unrecoverable failure/unit-data loss. No partition writes, custom boot, kexec or signature-policy experiments under this plan. Source availability is not bootability.|

## Stages, deliverables and acceptance

1. **Read-only display/service/ABI map (next).** Identify processes holding display nodes, likely client protocol/library paths, init/supervisor relations, free resources and startup mechanism. Record exact commands, missing utilities and outcomes in a scrubbed per-unit evidence note. Avoid repeated full inventory. Exit gate: a specific evidenced client path, or an honest unresolved path; never infer availability from file names alone.
2. **Off-TV prototype specification/build proposal.** Choose a compatible toolkit only after Stage 1. Record retained/replaced component ledger, manual launch/exit design, bounded resource/runtime budget and recovery/stop conditions. No TV copy or execution here. If no usable client path exists, continue interface research rather than terminate vendor services. A new build/tooling scope follows repository controls; don't execute downloaded SDK installers casually.
3. **Owner-notified, bounded nonpersistent UI test, only after prerequisites.** First establish independent administrative access/escape and a restoration design; don't use destructive testing to prove it. No hooks. Compare panel, existing HDMI2 SDR Filmmaker baseline, AppleTV normal protected playback, audio/mute/volume, input switching, remote/CEC, standby/wake and thermal behavior. Keep HDR untouched initially. Stop immediately on lost control, unexpected power behavior, memory pressure or viewing disruption; do not improvise takeover. Record observed vs untested functions. This stage has **not** run.
4. **Userland integration, then optional persistence.** Only if it materially advances the owner goal: alternative-userland client prototype with scoped devices/mounts and cleanup. After repeatable manual success, characterize cold boot vs standby/snapshot startup, storage expiry, hook ordering and escape before proposing an opt-in startup hook. Persistent hooks need owner notice and a tested disable path. No guarantee SSH survives compositor/init changes.
5. **Replacement feasibility track.** Continue bounded off-TV source/BSP/build-closure work under existing controls. Characterize legitimate boot/recovery documentation without bypass experiments or raw provisioning reads. Route 3 remains gated on restoration and dependencies; Route 4 on boot acceptance + independent recovery + owner decision. A launcher success does not retire this track or count as a replacement OS.

## Concrete next read-only TV experiments — proposed, NOT executed

Run over the established SSH path, sequentially; capture output on the controlling PC/box, not to files on the TV. Tools/options may differ on BusyBox: record absence, don't install a substitute. No commands below open devices for rendering, perform modesets, invoke unknown bus methods or stop/restart processes. Do not dump command lines, environments, os_info, whole logs or private storage. Before committing output, inspect and redact identifiers/unexpected sensitive fields.

### A. Display owners and supervisor identity (first priority)

```sh
ps -eo pid,comm
cat /proc/1/comm
ls -l /dev/dri/card0 /dev/fb0 /dev/fb1
for p in /proc/[0-9]*; do
    hits=$(readlink "$p"/fd/* 2>/dev/null |
        grep -E '^/dev/(dri/[^/]+|fb[0-9]+|mali[0-9]*)$')
    if [ -n "$hits" ]; then
        printf 'pid=%s comm=' "${p##*/}"
        cat "$p/comm"
        printf '%s\n' "$hits"
    fi
done
```

If `ps` options fail, the `/proc` loop still reports display owners by comm, without process arguments. Names/FDs alone do not establish dependency or safe termination.

### B. Client interfaces and passive display attributes

```sh
for f in /usr/lib/libEGL.so* /usr/lib/libGLESv2.so* \
         /usr/lib/libwayland-client.so* /usr/lib/libgbm.so*; do
    [ -e "$f" ] && ls -l "$f"
done
for s in /run/wayland-* /tmp/wayland-*; do
    [ -S "$s" ] && ls -l "$s"
done
for f in /sys/class/graphics/fb[01]/name \
         /sys/class/graphics/fb[01]/virtual_size \
         /sys/class/graphics/fb[01]/bits_per_pixel \
         /sys/class/drm/card0-*/status; do
    [ -r "$f" ] && printf '%s: ' "$f" && cat "$f"
done
ls -d /etc/init /etc/systemd/system /usr/lib/systemd/system 2>/dev/null
```

No socket at guessed paths is not proof none exists. After A, substitute the **observed numeric compositor PID** in these targeted reads (do not type `PID` literally):

```sh
readlink /proc/PID/exe
grep -E '/[^ ]*(libEGL|libGLES|libwayland|libgbm|libmali)[^ ]*' /proc/PID/maps
```

Inspect only the subsequently identified compositor supervisor definition for dependencies/respawn, and the identified Homebrew startup entry for ordering; redact before retention. Do not run scripts or bus methods. Wayland client compatibility and graphics-buffer ABI remain unproved even with libraries/socket present.

### C. Userland/resource and kernel compatibility

```sh
command -v readelf file chroot unshare
if command -v readelf >/dev/null 2>&1; then
    readelf -h /bin/busybox
    readelf -l /bin/busybox | grep 'interpreter'
fi
grep -E '^(MemAvailable|MemFree|SwapTotal|SwapFree):' /proc/meminfo
df -k /home /media /tmp
cat /proc/filesystems
if [ -r /proc/config.gz ]; then
    zcat /proc/config.gz |
      grep -E '^(CONFIG_(ARM|ARM64|MODULES|MODVERSIONS|IKCONFIG|IKCONFIG_PROC|DRM|FB)=|# CONFIG_MODVERSIONS is not set)'
fi
```

A static BusyBox has no ELF interpreter; establish a representative dynamic vendor executable later before choosing libraries. Config absence is a missing observation, not a negative feature result. These checks do not justify raw partition reads, driver loading, chroot execution or boot tests. Existing inventory already records bank geometry; no need to probe it again for UI work.

## Open questions / reproducibility

- Which compositor/client protocol actually works, and can custom clients coexist with HDMI/protected video planes and remote focus?
- What vendor services must remain for panel, HDMI RX/HDCP, audio, power/thermal and CEC? Driver filenames are not a working interface contract.
- Which libraries/loader/graphics-buffer ABI and 4.4-kernel-compatible userland are usable with realistic memory/storage headroom?
- Does cold boot differ from snapshot/standby resume, and how can a failed hook be disabled without the UI it obscures?
- Which owner-selected retained/replaced boundary counts as success? A shell milestone is not assumed to answer this.
- Exact suffix/PCB/panel assembly, exact running kernel config/source mapping, image verification policy, p38 content/selection validity and independent recovery remain unresolved.

For another TV, reuse the staged method and command intent only. Re-establish identity, permissions, display ownership, ABI, hardware baselines and recovery separately; never transplant partitions, board assumptions, credentials or provisioning. Save observations with timestamps in Atlantic/Reykjavik, commands and output provenance, marking all partial/unavailable checks. No target testing occurred as part of this document/review update.
