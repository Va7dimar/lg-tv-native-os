# TVs in this repo

Generic method lives in [`REPRODUCING.md`](../REPRODUCING.md), [`tooling/`](../tooling/), and [`docs/superpowers/`](../docs/superpowers/) (inspection-tool plans). [`SOURCES.md`](../SOURCES.md) at the repo root points at each TV's input record. Material specific to one TV goes under `tvs/<vendor>-<model>/`.

| TV | Folder | Status |
|---|---|---|
| LG 65NANO756PR (webOS 6.0, KLP 1.0) | [lg-65nano756pr](lg-65nano756pr/README.md) | Owner-rooted + Homebrew Channel 2026-11-08; nothing flashed; custom-OS boot still no-go |

## Adding a new TV
1. `cp -r tvs/_template tvs/<vendor>-<model>` (lowercase, e.g. `samsung-qe55q80`).
2. Fill in `docs/device-facts.md` from read-only queries only. Redact serials, MACs and pairing keys.
3. Find the vendor's official open-source page for the exact model. Record downloads in the TV's `SOURCES.md` (URL, catalog/release id, filename, bytes, SHA-256, date, method). Keep the large files out of git: `sources/catalog/archives/`, `sources/sdk-candidates/**/assets/`, guide archives, and `inputs/` are gitignored.
4. Follow [`REPRODUCING.md`](../REPRODUCING.md) step by step. Reuse [`tooling/`](../tooling/) (bounded, read-only archive readers) and write results to `tvs/<tv>/evidence/`.
5. Record decisions in `docs/decision-record.md`, feasibility in `docs/feasibility.md`, chronology in `docs/project-log.md`, and restart notes in `handoff/`.
6. Add a row to the table above and a row in the root [`SOURCES.md`](../SOURCES.md).
