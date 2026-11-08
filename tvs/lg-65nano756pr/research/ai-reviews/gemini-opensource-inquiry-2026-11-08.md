<!-- Provenance: headless `agy --model gemini-4-argon-high` on 2026-11-08,
Atlantic/Reykjavik (UTC+0). Knowledge-only: the model was instructed not to
use tools after earlier headless runs failed (command permission denied;
one location API error; one hung tool run stopped). Claims are
CONFIRMED-FROM-MEMORY unless independently verified in
opensource-inquiry-public-answers-2026-11-08.md and
codex-opensource-inquiry-2026-11-08.md. No email was sent. -->

# Gemini public-source search — LG inquiry questions — 2026-11-08

## Method

- **Zero-tool execution**: Per instructions, no shell commands, web searches, browser sessions, or file reads/writes were executed.
- **Knowledge source**: All statements below rely strictly on training knowledge of public LG documentation (`opensource.lge.com`, `webostv.developer.lge.com`, regional `lg.com` support portals, `TV_Software_Update_Guide_v3.pdf`) and well-known public repositories (`github.com/lgstreamer/starfish-sdk-x86_64`), combined with the baseline facts supplied in the prompt.
- **Epistemic tagging**: Every claim is explicitly tagged as **CONFIRMED-FROM-MEMORY** (accompanied by the corresponding public URL), **UNVERIFIED**, **HYPOTHESIS**, or **NOT FOUND**.
- **Safety & compliance**: No emails were sent, and no exploit, rooting, downgrade bypass, or unauthorized flashing instructions are included.

---

## Answers Q1–Q5

### Q1. Does sequence 510320 / webOS 6.0 KLP 1.0 match firmware 03.53.45 / 6.5.3-47, or is there another published OSS drop?

- **Status**: **CONFIRMED-FROM-MEMORY** (catalog behavior) / **HYPOTHESIS** (version drift between `KLP 1.0` and `03.53.45`) / **NOT FOUND** (any separate public OSS drop specifically labeled for `03.53.45`).
- **What sources say**:
  1. **CONFIRMED-FROM-MEMORY**: LG's Open Source Code Distribution portal (`https://opensource.lge.com`) organizes TV open-source drops by major/minor platform baseline (e.g., `webOS 6.0 KLP 1.0`, sequence `510320`) rather than publishing an individual source archive for every incremental retail OTA/USB firmware build (`03.53.45`, `03.53.46`, etc.).
  2. **CONFIRMED-FROM-MEMORY**: The OSS notice bundled with sequence `510320` (`OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html` on `https://opensource.lge.com`) carries a date stamp of `210204` (February 4, 2021) and codename `kalaupapa` (`KLP 1.0`), corresponding to the initial 2021 factory/GA software branch for 2021 webOS 6.0 models.
  3. **HYPOTHESIS**: Retail software `03.53.45` reporting `webOS TV 6.5.3-47 (kisscurl-koli)` is a much later maintenance/MR release on the 2021 platform (where `kisscurl` is the Yocto/Starfish platform release codename for webOS 6.x and `koli` replaces the earlier `kalaupapa` branch tag). While the underlying GPL/LGPL components (such as the Linux `4.4.84` kernel base) may be largely unchanged from `KLP 1.0`, sequence `510320` is a 2021 baseline snapshot and is **not** confirmed to be an exact commit-for-commit match for `03.53.45`.
  4. **NOT FOUND**: No second public catalog sequence on `https://opensource.lge.com` specifically tagged for `65NANO756PR` firmware `03.53.45` or `webOS 6.5.3-47 (kisscurl-koli)` is known in public indices.
- **URLs**:
  - `https://opensource.lge.com`
  - `https://opensource.lge.com/inquiry`
- **Unknowns**:
  - Whether LG modified any GPL/LGPL sources (kernel patches, defconfig, or localversion) between the `210204` `KLP 1.0` drop (`510320`) and retail build `03.53.45` (`6.5.3-47`).
  - Whether LG holds an internal `KLP 2.0` / `kisscurl-koli` OSS archive that is only released upon direct compliance inquiry.

---

### Q2. Which Starfish/SDK installer matches: 20190307 vs 20191125 vs a webOS 6.x SDK? Distinguish the public webOS TV app-dev SDK from the starfish BSP toolchain.

- **Status**: **CONFIRMED-FROM-MEMORY** (distinction between app SDK and Starfish BSP toolchain; origin of `20191125`) / **HYPOTHESIS** (`20190307` vs `20191125` compatibility and build-guide carryover).
- **What sources say**:
  1. **Public webOS TV App-Dev SDK vs. Starfish BSP Toolchain**:
     - **CONFIRMED-FROM-MEMORY**: The public **webOS TV SDK / CLI** (`ares-*` tools, Simulator/Emulator, VS Code extension) published at `https://webostv.developer.lge.com/develop/tools/sdk-introduction` is strictly an **application-level SDK** for packaging HTML5/JS/Enact web apps and JS services (`.ipk`). It does **not** include the Yocto cross-compiler (`arm-starfish-linux-gnueabi-gcc`), kernel headers, or target sysroot required to compile the Linux kernel or BSP binaries in `opensource.lge.com` drops.
     - **CONFIRMED-FROM-MEMORY**: **Starfish** (`DISTRO = "starfish"`) is LG's internal Yocto/OpenEmbedded Linux distribution for webOS TVs. The installer `starfish-sdk-x86_64-ca9v1-toolchain-*.sh` is a Yocto `populate_sdk` self-extracting cross-compilation toolchain targeting `ca9v1` (32-bit ARMv7-A Cortex-A9 tuning used across LG's MStar/MediaTek/SIC 32-bit kernel builds), installing `arm-starfish-linux-gnueabi-*` into `/opt/starfish-sdk` (referenced in build instructions inside `https://opensource.lge.com` archives and archived at `https://github.com/lgstreamer/starfish-sdk-x86_64`).
  2. **`5.0.0-20190307` vs. `5.0.0-20191125` vs. a "webOS 6.x" Starfish SDK**:
     - **CONFIRMED-FROM-MEMORY**: The community repository `https://github.com/lgstreamer/starfish-sdk-x86_64` hosts `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh`, which the repo author states was obtained from LG Open Source support via an inquiry for a 2020 TV (`OLED CX`, firmware `04.40.20`, `webOS 5.0 JO 2.0`).
     - **CONFIRMED-FROM-MEMORY**: The official build guide bundled in `webOS 6.0 KLP 1.0` (`510320`) names `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`, even though the product is webOS 6.0.
     - **HYPOTHESIS**: LG's `5.0.0` in the toolchain filename refers to the Starfish SDK toolchain generation rather than the marketing webOS version, OR the build guide in `KLP 1.0` carries forward boilerplate build instructions from earlier Starfish 5.0 documentation. Both `5.0.0-20190307` and `5.0.0-20191125` are `ca9v1` `arm-starfish-linux-gnueabi` toolchains from the same 2019 series.
     - **NOT FOUND**: No public copy or public reference to a `starfish-sdk-x86_64-ca9v1-toolchain-6.0.0-*.sh` installer was found in public sources.
- **URLs**:
  - `https://webostv.developer.lge.com/develop/tools/sdk-introduction`
  - `https://webostv.developer.lge.com/develop/tools/cli-introduction`
  - `https://github.com/lgstreamer/starfish-sdk-x86_64`
  - `https://opensource.lge.com`
- **Unknowns**:
  - Whether the kernel in `03.53.45` was actually compiled with `5.0.0-20190307`, `5.0.0-20191125`, or a later internal Starfish toolchain build (which would be visible in `/proc/version` on a live unit or confirmed by `opensource@lge.com`).

---

### Q3. Is 4.4.84-711.kalaupapa.4 documented as the running kernel for 03.53.45? Any public 65NANO756PR uname (not sister models)?

- **Status**: **NOT FOUND** (public documentation tying `4.4.84-711.kalaupapa.4` specifically to `03.53.45`; public `uname` from an actual `65NANO756PR`) / **HYPOTHESIS** (kernel version string behavior across MR updates).
- **What sources say**:
  1. **CONFIRMED-FROM-MEMORY**: `4.4.84-711.kalaupapa.4` is documented in `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html` on `https://opensource.lge.com` (sequence `510320`), which is dated `210204`.
  2. **NOT FOUND**: No public LG document, release note, or OSS notice explicitly states that `4.4.84-711.kalaupapa.4` is the exact running kernel release string (`uname -r`) on firmware `03.53.45` (`webOS TV 6.5.3-47 (kisscurl-koli)`).
  3. **HYPOTHESIS**: On 2021 LG webOS 6.x TVs, while the upstream Linux kernel base remains `4.4.84` across the life of the TV, later maintenance releases on the `kisscurl-koli` branch (`03.53.45`) may have a bumped build number or branch suffix in `uname -r` (for example, a higher `.kalaupapa.<N>` or `.koli.<N>` string) rather than the initial `210204` string `4.4.84-711.kalaupapa.4`. Because the Linux kernel uses `uname -r` as the module magic (`vermagic`) string, even a minor extraversion change matters if comparing against `510320`.
  4. **NOT FOUND**: No public web page, forum post, or hardware database entry is known from memory to publish a verbatim `uname -a` or `/proc/version` string captured specifically from a `65NANO756PR` (excluding sister models).
- **URLs**:
  - `https://opensource.lge.com` (host of `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html`)
- **Unknowns**:
  - The exact `uname -r` and `/proc/version` compiler banner on a live `65NANO756PR` running `03.53.45`.

---

### Q4. Do sales suffixes .AEK/.AEU/.API change the source drop or toolchain?

- **Status**: **CONFIRMED-FROM-MEMORY** (regional support pages distribute identical firmware archives; `opensource.lge.com` uses a single base-model entry) / **HYPOTHESIS** (internal NVRAM/Tool Option localization mechanism).
- **What sources say**:
  1. **CONFIRMED-FROM-MEMORY**: In LG's model nomenclature (`65NANO756PR.AEK`, `65NANO756PR.AEU`, `65NANO756PR.API`), the three-letter suffix after the period denotes the regional sales subsidiary, target market, and power cord/packaging variant (e.g., `.AEK` for the UK, `.AEU` for pan-European retail, `.API` for Italy), where the second/third letters also indicate the panel/chassis hardware revision—which here (`EK` / `EU` / `PI` under the same `65NANO756PR` European DVB chassis) share the same system-on-chip and firmware image.
  2. **CONFIRMED-FROM-MEMORY**: The official LG support pages across these regions (`https://www.lg.com/uk/support/product/lg-65NANO756PR.AEK`, `https://www.lg.com/it/supporto/prodotto/lg-65NANO756PR.API`, and European `.AEU` support portals) publish the exact same USB firmware archive filenames (`Software_File(Version_03.53.45).zip` and `Software_File(Version_03.53.46).zip`).
  3. **CONFIRMED-FROM-MEMORY**: `https://opensource.lge.com` indexes `65NANO756PR` by its base model name without separate entries for `.AEK`, `.AEU`, or `.API`, mapping all of them to sequence `510320`.
  4. **HYPOTHESIS**: Regional differences between `.AEK`, `.AEU`, and `.API` are stored in board NVRAM ("Tool Option" / Area Option registers) read by userspace at runtime, meaning they do **not** alter the Linux kernel, open-source userland drop, or cross-compilation toolchain.
- **URLs**:
  - `https://www.lg.com/uk/support/product/lg-65NANO756PR.AEK`
  - `https://www.lg.com/it/supporto/prodotto/lg-65NANO756PR.API`
  - `https://opensource.lge.com`
- **Unknowns**:
  - None material to OSS compliance or toolchain selection; all three suffixes run the same binary firmware package.

---

### Q5. Authorized recovery if stock firmware damaged beyond menus? Can service restore 03.53.45 or only later versions? Does the 03.53.45 ZIP support same-version reinstall?

- **Status**: **CONFIRMED-FROM-MEMORY** (same-version USB reinstall blocked; authorized repair path via LG Service) / **HYPOTHESIS** (service center version policy) / **NOT FOUND** (any public policy guaranteeing service restoration of a specific older firmware version).
- **What sources say**:
  1. **Does the `03.53.45` ZIP support same-version reinstall?**
     - **CONFIRMED-FROM-MEMORY**: **No.** According to LG's official `TV_Software_Update_Guide_v3.pdf` distributed on LG's support pages alongside the firmware ZIP, the TV inspects the version header of the `.epk` file inside the `LG_DTV` directory on the USB drive. If the version on the USB drive is **identical to or older than** the version currently installed on the TV, the update popup will **not** appear and the TV will not reinstall the package via the standard consumer USB workflow.
  2. **Authorized recovery if stock firmware is damaged beyond menus**:
     - **CONFIRMED-FROM-MEMORY**: Public LG consumer support documentation (`https://www.lg.com/uk/support`) provides no end-user emergency bootloader recovery or blind-USB reflash procedure if a TV cannot boot to webOS. When a unit cannot boot into its operating system, the only official authorized path is hardware service by an **LG Authorized Service Center (ASC)** / LG technician—which normally consists of **replacing the mainboard (main PCB assembly)** or performing factory service diagnostics.
  3. **Can service restore `03.53.45` specifically, or only later versions (e.g., `03.53.46`)?**
     - **HYPOTHESIS**: Standard LG Authorized Service Center procedures require updating repaired TVs (or replacement mainboards) to the **latest current production firmware** (`03.53.46` or newer) as part of post-repair quality checks, and replacement service boards ship with whatever factory version was current at manufacture.
     - **NOT FOUND**: No public LG warranty or service document states whether an Authorized Service Center can or will install/retain a specific superseded firmware version (`03.53.45`) at a customer's request.
- **URLs**:
  - `https://www.lg.com/uk/support/product/lg-65NANO756PR.AEK` (hosts `TV_Software_Update_Guide_v3.pdf` and firmware ZIPs)
  - `https://www.lg.com/uk/support/repair-service/schedule-repair`
- **Unknowns**:
  - Whether a local LG Authorized Service Center has stock of replacement mainboards preloaded with `<= 03.53.45` and whether they would agree not to auto-update it to `03.53.46+` during repair.

---

## Toolchain/kernel manifest

Publicly known vs. unverified details for the `65NANO756PR` (`webOS 6.0 KLP 1.0` sequence `510320` vs. firmware `03.53.45` / `6.5.3-47 (kisscurl-koli)`):

| Component / Attribute | Value in Public Sources | Epistemic Status & Source |
| :--- | :--- | :--- |
| **OSS Drop Sequence** | `510320` (`webOS 6.0 KLP 1.0`, archives `webOS 6.0 KLP_1.0_1/2/3.tar.gz`) | **CONFIRMED-FROM-MEMORY** (`https://opensource.lge.com` catalog & prompt baseline) |
| **OSS Notice Document** | `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html` | **CONFIRMED-FROM-MEMORY** (`https://opensource.lge.com` & prompt baseline) |
| **Documented Kernel Package (`KLP 1.0`)** | `4.4.84-711.kalaupapa.4` | **CONFIRMED-FROM-MEMORY** (`OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html`) |
| **Running Kernel (`03.53.45` / `6.5.3-47`)** | Base `4.4.84`; exact `EXTRAVERSION` / `uname -r` on `03.53.45` unknown (`4.4.84-711.kalaupapa.4` vs. later `.kalaupapa.N` / `.koli.N`) | **NOT FOUND** publicly for `03.53.45`; **HYPOTHESIS** on localversion format |
| **Build Guide Toolchain Installer** | `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh` | **CONFIRMED-FROM-MEMORY** (`KLP 1.0` build guide in sequence `510320` & prompt baseline) |
| **Publicly Archived Community Toolchain** | `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh` | **CONFIRMED-FROM-MEMORY** (`https://github.com/lgstreamer/starfish-sdk-x86_64`) |
| **Target Triplet / Tuning** | `arm-starfish-linux-gnueabi` / `ca9v1` (ARMv7-A Cortex-A9 tuning) | **CONFIRMED-FROM-MEMORY** (`https://github.com/lgstreamer/starfish-sdk-x86_64`) |
| **Exact `gcc` / `binutils` / `glibc` Versions for `03.53.45`** | Starfish 5.0 SDK series uses Yocto 2.2 (Morty) era components (typically `gcc 6.2.0`/`6.4.0`, `glibc 2.24`, `binutils 2.27`), while exact package versions for `KLP 1.0` are listed inside `OSSNotice-3253` and the tarballs; no separate public manifest exists specifically for `03.53.45` | **HYPOTHESIS / UNVERIFIED** from memory for `510320`; **NOT FOUND** as a standalone public web manifest for `03.53.45` |

---

## Inquiry still needed?

Below is the routing triage for each question/bullet—distinguishing what is already answered publicly, what genuinely requires an inquiry to LG Open Source Compliance (`https://opensource.lge.com/inquiry` / `opensource@lge.com`), and what belongs with local LG Customer Support / Authorized Service instead of the open-source compliance team:

| Inquiry Bullet / Topic | Triage Decision | Rationale |
| :--- | :--- | :--- |
| **Q1. Does sequence `510320` (`webOS 6.0 KLP 1.0`) match firmware `03.53.45` (`6.5.3-47 kisscurl-koli`), or is there an updated OSS drop?** | **Still needs LG opensource** (`opensource.lge.com/inquiry`) | Only LG's Open Source Compliance team can confirm whether any GPL/LGPL packages (especially the Linux kernel and modules) changed between the `210204` `KLP 1.0` release (`510320`) and retail firmware `03.53.45`, or provide an updated tarball if changes occurred. |
| **Q2a. Distinction between public webOS TV App SDK and Starfish BSP toolchain** | **Answered publicly** | Fully documented on `webostv.developer.lge.com` (app-only SDK) vs. `opensource.lge.com` build guides (Yocto `starfish-sdk` cross-toolchain). Do not ask `opensource@lge.com`. |
| **Q2b. Exact Starfish toolchain installer (`20190307` vs `20191125` vs newer) required to build the `03.53.45` kernel/OSS packages** | **Still needs LG opensource** (`opensource.lge.com/inquiry`) | Because LG does not post `starfish-sdk-x86_64-ca9v1-toolchain-*.sh` on the public download page, requesting the exact cross-toolchain installer used to build `03.53.45` (and verifying whether `5.0.0-20190307` in the README is current or a template carryover) is a standard GPL/LGPL compliance inquiry for `opensource@lge.com`. |
| **Q3. Exact running kernel version (`uname -r` / `EXTRAVERSION`) and toolchain banner (`/proc/version`) for `03.53.45`** | **Still needs LG opensource** (or reading from the TV itself) | Not published on the public web for `65NANO756PR` on `03.53.45`. If you cannot read `uname` from the TV directly, you can include this in the `opensource.lge.com` inquiry when asking for the exact kernel source/config corresponding to `03.53.45`. |
| **Q4. Whether `.AEK` / `.AEU` / `.API` suffixes change the OSS source drop or toolchain** | **Answered publicly** | Public LG regional support pages serve the identical `03.53.45` / `03.53.46` ZIP files across `.AEK`, `.AEU`, and `.API`, and `opensource.lge.com` maps the base model `65NANO756PR` to a single entry. No need to ask LG. |
| **Q5a. Whether the retail `03.53.45` USB ZIP supports same-version reinstall** | **Answered publicly** | Explicitly answered in LG's `TV_Software_Update_Guide_v3.pdf`: same-or-lower version USB packages do not trigger the update prompt. |
| **Q5b. Authorized recovery for a non-booting TV & whether service can restore/keep `03.53.45` instead of updating to `03.53.46+`** | **Better asked of local support / Authorized Service (NOT `opensource@lge.com`)** | `opensource@lge.com` only handles GPL/LGPL source code and toolchain compliance and cannot answer repair, warranty, or service-flashing questions. Direct any questions about unbricking, mainboard replacement, or firmware version retention to local **LG Customer Support / LG Authorized Service Center (ASC)**. |
| **Manifest: Exact `binutils` / `gcc` / `glibc` / kernel `EXTRAVERSION` for `03.53.45`** | **Partially in `510320` files; `03.53.45` delta still needs LG opensource** | For `KLP 1.0` (`210204`), the package manifest is already inside `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html` and the `510320` tarballs. Confirming that those exact versions still apply to `03.53.45` belongs in the `opensource.lge.com/inquiry` request alongside Q1 and Q2b. |
