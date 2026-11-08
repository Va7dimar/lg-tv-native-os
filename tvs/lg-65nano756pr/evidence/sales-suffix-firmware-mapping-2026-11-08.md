# Sales suffixes vs firmware lists — 65NANO756PR

Recorded 2026-11-08 later, Atlantic/Reykjavik (UTC+0). Desk research
only. No TV action, no firmware ZIP downloaded, no chassis opening.

This unit’s on-screen Model field is `65NANO756PR` with no extra suffix
(TV Information photo, 2026-11-08 14:59). The rear rating / ID label
has not been photographed. Sales suffix therefore remains **unknown**.

## How the suffix appears

| Surface | What this pass found | Authority |
|---|---|---|
| TV Information / on-screen Model | This unit showed `65NANO756PR` only | Owner photo, `docs/device-facts.md` |
| Rear product ID / rating label | Official USB update guide tells the owner to read the model name from “the back of the product ID labels” before downloading software | `TV_Software_Update_Guide_v3.pdf` English page 1 (fetched 2026-11-08; 2,062,230 bytes; SHA-256 `631f18abd8360e9f2328ddb9a41dc4cc4377a1f1a7f706e7c953af4f152ed2e5`; not committed) |
| LG USA “identify model” / manual-update help | Model number is on the rear label (location can vary by model); a mute-key shortcut is also described | https://www.lg.com/us/support/help-library/lg-tv-how-to-manually-update-software--20154165668198 |
| LG.com support URL and page heading | Regional sites publish `65NANO756PR` plus a dotted product code | Official support pages listed below |
| Energy / product-information sheet | Related official PIS files use a “model identifier” that can omit the dotted suffix even when a retailer filename includes it. This model’s UK PIS download is named `65NANO756PR_PIS.pdf` | Example PIS filename `50UR78006LK.AEK-product-fiche.pdf` whose model identifier is `50UR78006LK`; this-model PIS: https://www.lg.com/uk/lgecs.downloadFile.ldwf?DOC_ID=20210615134741&FILE_NAME=65NANO756PR_PIS.pdf&GSRI_DOC=GSRI&ORIGINAL_NAME_b1_a1=65NANO756PR_PIS%5B20210615113408781%5D.pdf&SPEC_DOWNLOAD=N&TC=DwnCmd |
| Official firmware “applicable model list” | Base names only (`65NANO756PR`), never `65NANO756PR.AEK` etc. | Greek support reference tabs, see below |

So: the suffix is a **sales / regional product code**, not something the
TV Information screen necessarily prints, and not something the
published SW applicable-model list uses. The place LG tells consumers
to read the model before a USB update is the **rear ID label**. An EU
energy-label or PIS “model identifier” may be the shorter base name.

## Official regional product codes seen for this base model

These are website listings, not this unit’s label.

| Code shown | Where | Notes |
|---|---|---|
| `65NANO756PR.AEK` | UK support page title | https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/ |
| URL slug `...AEKD` while the page title prints `.AEK` | Same UK product, alternate URL | https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEKD/ — fetched 2026-11-08; heading is `65NANO756PR.AEK`. The trailing `D` here looks like a UK site/catalog slug, not a separate firmware branch |
| `65NANO756PR.AEU` | Sweden; Portugal; Greece URL | https://www.lg.com/se/support/produktsupport/cs-65NANO756PR.AEU/ ; https://www.lg.com/pt/suporte/produto-suporte/cs-65NANO756PR.AEU/ ; https://www.lg.com/gr/support/product/lg-65NANO756PR.AEU |
| `65NANO756PR.API` | Italy; also a Greece URL heading | https://www.lg.com/it/supporto/supporto-prodotto/cs-65NANO756PR.API/ ; https://www.lg.com/gr/support/product/lg-65NANO756PR.API (Greek site heading followed the URL suffix while listing the same software files as the `.AEU` URL) |

Do **not** treat a support-page heading as this TV’s suffix. The Greek
site accepted both `.AEU` and `.API` URLs for the same software list.
The UK `.AEKD` URL displayed `.AEK`.

An earlier retailer PDF mentioned an `.AEK` suffix; that remains a
retailer claim, not a reading from this set. Nordic/EU support pages
more often show `.AEU`. Iceland is not independently listed in this
pass.

## How suffixes map to firmware packages

Fetched the same `Software_File` listings on UK `.AEK`/`.AEKD`, Sweden
`.AEU`, Italy `.API`, and Greece `.AEU`/`.API` pages:

| Package | Listed size | Listed date | Notes |
|---|---|---|---|
| `Software_File(Version_03.53.45).zip` | 1,176,144K | 30/09/2025 | Same size and date on the regional pages above |
| `Software_File(Version_03.53.46).zip` | 1,176,026K | 20/10/2026 | Same size and date on those pages |
| `TV_Software_Update_Guide_v3.pdf` | 2,014K | same dates as the neighbouring ZIP | Official USB/network update instructions |

Every applicable-model list checked names **`65NANO756PR` without a
suffix**, together with many other 2021 UP77/UP78/UP80/UP81 and
NANO753/756/759 sizes. No dotted suffix appears in those lists.

Compared from the Greek reference tabs (2026-11-08):

- 03.53.45 list: 114 base-model names, including `65NANO756PR`
- 03.53.46 list: 117 base-model names, including `65NANO756PR`
- Names only in 03.53.46: `55UP77106LB`, `65UP77106LB`, `75UP77109LC`
- Names only in 03.53.45: none

Conclusion from official pages: these published SW files are keyed by
**base model family**, not by `.AEK` / `.AEU` / `.API`. Identical listed
sizes and dates across those regional pages are consistent with one
shared package per version, but the ZIP bytes were not downloaded or
hashed here, so byte-identity is not certified.

Official guide wording (English page 2): if the USB package is the
**same or lower** version than the TV, the install message does not
appear. That is a consumer update constraint, not proof that every
suffixed unit is electrically identical.

Page text on the support downloads: “Software upgrades include device
drivers and firmware updates only for specific models.” The specific
models are the base-name list, not the dotted sales codes.

## Unofficial letter decoding (not used as authority)

A third-party article (https://en.tab-tv.com/lg-aeu-aek-tvs-which-means/,
2021) interprets codes such as AEU/AEK as a generation letter plus a
region (EU vs UK). It is useful background only. It does not explain
`.API` or the UK `.AEKD` URL slug, and LG has not been seen to publish
that decode on the pages checked here.

A webOS community note that firmware became “global” after 2021 is
likewise unofficial and is not treated as an LG statement.

## What this does not prove

- This unit’s own suffix, board, panel, or SoC
- That every NANO756PR suffix is hardware-identical
- That catalog source sequence 510320 is suffix-specific (the
  open-source catalog search used the base model name)
- That installing 03.53.46 is desirable (hold remains: stay on 03.53.45,
  Auto Update OFF)

## Still useful next evidence

A photo of the rear product ID / rating label, showing the printed
model or product code after `65NANO756PR`, would close the suffix field.
Do not copy the serial number into the repository.
