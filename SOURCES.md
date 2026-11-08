# External inputs (not committed)

Large or vendor-licensed downloads are not in git. Each TV records them in its own `SOURCES.md`: URL, catalog or release id, filename, bytes, SHA-256, date, method, and where the bytes were used.

| TV | Record |
|---|---|
| LG 65NANO756PR | [tvs/lg-65nano756pr/SOURCES.md](tvs/lg-65nano756pr/SOURCES.md) |

Re-fetch steps and hashes for that unit are in its record. Compare a new download with the recorded SHA-256. A match shows the same bytes used here. It does not prove the file is authentic or a valid archive. If a hash differs, record the new hash and treat the file as a new input.

Those files stay out of git. `.gitignore` excludes the per-TV locations (`tvs/*/sources/catalog/archives/`, `inspection-*`, SDK `assets/` and `inspection-*`, user-guide archives) and the same names at the old top-level paths, plus `tvs/*/inputs/`.
