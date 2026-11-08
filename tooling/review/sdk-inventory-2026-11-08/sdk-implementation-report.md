# SDK metadata inventory — current verification status

Updated 2026-11-08T06:32:36.030464+00:00 (Atlantic/Reykjavik): **27/27 targeted synthetic tests PASS in actual box runtime; successful synthetic isolation preserved. Independent SPEC/QUALITY review and actual-run handoff remain pending. Actual SDK payloads NOT read or hashed.** See `tooling/review/sdk-inventory-2026-11-08/orchestrator-verification-addendum.md`, logs15–17, and current SHA256SUMS. Initial Codex sandbox isolation failure below is preserved historical context, not current host-runtime status.

## Historical implementer report before orchestrator host verification

# SDK metadata inventory implementation — 2026-11-08

Status: implemented for independent SPEC/QUALITY review; **not ready for actual payload invocation**. Synthetic parser checks pass, but successful isolation is unverified because this runtime rejects bwrap network namespace setup. No SDK/archive/source asset was opened, read, hashed, parsed, executed, or inspected during implementation. No changes to existing tools, libkadaptor, configuration, repositories, or dependencies. No external network requests, installations, builds, TV operations, or actual production invocation.

## Delivered files

- `tooling/sdk_inventory_phase.py`: frozen production input specifications, descriptor-based pins, bounded XZ/gzip streaming, maintained tarfile parsing, metadata policy, shared counters, JSONL, and atomic manifest publication.
- `tooling/isolate_sdk_inventory.py`: mandatory closed production CLI, bwrap/prlimit/timeout launcher, stable individual input descriptor binds, outside launcher result, and library-only synthetic fixture injection.
- `tooling/tests/test_sdk_inventory_phase.py`: 27 stdlib unittest methods; every fixture is synthetic. No optional fixture module was needed.
- This report and the complete review package at `tooling/review/sdk-inventory-2026-11-08/`.

## Contract implementation and explicit scope

Full immutable size/SHA256 checks, SDK literal marker, slice offset, and compression signatures precede construction of any decoder. Descriptors stay open; device/inode/size/mtime/ctime/link-count are rechecked after pins, before and after parsing, and at completion. The wrapper binds the held descriptors individually, never a whole asset directory. Production CLI paths must equal all three exact paths in the reader requirements. No selectors, pin overrides, offset overrides, budget overrides, test flags, extraction, recursion, or member content hashing exist. Direct execution of the worker refuses production use; use the launcher.

One phase shares 200,000 observed headers (including hidden PAX/GNU headers), 100,000,000 metadata bytes, an independent 4 GiB logical regular-size limit, and an independent 4 GiB total decoder-output limit. These counters are not combined or reset after failure. The first exceeding observation is included in false-manifest totals; decoder chunks are at most 65,536 bytes. Full decoder output includes headers, discarded payload, padding, read-ahead, and EOF drain. Selected bytes remain zero. The 16 MiB/member and 64 MiB combined selection policies are recorded as future policy; extraction is not implemented or claimed tested.

Metadata charging is deliberately conservative: decoded header name/link/uname/gname UTF8 bytes, padded PAX/GNU extension body lengths, then resolved name/link/PAX keys and values. Repeated fields and overwritten extension values remain charged. `raw_name` means maintained-parser decoded name after PAX/GNU substitution and before our canonicalization; it is not a byte-for-byte copy of a physical tar header. No custom tar-header parser exists. Normal links receive lexical safety checks and `recorded_not_followed`; targets are never opened, followed, or resolved against the filesystem. Unsafe parent components (even internally cancelling ones), backslashes, absolute/drive paths, duplicate canonical paths, devices/FIFOs, sparse entries, unknown types, and nonregular payloads fail closed. Conventional `.` root-directory records are permitted.

XZ uses LZMADecompressor with an explicit 256 MiB memlimit. Gzip uses zlib's maintained gzip decoder. Both enforce one stream, rejecting any compressed trailing bytes, including zeros or another stream. EOF is accepted only after complete decoder integrity validation. A reviewed CPython 3.13 tarfile `_frombuf` hook delegates parsing to stdlib, counts extension headers through `_proc_member`, records the first zero header, and converts malformed-header errors that TarFile.next could otherwise tolerate into failures. A forward-only file adapter avoids tarfile's separate stream read-ahead buffer; all our buffered decoded bytes remain available to the tail check. At least two zero blocks and block-aligned zero padding are required, including for empty archives. Nonzero decoded data after the first tar EOF header fails, including data already buffered. Exact compressed bytes consumed is reported at compression EOF; it is null if unknown on a failed/incomplete stream. Read bytes include read-ahead and are reported separately from full-file hash bytes.

The launcher starts a single 120-second deadline before preflight, shares its absolute monotonic deadline with the worker, and uses the remaining time for timeout/subprocess limits. AS is 1 GiB, not RSS; CPU/core/fd/file-size limits are explicit. Tarfile extended-header allocations still depend on AS/wall backstops; semantic checks do not prove containment of every parser allocation. The output disk floor is observed 10 GiB before work and before writes; space is not reserved. Metadata files are data, and noexec is explicitly false. Production runtime is the local Linux x86_64 `/usr/bin/python3` layout with only its interpreter, stdlib, dynamic-library runtime, exact worker file, three input binds and output bind. The sandbox requests unshared namespaces, clears environment, hides host home/root/credentials, and makes its root/runtime/input/proc/dev read-only; only the output mount is writable. This mount arrangement remains **unverified in a successful sandbox** here.

Fresh outputs are created without symlink ancestry using directory descriptors; files are exclusive/nofollow and writes remain relative to the held output descriptor. Manifests publish atomically with link(2), refusing overwrite. No existing output is deleted or replaced. Partial JSONL is referenced by false manifests. `launcher-result.json` is the authoritative outside final result even if a worker was killed after publishing its own manifest. A missing worker manifest gets a false fallback. On a pre-existing/unsafe output path, no manifest is written there: the CLI returns bounded failure JSON. Physical write failure or an unmet disk floor can prevent any persisted failure report; the CLI fails and never declares success. Normal failure/timeout/startup cases are covered by synthetic tests, not claims of guaranteed disk availability.

## Actual TDD evidence

Every log preserves UTC timestamp, exact argv (and nondefault cwd), full combined output, and process exit code. Only the newly created SDK test module was discovered.

| Log | Actual outcome |
| --- | --- |
| `01-red.txt` | Missing new module; import discovery error, exit 1. This alone was not treated as behavioral TDD evidence. |
| `02-behavior-red.txt` | API scaffold, before implementation: 16 tests; 1 failure and 47 errors including subtest observations; exit 1. |
| `03-first-implementation.txt` | 16 tests; 15 passed, 1 sandbox-blocked skip; exit 0. |
| `04-regression-red.txt` | 24 tests; 1 error exposing a missing truthful enforced-AS field, 1 blocked skip; exit 1. |
| `05-regression-green.txt` | 24 tests; 23 passed, 1 blocked skip; exit 0. |
| `06-synthetic-isolation-evidence.txt` | Actual full-path launcher attempt using synthetic fixtures; exit 1. Preserves exact command, launcher/worker-fallback manifests, stdout and stderr. |
| `07-provenance-red.txt` | 26 tests; missing pin-verification provenance field, 1 error, 1 blocked skip; exit 1. |
| `08-provenance-green.txt` | Attempted green, actually FAILED: 26 tests; descriptor replacement escaped timestamp-only mutation detection, 1 failure, 1 blocked skip; exit 1. Filename is historical, not a success claim. |
| `09-provenance-green.txt` | Added link-count stability check: 26 tests; 25 passed, 1 blocked skip; exit 0. |
| `10-synthetic-as-backstop.txt` | Four targeted parser tests under actual prlimit 1 GiB AS / core=0 / nofile=64 and timeout: 4 passed, exit 0. This is not sandbox success. |
| `12-isolated-cli-red.txt` | 27 tests; subprocess regression exposed sibling import failure under Python `-I`, 1 failure, 1 blocked skip; exit 1. |
| `13-final-green.txt` | Explicit trusted tool-directory import: 27 tests; 26 passed, 1 blocked skip; exit 0. |
| `14-final-green.txt` | Final code with loopback-only synthetic connectivity probe: 27 tests; 26 passed, 1 blocked skip; exit 0. |
| `11-runtime-versions.txt` | Python 3.13.5, bubblewrap 0.12.0, util-linux prlimit 2.41.5, GNU timeout 9.7; actual outputs and exit codes. |

The final synthetic probe uses only loopback connectivity plus namespace comparison; it makes no external network request. Tests cover all three synthetic inputs together, pins-before-parser, size and nofollow leaf/ancestor protection, wrong offset/marker/signature, mutation/replacement, both codecs valid/corrupt/truncated/concatenated/trailing, integrity failure after tar logical EOF, missing/malformed tar EOF, read-ahead tail rejection, bounded decoder reads, small safe LZMA dictionary above a lowered library test limit, PAX/global-PAX/GNU names, hidden-header counts, unsafe names/links/duplicates/devices/sparse, shared member/metadata/logical/fullstream ceilings, pin/decode deadline checks, fresh/dangling/symlink output protection, atomic no-overwrite false manifests, closed production CLI, startup failure, timeout, and exact individual bind command construction.

## Isolation blocker and remaining review

The actual synthetic production-like bwrap launch failed with:

```
bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted
```

The worker never started in that attempt. Both persisted outside launcher and fallback worker manifests say `ok=false`. The unittest marks this as a blocked skip, not a pass. Home hiding, distinct network namespace, and inability to modify inputs are assertions in the full-path synthetic harness but **were not reached or demonstrated**. No sandbox bypass or fallback to an unsandboxed production run was attempted. A successful synthetic isolation run on a supported runtime remains required before actual payload use, along with parent independent SPEC/QUALITY review. These self-tests are not that independent review. Runtime portability and the private maintained-parser hook require explicit review if Python changes.

## Proposed command — NOT EXECUTED

See `proposed-metadataonly-command.txt` in the review package. It specifies all three immutable production paths and the exact pending-review output path supplied by the parent. This implementation stage does not authorize executing it. Input pins total 498625937 bytes; SHA256/size values are copied from the contract, not recomputed against real assets. The package contains whole production/test/report files, contract and requirement snapshots, and `SHA256SUMS.txt` hashing only these allowed review artifacts.
