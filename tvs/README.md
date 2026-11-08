# TVs in this repo

Generic method lives at the top level: `playbooks/tv-os-research.md`, `REPRODUCING.md`, `tooling/`, `SOURCES.md` (format). Material specific to one TV goes under `tvs/<vendor>-<model>/`.

| TV | Folder | Status |
|---|---|---|
| LG 65NANO756PR (webOS 6.0, KLP 1.0) | [lg-65nano756pr](lg-65nano756pr/README.md) | Research and static inspection; nothing flashed |

The first TV was done before this layout existed, so its files still sit at the top level. Its per-TV README maps them, and they have not been moved.

## Adding a new TV
1. `cp -r tvs/_template tvs/<vendor>-<model>` (lowercase, e.g. `samsung-qe55q80`).
2. Fill in `device-facts.md` from read-only queries only. Redact serials, MACs and pairing keys.
3. Find the vendor's official open-source page for the exact model. Record downloads in the TV's `SOURCES.md` (URL, catalog/release id, filename, bytes, SHA-256, date, method). Keep the large files out of git: put them under `tvs/<tv>/inputs/`, which is gitignored.
4. Follow `playbooks/tv-os-research.md` phase by phase. Reuse `tooling/` (bounded, read-only archive readers) and write results to `tvs/<tv>/evidence/`.
5. Record decisions in `decision-record.md` and restart notes in `handoff/`.
6. Add a row to the table above.
