# Claude Opus 5.5 high — SDK/boot notes review — 2026-11-08

Read-only review of supplied notes. Prompt forbade flashing/exploit how-tos.

# Review: 65NANO756PR / 03.53.45 off-TV notes

## 1) Binutils after the third filename pass

**The conclusion stays binutils UNKNOWN.** Everything in this pass is either something missing (no bfdver.h, no versioned sonames, no .pc file, no man pages, no debug source) or a count and size that can't pin a version (22 binutils.mo locales, 10 gold.mo locales, ld/ld.gold byte sizes). The debug prefixes name glibc and libgcc packages, not binutils. None of this identifies a version.

**One plaintext candidate is still worth a reviewed plan: the gettext header in `binutils.mo` / `gold.mo`.** The first catalog entry usually holds `Project-Id-Version: binutils 2.xx` as readable text.
- Caveat: that field records the version the *translation* was made for, which can be older than the binutils that was built. Record the result as "translation catalog for ≥2.xx", not as the toolchain version.
- Read two or three locales for each catalog and keep the highest value.
- Lower priority: a filename-only check for `*manifest*`, `opkg/status` or `dpkg/status` in the target sysroot. If none exist, stop there.

## 2) How to frame the four version facts

| Item | Status |
|---|---|
| UAPI `LINUX_VERSION_CODE` 266752 = 4.18.0 | **Fact** about the SDK sysroot headers. It says nothing about the TV's running kernel. |
| Kernel 4.4.84 in the official 65NANO756PR catalog source | **Fact** about LG's published source package. The running kernel has not been observed on this unit. |
| Gap between 4.18 headers and the 4.4 kernel | **Normal.** Toolchain headers are often newer than the target kernel, so this is not a contradiction. |
| Official guide names `…ca9v1-toolchain-5.0.0-20190307.sh` | **Fact** (documentary). No public copy has been found. |
| Acquired copy is 20191125 | **Fact.** That it came from LG via an inquiry, for webOS 5 / CX, is the **community author's claim**. |
| 20191125 ≈ 20190307 in content | **Hypothesis**, not verified. |
| The SDK matches this unit's webOS 6.5 firmware | **Unproven.** The SDK is labelled webOS 5 and the unit runs webOS 6.5. |
| GCC 8.2 + glibc 2.28 + 4.18 headers looks like Yocto 2.6 "thud", whose stock binutils is 2.31.1 | **Hypothesis.** Check it against public Yocto release notes and log it as "consistent with". It must not fill the binutils field. |
| SoC | **Unknown.** Sibling C1 reports of the kisscurl-koli string don't settle it. |

## 3) Legitimate boot/recovery: confirmed vs rumor

**Confirmed (official documents):**
- LG publishes official software ZIPs for this model: 03.53.45 and 03.53.46.
- There is a consumer USB update path for official packages.
- The guide says a lower-version file won't work and a higher one can be detected.
- Factory reset and power cycling only restore settings.

**Unofficial or rumor:**
- Service, InStart or factory menus as a recovery path
- Downgrade writeups
- Booting a custom image

**Does the official USB update change the no-go? No.** It describes a stock, same-or-newer update that depends on the TV's own updater still working. No official document says it accepts non-LG images, rolls back, or recovers from damaged bootloader or system partitions. The "lower version won't work" line actually supports the no-go, because it documents that there is no official rollback.

Two side notes:
- On paper, moving to 03.53.46 looks one-way. If your research depends on the 03.53.45 state, keeping Auto Update OFF matters.
- The TV offered 1142 MB, but the support page lists 1,176,026 KiB (about 1148 MiB). The gap probably comes from units or from ZIP vs payload. Don't use either size to prove which file is which.

## 4) Recommended next step

Write a **reviewed selected-text plan** to read only the gettext header entry of 2–3 `binutils.mo` files and 1–2 `gold.mo` files from the archive you already have. That means no new downloads and nothing executed, with paths and byte limits fixed in advance. Then log the result as a bounded fact ("translation catalog ≥ X") next to the Yocto-thud hypothesis.

Secondary, also off-TV: look in the official catalog kernel source you already have for SoC or board names in defconfig and Kconfig filenames, to narrow down which SoC this unit uses.
