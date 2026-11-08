# Tooling progress

Updated: 2026-11-08 04:51 Atlantic/Reykjavik

- Independent review failed SPEC/quality (`tooling/review/independent-review.md`); probes left in place
- Regression tests added first: 13 failed (12 fail + 1 error) in `artifacts/red-review-regressions.txt`
- Coherent fix landed for aggregate ceilings, fail-stop, symlink decision, parser-surfaced sparse, isolated entrypoint docs, disk CLI floor, stream=True, isolate symlink policy, selected namespacing, stdout JSON, unused hasher
- Green: 13/13 regressions OK; full suite `Ran 61 tests` `OK` (`artifacts/green-after-review-fixes.txt`)
- Catalog originals still not parsed
- Versioned fix package: `tooling/review/fix-2026-11-08/`
- Next: parent dispatches independent re-review before any catalog-archive parse
- Not established: BSP compatibility, boot route, recovery, installable OS
