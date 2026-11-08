The new photo pins down the userspace label on your unit and nothing else. The SDK facts, the 4.4.84 kernel fact and the KLP 1.0 source drop all stay as they were. Nothing was edited or run; I read the two new evidence files and searched the repo for related terms. Your new mapping note (`evidence/webos-6.5.3-47-kisscurl-koli-mapping-2026-11-08.md`) is careful and mostly right. My additions are marked **(new)**.

## Confirmed
- **What the photo shows:** Model `65NANO756PR` with no suffix on that screen, webOS TV Version `6.5.3-47 (kisscurl-koli)`, storage `1.07/2.03GB`. That is all it shows. It does not give the dotted Software Version, sales suffix, SoC, board or running kernel.
- **Source drop:** LG's open-source catalog for this model is webOS 6.0 KLP 1.0, sequence 510320. Its kernel Makefile says Linux 4.4.84, inside a `linux-4.4.3` directory. The notice file labels the kernel packages `4.4.84-711.kalaupapa.4` (`sources/catalog/notice-inventory.md:13`).
- **Stock packages:** LG's official 03.53.45 and 03.53.46 packages list both 65NANO756PR and 65NANO753PR.
- **The two version numbers are separate:** your doc and the CleanFrame doc agree that the webOS TV Version is not the dotted firmware number.
- **(new) Official RTK hints, but no proof:** the official build guides name an `RTK2875/tv006/emmcold_defconfig` kernel config, and the notice file has an OMX "RTK" label. These are LG's own documents and point the same way as the 50UP81009LR RTD2875 report. Still, a defconfig in a source drop doesn't measure the SoC in this TV.

## Hypothesis
- **What `6.5.3-47` is:** probably a later webOS 6 userspace build on the 2021 platform. Another 65NANO756PR owner's earlier `6.5.0-24` fits a set that took normal updates while the catalog entry stayed "webOS 6.0 KLP 1.0".
- **Dotted version:** 03.53.45 is the most likely value, because several independent reports pair it with 6.5.3-47. 03.53.46 is just as possible. Treat it as unknown until the photo arrives.
- **SoC:** an RTD2875-class Realtek chip is plausible. It is supported by the official defconfig path, the RTK notice label and the UP81 note. But `kisscurl-koli` is a weak clue, since the same string appears on C1 OLEDs that use a different SoC family.
- **(new) Codename reading, to check rather than assert:**
  - "KLP" may abbreviate **kalaupapa** (K-L-P), the extraversion in the source notice. If so, the KLP 1.0 drop is a kalaupapa-branch snapshot.
  - The NANO753PR uname `4.4.84-723.kcl4tv.20` has a different build number (723 vs 711) and tag. `kcl` could be **kisscurl** just as easily as koli.
  - If both readings hold, the installed build is probably *newer than* the published source snapshot. They would share the 4.4.84 base but not be the identical build. This is a guess from letter patterns; record it as one.

## Does not change
- **SDK naming:** the official guides still name `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`. The community SDK is still 5.0.0-20191125 (glibc 2.28 headers, UAPI `linux/version.h` 4.18.0). `6.5.3` is a webOS userspace version, not an SDK date or toolchain version, so it doesn't settle 20190307 vs 20191125.
- **Kernel:** the 4.4.84 Makefile fact stands. The NANO753PR uname makes a 4.4.84 *base* on the running TV more likely, but the extraversion on *this* TV is unmeasured.
- **binutils:** its version is still unknown. Boot and recovery gates are unchanged.

## Still open, and what to ask for in the Software Update photo
Path: Support → Software Update. Photograph the screen only.
1. **The dotted "Current Software Version"**, with every digit readable (03.53.45, 03.53.46 or something else). Note any letters or suffix after the number.
2. **The "Allow Automatic Updates" toggle**, recorded as it is. Don't change it.
3. **Any status text already showing** (for example "update available" or a version offered). Ask the owner **not** to press "Check for Updates" or anything that downloads or installs.
4. **The date/time of the photo**, and a check that no serial or MAC number is in frame before anything is transcribed.
5. **What the screen won't settle**, so expectations stay set: SoC, board, the running `uname`, and whether the installed build matches the KLP 1.0 source. Even with the dotted number, the follow-up is a read-only lookup: does LG's open-source catalog have an entry tied to that exact version, beyond the model-level 510320?

Other open items: the sales suffix from the back label, panel, board and SoC, and the live kernel string. All of these stay unmeasured unless a permitted readout turns up. The 401 APIs stay as they are.
