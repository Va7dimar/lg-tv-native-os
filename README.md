# LG TV native-OS research (65NANO756PR, webOS 6)

Research, evidence, tooling and plans for investigating an internal OS replacement on an owned LG TV. Method is generic and the repo holds several TVs.

- [`tvs/`](tvs/README.md): index of TVs, plus **Adding a new TV** and [`tvs/_template/`](tvs/_template/)
- [`tvs/lg-65nano756pr/`](tvs/lg-65nano756pr/README.md): this unit (facts, evidence, control, sources, handoff). Owner-run root and Homebrew Channel confirmed 2026-11-08; nothing flashed; custom/native OS remains the goal.
- [`SOURCES.md`](SOURCES.md): where excluded downloads are recorded
- [`playbooks/tv-os-research.md`](playbooks/tv-os-research.md), [`REPRODUCING.md`](REPRODUCING.md), [`tooling/`](tooling/): generic method and read-only inspection tools

## Structure

| Path | What it is |
|---|---|
| `README.md`, `SOURCES.md`, `REPRODUCING.md` | Entry points |
| `playbooks/` | Generic method, for any TV |
| `docs/superpowers/` | Generic inspection-tool plans. This unit's OS plan is under its own `docs/plans/` |
| `tooling/` | Read-only inspection tools, tests, and review packages |
| `tvs/_template/` | Copy this to start another TV |
| `tvs/lg-65nano756pr/docs/` | Device facts, feasibility, project log, native-OS plan |
| `tvs/lg-65nano756pr/evidence/` | Inspection records and the decision record |
| `tvs/lg-65nano756pr/control/` | Remote helper, control research, menu notes |
| `tvs/lg-65nano756pr/research/ai-reviews/` | Saved model research and review outputs |
| `tvs/lg-65nano756pr/research/plan-reviews/` | Subscribed plan-review packets |
| `tvs/lg-65nano756pr/sources/` | Input record, notice catalog, saved LG pages |
| `tvs/lg-65nano756pr/handoff/` | Pause notes and next-work handoffs |

## Excluded inputs
Large or vendor-licensed inputs are **not** committed: LG open-source archives (`tvs/lg-65nano756pr/sources/catalog/archives/`), staged/extracted inspection outputs (`tvs/lg-65nano756pr/sources/catalog/inspection-*/`, `tvs/lg-65nano756pr/sources/sdk-candidates/**/inspection-*/`), SDK installer/sysroot downloads (`tvs/lg-65nano756pr/sources/sdk-candidates/**/assets/`), and LG user-guide copies (`tvs/lg-65nano756pr/sources/official-webos6-guide.zip`, `tvs/lg-65nano756pr/sources/official-guide-extracted/`, `tvs/lg-65nano756pr/sources/official-guide-eng.txt`). They are recorded by SHA-256 and download URL in the per-TV record linked from [`SOURCES.md`](SOURCES.md) and in the evidence manifests, so they can be re-fetched and verified. No pairing keys, serials or MAC addresses are stored.
