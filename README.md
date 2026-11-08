# LG TV native-OS research (65NANO756PR, webOS 6)

Research, evidence, tooling and plans for investigating an internal OS replacement on an owned LG TV. Method is generic and the repo holds several TVs.

- [`tvs/`](tvs/README.md): index of TVs, plus **Adding a new TV** and [`tvs/_template/`](tvs/_template/)
- [`tvs/lg-65nano756pr/`](tvs/lg-65nano756pr/README.md): first TV; maps to its existing paths
- [`SOURCES.md`](SOURCES.md): every excluded download (LG archives, community SDK) with URL, size, SHA-256, date, method, and where it was used
- [`playbooks/tv-os-research.md`](playbooks/tv-os-research.md), [`REPRODUCING.md`](REPRODUCING.md), [`tooling/`](tooling/): generic method and read-only inspection tools

## Excluded inputs
Large or vendor-licensed inputs are **not** committed: LG open-source archives (`source-catalog/archives/`), staged/extracted inspection outputs (`source-catalog/inspection-*/`, `sdk-candidates/**/inspection-*/`), SDK installer/sysroot downloads (`sdk-candidates/**/assets/`), and LG user-guide copies (`official-webos6-guide.zip`, `official-guide-extracted/`, `official-guide-eng.txt`). They are recorded by SHA-256 and download URL in [`SOURCES.md`](SOURCES.md) and the evidence manifests so they can be re-fetched and verified. No pairing keys, serials or MAC addresses are stored.
