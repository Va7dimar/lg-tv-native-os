# Adaptation libkadaptor phase review package

Date: 2026-11-08 ~06:21 Atlantic/Reykjavik
This package is for independent review. It is not a self-approval to run the real archive2 inspection.

## What was added

New isolated single-member hardware-adaptation phase. CORE TWO allowlists, CLI test flags, and reviewed reader hashes were not changed. The prior all-three inventory PARTIAL remains recorded and was not retried.

Pinned production target: outer `webOS 6.0 KLP_1.0_2.tar.gz` 511945894 / SHA256 `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832` member exactly `soc/libkadaptor-1.0.0-908.3.tar.gz` 123840909 / SHA256 `46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25`.

## Implementation worker

Primary implementation/test reasoning: Codex CLI `codex-cli 0.166.0`, model `gpt-6.1-sol`, `model_reasoning_effort=high`, `--approve-for-me` (workspace-write sandbox). No `--dangerously-bypass-approvals-and-sandbox`. First launch failed immediately (incompatible `--sandbox` + `--approve-for-me`); retry succeeded.

Codex session id: `01a1b9c8-c9e9-7571-84c7-f28feeb60679`
Codex wall: started 2026-11-08 06:11:46 UTC, ended 2026-11-08 06:20:41 UTC (534917 ms, about 8m 55s)
Tokens used: 59065
Codex last message and CLI log: `/workspace/lg-tv/tooling/artifacts/codex-adaptation-last-message.txt`, `codex-adaptation-cli.log`

Independent re-run after Codex (this executor, no real archives): 54 new tests OK in 0.322s; full suite 139 tests OK in 0.585s.

## TDD

Red (Codex, stub returning missing-behavior): `red-adaptation-phase.txt` — Ran 49 tests in 0.153s, FAILED (failures=51, errors=13). Failures are assertion-level (`'hash'/'size' not found in 'missing adaptation behavior'`), not only ImportError. Five extra tests were added after that red snapshot.

Green new: `green-adaptation-phase.txt` — Ran 54 tests in 0.269s OK
Green full: `green-adaptation-full-suite.txt` — Ran 139 tests in 0.594s OK (85 prior + 54 new)

## Proposed command

See `PROPOSED-INSPECTION-COMMAND.txt`. Do not execute until independent review and parent audit handoff. Never include `--synthetic-fixture-mode` on the production command.

## Residuals for reviewers

- Existing `phase.json`/`phase.md` collisions are reported as `status=failed` / `ok=false`, but `_persist` then atomically overwrites those index names with the failed document (selected payload collisions use O_EXCL and leave the existing file). Reviewers should decide whether overwriting a colliding index is acceptable.
- Failed indices are best-effort if permissions, disk, or an external kill prevent writes; `phase-failed.json` is used when the primary index path is a symlink/unusable.
- `noexec_output_demonstrated` is false; mode 0644 is not a noexec mount.
- `prlimit --as` limits VSZ, not RSS.
- Disk checks are free-space observations, not reservations.
- `tarfile.next()` PAX/GNU allocations happen before semantic caps; isolation AS/wall is the backstop.
- Outer decoded size charges logical sizes of regular file members only (not tar headers or directories).
- Selected text still buffers one member up to the 16 MiB cap; unclaimed and binary copy use 1 MiB chunks and do not keep whole unclaimed payloads.
- Production archives were not opened, hashed, or parsed during development or after green.
- Hardware API header selection is conservative (`.h`/`.hpp` under include/api/hardware/adaptor/hal/kadaptor, or names containing `api`). Unrelated private headers are not selected.
- Codex notes its own process sandbox initially blocked bwrap NETLINK_ROUTE; the isolation integration test later passed with launcher flags intact.

No Page edits, TV/build actions, ceiling raises, or real-archive run were performed.
