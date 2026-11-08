# Hardware adaptation (libkadaptor) phase addendum

Date: 2026-11-08 06:09 Atlantic/Reykjavik
Owner authorizations: t71u autonomous off-TV research/source inspection/tooling without per-file checkpoints; t74u cost priority to use subscribed AI/Cursor for heavy work.
Scope: one new isolated **hardware-adaptation** phase. This does not change CORE TWO allowlists, CLI test flags, or reviewed reader hashes. The prior all-three inventory PARTIAL (200000 members, incomplete Chromium) remains recorded and is not retried.

Pinned outer (do not open during development):

| File | Bytes | SHA256 |
|---|---|---|
| `webOS 6.0 KLP_1.0_2.tar.gz` | 511945894 | `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832` |

Pinned member (exactly one; no other package copies):

| Member | Bytes | SHA256 |
|---|---|---|
| `soc/libkadaptor-1.0.0-908.3.tar.gz` | 123840909 | `46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25` |

## Mechanism

One isolated invocation, one shared deadline and shared counters (no per-package reset):

1. Observe free disk (>= 10 GiB) before the phase and before writes (observation, not a reservation).
2. Open the outer file with `O_NOFOLLOW`; verify size and SHA256 **before** any tar parse.
3. Forward-read outer members with existing path/link/type/duplicate policy.
4. Charge outer decoded size from **logical sizes of regular file members only**, not tar headers/directories.
5. Stream-copy only the pinned member to `staged/` while hashing (do not buffer unclaimed payloads; discard them in chunks). NUL is allowed in this binary copy mode only.
6. Verify copied size and hash, then **re-hash the staged file before** any inner read.
7. Inventory that one inner archive; select NUL-free README/build/config/hardware-API-header/license/manifest evidence. No script execution. No further nested expansion.
8. Any failed/partial/timeout/collision/path error stops the phase and never marks `ok=true`. Output-path collisions are recorded as `status=failed` (not an uncaught crash).

## Hard ceilings (cannot be raised)

| Control | Limit |
|---|---|
| Wall | 120 s total (hash + copy + inner) |
| Address space | 1 GiB (`prlimit --as`; VSZ, not RSS) |
| Members | 200000 shared |
| Pathname/metadata | 100000000 bytes shared |
| Phase expanded + materialized | 4 GiB (outer logical regular + staged copy + inner logical + selected copies) |
| Outer compressed input | 512 MiB |
| Outer logical regular payload | 640 MiB |
| Target / materialized binary | 128 MiB each and 128 MiB total |
| Admitted compressed (outer + target) | 1 GiB |
| Selected text | 16 MiB each, 64 MiB combined |
| Disk reserve | >= 10 GiB observed |
| Nesting | one inner level |

`tarfile.next()` PAX/GNU allocations happen before semantic caps; isolation AS/wall is the backstop. `noexec_output_demonstrated` remains false; mode `0644` is not a noexec mount.

## CLI

Production pins are hardcoded. The production command cannot swap the target member, hashes, or sizes.

```
python3 /workspace/lg-tv/tooling/isolate_adaptation_phase.py \
  --outer "/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-adaptation-PENDING-REVIEW
```

An explicit `--synthetic-fixture-mode SPEC.json` exists only for isolated tests. It may supply fixture hashes/sizes for the **same pinned member name** and a synthetic outer file. It must not retarget a different package. The proposed real command never includes that flag.

This addendum does not authorize reading original LG archives during development, TV/build actions, ceiling raises, or a self-approved real inspection after green. Independent review and parent handoff come next.
