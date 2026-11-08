# Tooling progress

Updated: 2026-11-08 05:10 Atlantic/Reykjavik

- Owner t68u quoted: `Continue`. Parent adopted CORE TWO ONLY (kernel + bootcode; not libkadaptor).
- Historical proposal retained: `handoff/targeted-inner-source-proposal.md`
- Executable addendum: `docs/superpowers/plans/2026-11-08-targeted-core-two-phase.md`
- New tools: `targeted_core_two_phase.py`, `isolate_targeted_phase.py` (approved metadata reader hash unchanged)
- RED: 23 tests, 16 failed + 3 errors (assertion-level after stub API): `artifacts/red-core-two-phase.txt`
- GREEN new: 24 tests OK; full suite 85 tests OK (`artifacts/green-core-two-phase.txt`, `green-core-two-full-suite.txt`)
- No original LG archives read, parsed, or hash-rechecked
- Chromium/all-three PARTIAL at 200000 members remains recorded and was not retried
- Versioned review package: `tooling/review/targeted-core-two-2026-11-08/`
- Next: parent independent review, then a later inspection handoff if granted
- Not established: BSP, boot route, recovery, installable OS
