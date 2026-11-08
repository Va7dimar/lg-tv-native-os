# Narrow stdio FD fix — implementation record

Date: 2026-11-08 UTC. Local NONREPO tooling; existing owner authorization t71–74, no owner checkpoint. Requested PRIMARY subscribed Codex gpt-6.1-sol/high. This session supplies no independent runtime attestation of the exact serving model, effort, or subscription billing route; no other provider or agent was invoked.

## Change and invariants

Launcher SHA256: `2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52`.

`_normalize_stdio()` fills absent 0–2 with `/dev/null` before `fresh_output` or input opens. Only `fstat` EBADF triggers replacement; other errors propagate. `open`/`dup2` errors propagate before held host descriptors are allocated. If open returns the normalized slot, it stays open; otherwise the temporary descriptor is closed after dup2. Existing open stdio slots remain open. Worker spawn explicitly uses `stdin=subprocess.DEVNULL`; stdout/stderr are the intended worker log files. Host input/output-directory descriptors therefore allocate above stdio, avoiding procfd sources being redirected to DEVNULL or logs during spawn. The generated bind source numbers are >=3 for every nested mask attempt (06-FIX-MATRIX.json); worker reachability is still host-unverified.

The bootstrap function is AST-identical to before: all >=3 descriptors, including above the lowered nofile ceiling, are closed and fully verified before reader import. Resource ceilings, pin logic, command construction, CLI, parser, symlink/XZ policies, and binds are unchanged. No low-FD rejection or other additional production behavior was introduced.

Only production edit: `tooling/isolate_sdk_inventory.py`. Only test edit: the new `tooling/tests/test_sdk_stdio_boundary.py` skip now explicitly requires NETLINK_ROUTE plus EPERM/Operation not permitted. Genuine bind errors remain failures. Existing two test modules and reader remain byte-identical to the recorded baseline. Normalization's intended context is launch before any held descriptor allocation; no concurrent descriptor-closing thread guarantees are added.

## TDD and actual execution

Before any production edit, the orchestrator recorded:

- `01-HOST-RED.txt`: historical generic isolation skip mistakenly hid genuine bind errors. Preserved unchanged; not relabelled.
- `02-HOST-FOCUSED-RED.txt`: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk_stdio_boundary.py' -v`, exit 1; 1 method / 7 closed-stdio subtests, 7 assertion failures, no import failures. Preserved unchanged.
- `red-evidence/mask-1.json`: pre-import fd 0 absent, not a writable input reopen. Other stdin-open masks show a pipe. Masks with output-directory aliasing fail bwrap binds. This harness does not reproduce the exact writable-reopen result from the separate independent probe.

After this fix, the only test execution here was:

```sh
SDK_STDIO_TEST_EVIDENCE_DIR=tooling/review/sdk-stdio-fix-2026-11-08/nested-evidence SDK_FD_TEST_EVIDENCE_DIR=tooling/review/sdk-stdio-fix-2026-11-08/nested-fd-evidence python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v
```

Exit 0; 35 methods, 1.205 seconds, no failures/errors, `OK (skipped=10)`: 31 methods complete without skips, 3 whole-test skips, and 7 subtest skips in the new method. See `03-NESTED-TARGETED.txt` and command metadata. All isolation skips observed here are bwrap NETLINK_ROUTE socket EPERM. Existing read-only tests retain their original skip code. No skip policy was weakened or sandbox evaded.

The bare high-FD cleanup and fail-closed bootstrap checks passed; sandbox high-256/257 containment and the synthetic full-path isolation test were blocked. All seven real-launch closed-stdio attempts have JSON captures with audit=null because bwrap was denied before the worker. `06-FIX-MATRIX.json` records masks 1–7, their original RED audits, current bind fd numbers, and blocked status. No host GREEN or independent verdict is claimed. The orchestrator's authorized ordinary-host rerun and independent re-review of this new hash remain pending; production execution remains pending review.

## Preserved review context and scope

The original independent >=3 fix SPEC/QUALITY PASS for launcher `35b6dd2c2187df8e6e9a5774befa63f2217e89b62c3f149747815d1952084771` remains valid for that reviewed defect, with its closed-stdin caveat. The historical v1 `488e34d3…f7f0` SPEC FAIL / QUALITY PASS context remains unchanged. This implementation record is not an independent review.

The allowlisted independent probe `probes-sdk-fd-fix-2026-11-08/probe-closed-stdin-fd0.json` separately shows an actual synthetic input alias on fd 0 with writable=true. Its contents were read; no actual SDK/archive asset was opened, hashed, or parsed. No sdk-candidates/source-catalog directory was searched. No production inventory command, source, installer, compiler/build, TV action, download, or install was executed. Test fixtures are synthetic only.

## Evidence

`before/` keeps the reviewed launcher and reader, plus a snapshot of the new test before this skip-only tightening. `current/` contains whole copies of all five allowlisted code/test files. `04-*.diff` are exact unified diffs against available before copies (reader diff empty). `05-CODE-SHA256SUMS.txt` lists current live code hashes; `08-EVIDENCE-SHA256SUMS.txt` covers these fixed evidence artifacts, snapshots, and preserved REDs, excluding active orchestrator capture files and itself.

Reader remains `c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f`; existing tests remain `aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0` and `f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10`. New regression test is `15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065`.
