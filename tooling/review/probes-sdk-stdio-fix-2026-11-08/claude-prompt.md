Read-only SPEC+QUALITY re-review of a narrow SDK launcher stdio-hardening fix.

Do NOT access/hash/parse anything under /workspace/lg-tv/sdk-candidates/. Do NOT edit files or run the production inventory command. Do not work around permission-denied reads; note them and continue.

Previous reviews are IMMUTABLE:
- tooling/review/sdk-inventory-independent-review.md : V1 SPEC FAIL (inherited fds)
- tooling/review/sdk-fd-fix-independent-review.md : FD>=3 fix SPEC PASS with closed-stdin fd0 alias caveat

Start with:
/workspace/lg-tv/tooling/review/sdk-stdio-fix-2026-11-08/10-HOST-VERIFICATION-ADDENDUM.md
Also read 04-isolate_sdk_inventory.py.diff, 07-IMPLEMENTATION-REPORT.md, live
/workspace/lg-tv/tooling/isolate_sdk_inventory.py
Expected SHA256: 2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52
Reader must remain c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f
New tests: /workspace/lg-tv/tooling/tests/test_sdk_stdio_boundary.py
Expected SHA256: 15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065

The fix should: _normalize_stdio() fill closed fds 0-2 with /dev/null BEFORE fresh_output/open_regular; subprocess.run stdin=DEVNULL; existing >=3 /proc cleanup unchanged. Seven closed-stdio masks (1-7).

Output:
### Claude model/effort actually used
### Strengths (file:line)
### Issues (Critical/Important/Minor)
### Residuals
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Must-fix if any (location, repro, expected outcome)
### Accessed sdk-candidates contents? (must be no)
