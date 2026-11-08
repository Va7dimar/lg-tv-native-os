# SDK launcher FD containment fix — 2026-11-08

Implemented for parent host verification and independent re-review. The V1 independent verdict remains SPEC FAIL / QUALITY PASS; this implementation does not issue a replacement independent verdict. The exact production command remains unchanged and **UNEXECUTED**.

Only the live launcher and FD regression module changed. Whole current copies of the launcher, unchanged reader, unchanged original 27-test module, and updated FD regression module are in `current/`. `05-launcher-vs-V1.diff` is the complete production delta: one bootstrap hunk, 20 added lines replacing one line. `06-current-file-hashes.json` records live-file SHA-256 values. No decoder/parser, cap, symlink policy, CLI, bind command, parent descriptor lifecycle, other tool, libkadaptor, or CORETWO change.

## Change and descriptor lifecycle

The parent still holds nofollow input descriptors and its output-directory descriptor through bwrap bind setup and retains its existing post-worker checks and closure. After bwrap has established the mounts, the trusted Python bootstrap enumerates `/proc/self/fd`, closes every descriptor above stderr, and enumerates again to verify none remains open. Enumeration covers arbitrary descriptor numbers, including inherited FDs above the lowered RLIMIT_NOFILE; there is no fixed 3–64 range or limit-based bound. Only EBADF is tolerated, including the already-closed transient directory-enumeration descriptor. Enumeration errors, other close/fstat errors, or surviving descriptors terminate bootstrap before reader import.

The reader is imported only after that verification. Its existing `directory_fd('/output')` then opens output afresh through the sandbox mount. Input and output descriptors subsequently opened through sandbox paths are legitimate and expected. The fix removes inherited host capabilities; it does not claim the running inventory has no open descriptors.

## Test evidence and matrix

All fixtures and probes are synthetic. No real archive/SDK asset or source-catalog content was accessed or hashed. No production command, installer/source/compiler, build, download, TV action, external provider, or independent cross-review was run.

| Requirement | Evidence | Actual result here |
| --- | --- | --- |
| V1 normal and high inherited descriptors leak | Preserved `02-host-focused-RED.txt` and `red-evidence/` | Parent's actual host run: 2 tests, 2 expected assertion failures; host parent reached and inherited inputs reopened writable |
| New behavior tests precede production edit | `03-nested-expanded-RED.txt` | 7 tests: 5 expected assertion failures, 2 blocked skips, test process exit 1 |
| Close ordinary inherited descriptor before reader import | Bare-bootstrap regression | PASS; fstat returns EBADF before audit opens anything |
| Close FD 256 despite child soft/hard nofile 64 | Bare-bootstrap regression | PASS; fstat returns EBADF |
| Close failure, enumeration failure, incomplete cleanup stop before reader import | Three bare-bootstrap fault-injection regressions | PASS; reader audit is never reached |
| Actual bwrap boundary, normal and high FDs 256/257 | Two host-boundary regressions | BLOCKED here: bwrap NETLINK_ROUTE EPERM; no post-fix host success claim |
| Inherited set empty; inherited numbers EBADF before new opens; no host parent walk or writable inherited reopen | Expanded host-boundary audit | Assertions retained/extended; blocked here, requires parent host run |
| Fresh `/output` parent cannot reach host marker; fresh RO input descriptors cannot reopen writable through procfd | Expanded host-boundary audit | Assertions added; blocked here, requires parent host run |
| Successful full three-synthetic-input isolation, readonly paths, hidden home | Existing integration + host-boundary tests | 3 integration tests blocked here; requires parent host run |
| Targeted SDK suite | `04-nested-targeted-GREEN.txt` | **34 total, 31 PASS, 3 blocked skips, 0 failures/errors; test process exit 0** |
| Reader unchanged | Live hash and byte comparison with preserved V1 | PASS, SHA-256 below |

The expanded host-only assertions have not independently been observed RED here because bwrap cannot start. Existing host RED proves the original boundary defect; the five new bare-bootstrap tests were observed failing against unchanged V1 before the production edit. Bare-bootstrap tests insert an audit/exit exactly before reader import and do not establish sandbox containment or run an unsandboxed inventory. No permissions or isolation flags were weakened to overcome the blocker.

Exact final targeted test argv:

```
python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v
```

Parent can run that unchanged test command in the ordinary actual host runtime. Setting `SDK_FD_TEST_EVIDENCE_DIR` to a new directory under this fix package also preserves normal/high synthetic audit JSON. Actual host verification and independent review of the new launcher hash remain required before any production handoff. This agent did not invoke an outside-host execution route.

## Current hashes

```
35b6dd2c2187df8e6e9a5774befa63f2217e89b62c3f149747815d1952084771  tooling/isolate_sdk_inventory.py
c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f  tooling/sdk_inventory_phase.py
f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10  tooling/tests/test_sdk_fd_boundary.py
aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0  tooling/tests/test_sdk_inventory_phase.py
```

Preserved V1 launcher: `488e34d3470403206c0974cc82cdd36f7a6078619aaabf0bda390e3ea040f7f0`. Current reader is byte-identical to V1. Existing RED/V1/review artifacts and the earlier 34-entry review package were not modified; the earlier package was not re-read or reverified outside this task's read allowlist. The existing implementation report was left intact; this is the new fix report.

## Remaining limits

- New launcher hash requires parent independent re-review and successful ordinary-host synthetic isolation proof. Nested skipped tests are not host passes.
- Cleanup depends on the already-mounted `/proc/self/fd`; inability to enumerate or complete cleanup fails closed. It runs before reader imports in the trusted single-threaded bootstrap.
- XZ CHECK_NONE can still be labelled integrity EOF; full-file pin behavior is unchanged. Absolute sysroot symlink targets still fail closed. Both are outside this FD fix.
- All existing runtime ceilings, noexec=false, address-space rather than RSS enforcement, observed rather than reserved disk floor, conservative metadata charging, and other previously recorded parser/runtime limits remain unchanged.
- No actual SDK full hash or production preflight was performed. Future approved real-phase checks remain the parent's responsibility; the production command and output path were not executed or created here.
