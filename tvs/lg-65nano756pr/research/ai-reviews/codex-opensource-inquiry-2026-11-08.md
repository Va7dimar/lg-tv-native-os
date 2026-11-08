<!-- Provenance: subscribed Codex (`codex exec`, gpt-6.1-sol / high),
2026-11-08 Atlantic/Reykjavik (UTC+0). Light cross-check of the Gemini
inquiry search against verified public/repo facts. No email was sent. -->

# Codex cross-check — LG inquiry questions — 2026-11-08

Checked against the supplied facts only; no live fetch.

## 1. Corrections (wrong or overclaimed Gemini statements)

- **Starfish 5.0 = Morty / GCC 6.x / glibc 2.24 / binutils 2.27:** contradicted as a general characterization by the inventoried 20191125 SDK: GCC 8.2.0 and glibc 2.28. Its binutils version remains unknown. [Community SDK](https://github.com/lgstreamer/starfish-sdk-x86_64)
- **`ca9v1` establishes Cortex-A9 and use across MStar/MediaTek/SIC:** not established by the supplied evidence. The installer name alone does not prove this TV’s CPU or SoC.
- **Suffix letters encode panel/chassis revisions; all variants share a SoC and identical firmware bytes:** unsupported. Regional pages show matching package metadata and base-model applicability; ZIP byte identity was not checked. [UK/.AEK](https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/), [Italy/.API](https://www.lg.com/it/supporto/supporto-prodotto/cs-65NANO756PR.API/)
- **Service normally replaces the mainboard and installs 03.53.46+:** unanswered. Authorized-service recovery methods and resulting software versions are unpublished.
- **`4.4.84-711.kalaupapa.4` is the exact OSS notice string:** not independently established by the supplied facts, which explicitly identify `kernel-1.0.0-711.kalaupapa.4.tar.gz`.
- **“No public Starfish 6.0.0 installer found”:** the supplied facts do not document that search result. They establish the named 20190307 installer, not the availability or absence of every other installer.

## 2. Supported Gemini conclusions

- Catalog sequence **510320** identifies the model’s **webOS 6.0 KLP 1.0** drop, with notice identifier containing `210204`. Calling it a 2021 baseline is reasonable date-code interpretation; an exact release date or commit-level match to **03.53.45** is unproven. No second public drop was found under this model name. [LG catalog](https://opensource.lge.com/product/list?keyword=65NANO756PR)
- The supplied guides name **20190307**. The community **20191125** copy comes from a **webOS 5.0 / OLED CX** inquiry and makes no 65NANO756PR/03.53.45 compatibility claim. [Community README](https://github.com/lgstreamer/starfish-sdk-x86_64)
- Neither the supplied kernel package nor the Realtek build configuration proves this unit’s running kernel or hardware. Its live `uname` remains unread.
- The public **webOS TV SDK** is for app development; it is distinct from the Starfish BSP toolchain. [SDK release notes](https://webostv.developer.lge.com/develop/tools/sdk-release-notes)

## 3. Extra public evidence Gemini missed

- A **65NANO753PR** report pairs firmware **03.53.45**, SDK **6.5.3**, and kernel **`4.4.84-723.kcl4tv.20`**. Both models appear in official firmware applicability lists. This is useful sister-model evidence, but does not establish the 65NANO756PR kernel. [Public report](https://github.com/lasharor/cleanyourtv-WebOS/issues/18)
- The inventoried SDK’s **UAPI `linux/version.h` = 4.18.0** does not establish the TV’s running kernel.
- The supplied update-guide finding says an equal or lower USB version produces no installation prompt. Thus same-version **03.53.45** reinstall is not established. Factory reset resets settings; it does not restore firmware.
- LG directs operational/customer-service questions to local support. [OSS inquiry guidance](https://opensource.lge.com/inquiry)

## 4. Inquiry still needed? (agree/disagree per bullet)

- **Q1:** Exact wording is absent. **Agree** if it asks whether this OSS baseline precisely matches 03.53.45; the catalog identity itself is already answered.
- **Q2 — matching toolchain:** **Agree.** Neither installer’s exact suitability for this model/firmware is established.
- **Q3 — kernel extraversion:** **Agree.** The sister-model report cannot settle this unit’s kernel.
- **03.53.45 manifest:** **Agree.** An exact source/build manifest remains missing.
- **Q4:** Exact wording is absent. If it concerns regional packages, **partly agree** that public evidence answers availability and listed applicability; hardware equivalence and binary identity remain unresolved.
- **Same-version USB:** **Agree that documented behavior is answered publicly:** equal-version packages do not prompt. A supported same-version reinstall method remains unestablished.
- **App SDK versus Starfish SDK:** **Agree—answered publicly.**
- **Recovery:** **Agree—ask local LG support**, including service method and resulting firmware version. [LG support](https://www.lg.com/uk/support/product-support/repair-request/)
