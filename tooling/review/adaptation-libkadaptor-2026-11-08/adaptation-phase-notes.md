# Adaptation phase implementation notes

Created:

- `tooling/adaptation_libkadaptor_phase.py`: pinned libkadaptor streaming copy, staged rehash, one inner inventory, hardware API/text evidence, shared budgets/deadline, and failed indices.
- `tooling/isolate_adaptation_phase.py`: timeout/prlimit/bwrap launcher with explicit input/output/module binds, held O_NOFOLLOW input descriptors, and synthetic-spec-only fixture overrides.
- `tooling/tests/test_adaptation_libkadaptor_phase.py`: 54 synthetic tests.
- `tooling/artifacts/red-adaptation-phase.txt`
- `tooling/artifacts/green-adaptation-phase.txt`
- `tooling/artifacts/green-adaptation-full-suite.txt`
- This note.

TDD command (initial temporary stub, before implementation):

```text
python3 -m unittest /workspace/lg-tv/tooling/tests/test_adaptation_libkadaptor_phase.py -v
Ran 49 tests in 0.153s
FAILED (failures=51, errors=13)
```

The saved red output includes assertion failures for missing behavior, not just import failures. Five additional failure-index regression tests were added during implementation; the two requiring further fixes were first observed failing with assertions.

Final new-test command:

```text
python3 -m unittest /workspace/lg-tv/tooling/tests/test_adaptation_libkadaptor_phase.py -v
Ran 54 tests in 0.269s
OK
```

Full-suite command:

```text
python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
Ran 139 tests in 0.594s
OK
```

The 85 prior tests passed unchanged. SHA256 checks before and after confirm all seven protected files remained identical. The reviewed plan was read and left unchanged.

Residuals: production archives were never opened, parsed, or hashed; production behavior has only synthetic validation. The current process sandbox blocked bwrap NETLINK_ROUTE creation, so the final test commands ran with approved sandbox escalation while retaining every launcher isolation flag; actual bwrap integration passed. Extended-header parser allocations remain subject to the AS/wall backstop. Failed diagnostic indices are best effort when output permissions, collisions, disk exhaustion, or an external hard kill prevent persistence; `phase-failed.json` is the fallback when the primary index is unusable. Disk checks are observations, not reservations; payload writes stop on reserve failure. `noexec_output_demonstrated` is false.

No TV actions, builds, installs, git operations, Page edits, production inspection, or review package creation were performed.
