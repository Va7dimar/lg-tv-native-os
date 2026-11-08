# SDK UTF8 boundary fix — pending independent review

Status: implemented and synthetically verified; NOT approved for an SDK rerun.
No actual SDK/source payload was read, hashed, parsed, selected, executed, or rerun. Existing partial output was never opened or changed. No agents, downloads, installers, builds, TV actions, permission changes, or isolation workarounds were used.

## Synthetic proof and its limit

The maintained CPython 3.13.5 `tarfile` GNU_FORMAT writer generates a valid longname/longlink for `99 * "a" + U+0100 + "-suffix"`. Its following 100-byte fixed field contains 99 ASCII bytes and `0xc4`, the first byte of U+0100. Production's original `_frombuf(... errors="strict")` raises before the maintained GNU substitution can replace that field. Both name and link reproduce, independently and together, with GZ and XZ.

This is a synthetic compatibility defect and proof. The actual SDK failing field, offset, and condition remain UNKNOWN. The contract's recorded error is consistent with this hypothesis but does not establish its cause. No actual archive bytes were examined.

## TDD evidence

1. Baseline reader and unchanged launcher/existing tests copied to `before/`; pinned reader and launcher hashes asserted before production edits.
2. New synthetic test file written first. `red.log` retains the COMPLETE pre-edit output and EXIT=1: 6 test methods, 18 subtest errors, all at the truncated UTF8 boundary. This includes six GNU roundtrip cases, two exact-budget cases, and ten GNU safety cases whose later policy checks were blocked by the same early decode error. The exceptions are the production defect, not fixture construction errors. PAX/USTAR baselines, ordinary multibyte accounting, and invalid-UTF8 rejection passed already.
3. Narrow production change applied. `green.log` retains COMPLETE targeted output and EXIT=0: 6 methods, no failures/errors/skips.
4. `sdk-suite.log` retains COMPLETE required SDK-only discovery output and EXIT=0: 41 test methods, OK (skipped=10). Three isolation methods and seven closed-stdio subtests skip because nested bwrap cannot create NETLINK_ROUTE sockets (EPERM). These tests and skip logic are unchanged. Argparse rejection messages in this log are expected test output.

Commands (executed by subprocess argument lists, so glob arguments are literal):

```sh
python3 -B -m unittest discover -s tooling/tests -p 'test_sdk_utf8_boundary.py' -v
python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v
```

Each run has a companion result JSON with command and exit; the full-suite result also records elapsed seconds. No full project suite was run.

## Fix matrix / contract reconciliation

| Concern | Before | Current behavior / evidence |
| --- | --- | --- |
| Raw fixed name/link | Strict UTF8 before substitution | Existing maintained `_frombuf` hook uses byte-preserving surrogateescape; no custom header parser |
| GNU/PAX extension bodies | Maintained strict decoder | Still strict: TarFile encoding UTF8 and errors=strict unchanged |
| Final resolved name/link | Strict budget encoding | Strict UTF8 remains mandatory before canonicalization, duplicate/link checks, or emit |
| Owners and other output metadata | Raw owners and PAX strings strict | Raw owners remain strict; final owners explicitly strict without double charging; PAX keys/values strict |
| Unresolved malformed bytes | Fail closed | Short raw name/link, long malformed extension name/link, raw owner/group remain rejected |
| Original raw byte budget | Could throw before charging | Only raw name/link charge with surrogateescape: original bytes recovered exactly, no replace/drop/surrogatepass |
| Valid multibyte charges | UTF8 bytes | Unchanged; U+0100 name plus é owner and ö group charges exactly 8 bytes (name charged raw+resolved) |
| Hidden headers | Each observed header is a member | Unchanged; combined GNU name+link has 3 headers, 1 emitted member; cap=2 rejects |
| Exact GNU metadata | Never reached with split field | 1466 bytes: 2*(13+512) extension headers/bodies + 200 raw field bytes + 2*108 resolved bytes; cap=1465 rejects |
| Paths/links/types | Existing fail-closed policy | Extended traversal, absolute/drive/backslash paths, escaping links, duplicates, devices/FIFO/sparse/unknown types still reject |
| JSON/raw_name meaning | ASCII-escaped JSON, name after substitution | Unchanged; Unicode JSON roundtrip asserted; unresolved surrogates cannot emit |
| Pin/offset/drain/EOF/integrity/shared caps | Existing checks | Code unchanged; existing synthetic regression suite passes where runtime available |
| Isolation/FD/stdio | Launcher and existing tests | Byte-identical snapshots and hashes; host-dependent probes still pending normal-host execution |

Policy choice: temporary malformed fixed name/link strings are allowed only within maintained parsing and raw-byte accounting; final unresolved malformed UTF8 is rejected. Even a safe-looking invalid name or link is not permitted as a surrogate path. Raw owner/group metadata remains rejected even if an extension could override it, preserving prior strictness outside name/link handling. `tarfile` applies its existing directory/USTAR semantics; this change introduces no normalization. The surrogateescape override is confined to `_frombuf`; the parser still decides all field boundaries and GNU/PAX substitution. Other fixed strings are checked strictly before processing. GNU's unused prefix area is interpreted/ignored by tarfile as before, not a new output field.

## Fixture coverage

All fixtures are generated from TarInfo plus maintained tarfile/compression writers, in memory and anonymous temporary files. No fixture reads a production path. All categories run with both gzip and XZ:

- Six split GNU roundtrip combinations: long name, long symlink target, both. The writer's final base header is directly asserted to end in byte 0xc4; this is fixture inspection only.
- Eight PAX Unicode, USTAR Unicode, USTAR prefix/long basename, and ordinary ASCII GNU longname/link baselines.
- Twelve malformed UTF8 cases: short safe raw name/link, malformed long name/link bodies, uname/gname.
- Seventy-four unsafe extended-member cases across GNU and PAX: traversal/absolute/drive/backslash names, escaping symlink/hardlink targets, duplicate canonical names, character/FIFO/sparse/unknown types; PAX sparse metadata as well.
- Exact raw/final metadata byte accounting and hidden-header cap checks; ordinary multibyte exact-limit and one-byte-short rejection.
- Existing SDK tests retain EOF, corrupt/truncated/concatenated compression, limits/deadlines, pin ordering, descriptor mutation/replacement, output freshness/publication, sparse and unsupported types, global PAX/hidden-header counts, FD cleanup, and closed stdio coverage.

## Review artifacts and remaining risks

`before/` preserves the entire original reader v1 and entire launcher/existing test files. `current/` contains the whole current reader, unchanged launcher/existing tests, and new tests. `change.diff` compares the reader against its exact before snapshot and the new test against /dev/null. `before-hashes.json` and `current-hashes.json` cover all these code files. `tarfile-hooks.txt` preserves the inspected maintained hook implementations. No repository-wide reads/status/diff were needed.

The actual SDK cause remains unverified. No successful actual inventory is claimed. The three isolation tests and seven stdio subtests require normal-host execution by the orchestrator. The existing private `_frombuf` API dependency and launcher's allocation/AS/wall backstops remain as before. No XZ check policy or symlink policy changes were made. This synthetic fix does not prove compatibility with every tar producer.

Parent must resume an independent reviewer and review the NEW reader hash before any future SDK phase. No self-approval or handoff execution performed. Any later output must be fresh and named `inspection-metadata-utf8-PENDING-REVIEW`; no future command was executed and old output must never be reused.

## Current code hashes

- `tooling/sdk_inventory_phase.py`: `e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4`
- `tooling/isolate_sdk_inventory.py`: `2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52`
- `tooling/tests/test_sdk_inventory_phase.py`: `aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0`
- `tooling/tests/test_sdk_fd_boundary.py`: `f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10`
- `tooling/tests/test_sdk_stdio_boundary.py`: `15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065`
- `tooling/tests/test_sdk_utf8_boundary.py`: `746defc12bdcfa73f211eaad30ba8e349bb70eda8a40e9ed5bbb9ab12a4c3d58`
