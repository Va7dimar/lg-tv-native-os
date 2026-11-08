You are performing a read-only SPEC + QUALITY code review of a local non-repo SDK metadata-only inventory tool.

Do NOT access, hash, open, or parse any file under /workspace/lg-tv/sdk-candidates/ (including the three production SDK/native/target assets). Do NOT edit any files. Do NOT run network commands. Do NOT execute installers or propose TV/flash/install actions. Synthetic reasoning and reading of tooling/review files only.

Read these files and review the implementation against the contract:

CONTRACT:
/workspace/lg-tv/tooling/review/sdk-inventory-2026-11-08/sdk-static-inventory-contract.md
REQUIREMENTS:
/workspace/lg-tv/tooling/review/sdk-inventory-2026-11-08/sdk-static-inventory-reader-requirements.md
ADDENDUM (read already by the independent reviewer; you may read it):
/workspace/lg-tv/tooling/review/sdk-inventory-2026-11-08/orchestrator-verification-addendum.md
IMPLEMENTATION REPORT:
/workspace/lg-tv/tooling/review/sdk-inventory-2026-11-08/sdk-implementation-report.md
READER:
/workspace/lg-tv/tooling/sdk_inventory_phase.py
Expected SHA256: c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f
LAUNCHER:
/workspace/lg-tv/tooling/isolate_sdk_inventory.py
Expected SHA256: 488e34d3470403206c0974cc82cdd36f7a6078619aaabf0bda390e3ea040f7f0
TESTS (understand intended behavior; do not require rerunning the whole suite; do not open real SDK assets):
/workspace/lg-tv/tooling/tests/test_sdk_inventory_phase.py
PROPOSED COMMAND (DO NOT EXECUTE):
/usr/bin/python3 -I -B /workspace/lg-tv/tooling/isolate_sdk_inventory.py \
  --sdk /workspace/lg-tv/sdk-candidates/20191125/assets/starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh \
  --native /workspace/lg-tv/sdk-candidates/20191125/assets/native_sysroot_dependencies.tar.gz \
  --target /workspace/lg-tv/sdk-candidates/20191125/assets/target_sysroot_dependencies.tar.gz \
  --output-dir /workspace/lg-tv/sdk-candidates/20191125/inspection-metadata-PENDING-REVIEW

Verify with file:line evidence:

1. Full size/hash/nofollow of all three inputs BEFORE any payload parse/decoder. Deadline covers hashes.
2. SDK literal MARKER:\n ending at offset 10820, then XZ magic, RO substream to EOF; other two gzip; production paths/pins/offset immutable; CLI cannot override.
3. Maintained tar/compression APIs including explicit private CPython 3.13 tarfile hook (_frombuf, _proc_member) — review correctness and portability.
4. Single compressed stream only; concat/trailing/corrupt/truncated/nonzero tar tail fail; decoder EOF drain and integrity; no unbounded read(-1).
5. 256 MiB LZMA memlimit; 1 GiB AS (VSZ not RSS); 120s global including hashes.
6. Shared 200000 observed headers (including hidden PAX/GNU) and conservative 100000000 UTF8 metadata; separate 4 GiB decoded full stream (headers/discard/padding/drain) and 4 GiB logical regular sizes — semantics accurate, not double-added into one counter.
7. No deeper archive expansion; unsafe/link/type/sparse/PAX policies; no extract/noexec.
8. Stable atomic false on error/budget/time/child kill; no false complete; no overwrite of worker manifest.
9. Fresh output; containment; RO inputs; home/credentials hidden; net unshared; 10 GiB free observation not reservation.
10. Metadata-only: selected_bytes=0; do not claim 16/64 MiB selection is an implemented extraction feature.
11. EOF is not just TarFile.next() stopping; multistream and junk must not be masked by default TarFile header-error-as-EOF behavior.

Output format:
### Claude model/effort you actually used
### Strengths (paths:lines)
### Issues
#### Critical
#### Important
#### Minor
For each issue: file:line, what, why, minimal fix.
### Residuals (honest limitations)
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Checkpoint for the exact planned METADATAONLY command: YES or NO, and conditions
### Whether you accessed any sdk-candidates asset contents (must be no)
