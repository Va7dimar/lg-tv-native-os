# Recovery case — documentary screen only

2026-11-08 04:17 Atlantic/Reykjavik. **G3-D BLOCKED; G3-V BLOCKED. No target operations authorized.**

## What is actually obtainable/documented
Official exact-base-model LG AEK and API support pages list stock firmwareZIPs03.53.45/.46 and a softwareupdate guide (URLs in boot-route.md). This establishes a public stock-update artifact lead only. No firmware downloaded; matching installed release/fullsuffix remainsunknown. Files not inspected or certified as full recovery media.

The exactmodel Argos support page covers normal powerreset/connection/standby troubleshooting. It does not establish recovery of overwritten bootloader/kernel/system partitions. Factoryreset is not assumed to replace lost firmware.

## Failure coverage, all unknown
- Recovery entry independent of the system being replaced:NOT identified.
- Recovery when kernel/userspace/display fail:NOT demonstrated.
- Recovery from interrupted write or affected boot regions:NOT established; storage/layout unknown.
- Independent early log/diagnostic channel when stockOS/display unavailable:NOT identified in checked exactmodel documents. Existing pairedSSAP is stockOS-dependent, not independent boot diagnostics; exposedports do not prove a recovery channel.
- Primary calibration/provisioning preservation and restore/non-impact:NOT established. No credentials/keys/calibration read or copied.
- Exact-compatible development target and lawful non-destructive validation route:NOT established. No spare purchase/opening/wiring/test authorized.

## Next safe evidence dependencies
Public source inspection (if its separate pre-read checkpoint passes) may reveal build/platform/documentation leads, not boot acceptance itself. Need exactvariant mapping and documented permissible boot/recovery methods with failure/region coverage, stockrestore applicability and data preservation; then a specifically approved validation method. No UI firmware-information request, enrollment,TVcommands,inquiry,flash or hardware access approved by t58u. No sourcecatalog label substitutes for installedfirmware. Source learning can complete without recoverypass; no targettest may.

Sources and boundedsearches: evidence/boot-route.md. This is a precise evidence gap, not a claim that manufacturer service recovery universally cannot exist.

# Follow-up — official stock packages vs independent recovery (2026-11-08 later, Atlantic/Reykjavik)

G3-D remains **BLOCKED**. G3-V remains **BLOCKED**. No firmware was
downloaded and no recovery media was prepared.

## What is now more specifically documented
Official regional support pages list stock `Software_File(Version_03.53.45).zip`
and `Software_File(Version_03.53.46).zip` for model lists that include
`65NANO756PR`, with `TV_Software_Update_Guide_v3.pdf`. See `boot-route.md`.
Those artifacts are **official stock update packages**, not inspected here and
not certified as full storage-restore or bootloader-recovery images.

An official guide excerpt says a lower-version USB package will not work and a
higher version can be detected. That documents a one-way consumer update
constraint; it does **not** establish:
- recovery when the stock updater / userspace cannot run
- recovery after overwritten bootloader or system regions
- installation of a non-LG image
- rollback from `03.53.46` to `03.53.45`, or re-install of the same version

Factory reset remains settings recovery, not firmware restore. The previously
acquired LG open-source catalog drop for this model is source code (kernel
4.4.84 among other packages), not a bootable recovery image.

Third-party service-menu and downgrade claims remain unofficial. No how-to
for those methods is recorded.

## Failure coverage
Unchanged: no independent recovery entry, no demonstrated recovery when
kernel/userspace/display fail, no coverage for interrupted writes to boot
regions, no independent early diagnostic channel, and no calibration /
provisioning preservation proof.

Documentary recovery no-go for a custom-OS experiment is **unchanged**. That
is an evidence limit, not a claim that manufacturer service recovery cannot
exist anywhere.

# Follow-up — official recovery beyond stock USB (2026-11-08 later, Atlantic/Reykjavik)

Desk-only. No firmware downloaded into git. The official update guide PDF
was fetched to `/tmp` for text extraction only (2,062,230 bytes, SHA-256
`631f18abd8360e9f2328ddb9a41dc4cc4377a1f1a7f706e7c953af4f152ed2e5`) and
was not committed. Independent reviews:
`research/ai-reviews/claude-official-recovery-2026-11-08.md` (repo guide
only; web tools declined),
`research/ai-reviews/codex-official-recovery-2026-11-08.md`,
`research/ai-reviews/gemini-official-recovery-2026-11-08.md` (second run,
using pasted official excerpts after a headless shell-permission miss).

## Newly confirmed official wording

`TV_Software_Update_Guide_v3.pdf` English page 2: if the USB package is
the **same or lower** software version than the TV, the install message
does not appear. That is stronger than the earlier “lower version will
not work” excerpt. It does **not** document a consumer way to reinstall
`03.53.45` over itself.

The same guide (English page 1) says to read the model name from the
**back product ID labels** before downloading the file, then unzip it
into a USB folder named `LG_DTV`.

## Official options checked

- **Stock USB or network update**, only when the stock updater can run,
  and only for a *newer* package than the installed version. Already
  documented. Same listed `Software_File` 03.53.45 / 03.53.46 sizes and
  dates appear across `.AEK`/`.AEKD` URL, `.AEU`, and `.API` support
  pages; applicable-model lists use the base name `65NANO756PR`. See
  `sales-suffix-firmware-mapping-2026-11-08.md`.
- **Factory / initial-settings reset**, when menus still work. Official
  2021/webOS 6 path in one LG USA article is All Settings → General →
  System → Reset to Initial Settings
  (https://www.lg.com/us/support/help-library/lg-tv-initialization-resetting-the-product-to-the-factory-default-state--20153293558665).
  Another LG USA article lists Support → Reset to Initial Settings for
  webOS 6.0. Either way, this reverts settings; it is not described as
  firmware restore.
- **Authorised repair / customer service** when the consumer updater
  cannot run. Public entry example:
  https://www.lg.com/uk/support/product-support/repair-request/ .
  What service would actually do (reflash, board swap, which software
  version) is not published.
- **LG Open Source Center** publishes source archives, not recovery
  images. https://opensource.lge.com/inquiry directs product-operation
  questions to local LG support.

Codex cited two Malaysia help-library titles about a TV shutting down
during an update and a firmware update that does not complete
(https://www.lg.com/my/support/product-support/troubleshoot/help-library/cs-CT20180005-1412243925324/
and
https://www.lg.com/my/support/product-support/troubleshoot/help-library/cs-CT20180005-1412237441121/).
Those URLs exist; this pass did not recover enough article body text to
independently quote their troubleshooting steps, so those steps are not
adopted as confirmed wording.

## Still not established

- Any public official consumer recovery loader, emergency USB mode, or
  procedure that works after overwritten bootloader, kernel, or system
  partitions.
- Same-version reinstall of 03.53.45 from the published ZIP.
- Using 03.53.46 as an unbrick path (and the existing hold remains:
  stay on 03.53.45, Auto Update OFF).
- Independent recovery of this specific unit.

Documentary recovery no-go for a custom-OS experiment is **unchanged**.
That remains an evidence limit, not a claim that manufacturer service
recovery cannot exist.

# Follow-up — root/Homebrew Channel is not independent recovery (2026-11-08 ~17:50 Atlantic/Reykjavik)

G3-D remains **BLOCKED**. G3-V remains **BLOCKED**. Owner-run root and a
visible Homebrew Channel catalog (`root-result-2026-11-08.md`) do not
identify:

- recovery entry independent of the stock system being replaced
- recovery when kernel, userspace, or display fail
- recovery from interrupted writes to boot/system regions
- an independent early log channel when stock OS/display is unavailable
- preservation/restore of unique calibration/provisioning

Homebrew Channel is itself stock-OS userspace. Factory reset remains
settings recovery (and would also be destructive to the recorded
baseline). Official consumer USB updating remains forward-only stock
packages when the updater can run (`boot-route.md`). Authorised repair
is still the public referral when the consumer updater cannot run.

Storage/layout, boot policy, and partition map remain **unknown**. This
note does not invent them from source labels or from root success.

Documentary recovery no-go for a custom-OS experiment is **unchanged**.
What evidence would move these gates, and what is research-safe versus
write-gated: `../handoff/post-root-research-2026-11-08.md`.
