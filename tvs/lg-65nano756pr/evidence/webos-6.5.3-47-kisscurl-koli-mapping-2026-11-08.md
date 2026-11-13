# Mapping `6.5.3-47 (kisscurl-koli)` — 2026-11-08 Atlantic/Reykjavik

On-screen value from this unit's TV Information photo
(2026-11-08 14:59 Atlantic/Reykjavik): **webOS TV Version `6.5.3-47 (kisscurl-koli)`**.
This is not the Support → Software Update dotted number. That photo is still
pending. No firmware ZIP was downloaded. Community rooting/homebrew threads
are cited only as version-pairing reports, not as instructions.
Owner-run root on this unit was later photo-confirmed
(`root-result-2026-11-08.md`); this mapping note still does not document
how that was done.

## Confirmed
- This TV displays webOS TV Version `6.5.3-47 (kisscurl-koli)`.
- Marketing/spec pages and the already-acquired LG open-source catalog
  label the model generation **webOS 6.0** / **webOS 6.0 KLP 1.0**
  (catalog sequence 510320, three `webOS 6.0 KLP_1.0_*.tar.gz` archives).
  A later `6.5.3-47` userspace string is compatible with that generation
  label; it does not by itself prove a different source drop.
- Official LG support listings for `65NANO756PR` (for example the UK
  `.AEK` page and other regional pages) publish stock software packages
  **03.53.45** and **03.53.46** that name `65NANO756PR` in the applicable
  model list. That is a stock-update artifact lead, not this unit's
  current dotted software version.
- The already-inspected official source kernel Makefile declares Linux
  **4.4.84**. The community SDK still self-labels **5.0.0-20191125**;
  official build guides still name **5.0.0-20190307**. Seeing `6.5.3-47`
  does not change those two documentary facts.

## Third-party version pairings (not this TV)
These are other people's reports or docs, not measurements of this set.

1. Multiple community reports pair **webOS `6.5.3-47 (kisscurl-koli)`**
   with dotted software **03.53.45** on 2021 webOS 6 TVs, including
   European C1 OLEDs (`OLED55C11LB`, `OLED77C18LA`).
   Source example: https://github.com/throwaway96/slopbro/issues/1
2. A closely related model **65NANO753PR** was reported with
   `firmwareVersion` **03.53.45**, `sdkVersion` **6.5.3**, and
   `Linux LGwebOSTV 4.4.84-723.kcl4tv.20 ... armv7l`.
   Source: https://github.com/lasharor/cleanyourtv-WebOS/issues/18
   Official 03.53.45/46 packages also list both `65NANO753PR` and
   `65NANO756PR`.
3. A third-party firmware note treats model `43NANO779PA` as platform
   **kisscurl / W21A**, and shows an example `os_info` platform string
   `kisscurl-koli` beside webOS TV Lite 6.5.0 and firmware 03.51.16.
   It also states that the webOS TV version is **not** the firmware
   number, and that similar model numbers can sit on different
   platforms (`43NANO779PA` vs `43NANO766QA`).
   Source: https://github.com/TheLord83/CleanFrame-webos/blob/main/docs/FIRMWARE.md
4. Another `65NANO756PR` owner previously reported
   `webOS TV 6.5.0-24 kisscurl-koli` (an earlier 6.5.x string on the
   same model name): https://github.com/Stremio/stremio-bugs/issues/1240
5. A third-party note about `50UP81009LR` claims webOS 6.5, Realtek
   **RTD2875**, `armv7l`. UP81 models appear on the same official
   03.53.46 applicable-model list as `65NANO756PR`. That is still not
   this unit's measured SoC.
   Source: https://github.com/ggfuchsi-oss/lg-webos-kexec

## Hypothesis
- `6.5.3-47` is an incremental webOS 6 userspace/build string on the
  2021 webOS 6.0 product generation. `kisscurl-koli` looks like LG's
  release/platform codename pair (hairstyle + qualifier), analogous to
  older `goldilocks-goobang`-style `webos_release_codename` values.
- The Software Update photo (15:02 Atlantic/Reykjavik) shows this unit
  is on **03.53.45**, with **03.53.46** offered and not installed. The
  earlier 03.53.45 pairing hypothesis is now confirmed for this TV.
- The sibling `4.4.84-723.kcl4tv.20` uname shares the **4.4.84** base
  with the catalog kernel Makefile, but a different extraversion than
  the source label `4.4.84-711.kalaupapa.4`. `kcl4tv` might relate to
  `koli`, but that etymology is unproven. This TV's running `uname`
  has not been read.
- `kisscurl-koli` is a **weak SoC discriminator**. The same webOS
  string is reported on 2021 C1 OLEDs (typically discussed as O20N /
  Alpha 9 Gen 4, not W21A) and on 2021 NanoCell/LCD models. Do not
  infer RTD2875, W21A, or Alpha 9 from the codename alone.

## What this does not change about SDK / BSP
- Official build guides still require
  `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`.
- The inventoried community SDK remains 5.0.0-**20191125** with glibc
  2.28 headers and UAPI `linux/version.h` 4.18.0. That header version
  is still not the TV kernel version.
- The matching LG open-source catalog entry for this **model name** is
  still webOS 6.0 KLP 1.0 / sequence 510320. No separate public catalog
  drop labeled `6.5.3-47` or `kisscurl-koli` was identified in this
  pass. KLP versus koli is not treated as proof they are the same
  identifier.
- Boot and recovery gates are unchanged.

## Still open
- This unit's dotted Software Version (photo 2).
- Sales suffix, board, panel, and SoC.
- Whether LG published source that matches this exact installed build
  rather than the model-level KLP 1.0 snapshot already acquired.
- Live kernel string on this TV.

## Update after Software Update photo
2026-11-08 15:02 Atlantic/Reykjavik: Software Version **03.53.45**,
Auto Update OFF, offer **03.53.46 / 1142MB** not installed. Details and
the stay-on-03.53.45 recommendation:
`evidence/firmware-03.53.45-to-03.53.46-2026-11-08.md`.
