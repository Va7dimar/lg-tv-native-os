# External inputs (not committed)

These inputs were used on the work machine (`/workspace/lg-tv/`) but are excluded from git because of size and/or vendor licensing. Each is recorded here by filename, size and SHA-256, so you can download it again and check it. All times are Atlantic/Reykjavik (UTC+0).

## 1. LG official open-source archives (TV: LG 65NANO756PR)

- **Source:** LG Open Source Center, official public site: <https://opensource.lge.com/product/list?keyword=65NANO756PR>
- **Catalog entry:** "webOS 6.0 KLP 1.0", release sequence **510320**.
- **How downloaded:** 2026-11-08 ~04:18–04:23, using the site's normal public download buttons in a browser (no hidden endpoints or scraping). The site gave no sizes, direct URLs or official checksums.
- **Manifest:** `tvs/lg-65nano756pr/evidence/catalog-manifest.json`

| File | Bytes | SHA-256 | Saved |
|---|---|---|---|
| `webOS 6.0 KLP_1.0_1.tar.gz` | 3,270,734,309 | `2bef84ebee68a860e9729ad5504ae6bf29b18b5fff9c12df0167e68613569970` | 04:19 |
| `webOS 6.0 KLP_1.0_2.tar.gz` | 511,945,894 | `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832` | 04:20 |
| `webOS 6.0 KLP_1.0_3.tar.gz` | 1,777,722,146 | `f37ca9716820849e37b946bdd5d91d52b51c765a95dc0b309203470015b6fa1c` | 04:22 |
| `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html` (committed) | 5,562,232 | `3e7a13e14f6cd328c9b5483c25c416e735da67dc5cd08131b61804a9b06fbf8f` | — |

**Where they were used:**
- Bounded member inventory: `tvs/lg-65nano756pr/sources/catalog/inspection-2026-11-08/`, then `tvs/lg-65nano756pr/evidence/archive-members.json`, `tvs/lg-65nano756pr/evidence/source-coverage-preliminary.*`
- Build-guide selection: `tvs/lg-65nano756pr/sources/catalog/inspection-build-guides-2026-11-08/`, then `tvs/lg-65nano756pr/evidence/build-guide-inspection.*`, `tvs/lg-65nano756pr/evidence/build-guide-execution-2026-11-08/`
- Kernel/bootcode ("core-two"): `tvs/lg-65nano756pr/sources/catalog/inspection-core-two-*/` (staged `kernel-*.tar.gz`), then `tvs/lg-65nano756pr/evidence/kernel-bootcode-inspection.*`, `tvs/lg-65nano756pr/evidence/core-two-execution-2026-11-08/`
- Adaptation layer (libkadaptor): `tvs/lg-65nano756pr/sources/catalog/inspection-adaptation-*/`, then `tvs/lg-65nano756pr/evidence/adaptation-inspection.*`
- Build/config closure: `tvs/lg-65nano756pr/evidence/build-closure-execution-2026-11-08/`, `tvs/lg-65nano756pr/evidence/project-config-execution-2026-11-08/`, `tvs/lg-65nano756pr/evidence/source-configuration-closure.*`

## 2. Starfish SDK (community release, NOT official LG)

- **Source:** <https://github.com/lgstreamer/starfish-sdk-x86_64/releases/tag/04.40.20>. This is a community/third-party release. Its authorship and any link to LG are unverified. LG's build guides ask for SDK `5.0.0-20190307`; this release is `5.0.0-20191125` and is only a candidate.
- **How downloaded:** 2026-11-08 06:10, with `curl --fail --location --proto =https --tlsv1.2 --max-filesize <expected>` from the release asset URLs (`.../releases/download/04.40.20/<file>`). The release publishes no digest.
- **Manifest:** `tvs/lg-65nano756pr/evidence/public-sdk-2026-11-08/acquisition-manifest.json` (exact commands and HTTP results)

| File | Bytes | SHA-256 | Saved |
|---|---|---|---|
| `native_sysroot_dependencies.tar.gz` | 8,017,931 | `f97498cc24de8a617be8e842962e30299be034730981ac8da0e216548a92f48a` | 06:10:40 |
| `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh` | 166,821,312 | `3029c64809fe93e6fe6bfb72ac9de6ec556452a0790feb0f9b23abed409e669b` | 06:10:43 |
| `target_sysroot_dependencies.tar.gz` | 323,786,694 | `b5bbe22da19a9fabea1f24cc1965e5a853e9d2935e9e5bdfcd81d7c83174f39b` | 06:10:50 |

**Where they were used** (read-only: never installed, executed or compiled):
- Header/prefix assessment: `tvs/lg-65nano756pr/evidence/public-sdk-2026-11-08/` (`sdk-header-findings.*`, `prefix-assessment*`)
- Static inventory runs: `tvs/lg-65nano756pr/evidence/sdk-inventory-*` (first run, UTF-8 filename fix, and the external-link logging run that finished with 66,880 entries). Raw outputs are in `tvs/lg-65nano756pr/sources/sdk-candidates/20191125/inspection-*/`, which is excluded.

## 3. LG user guide (excluded)
`tvs/lg-65nano756pr/sources/official-webos6-guide.zip`, `tvs/lg-65nano756pr/sources/official-guide-extracted/` (35 language PDFs) and `tvs/lg-65nano756pr/sources/official-guide-eng.txt` came from LG's public manual page for the model (see `tvs/lg-65nano756pr/sources/web-snapshots/official-guide.html` and `tvs/lg-65nano756pr/sources/web-snapshots/model-support.html`). To re-obtain them, search the model on lg.com support.

## Re-obtain and verify
```bash
mkdir -p tvs/lg-65nano756pr/sources/catalog/archives tvs/lg-65nano756pr/sources/sdk-candidates/20191125/assets
# LG archives: download manually from the catalog URL above into tvs/lg-65nano756pr/sources/catalog/archives/
for f in native_sysroot_dependencies.tar.gz starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh target_sysroot_dependencies.tar.gz; do
  curl --fail -L --proto =https -o "tvs/lg-65nano756pr/sources/sdk-candidates/20191125/assets/$f" \
    "https://github.com/lgstreamer/starfish-sdk-x86_64/releases/download/04.40.20/$f"; done
sha256sum tvs/lg-65nano756pr/sources/catalog/archives/* tvs/lg-65nano756pr/sources/sdk-candidates/20191125/assets/*   # compare with the tables above
```
A matching hash shows you have the same bytes used here. It does not prove the file is authentic or a valid archive. Vendors can replace downloads; if a hash differs, record the new hash and treat the file as a new input.
