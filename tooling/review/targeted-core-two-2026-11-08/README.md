# Bounded archive inventory tooling

Box-only streaming reader for untrusted `.tar.gz` trees. It writes a JSON/Markdown inventory and can copy selected safe plaintext members. It does not execute archive contents, follow links, expand nested archives, or talk to the TV.

Hard maxima are pinned in `bounded_archive_inventory.py` and cannot be raised by flags.

## Reproduce tests (synthetic fixtures only)

```bash
python3 --version
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
```

Expected for the reviewed fix revision: `Ran 61 tests` and `OK` (historical48-test suite preceded the fix loop). Do not point the tool at `source-catalog/archives/` until an independent review of this tooling has passed.

## Direct (non-isolated) invocation

```bash
python3 /workspace/lg-tv/tooling/bounded_archive_inventory.py \
  --input /path/to/fixture.tar.gz \
  --output-dir /path/to/empty-output \
  --select docs/note.txt
```

Outputs go only to `--output-dir`: `inventory.json`, `inventory.md`, optional `selected/`.

## Isolated invocation

```bash
python3 /workspace/lg-tv/tooling/isolate_inventory.py \
  --input /path/to/fixture.tar.gz \
  --output-dir /path/to/empty-output
```

Uses existing `timeout` 9.7, `prlimit` 2.41.5, and `bwrap` 0.12.0. A non-exec output mount is **not** demonstrated on this box and is not claimed.


## Isolation is required for untrusted inputs

Use `isolate_inventory.py` for catalog or other untrusted archives. Semantic member/path/expansion caps do not prevent CPython `tarfile` from allocating PAX/GNU extended headers inside `next()`. The process `timeout` and `prlimit --as` wrappers are the allocation and wall-time backstop.

`--min-free-disk-bytes` cannot be set below 10 GiB on the CLI. Selected files land under `selected/<archive-basename>/` with mode `0644`. That mode is not a noexec mount; this tool never executes archive content.


## CORE TWO targeted phase (new revision, needs its own review)

`targeted_core_two_phase.py` plus `isolate_targeted_phase.py` copy exactly kernel and bootcode payloads from one outer archive and inventory each at one inner level. This is not a generic recursive extractor and does not retry the Chromium/all-three scan.

Synthetic tests:

```bash
python3 -m unittest /workspace/lg-tv/tooling/tests/test_targeted_core_two_phase.py -v
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
```

The later real inspection command is documented as **proposed only** in `tooling/review/targeted-core-two-2026-11-08/PROPOSED-INSPECTION-COMMAND.txt`. Do not run it until independent review passes and parent hands off the inspection. This session did not read original LG archives.
