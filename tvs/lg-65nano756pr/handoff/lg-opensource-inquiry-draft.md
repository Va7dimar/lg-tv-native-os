# LG open-source inquiry draft — NOT SENT

Recorded 2026-11-08 later, Atlantic/Reykjavik (UTC+0).

This is a draft only. It has not been emailed, submitted through the
inquiry form, or otherwise sent.

## Public-source check — 2026-11-08 later, Atlantic/Reykjavik (UTC+0)

Gemini (`agy --model gemini-4-argon-high`) searched these questions
first (knowledge-only after headless tools failed). Codex
cross-checked. Reconciled notes:
`research/ai-reviews/opensource-inquiry-public-answers-2026-11-08.md`.

**Still needed from LG Open Source (questions 1–3, and the matching
toolchain/kernel manifest for 03.53.45):** public pages identify the
model-level drop `webOS 6.0 KLP 1.0` / sequence 510320 and name
installer `…5.0.0-20190307.sh`, but they do not confirm that drop or
installer against software 03.53.45 / webOS 6.5.3-47 (kisscurl-koli).
The public `…5.0.0-20191125.sh` copy is attributed to a webOS 5 / OLED
CX inquiry, not this set. This unit’s running kernel extraversion has
not been published.

**Already answered publicly (can be shortened):** sales-suffix
listings use the base model name on both the OSS catalog and regional
firmware pages; `TV_Software_Update_Guide_v3.pdf` says a same-or-lower
USB package does not show the install prompt.

**Better asked of local LG support, not `opensource@lge.com`:**
authorized recovery if the TV cannot boot or reach the USB updater,
and whether service would restore 03.53.45 or only a later version.

Do not send this draft from the public-source check alone.
 The parent should use
`DraftExternalMessage` if the owner later approves a send.

Do not attach serial numbers, MAC addresses, pairing keys, or photos
that show those identifiers.

## Recipients and channels

Primary (open-source correspondence):

- Email: `opensource@lge.com`
  Documented in LG open-source notice pages as the address for
  requesting disclosed source on CD-ROM, for example
  https://gscs-manual.lge.com/PNZ/MFL71955451/English/content40.html
- Web form: https://opensource.lge.com/inquiry
  Use inquiry type **Open Source License and Open Source Code used in
  our product**. Suggested form fields: Category `TV/AV` / sub-category
  `TV`; Model Name `65NANO756PR`; paste the body below.

The inquiry page itself says questions about software/hardware updates,
installation, product operation, or customer service belong on local LG
support (`https://www.lg.com/common/index.jsp` → country → Support →
Contact Us), not on the FOSS site. The recovery questions below may
therefore be redirected. If so, send the recovery paragraph separately
to local support / an official repair request page such as
https://www.lg.com/uk/support/product-support/repair-request/ (or the
Iceland/EU equivalent), without mixing it into a source-code request.

Do not use the Open Source Projects GitHub issue option for this model
inquiry.

## Suggested subject

Public source correspondence for 65NANO756PR software 03.53.45 / webOS TV 6.5.3-47 (kisscurl-koli)

## Suggested body

Hello LG Open Source Program / Open Source Center,

I am requesting publicly releasable information about the open-source
packages that correspond to the software actually installed on a
consumer LG television. I already downloaded the exact-model catalog
entry that your public site lists for this model name, and I would like
to confirm whether that drop matches the installed build.

Unit (from the TV’s own information screens; sales suffix not shown there):

- Model name: 65NANO756PR
- webOS TV Version: 6.5.3-47 (kisscurl-koli)
- Software Version: 03.53.45
- Sales / product-code suffix (for example .AEK, .AEU, or .API): unknown
  from the on-screen model field. I can supply the rear rating-label
  product code privately if needed, without posting the serial number
  here.

What I have already obtained from https://opensource.lge.com/product/list?keyword=65NANO756PR :

- Catalog label: webOS 6.0 KLP 1.0
- Release sequence: 510320
- Three archives named `webOS 6.0 KLP_1.0_1.tar.gz`,
  `webOS 6.0 KLP_1.0_2.tar.gz`, and `webOS 6.0 KLP_1.0_3.tar.gz`
- Accompanying notice: `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html`
- The notice labels a kernel package as 4.4.84-711.kalaupapa.4
- The official build guides packaged with that drop name the toolchain
  installer `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`

Could you please confirm, for software 03.53.45 / webOS TV Version
6.5.3-47 (kisscurl-koli) on 65NANO756PR:

1. Whether catalog sequence 510320 / webOS 6.0 KLP 1.0 is the matching
   source release for this installed build, or whether a different
   kernel manifest, notice, or archive set should be used.
2. Which Starfish / SDK toolchain build (exact installer filename and
   date stamp, including whether 5.0.0-20190307 is still the correct
   one) corresponds to that build.
3. The corresponding kernel source identifier or extraversion that
   should match the running kernel (the notice value above is
   4.4.84-711.kalaupapa.4; I have not read the TV’s live uname).
4. Whether the sales suffix (.AEK, .AEU, .API, or another code) changes
   which source drop or toolchain applies, or whether the base model
   name is sufficient.

Separately, if the stock firmware on this television were damaged so
that it would not boot, or could not run the normal USB or network
software update: what authorized recovery options does LG document?
In particular:

- Is there any publicly documented consumer recovery or emergency-update
  procedure that works when the normal menus and USB update prompt are
  unavailable?
- Can an LG or authorised service centre restore stock firmware, and
  would that restore 03.53.45 or only a later published version?
- Does the published `Software_File(Version_03.53.45).zip` package
  support reinstalling the same version? The official
  `TV_Software_Update_Guide_v3.pdf` states that the USB install prompt
  does not appear when the USB package is the same or a lower version
  than the software already on the TV.

I understand from https://opensource.lge.com/inquiry that product
operation and customer-service questions may need to go to local LG
support. If that is the correct channel for the recovery questions,
please say so. I am asking only for information that LG can publicly
release.

Thank you.

## Parent send notes

If approved later:

- To: `opensource@lge.com`
- Connector: owner email (Gmail), not this bot’s inbox, unless the owner
  chooses otherwise
- Do not include serial, MAC, pairing data, or exploit/root discussion
- Do not promise a custom operating system or request flashing help
- Status as of this file: **not sent**
- Public-source check 2026-11-08 later: source/toolchain match still
  unanswered; recovery belongs on local support. See
  `research/ai-reviews/opensource-inquiry-public-answers-2026-11-08.md`.
  Do not send from that check alone.
