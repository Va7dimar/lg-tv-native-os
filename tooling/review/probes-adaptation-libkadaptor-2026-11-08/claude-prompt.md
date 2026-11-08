You are performing a read-only SPEC + QUALITY code review of a local non-repo archive adaptation tool.

Do NOT access, hash, or parse any file under /workspace/lg-tv/source-catalog/archives/ or any file named like "webOS 6.0 KLP_1.0_*.tar.gz" on disk. Do NOT edit any files. Do NOT run network commands. Do NOT propose TV/flash/install actions. Synthetic reasoning only.

Read these files and review the implementation against the contract:

CONTRACT:
/workspace/lg-tv/docs/superpowers/plans/2026-11-08-adaptation-libkadaptor-phase.md

READER:
/workspace/lg-tv/tooling/adaptation_libkadaptor_phase.py
Expected SHA256: 7884236467e1533de7e3ac1266c602845cee35f4acbda11612d7e01dd36842c2

LAUNCHER:
/workspace/lg-tv/tooling/isolate_adaptation_phase.py
Expected SHA256: 192dce045e47c30379e35e66584f6d21b584ecf6418a9729d1d334777730e55b

TESTS (for understanding intended behavior; do not require rerunning the whole suite):
/workspace/lg-tv/tooling/tests/test_adaptation_libkadaptor_phase.py

Planned production command (DO NOT EXECUTE):
python3 /workspace/lg-tv/tooling/isolate_adaptation_phase.py \
  --outer "/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-adaptation-PENDING-REVIEW

Verify these requirements and report evidence with file:line references:

1. Hash/size of outer file verified BEFORE any tar parse.
2. Only member soc/libkadaptor-1.0.0-908.3.tar.gz (123840909 bytes, SHA256 46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25) may be copied.
3. Staged file re-hashed BEFORE one inner inventory.
4. Exact pins: production CLI and synthetic test mode cannot retarget a different package. Synthetic mode may only supply fixture hashes/sizes for the same pinned member name.
5. Unclaimed payloads discarded in bounded chunks (not fully buffered).
6. Shared whole-phase budgets: 120s wall, 1GiB AS, 200000 members, 100000000 pathname bytes, 4GiB charged expanded (outer logical regular + staged copy + inner logical + selected copies), 640MiB outer logical regular-only, 128MiB binary each and combined, 1GiB admitted compressed (outer file + copied target), 16MiB/64MiB plaintext, 10GiB disk floor (observed, not reserved).
7. Path/link/type/duplicate/sparse policy; PAX/GNU allocation inside tarfile.next() acknowledged with isolation AS/wall as backstop.
8. Stop entire phase on partial/fail; never ok=true then.
9. Fresh output required; output index collision marks failed. Known behavior: collision then overwrites old index — judge impact for the exact fresh command vs general quality. Record as important if true, not automatically deployment-unsafe for a fresh output dir.
10. Symlink containment; no /home /root /cursor /network in launcher.
11. No deeper nested expansion; no member execution.
12. Selection: README/build/config/license/manifest + conservative hardware headers.
13. noexec remains false; AS is VSZ not RSS; disk observed; outer_decoded is regular logical sizes not full tar stream. These are honest residuals, not automatic must-fixes.
14. Hard ceilings cannot be raised by CLI.

Output format:
### Claude model/effort you actually used
### Strengths (with paths:lines)
### Issues
#### Critical
#### Important
#### Minor
For each issue: file:line, what, why, minimal fix.
### Residuals (honest limitations)
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Checkpoint for the exact planned command: YES or NO, and conditions
### Whether you executed anything against catalog archives (must be no)
