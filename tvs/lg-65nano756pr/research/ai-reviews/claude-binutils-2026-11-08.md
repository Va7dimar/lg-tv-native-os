## Confirmed

**Binutils (Q1)**
- No binutils version is established. None of the ten plaintext files contains one, and the filename search only shows that binutils is present. It does not give a version.
- The symlinks only confirm the target triple `arm-starfish-linux-gnueabi` and where the tools live. They carry no version.
- The `binutils.mo` catalogs only show binutils was built with translations (NLS). Even if you read them, the `Project-Id-Version` header records the translation's version, which can lag behind the build. They are also binary, so the selector correctly rejects them.
- `gnu-versions.h` holds glibc interface version numbers (obstack, getopt, glob and similar). It has nothing to do with binutils.
- The copy of `plugin-api.h` under the gcc plugin includes comes from GCC 8.2's own source tree, not from the installed binutils. Which enum tags it has can only bound the GCC source snapshot. It isn't binutils evidence.
- The CMake FindBinUtils modules are generic and say nothing about this SDK.
- **Conclusion:** filename evidence alone cannot give a binutils version with what has been searched so far. The one exception is the shared-library names below, which nobody has searched for yet.

**Headers vs kernel (Q3)**
- The 4.18.0 in `linux/version.h` comes from the UAPI headers that glibc 2.28 was built against. It describes the build environment, not the kernel the code will run on.
- The kernel-to-userspace interface is backward compatible: older interfaces keep working on newer kernels. The reverse case, headers newer than the running kernel, is normal practice. Code built this way works on 4.4.x as long as it doesn't depend on syscalls, ioctls, flags or struct fields added after 4.4. Those fail at runtime, typically with `ENOSYS` or `EINVAL`.
- Any `#if LINUX_VERSION_CODE >= ...` check in userspace will assume 4.18 features at compile time. Portable code should detect features at runtime instead.
- Building a kernel doesn't use the SDK's UAPI headers at all, because the kernel uses its own in-tree headers. For a kernel build, the SDK only contributes GCC 8.2 and its binutils.
- 4.4.84 is the version in the source Makefile, and the directory name `linux-4.4.3` is misleading. As you noted, this is not a uname taken from the TV.

## Hypothesis
- **Yocto release guess:** GCC 8.2, glibc 2.28 and linux-libc-headers 4.18 together match upstream Yocto 2.6 "thud", which shipped binutils 2.31.1. On that basis, binutils 2.31.x is a reasonable guess but not a finding. LG could have pinned or patched a different version.
- **20190307 vs 20191125:** both carry the 5.0.0 label, which suggests the same layer generation and the same component versions. Nothing inspected so far shows this.
- **GCC 8.2 with Linux 4.4.84:** 4.4.84 came out in Aug 2017, before GCC 8 was released in May 2018. Expect new warnings and possibly build failures under `-Werror`. Whether this exact pairing works is unverified, and I'm not claiming any specific breakage.

## Recommended next bounded step (Q2)
Run these in order. The first one reads no content at all.

1. **Filename-only search of `members.jsonl`:**
   - `libbfd-*.so` and `libopcodes-*.so`. When binutils is built with shared libraries, it names them with the release, e.g. `libbfd-2.31.1.so`. Yocto's nativesdk binutils usually builds them this way. A hit would give the version from metadata alone.
   - `*.manifest`, `*/opkg/status`, `*/dpkg/status`, `*/opkg/info/*binutils*.control`. These are package databases that list versions as plain text.
   - `man1/*-as.1` and `man1/*-ld.1`, and only if uncompressed. The man page header line has the form `.TH ... "binutils-X.Y"`.
2. **Only if step 1 finds something:** read one small plaintext file, size-checked against the 32 KiB limit. Candidates are `libbfd.la` (its `dlname=` line holds the versioned name), a `*binutils*.control` file, or the first lines of a man page. Reject an opkg/dpkg status file if it is over the limit. Reject RPM databases outright, since they are binary.
3. **If step 1 finds nothing:** no plaintext route looks promising. Record binutils as UNKNOWN with the 2.31.x hypothesis attached. Don't widen the selector to `.mo` files or ELF binaries just for this.

## Still open (Q4 and related)
- **Component versions in the official 20190307 SDK:** GCC, glibc, UAPI headers, binutils and LG patch level. There is no inventory or hash of that installer, so it can't be compared yet.
- **Low-cost doc-to-doc check:** compare what the official build guide states with the `environment-setup` you have already read. The things to compare are the `CROSS_COMPILE` prefix, the `ca9v1` tune versus the CPU/FPU flags in `environment-setup`, and the expected environment-setup filename. This confirms the two SDKs have the same shape, not the same versions.
- **glibc on the TV:** for userspace, this matters more than the kernel headers. Binaries built against glibc 2.28 need a glibc of 2.28 or later on the device, and the TV's version isn't established.
- **glibc's minimum kernel version:** this is the `--enable-kernel` / `OLDEST_KERNEL` setting, which Yocto defaults to 3.2.0. If LG set it above 4.4, binaries would refuse to start on the TV. The value is stored in the ELF ABI-tag note inside `libc`/`ld.so`. Reading it is static parsing, not execution, but it would mean relaxing the plaintext-only policy. That's your call.
- **The TV's running kernel version and LG's patch set:** only the source base (4.4.84) is known.
- **Whether LG's guide prescribes this SDK for kernel builds** or a separate toolchain.
