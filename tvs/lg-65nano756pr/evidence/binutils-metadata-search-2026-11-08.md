# Binutils version — metadata-only filename search

2026-11-08 14:45 Atlantic/Reykjavik. Search of the already-generated
`sdk-candidates/20191125/inspection-metadata-links-PENDING-REVIEW/members.jsonl`
index only. No new SDK member contents were selected, and no installer,
compiler, assembler, or linker was executed.

## Confirmed from this search
- No indexed member name contains `bfdver` or a clearly labeled
  `BFD_VERSION_STRING` header.
- GCC 8.2.0 `libexec` entries named `as`, `ld`, `ar`, `nm`, `objcopy`,
  `objdump`, and `strip` are **symlinks** to prefixed binaries such as
  `../../../../../bin/arm-starfish-linux-gnueabi/arm-starfish-linux-gnueabi-as`
  (and the aarch64 counterparts). Those targets are not plaintext and
  must not be executed to obtain `--version`.
- Locale catalogs `.../LC_MESSAGES/binutils.mo` exist in many languages
  (about 615 B to 341964 B). They are binary gettext files, not valid
  selected plaintext under the current UTF-8 policy, and most exceed the
  earlier 32 KiB-per-member research plan.
- Small CMake helper files exist:
  - `sysroots/x86_64-starfishsdk-linux/usr/share/cmake-3.12/Modules/CMakeFindBinUtils.cmake` (3662 B)
  - `.../Compiler/GNU-FindBinUtils.cmake` (1580 B)
  and related IAR/Clang/Flang FindBinUtils modules. These are generic
  CMake modules by name; contents were not read.
- `gnu-versions.h` exists at 2342 B in both
  `sysroots/ca9v1-starfishmllib32-linux-gnueabi/usr/include/gnu-versions.h`
  and target `usr/include/gnu-versions.h`. By name this is a glibc
  interface-version header, not a binutils release file. Contents not read
  in this pass.
- `plugin-api.h` exists at 14593 B in both ARM and AArch64 GCC 8.2.0
  plugin include trees. By name this is the linker plugin API header, not
  proof of a binutils package version. Contents not read in this pass.

## Already established by the earlier ten-file plaintext run
Environment-setup names the prefixed `as`/`ld` tools and sets
`CROSS_COMPILE=arm-starfishmllib32-linux-gnueabi-` but contains no
binutils version assignment. site-config likewise has no binutils version.

## Limits
Filename evidence cannot assign a binutils version. A future plaintext
selection of CMake modules, `gnu-versions.h`, or `plugin-api.h` would
need its own reviewed exact-command if attempted; none of those names
is a high-confidence version source. Reading binaries or running
`as`/`ld`/`gcc` remains out of scope.

## Official 20190307 comparison (unchanged)
LG build guides name `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`.
The inventoried candidate is community `5.0.0-20191125`. Same major
starfish 5.0.0 label is not equivalence of compiler, headers, sysroot,
or licensing.
## Second filename pass (Claude-suggested names, still metadata-only)
2026-11-08 14:43 Atlantic/Reykjavik. Same members.jsonl, no content reads.

Searched for `libbfd-*`, `libopcodes-*`, `libbfd.so`/`libopcodes.so`,
`*.manifest`, `opkg/status`, `dpkg/status`, `opkg/info/*binutils*`,
`man1/*-as.1` / `man1/*-ld.1`, and `libbfd.la` / `libopcodes.la`.

Result: **no hits** except the already-known CMake FindBinUtils modules.
There are no versioned shared-library names such as `libbfd-2.31.1.so` in
this index. That does not prove the tools were statically linked; it only
means this inventory has no versioned libbfd/libopcodes filenames.

Claude Opus 5.5 high (signed-in subscription, 71.168s, exit 0, read-only)
independently reviewed the first search. Saved as
`tvs/lg-65nano756pr/research/ai-reviews/claude-binutils-2026-11-08.md`.
Checked against the index: its advice that gnu-versions.h / plugin-api.h /
CMake modules / .mo files are poor version sources is consistent with the
filenames; the suggested libbfd filename search was executed and was empty.

Its Yocto 2.6 "thud" / binutils 2.31.x pairing is a **hypothesis** from
the known GCC 8.2 + glibc 2.28 + linux-libc-headers 4.18 combination, not
a finding. LG could have pinned a different binutils.

On headers vs kernel, treat as analysis not execution proof: a 4.18 UAPI
header describes the SDK/glibc build environment; building userspace
against newer UAPI than a 4.4 kernel is common and fails at runtime only
if newer syscalls/fields are actually used; kernel builds use in-tree
headers, so this UAPI version is not itself a kernel-build blocker.

