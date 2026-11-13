# U0 desk-only boot-route screen

Recorded 2026-11-08 04:17 Atlantic/Reykjavik. Status: **DEPLOYMENT NO-GO under presently verified evidence**, not universal impossibility. E1 source learning may continue; no build/TV/hardware action authorized.

## Existing research considered first
Read native-os-feasibility.md, source-catalog/notice-inventory.md and current plan Tasks0/2/scopes. Prior OSE/DevMode/homebrew distinctions, two candidate board trails and exact-model GPL catalog remain useful but do not establish boot acceptance. This pass targeted exact-model/candidate identifiers, not another generic OSE discussion. Actual suffix/firmware/board/SoC/panel remain unknown.

## Bounded new public screen
Three searches total (two WebSearch,one X),three page reads; no firmware or source download by this worker.
1. WebSearch: LG 65NANO756PR UD15D EBU66527491 EAX69581701 custom OS boot recovery firmware manufacturer2026.
2. WebSearch: exact65NANO756PR recovery/bootloader/USB firmware LG2026.
3. Public X: (65NANO756PR OR UD15D OR EAX69581701 OR EBU66527491) AND (boot OR recovery OR customOS OR GrokBot OR @bot); zero returned posts. Search included Grok Bot/@bot as method leads. No inference from a zero-result search.

|Read source|Direct finding|Limit|
|---|---|---|
|https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/|Official exact-base-model AEK support lists model-specific stock firmware03.53.45 and03.53.46, and TV_Software_Update_Guide_v3.pdf. Page says updates include drivers/firmware only for specific models.|Already-known stock-update lead reconfirmed. No documented arbitrary-image boot acceptance, independently callable recovery loader or full storage restore procedure on this page. AEK is not confirmed unit suffix. No ZIP/PDF downloaded.|
|https://www.lg.com/it/supporto/supporto-prodotto/cs-65NANO756PR.API/|Official same-base-model API regional page likewise lists stock03.53.45/.46 and update guide.|Additional regional listing, NOT proof this unit is API or these packages restore altered boot/system regions. No arbitrary-OS boot method shown.|
|https://argos-support.co.uk/9429307-lg-65nano756pr-aek-nano-scoop|Exact-model retailer support describes ordinary power reset/connection troubleshooting for standby/no-picture, and factory reset for tuning.|Power cycling/factoryreset is not documented reinstall of damaged boot/system software. No reset or TV action performed or recommended as an independent recovery proof.|

Search-only low-relevance hits (not fetched/used as authority):generic webOS privacy/customization guide and third-party normal-update guide. No credible exact-board full-OS project or lawful custom-image acceptance lead emerged. No exploit/service-menu/private-API instructions investigated.

## Stop/go
U0 produces a dated deployment-no-go finding: **no verified legitimate custom-OS boot route for this unit/board in checked sources**. It does not say no route exists anywhere. Reconsider only on a public exact-board route with applicable revision/acceptance format/limits, independently recoverable failure coverage and compatible lawful hardware support. Identity mapping and source evidence must then be reconciled. This screen is not G3-D or G3-V proof. E1 bounded source-learning remains approved despite this finding. No architecture selected; internal OS goal unchanged.

# Follow-up public screen — stock update vs custom boot (2026-11-08 later, Atlantic/Reykjavik)

No firmware ZIP or update-guide PDF was downloaded. No USB media was prepared.
No flashing how-to is recorded here.

## Confirmed from official support pages
- UK product support for `65NANO756PR.AEK` / page title also showing `.AEKD`
  (`https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEKD/`) lists:
  - `Software_File(Version_03.53.45).zip` (listed 1176144K, 30/09/2025)
  - `Software_File(Version_03.53.46).zip` (listed 1176026K, 20/10/2026)
  - `TV_Software_Update_Guide_v3.pdf` next to both
- Page text: software upgrades include device drivers and firmware updates only
  for specific models.
- Regional applicable-model lists (for example the Greek/Norwegian support
  pages) include `65NANO756PR` among many 2021 UP/NANO models that share those
  SW files. That is a listing, not proof of this unit's sales suffix
  (still unknown; TV Information showed `65NANO756PR` with no extra suffix).
- Official LG help articles describe a *consumer stock* USB update path for
  official software packages. An official update-guide excerpt states that a
  *lower* version on USB will not work, while a *higher* version can be
  detected. Same-version behaviour is not independently quoted here.
- This is ordinary official-update language. It is **not** documentation that
  the TV will accept a custom image, unlock a bootloader, or boot a
  replacement OS.

## Rumor / unofficial (not used as authority)
- Third-party service-menu / InStart / factory-menu writeups. No official
  consumer document fetched in this pass describes those menus as an
  independent custom-image recovery path for this model. Entry methods are
  not recorded here.
- Community firmware-downgrade writeups exist. They are unofficial and are
  not documented or recommended here.

## Stop/go
Unchanged: **no verified legitimate custom-OS boot route** for this unit in
checked sources. Official stock USB updating does not fill that gap.

# Follow-up — official USB guide wording (2026-11-08 later, Atlantic/Reykjavik)

`TV_Software_Update_Guide_v3.pdf` English page 2, extracted from the
official download (hash in `recovery-case.md`; file not committed):
if the USB memory device holds the **same or lower** software version
than the TV, the install message does not appear. Combined with the
already-recorded support-page listings, official consumer updating is
forward-only when the stock UI can show that prompt.

It still does not document acceptance of a custom image, a bootloader
unlock, or a replacement OS. Deployment no-go is unchanged.

# Follow-up — owner-run root does not create a custom boot route (2026-11-08 ~17:50 Atlantic/Reykjavik)

Owner-run SlopBro succeeded on this unit; Homebrew Channel is present
after reboot (`root-result-2026-11-08.md`). That is stock-webOS userspace
persistence plus a community app catalog. It is **not** documented
acceptance of a custom image, a bootloader unlock, or a replacement OS.

Bounded public re-check (desk-only; no firmware download, no USB media):

1. WebSearch: `LG 65NANO756PR custom OS boot recovery bootloader unlock 2026`.
2. WebSearch: `webOS 6 NANO756 custom firmware bootloader U-Boot USB recovery official`.

| Source | Direct finding | Limit |
| --- | --- | --- |
| https://www.lg.com/uk/support/product-support/cs-55NANO756PR.AEK/ (sibling 55" NANO756PR support; same listed `Software_File` 03.53.45 / 03.53.46 + `TV_Software_Update_Guide_v3.pdf`) | Official consumer path remains stock signed updates for specific models. | Sibling listing, not this 65" unit’s suffix. No arbitrary-image boot. |
| Already-cited exact-base-model 65" pages in this file | Unchanged stock 03.53.45 / 03.53.46 USB packages. | Still not custom-OS boot. |
| https://tv.slada.sk/guides/rooting-guide | Third-party claim that the bootloader is signed and that modifications sit on top of webOS. | Unofficial; **not** adopted as this unit’s measured boot policy. Rooting-guide how-to content is not copied here. |
| Android LG custom-ROM / phone bootloader-unlock hits | Phones/watches, not this TV. | Irrelevant to 65NANO756PR webOS. |

No public exact-board route with applicable revision, acceptance format,
limits, and independently recoverable failure coverage appeared. Source
U-Boot 2012.07 / k6l labels in the GPL drop remain **source** labels, not
live boot acceptance (`kernel-bootcode-inspection.md`).

## Stop/go
Unchanged: **DEPLOYMENT NO-GO under presently verified evidence.** Root
plus Homebrew Channel does not fill U0 / G3-D. Reconsider only on a public
exact-board legitimate custom-OS boot route as already stated above. No
architecture selected; internal OS goal unchanged. No flash, no USB custom
image.
