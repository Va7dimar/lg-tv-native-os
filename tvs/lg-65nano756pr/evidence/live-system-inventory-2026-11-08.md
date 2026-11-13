# Live on-TV system inventory — LG 65NANO756PR (rooted)

Collected 2026-11-08 ~17:58 Atlantic/Reykjavik over SSH (root, key auth) from the
owner's PC AC-009 to the rooted TV. READ-ONLY commands only; no writes to any
partition. Serial number, nduid, and MAC addresses were present in the raw output
and are deliberately **excluded** from this repo.

## Confirmed hardware / platform (first-party, from the running TV)
- SoC (kernel `Hardware:` string): **Realtek RTD2875** (cmdline also labels `chip=K7LPA0`, LG's board/platform code)
- Board: `board_type=K7LP_DVB`, `device_name=k7lp`, `hardware_id=HE_DTV_W21P_AFADATAA`, `hardware_revision=BOARD_DV_1ST`
- CPU: ARMv7l (32-bit userland), 4 cores, CPU implementer 0x41 (ARM), part `0xd05` (Cortex-A55 class), NEON/VFPv4/AES/CRC32
- GPU: ARM **Mali** (`mali_kbase`, `mali_fb`); DRM at `/dev/dri/card0`; framebuffers `/dev/fb0`,`/dev/fb1`
- RAM: cmdline/device_info report 1.5 GB; MemTotal ~1.07 GB visible to Linux
- eMMC: ~7.3 GiB (`/dev/mmcblk0`, 7634944 KiB) + `mmcblk0boot0/boot1` (4 MB each) + `rpmb`
- Panel: BOE, 65", NANO75, direct LED backlight, local dimming off (from cmdline)
- WiFi: MediaTek `mt7663` (USB); DVB tuners/demods: `si2178b`, `rda5815m`, `a8303`, `demod_khal`
- tvregion=DVB, countryGrp=4

## OS / build
- `webOS TV 6.5.3` / starfish `Rockhopper release 6.5.3-47 (kisscurl-koli)`
- Kernel: **Linux 4.4.84-723.kcl4tv.20 #1 SMP PREEMPT Sat Sep 13 08:10:52 UTC 2025 armv7l**
- Built with **gcc 8.2.0** (matches the LG SDK/toolchain evidence already on file)
- Software version 03.53.45 (unchanged; Auto Update OFF, 03.53.46 not installed)

> The on-TV kernel 4.4.84 and gcc 8.2.0 line up with the LG open-source catalog drop
> and SDK findings already recorded. This is first-party confirmation, not just catalog labels.

## Boot + rootfs (from /proc/cmdline and mount)
- Boots `root=/dev/mmcblk0p27 ro rootfstype=squashfs` — root is a **read-only squashfs**
- `snapshot resume=/dev/mmcblk0p53` (CRIU snapshot/resume), `criu_enabled`
- BSP overlay: `/dev/mmcblk0p29` (squashfs) mounted at `/overlay/bsppart`, then overlayfs
  for `/etc`, `/lib`, `/mnt`, `/usr`, `/var` (lowerdir from bsppart; read-only)
- Writable ext4 user areas: `p57` (`/mnt/lg/db8`,`/var/db`), `p58` (`/var`,`/home`,`/mnt/lg/user`),
  `p59` (`/media`, appstore). Config/data live here; system code does not.
- Swap: `p52` (eswap/dm-0) and `p54` (apphib/dm-1)

## A/B (dual-bank) layout — important for recovery reasoning
Partitions form two parallel banks of the same sizes:
- Bank A: `p27` rootfs(1.4G), `p28`(15M), `p29` bsp(60M), `p30` otncabi(52M), `p31` otycabi(1M),
  `p32` fonts(100M), `p33`(1.5M), `p34` license(2M), `p35`(5M), `p36`(128K), `p37`(1M)
- Bank B: `p38` rootfs(1.4G), `p39`(15M), `p40`(60M), `p41`(52M), `p42`(1M), `p43`(100M),
  `p44`(1.5M), `p45`(2M), `p46`(5M), `p47`(128K)
Currently booted from Bank A (`p27`). Bank B (`p38`) is the alternate/standby copy.
This A/B redundancy is a genuine, first-party recovery signal: a bad write to one bank
may leave the other bootable. NOT yet proven which bootloader logic selects the bank,
and nothing here authorizes writing to either.

## Partition table note
No valid GPT (gdisk offered to *create* one — declined). Layout is vendor-defined; names
above are inferred from mountpoints + cmdline, not from on-disk GPT labels.

## Mount highlights
- `/` squashfs ro (p27); `/overlay/bsppart` squashfs ro (p29); fonts/license/otycabi/otncabi squashfs ro
- Many `com.webos.service.voice.performer` jail mounts (the Voice app SlopBro used as the entry)
- Netflix / YouTube apps are squashfs loop images under `/media/squashfs/apps` with ext4 overlays

## Safety posture
Root rootfs is read-only squashfs by design. All persistent customization the stock OS
does goes through the ext4 user/overlay partitions, not the system squashfs. Any custom-OS
work must respect: NEVER overwrite kernel/rootfs/tvservice/boot partitions without a verified
boot route AND independent recovery, per the TV's own brick warning.

## Excluded secrets (kept out of git)
serial_number, nduid, wifi_addr (MAC), wired_addr/ethaddr (MAC). Held only in volatile
session output, not committed.

## Boot/recovery read-only pass (2026-11-08 ~18:00 Atlantic/Reykjavik)
- Booted bank confirmed: `root=/dev/mmcblk0p27` (Bank A).
- No `/etc` file references bank selection (`mmcblk0p38`, `active_bank`, `bootbank`, `otacfg`):
  bank choice is not made by userspace config; it most likely lives in the bootloader/boot
  partitions (unverified).
- No `fw_printenv`/`fw_setenv` and no `/etc/fw_env.config`: no standard U-Boot env access from Linux.
- `/mnt/otycabi` and `/mnt/otncabi` are small read-only overlay trees (`tmp`,`usr`,`var`), dated
  2025-09-13 (same as the build) — look like OTA/"cabinet" payload overlays, not a bootloader.
- `/var/run/nyx/os_info.json`: image `starfish-global-secured`, `encryption_key_type: prodkey`,
  `webos_name: webOS TV Lite`, build 20250913080627, manufacturing version 03.53.45.
  - **`secured` + `prodkey` is strong evidence of a signed/secure-boot production image.**
    A modified kernel or rootfs would likely be rejected by the bootloader. This is the main
    obstacle for a native-OS replacement and is NOT yet characterized.
- dmesg ring buffer had already rotated past early boot (only Realtek audio/log lines); bootloader
  messages were not retrievable this way.

## What this means for the custom-OS goal
1. Flashing a custom kernel/rootfs is **not** a viable next step: signed image (`secured`/`prodkey`)
   plus no known bank-select mechanism plus no independent recovery = brick risk.
2. Viable without touching system partitions: run custom userspace from writable storage
   (`/media/developer`, `/home`, `p58`/`p59`) as root — e.g. a custom full-screen launcher/UI,
   or a chroot of another Linux userland drawing via the Mali DRM/framebuffer — started at boot
   through the Homebrew Channel startup hook. This gives a "custom OS experience" on top of the
   stock signed kernel.
3. Open questions: how the bootloader verifies images and selects A/B; whether `/dev/dri/card0`
   is usable while the stock compositor runs; whether the stock UI can be stopped/replaced
   cleanly and restored on reboot.
