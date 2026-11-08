# Bounded archive inventory tooling

Box-only streaming reader for untrusted `.tar.gz` trees. It writes a JSON/Markdown inventory and can copy selected safe plaintext members. It does not execute archive contents, follow links, expand nested archives, or talk to the TV.

Hard maxima are pinned in `bounded_archive_inventory.py` and cannot be raised by flags.

## Reproduce tests (synthetic fixtures only)

```bash
python3 --version
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
```

Expected: `Ran 48 tests` and `OK`. Do not point the tool at `source-catalog/archives/` until an independent review of this tooling has passed.

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
  --output-dir /path/to/empty-output \
  --min-free-disk-bytes 1
```

Uses existing `timeout` 9.7, `prlimit` 2.41.5, and `bwrap` 0.12.0. A non-exec output mount is **not** demonstrated on this box and is not claimed.


## Isolation is required for untrusted inputs

Use `isolate_inventory.py` for catalog or other untrusted archives. Semantic member/path/expansion caps do not prevent CPython `tarfile` from allocating PAX/GNU extended headers inside `next()`. The process `timeout` and `prlimit --as` wrappers are the allocation and wall-time backstop.

`--min-free-disk-bytes` cannot be set below 10 GiB on the CLI. Selected files land under `selected/<archive-basename>/` with mode `0644`. That mode is not a noexec mount; this tool never executes archive content.
