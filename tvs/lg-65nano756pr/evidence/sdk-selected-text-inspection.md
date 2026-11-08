# SDK selected plaintext — ten files, not installed

Recorded 2026-11-08 14:03:46.778–14:03:59.987 Atlantic/Reykjavik (UTC+0).
Exact reviewed command run once; exit 0; 13.209 s outer. Reader
`3598007632b1c13790d16cad9f6a68c23e5f4b35a4996948a3917bef2d8f8168`, launcher
`c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a`, command
`4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7`.
Reviews: prior selector SPEC FAIL
(`tooling/review/sdk-text-selector-independent-review.md`); `./` prefix
re-review SPEC PASS / QUALITY PASS
(`tooling/review/sdk-text-selector-dot-prefix-independent-review.md`).

No installer was sourced or executed. No compiler or binutils binary was
run. No TV action. Output:
`sdk-candidates/20191125/inspection-selected-text-PENDING-REVIEW/`
(historical PENDING-REVIEW name; directory was absent and reviewed before
this single run). Evidence copies:
`tvs/lg-65nano756pr/evidence/sdk-selected-text-execution-2026-11-08/`.

## Run gates

All three pins verified before parse (498625937 B). Worker and launcher
`ok=true`, mode `SELECTEDTEXT`, `selected_bytes=50478`, ten generated
mode-0600 `selected-*.txt` files whose bytes and SHA-256 match the JSONL
rows. All six SDK members were stored as `./`+canonical and were accepted.
The four target members matched exactly. All three streams reported
`tar_eof` and reader `integrity_eof`. 66880 JSONL rows (same count as the
earlier metadata-only success). Member contents were treated as inert
plaintext, never executed.

## What the ten files actually say

- **SDK self-identity** (`version-…`, 125 B): Distro `starfish`, Distro
  Version `5.0.0`, Metadata Revision
  `032f3c60ecca3ecc5a2411216bee122c714335ca`, Timestamp `20191125070704`.
  Environment `OECORE_DISTRO_VERSION=5.0.0` and
  `OECORE_SDK_VERSION=5.0.0-20191125`. This is the community candidate's
  own label, not an authenticated release and not equivalence to official
  SDK `20190307`.
- **Target triple / flags** (environment-setup, 4321 B): prefix
  `arm-starfishmllib32-linux-gnueabi-`; configure
  `--target=arm-starfishmllib32-linux-gnueabi --host=arm-starfishmllib32-linux-gnueabi --build=x86_64-linux`;
  `OECORE_TARGET_ARCH=arm`, `OECORE_TARGET_OS=linux-gnueabi`; CC flags
  `-march=armv7-a -mthumb -mfpu=neon -mfloat-abi=softfp -mcpu=cortex-a9 -mtune=cortex-a9`.
  Assumed install prefix `/opt/starfish-sdk-x86_64/5.0.0-20191125` (text
  only; nothing was installed there). The selected include-fixed README
  path uses the related but shorter triple `arm-starfish-linux-gnueabi`
  and directory `8.2.0`. PATH also lists
  `arm-starfishmllib32-linux-musl`; that is a PATH component, not a libc
  selection.
- **GCC**: compiler name `arm-starfishmllib32-linux-gnueabi-gcc`; version
  **label** `8.2.0` from the include-fixed directory component. The README
  body is the generic GCC fixincludes notice and contains no version.
  `gcc --version` was not executed.
- **Binutils**: environment names `as`, `ld`, `ar`, `nm`, `objcopy`,
  `objdump`, `ranlib`, `strip` with the same prefix. **No version string**
  appears in these ten files, including site-config. Version remains
  UNKNOWN.
- **Kernel headers**: both SDK and target `linux/version.h` (97 B, byte
  identical) define `LINUX_VERSION_CODE 266752`, which decodes with the
  file's own `KERNEL_VERSION` macro as **4.18.0**. Provider file text is
  `lib32-linux-libc-headers`. This is UAPI header text, not the TV's
  previously recorded running kernel **Linux 4.4.84**, and not a hardware
  match.
- **glibc**: both SDK and target `features.h` (15721 B, byte identical)
  define `__GLIBC__ 2` and `__GLIBC_MINOR__ 28` (and `__GNU_LIBRARY__ 6`).
  Provider file text is `lib32-glibc`. These are userspace header macros,
  not an executed libc binary and not ABI proof versus the TV. No
  `__UCLIBC__` or `__MUSL__` macros appear in `features.h`.
- **site-config** (13611 B): autoconf cache (little-endian, etc.).
  `ac_cv_linux_vers=2` is a cached uname-style major, not kernel 4.18 and
  not 4.4.84. No gcc/binutils/glibc version assignments.

## Still not established

Compatibility with official build-guide SDK 20190307; compatibility with
this TV's kernel, userspace, board, or panel; binutils version; executed
compiler identity; full LG BSP; legitimate custom boot or independent
recovery; any permission to install or run the SDK. Prior Chromium 200k,
adaptation 64 MiB, and earlier SDK UTF-8 / unsafe-link partials remain
their own histories. This successful selected-text phase does not close
those.
