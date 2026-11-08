# CORE TWO targeted phase — implementation report

Recorded: 2026-11-08 05:11 Atlantic/Reykjavik
Owner t68u quoted in full: `Continue`
Scope adopted by parent: CORE TWO ONLY (kernel + bootcode). Optional libkadaptor is out of scope.
This is a self-implementation report, not an independent review and not an inspection handoff.

No original LG catalog archive was read, parsed, or hash-rechecked. The prior all-three inventory PARTIAL (200000-member cap, incomplete Chromium) was not retried.

## Decision records

- Historical proposal (retained, marked historical): `tvs/lg-65nano756pr/handoff/targeted-inner-source-proposal.md`
- Executable addendum: `docs/superpowers/plans/2026-11-08-targeted-core-two-phase.md`
- Checklist note: `tvs/lg-65nano756pr/handoff/approval-checklist.md` (2026-11-08 05:06 Atlantic/Reykjavik)

## What was implemented

New revision (does not modify the reviewed metadata reader):

| Path | Role |
|---|---|
| `tooling/targeted_core_two_phase.py` | One-shot outer verify/hash, allowlisted binary copy, staged re-hash, one inner inventory + evidence select |
| `tooling/isolate_targeted_phase.py` | `timeout` + `prlimit` + `bwrap --unshare-all` around the phase; binds the phase module and the existing reader helper |
| `tooling/tests/test_targeted_core_two_phase.py` | 24 synthetic tests |

Reviewed metadata reader hashes unchanged:

```
ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c  tooling/bounded_archive_inventory.py
eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915  tooling/isolate_inventory.py
```

Pinned production targets (not opened here):

- `soc/kernel-1.0.0-711..4.tar.gz` 170350960 `110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962`
- `soc/bootcode-1.0.0-1099.7.tar.gz` 12014324 `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e`
- Outer archive2 expected 511945894 `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832`

Shared budgets do not reset per package: members, pathname bytes, expanded/materialized bytes, selected-text bytes, and a single wall deadline covering hash + staging + both inners.

## TDD

1. Addendum and decision records first.
2. Tests plus a stub API so failures are assertions, not missing imports.
3. Red: `python3 -m unittest /workspace/lg-tv/tooling/tests/test_targeted_core_two_phase.py -v`

```
Ran 23 tests in 0.026s
FAILED (failures=16, errors=3)
EXIT:1
```

Artifact: `tooling/artifacts/red-core-two-phase.txt` (2026-11-08). Four stubs accidentally passed (allowlist pin, non-evidence names, catalog-filename guard, unallowlisted-not-copied because the stub copied nothing). Isolation/exact-copy errored on missing files or an empty command.

4. Implementation of the phase and launcher. One sparse-budget test was added immediately before implementation (not present in the 23-test red file; it would have failed on the stub).
5. Green:

```
python3 -m unittest /workspace/lg-tv/tooling/tests/test_targeted_core_two_phase.py -v
Ran 24 tests in 0.142s
OK
EXIT:0
```

```
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
Ran 85 tests in 0.277s
OK
EXIT:0
```

Artifacts: `tooling/artifacts/green-core-two-phase.txt`, `tooling/artifacts/green-core-two-full-suite.txt` (2026-11-08 05:11 Atlantic/Reykjavik).

## Requirements traceability

| Requirement | Test / code |
|---|---|
| CORE TWO only; no libkadaptor | `test_core_two_pins_exact_targets_and_excludes_libkadaptor`, `test_unallowlisted_libkadaptor_is_not_copied` |
| Outer SHA256/size/no-follow before listing | `test_wrong_outer_hash_never_reads_members`; `bai.open_regular_nofollow` |
| Exact copy + re-hash before inner | happy-path copy bytes; staged `verified_before_inner` |
| NUL allowed only in binary copy | happy path copies gzip/NUL payload; `blob.bin` with NUL not selected |
| Evidence plaintext 16MiB / 64MiB combined | `is_evidence_plaintext_name` tests; selected README/LICENSE |
| Missing/duplicate/hash/type/size | dedicated rejection tests |
| Path/link policy | `test_absolute_and_parent_paths_fail_closed`, `test_symlink_target_rejected` |
| One inner level | `test_inner_nested_archive_not_expanded` |
| Combined binary / outer-decoded / phase-expanded | combined, outer_decoded, sparse expanded tests |
| Shared member budget | `test_member_budget_does_not_reset_for_inner` |
| Global deadline | `test_global_deadline_does_not_reset` |
| Disk observation | `test_disk_reserve_failure` |
| Isolation + honest noexec | command-shape + integration tests; `noexec_output_demonstrated: false` |
| Limits unraisable | `test_phase_limits_cannot_be_raised` |
| No Chromium retry | addendum + decision records; phase never opens archive1/3 |

## Proposed later command (NOT executed)

See `tooling/review/targeted-core-two-2026-11-08/PROPOSED-INSPECTION-COMMAND.txt`.

## Residuals (honest)

- This green suite is not an independent review. Do not inspect real archive2 until parent’s reviewer passes this revision and parent hands off that run.
- Semantic caps still do not contain `tarfile.next()` PAX/GNU allocations. Isolation AS/wall is the backstop.
- `prlimit --as` is virtual address space, not RSS.
- Disk checks observe free space; they do not reserve it.
- noexec output mount remains undemonstrated and is reported `false`. Staged/selected mode `0644` is not a noexec mount.
- Phase expanded accounting double-charges copies as specified; a reviewed real run may still not fit unknown logical expansion inside the 4 GiB / 640 MiB outer-decoded caps. Limits were not softened.
- A successful later inner inventory would still not prove BSP compatibility, a boot route, recovery, or a replacement OS.
