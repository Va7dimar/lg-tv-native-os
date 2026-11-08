# Codex — SDK/boot notes review — 2026-11-08

Subscribed Codex (`gpt-6.1-sol` / high). Prompt forbade flashing/exploit how-tos. Hypothesis only.

1. **Binutils remains UNKNOWN.** This pass strengthens the conclusion that the filename index offers no obvious release identifier. Binary sizes, locale counts, linker scripts, and GCC/glibc package labels cannot establish its version. Neither `libiberty.h` nor GCC’s bundled `plugin-api.h` is a high-confidence binutils-release candidate. A package manifest or explicit binutils build/version record would merit future selected-text review **if identified**; none is established here.

2. **Keep each fact attached to its artifact.**
   - **4.18.0:** UAPI header version in the acquired community SDK; not evidence of the TV’s running kernel. UAPI headers describe userspace interfaces, and newer headers do not guarantee compatibility with an older kernel. [Linux documentation](https://www.kernel.org/doc/html/latest/kbuild/headers_install.html)
   - **4.4.84:** version in the inspected official model-associated kernel source package; not independently confirmed as the kernel running under 03.53.45.
   - **20190307:** installer filename named by LG’s guides.
   - **20191125:** acquired community artifact’s date label, with provenance attributed to its publisher.

   Equivalence between those SDK builds, applicability to this unit, and explanations involving shared BSPs or backports remain **hypotheses**. Neither the header version nor `kisscurl-koli` identifies this unit’s SoC.

3. **Official stock updating is documented; independent recovery is unproven.** Your supplied official evidence supports model-listed stock software distribution and consumer USB updating, including the stated version restriction. It does not establish custom-image acceptance or restoration after bootloader/system partitions are overwritten. Factory reset is settings recovery. Third-party service-menu and downgrade accounts remain unofficial and do not establish an independent recovery path for this model.

   **The documentary recovery no-go therefore stands:** a recoverable custom-OS experiment is unsupported by the available documentation. That is an evidence limit, not proof that recovery is impossible.

4. **Next step:** prepare a model/software-specific LG support or open-source inquiry requesting the matching toolchain manifest—including binutils version—and written clarification of authorized recovery scope after boot/system corruption. The request should explicitly distinguish recovery from ordinary USB updating. This needs no rooting, firmware download, or TV software change.
