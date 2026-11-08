# Gemini argon-high — SDK/boot notes review — 2026-11-08

Headless `agy --model gemini-4-argon-high`. Prompt forbade flashing/exploit how-tos. Hypothesis only.

Note: Gemini wrote that equal-or-lower USB versions are ignored. Official excerpt quoted in our notes only says a *lower* version will not work and a *higher* version can be detected. Same-version behaviour is not treated as confirmed.

### 1) `binutils` Conclusion & Remaining Plaintext Candidates

* **Conclusion unchanged (`binutils: UNKNOWN`):** The third filename pass confirms that no filename, path, or `-r0` debug directory in `members.jsonl` explicitly states the `binutils` version.
* **Remaining pure-plaintext candidates:** **None with high confidence** for an exact `2.xx` version string.
  * **`ldscripts/*` (308 files):** Low confidence for an exact version. Standard GNU linker scripts do not embed the `binutils` version number; at best, their header comments provide a FSF copyright year range (giving a lower-bound release year).
  * **`libiberty.h` / `plugin-api.h` (under GCC 8.2.0 plugin includes):** Low confidence. These belong to the GCC 8.2.0 package tree rather than standalone `binutils`. While `plugin-api.h` enum definitions and copyright years track upstream GNU toolchain dates, they do not prove the exact packaged `binutils` revision.
  * *(Note: The authoritative version string resides in the gettext `Project-Id-Version` metadata of `binutils.mo`/`gold.mo` and `.rodata` of the `*-ld*` binaries, which are compiled binary files rather than pure plaintext.)*

---

### 2) Framing Kernel, UAPI, and SDK Dates (Fact vs. Hypothesis)

* **Confirmed Facts:**
  * **Target Unit:** `65NANO756PR` runs webOS `6.5.3-47` (`kisscurl-koli`), SW `03.53.45` (with `03.53.46` offered), and maps to **webOS 6.0 (KLP 1.0)** and **Linux 4.4.84** in LG’s open-source catalog.
  * **Acquired SDK (`5.0.0-20191125`):** Contains **Linux 4.18.0** UAPI headers (`LINUX_VERSION_CODE 266752`), **glibc 2.28** (`2.28-r0`), and **GCC 8.2.0** (`8.2.0-r0`) in a Yocto/OpenEmbedded layout. Its provenance is a third-party repository attributing it to a webOS 5.0 / OLED CX (`04.40.20`) inquiry.
  * **Documented SDK (`5.0.0-20190307`):** Named in official LG build guides (`starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`), but not publicly located.
* **Hypotheses (Require Verification):**
  * **UAPI 4.18.0 vs. Kernel 4.4.84:** In Yocto-based SDKs (e.g., Yocto 2.6 "Thud", which pairs glibc 2.28, GCC 8.2, and 4.18 `linux-libc-headers`), the toolchain UAPI headers are decoupled from—and routinely newer than—the SoC vendor's BSP kernel (`4.4.84`). This is standard cross-toolchain practice, not a contradiction, **assuming** this SDK generation was used for this target.
  * **`20190307` vs. `20191125` & webOS 5.0 vs. 6.0:** It is a **hypothesis** that `20191125` is a minor rebuild of the `20190307` `5.0.0` toolchain, and a separate **hypothesis** that a `starfish 5.0.0` (webOS 5.0) toolchain matches the ABI/toolchain used for `65NANO756PR`’s webOS 6.0/6.5 (`kisscurl-koli`) userspace.
  * **Shared `kisscurl-koli` string:** Indicates a shared webOS platform branch with C1 OLEDs, **not** a shared SoC or kernel configuration.

---

### 3) Boot/Recovery: Confirmed vs. Rumor & Impact on Documentary No-Go

* **Confirmed (Official Documentation):**
  * LG distributes full ~1.17 GB `.zip` update packages (`03.53.45`, `03.53.46`) shared across multiple 2021 UP/NANO models including `65NANO756PR`.
  * The official consumer USB update path operates from a running stock OS and enforces a **strict upward version check** (equal or lower versions are ignored).
  * Consumer factory reset and power-cycling only clear user settings/state, not firmware partitions.
  * Open-source catalog drops provide source code (`KLP 1.0`, Linux `4.4.84`), not bootable recovery images.
* **Rumor / Unverified (Third-Party):**
  * Third-party claims regarding service menus or downgrade tricks are unofficial and unsubstantiated as an independent firmware/boot recovery path for this model.
* **Does the official USB update change the documentary recovery no-go?**
  * **No.** The documentary recovery **no-go remains unchanged**. A stock USB update requires an intact, booting webOS userspace to detect and apply a higher-version LG-signed package; it provides no evidence of bootloader-level recovery from a bricked/overwritten system partition and no path for booting custom images.

---

### 4) Recommended Next Off-TV Research Step

1. **Cross-check the already-acquired `65NANO756PR` KLP 1.0 / Linux 4.4.84 catalog metadata (off-TV, read-only):** Review the open-source notice (`README` / build notes) and kernel default configuration files in the `65NANO756PR` OSS package to:
   * Identify the exact target SoC family and architecture (ARMv7 vs. AArch64) for `65NANO756PR` from source configs rather than sibling model comparisons.
   * Check whether the KLP 1.0 OSS build notes specify `starfish-sdk-...-5.0.0-20190307.sh` or a newer `6.0.0` toolchain filename.
2. **Close out `binutils` only if bounding the year is useful:** Since no pure-plaintext file will yield the exact `2.xx` string, either leave `binutils` as `UNKNOWN (Yocto glibc-2.28/gcc-8.2 era)` or—if a future reviewed plan permits reading just the plaintext copyright header of `plugin-api.h` or one `ldscripts` file—use that solely to confirm the upstream FSF copyright year bound (e.g., 2018).
