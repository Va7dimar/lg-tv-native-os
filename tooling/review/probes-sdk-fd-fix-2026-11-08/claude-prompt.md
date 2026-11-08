You are performing a read-only SPEC + QUALITY re-review of a minimal launcher FD-containment fix.

Do NOT access, hash, open, or parse any file under /workspace/lg-tv/sdk-candidates/. Do NOT edit files. Do NOT run the production SDK inventory command. Do NOT run network commands or TV actions. Do not work around permission-denied reads; note them and continue with what you can read.

Previous independent review (IMMUTABLE, do not rewrite):
/workspace/lg-tv/tooling/review/sdk-inventory-independent-review.md
It was SPEC FAIL / QUALITY PASS due to inherited host fds (pass_fds) allowing openat parent walk and writable /proc/self/fd reopen. That FAIL evidence must stay recorded.

Start with:
/workspace/lg-tv/tooling/review/sdk-fd-fix-2026-11-08/09-HOST-VERIFICATION-ADDENDUM.md

Also read:
- /workspace/lg-tv/tooling/review/sdk-fd-fix-2026-11-08/05-launcher-vs-V1.diff
- /workspace/lg-tv/tooling/review/sdk-fd-fix-2026-11-08/07-FD-FIX-REPORT.md
- /workspace/lg-tv/tooling/isolate_sdk_inventory.py
  Expected SHA256: 35b6dd2c2187df8e6e9a5774befa63f2217e89b62c3f149747815d1952084771
- Confirm reader unchanged:
  /workspace/lg-tv/tooling/sdk_inventory_phase.py
  Expected SHA256: c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f
- /workspace/lg-tv/tooling/tests/test_sdk_fd_boundary.py
- host-green-evidence and red-evidence under the fix package if useful
- 02-host-focused-RED.txt and 08-HOST-GREEN.txt summaries

Expected launcher-only delta: bootstrap enumerates /proc/self/fd, closes every FD >= 3 (including numbers above RLIMIT_NOFILE 64), re-enumerates and fails closed if any survive, then imports the reader and opens /output freshly. No parser/policy/ceiling changes.

Verify with file:line evidence:
1. Normal inherited fds and high fds (e.g. 256/257) are closed before reader import.
2. No host parent escape via leftover dir fd; no writable reopen of inherited input fds.
3. Fresh sandbox-opened input/output fds are legitimate and cannot reach HOST_PARENT_SENTINEL; path RO and home hidden still hold.
4. Close/enumeration/survivor errors fail closed before reader import.
5. Reader/policies unchanged; original 27-test module hash unchanged.
6. Any remaining holes (TOCTOU, /proc assumptions, stdin/out kept, leftover leak).

Output format:
### Claude model/effort you actually used
### Strengths (paths:lines)
### Issues
#### Critical
#### Important
#### Minor
### Residuals
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Must-fix (if any): location, repro, expected minimal outcome
### Whether you accessed sdk-candidates asset contents (must be no)
