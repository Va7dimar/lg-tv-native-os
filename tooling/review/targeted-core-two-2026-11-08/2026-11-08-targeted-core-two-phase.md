# Targeted CORE TWO inner-phase tooling addendum

Date: 2026-11-08 05:06 Atlantic/Reykjavik
Approval: owner t68u quoted in full as `Continue`. Parent adopts CORE TWO ONLY (kernel + bootcode) after stating that targeted kernel/bootcode/adaptor inspection required a reviewed new scope and was paused. Optional `libkadaptor` is not included.
Historical proposal (not the executable contract): `handoff/targeted-inner-source-proposal.md`
Parent metadata reader (unchanged, separately reviewed): `docs/superpowers/plans/2026-11-08-bounded-source-inventory.md` and `tooling/bounded_archive_inventory.py`
Status: implementable box-only synthetic-fixture tooling. This does **not** authorize reading, parsing, or hash-rechecking original LG catalog archives; TV/hardware/account actions; firmware; flashing; builds; downloaded-code execution; package installation; network requests; recursive extraction; a Chromium/all-three retry; or a self-approved inspection handoff.

A green synthetic suite is not an independent review and does not admit the real archive2 inspection. Parent will independently review this new revision, then hand off any real inspection.

This phase produces staged copies plus one inner-level documentation inventory. It does **not** establish a compatible BSP, SoC/running kernel, boot route, recovery path, or installable replacement OS.

## Scope adopted (CORE TWO ONLY)

Exactly these outer members, from completed archive2 only:

| Member | Expected compressed payload bytes | Expected payload SHA256 |
|---|---|---|
| `soc/kernel-1.0.0-711..4.tar.gz` | 170350960 | `110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962` |
| `soc/bootcode-1.0.0-1099.7.tar.gz` | 12014324 | `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e` |

Outer input (production values; this session must not open the file):

| File | Bytes | SHA256 |
|---|---|---|
| `webOS 6.0 KLP_1.0_2.tar.gz` | 511945894 | `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832` |

`soc/libkadaptor-1.0.0-908.3.tar.gz` is **not** copied or inventoried, even if present as an outer member. No Chromium rescan. The prior all-three invocation PARTIAL at 200000 members remains recorded.

## Goal

Ship a narrowly scoped, tested phase tool under `/workspace/lg-tv/tooling/` that, after independent review and a later parent handoff, can run as **one isolated invocation** with a **shared closed budget**:

1. Verify the outer file (regular, `O_NOFOLLOW`, expected size and SHA256, compressed size <= 512 MiB).
2. Forward-read the outer archive with the existing path/link/type/duplicate policy.
3. Copy only the two allowlisted regular-file payloads as binary (NUL permitted in this copy mode only).
4. Reject missing targets, duplicates, hash/type/size mismatches, and output collisions.
5. Re-verify each staged package hash **before** any inner read.
6. Inventory each staged package at **one** inner level only. Deeper nested archives are metadata-only and never expanded.
7. Select safe README/build/config/board/license/manifest plaintext evidence (NUL-free, not binaries). Never run scripts or follow embedded instructions.
8. Stop the entire phase on failed/partial/timeout and never mark `ok=true`.

This session uses synthetic fixtures only. Tests may substitute smaller sizes/hashes via an explicit test helper; production defaults stay pinned and cannot be raised by flags.

## Hard ceilings (cannot be raised; do not soften if real fit is unknown)

| Control | Hard default | Notes |
|---|---|---|
| Outer compressed size | 512 MiB (536870912) | Single archive2 input |
| Binary copy each | 200 MiB (209715200) | Exact observed size/hash still required |
| Binary copy combined | 320 MiB (335544320) | Kernel+bootcode observed 182365284; unproven until a reviewed real run |
| Combined admitted compressed | 1 GiB (1073741824) | Outer file bytes + copied nested bytes |
| Outer decoded stream | 640 MiB (671088640) | Logical regular-member sizes while forward-reading archive2 |
| Phase expanded + materialized | 4 GiB (4294967296) | Outer decoded + staged copies + inner logical + selected copies (double-charge copies) |
| Members | 200000 total | Shared across outer validation/copy and both inner inventories; **no per-package reset** |
| Pathname + metadata bytes | 100000000 total | Shared; no per-package reset |
| Selected plaintext per member | 16 MiB (16777216) | Unchanged from the metadata reader |
| Selected plaintext combined | 64 MiB (67108864) | Additional combined cap |
| Wall | 120 s **total** | Includes outer hash, staging, and both inners; not 120 s per package |
| Address space | 1 GiB (1073741824) | Isolated process `prlimit --as`; VSZ, not RSS |
| Free disk | >= 10 GiB | Observation before phase and before materialization/selected writes; not a reservation |
| Nesting | one controlled inner level | No third-level expansion |
| Stdout | 64 KiB | Status only |

Python `tarfile` allocates PAX/GNU extended headers inside `next()` before semantic caps. Isolation AS/wall is the allocation backstop. Do not claim semantic caps contain parser allocations. `noexec` output remains **not demonstrated** (`false`); selected/staged mode `0644` is not a noexec mount.

## Mechanism

Reuse policy helpers from the reviewed metadata reader (`canonicalize_member_path`, `classify_link_target`, `logical_member_size`, `open_untrusted_tar_gz`, `open_regular_nofollow`, containment writes). Do not turn that reader into a generic recursive extractor and do not change its reviewed hash history.

Phase files (new revision):

- `tooling/targeted_core_two_phase.py`
- `tooling/isolate_targeted_phase.py`

Outputs under `--output-dir` only: `phase.json`, `phase.md`, `staged/<allowlisted-basename>`, optional `selected/<staged-basename>/...`. Existing `inventory.json` from the prior Chromium/all-three run must not be overwritten by this tool (use distinct filenames). Atomic temp+fsync+replace. `ok=true` only if the outer hash matched, both targets were copied and re-hashed, both inners completed, no policy/limit/timeout error occurred, and no unallowlisted binary was materialized.

Isolation launcher: `timeout --kill-after=5s` + `prlimit --as/--cpu/--core=0/--nofile=64` + `bwrap --unshare-all` with RO explicit outer input and tool, writable explicit output, no `/home` `/root` `/cursor`, no network, cleared environment.

## Proposed later command (NOT executed in this session)

```
python3 /workspace/lg-tv/tooling/isolate_targeted_phase.py \
  --outer "/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW \
  --expected-outer-bytes 511945894 \
  --expected-outer-sha256 95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832
```

Do not run that command until independent review passes and parent hands off the real inspection.

## Tests

Synthetic fixtures only. Record assertion-level RED (not merely ImportError) then GREEN for new tests plus the existing metadata-reader suite (61 tests). Cases: exact copy with NUL allowed only in binary mode; unallowlisted/oversize rejection; wrong hash/size/missing targets; path/link/type/duplicates; single-level depth; combined compressed and decompressed/materialized budgets; sparse logical size; parser-allocation backstop / isolation command; global deadline; containment and disk failures; isolation integration.
