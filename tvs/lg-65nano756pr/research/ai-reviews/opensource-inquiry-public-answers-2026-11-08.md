# Public answers vs LG inquiry — 2026-11-08

Recorded 2026-11-08 later, Atlantic/Reykjavik (UTC+0). Desk research
only. No email, form, or firmware ZIP was sent or downloaded in this
pass. Auto Update remains OFF; do not install 03.53.46 from this note.

Gemini (`agy --model gemini-4-argon-high`) produced a knowledge-only
search after headless tool use failed (see
`gemini-opensource-inquiry-2026-11-08.md`). Codex then cross-checked
that write-up against independently fetched or already-recorded public
facts (`codex-opensource-inquiry-2026-11-08.md`). This file is the
reconciled verdict: confirmed public sources vs guesses vs still
unanswered.

## Verdict

The draft inquiry in `handoff/lg-opensource-inquiry-draft.md` is
**still warranted for source/toolchain matching**, and it is **still
not sent**. Public pages do not say that catalog sequence 510320 is
an exact match for software 03.53.45 / webOS 6.5.3-47 (kisscurl-koli),
do not choose between Starfish `5.0.0-20190307` and `5.0.0-20191125`
for this build, and do not publish this unit’s running kernel
extraversion or a per-build toolchain manifest.

Recovery questions should stay out of an `opensource@lge.com` request
and go to local LG support if they are asked at all. A few other
draft bullets are already answered publicly and can be shortened.

## Answers found (confirmed public sources)

1. **This model name has one public OSS catalog entry.**
   https://opensource.lge.com/product/list?keyword=65NANO756PR lists
   **webOS 6.0 KLP 1.0**, sequence **510320**, archives
   `webOS 6.0 KLP_1.0_{1,2,3}.tar.gz`, and notice
   `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html`. No second public
   drop labeled for 03.53.45 or `kisscurl-koli` was found. That is a
   model-level catalog fact, not proof the drop matches the installed
   firmware commit-for-commit. The `210204` stamp in the notice
   filename is consistent with a 2021 baseline snapshot.

2. **Guides in that drop name toolchain `5.0.0-20190307`.**
   Official packaged build guides name
   `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh` and the
   kernel component `kernel-1.0.0-711.kalaupapa.4.tar.gz`. Project
   records also cite the notice string `4.4.84-711.kalaupapa.4`. The
   inspected kernel Makefile declares Linux **4.4.84**. None of that
   is a live `uname` from this TV.

3. **`5.0.0-20191125` is a community copy attributed to a different
   product.**
   https://github.com/lgstreamer/starfish-sdk-x86_64 (README fetched
   2026-11-08) says that installer came from an LG inquiry for
   **webOS 5.0 JO 2.0** / `OLED65CX5LB` and “should be the exact same
   toolchain” used for OLED CX firmware **04.40.20**. It does **not**
   claim to match 65NANO756PR or 03.53.45.

4. **Public “webOS TV SDK 6.x” is the app-development SDK, not
   Starfish.**
   https://webostv.developer.lge.com/develop/tools/sdk-release-notes
   describes tools to create, debug, package, and test webOS TV apps.
   That is separate from the Yocto `starfish-sdk-…ca9v1-toolchain-*.sh`
   named in the OSS build guides.

5. **Published stock firmware lists use the base model name.**
   Official regional pages for `.AEK`, `.AEU`, and `.API` list
   `Software_File(Version_03.53.45).zip` and
   `Software_File(Version_03.53.46).zip` with the same listed sizes
   (1,176,144K and 1,176,026K) and dates, and applicable-model lists
   name `65NANO756PR` without a suffix. Example pages:
   https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/ ,
   https://www.lg.com/it/supporto/supporto-prodotto/cs-65NANO756PR.API/ ,
   https://www.lg.com/gr/support/product/lg-65NANO756PR.AEU .
   The OSS catalog likewise keys the search on the base model name.
   ZIP bytes were not downloaded or hashed here, so byte-identity
   across regions is not certified. This answers the *listing*
   question: public firmware and source pages do not publish separate
   drops per `.AEK`/`.AEU`/`.API`. It does not prove identical
   hardware or identical ZIP contents.

6. **Same-or-lower USB packages do not prompt.**
   Official `TV_Software_Update_Guide_v3.pdf` (English page 2; already
   extracted in `evidence/recovery-case.md` and
   `evidence/sales-suffix-firmware-mapping-2026-11-08.md`) says the
   USB install message does not appear if the package is the **same
   or lower** version than the software already on the TV. A supported
   consumer reinstall of 03.53.45 over itself is therefore not
   documented.

7. **Ordinary consumer recovery stops at menus and a working updater.**
   Factory / initial-settings reset is documented as a settings reset,
   not firmware restore
   (https://www.lg.com/us/support/help-library/lg-tv-initialization-resetting-the-product-to-the-factory-default-state--20153293558665).
   No public official consumer recovery loader or emergency USB mode
   was found for when menus or the USB update prompt are unavailable.
   https://opensource.lge.com/inquiry directs product-operation and
   customer-service questions to local LG support. A public repair
   pathway exists, for example
   https://www.lg.com/uk/support/product-support/repair-request/ .
   What an authorised centre would do (reflash vs board swap, and
   which software version) is unpublished.

8. **Sister-model kernel, not this TV.**
   A public 65NANO753PR report pairs firmware **03.53.45**, sdk
   **6.5.3**, and `uname` **`Linux LGwebOSTV 4.4.84-723.kcl4tv.20
   #1 SMP PREEMPT Sat Sep 13 08:10:52 UTC 2025 armv7l GNU/Linux`**
   (https://github.com/lasharor/cleanyourtv-WebOS/issues/18). Both
   65NANO753PR and 65NANO756PR appear on official 03.53.45/46
   applicable-model lists. This is **not** a reading from this
   65NANO756PR. It does show that a nearby model on the same dotted
   firmware can report extraversion `723.kcl4tv.20` rather than
   `711.kalaupapa.4`.

## Guesses / overclaims (do not treat as fact)

From Gemini unless noted; Codex agreed these should be downgraded.

- Starfish 5.0.0 is “typically Yocto 2.2 Morty / gcc 6.x / glibc 2.24
  / binutils 2.27”. **Wrong as a generalisation.** The inventoried
  community 20191125 SDK has GCC **8.2.0** and glibc **2.28**
  filenames and UAPI 4.18.0. Binutils remains UNKNOWN.
- `ca9v1` proves a Cortex-A9 SoC “used across MStar/MediaTek/SIC”
  builds. **Not established.** The installer tuple is not this TV’s
  measured CPU. A catalog kernel guide names a Realtek
  `rtd2875` defconfig as a *provided build candidate only*.
- `.AEK`/`.AEU`/`.API` letter pairs encode panel/chassis hardware
  revisions and all three share one SoC and one identical firmware
  binary. **Unsupported.** They are treated here as regional sales
  codes; package listings match, hardware/byte identity is unproven.
- Authorised service “normally replaces the mainboard” and would
  restore **03.53.46+** rather than 03.53.45. **Unpublished.** Keep
  as unknown.
- `5.0.0-20190307` and `5.0.0-20191125` are interchangeable members
  of the same series, or the 20190307 name is leftover boilerplate.
  **Hypothesis.**
- `kisscurl` / `koli` replacing `kalaupapa` as a branch tag.
  **Hypothesis.**
- No public `starfish-sdk-…-6.0.0-*.sh` exists anywhere. **Not
  exhaustively proven** this pass; none was found in the checks
  that were run.

## Still unanswered (why the inquiry remains useful)

| Draft question | Status |
|---|---|
| Does sequence 510320 / webOS 6.0 KLP 1.0 match installed 03.53.45 / 6.5.3-47 (kisscurl-koli), or is there another kernel manifest, notice, or archive set? | **Still needs LG Open Source.** Catalog identity is public; exact match to this firmware is not. |
| Which Starfish installer (exact filename, including 20190307 vs 20191125) corresponds to that build? | **Still needs LG Open Source.** Guides name 20190307; the only public download found is a CX/webOS 5 community copy of 20191125. |
| Corresponding kernel source identifier / extraversion for the running kernel? | **Still unanswered for this unit.** Notice/package strings are for the KLP 1.0 drop; this TV’s `uname` has not been read. |
| Does the sales suffix change the source drop or toolchain? | **Mostly answered publicly** at the listing level (one catalog entry; firmware lists use the base name). Hardware equivalence remains unknown and is not an OSS-desk question. |
| Published toolchain/kernel manifest (binutils, gcc, glibc, extraversion) for *this build*? | **Still needs LG Open Source** for 03.53.45. The KLP 1.0 notice/tarballs are a baseline manifest, not confirmed as this firmware’s. |
| Authorized recovery if stock firmware is damaged beyond menus? Can service restore 03.53.45? Does the 03.53.45 ZIP support same-version reinstall? | **Same-version USB: answered publicly (no prompt).** **Unbootable recovery / which version service would write: not published; ask local LG support, not `opensource@lge.com`.** |

The inquiry draft should keep questions 1–3 and the toolchain/manifest
request, optionally shorten question 4 to “please confirm the base
model name is sufficient”, and move the recovery paragraph to a
separate local-support note if it is sent later. Status remains
**not sent**.
