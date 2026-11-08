Read-only SPEC+QUALITY independent review of a narrow SDK reader UTF-8 boundary fix.

Do NOT access/hash/parse anything under /workspace/lg-tv/sdk-candidates/. Do NOT edit files or run any production inventory command. Do not work around permission-denied reads; note them and continue.

Previous reviews are IMMUTABLE and must not be rewritten:
- tooling/review/sdk-inventory-independent-review.md (V1 SPEC FAIL, inherited fds)
- tooling/review/sdk-fd-fix-independent-review.md (FD>=3 PASS, closed-stdin caveat)
- tooling/review/sdk-stdio-fix-independent-review.md (stdio PASS)

Start with:
/workspace/lg-tv/tooling/review/sdk-utf8-fix-2026-11-08/package/HOST-VERIFICATION-ADDENDUM.md
Also read package/review-packet.md, ../contract.md, package/change.diff, live
/workspace/lg-tv/tooling/sdk_inventory_phase.py
Expected reader SHA256: e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4
Launcher must remain: 2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52
New tests: /workspace/lg-tv/tooling/tests/test_sdk_utf8_boundary.py
Expected SHA256: 746defc12bdcfa73f211eaad30ba8e349bb70eda8a40e9ed5bbb9ab12a4c3d58

Fix intent: GNU fixed name/link fields may end mid-UTF-8 (e.g. 99 ASCII + 0xc4) before maintained GNU/PAX substitution. Transient raw name/link decode/charge may use surrogateescape; extension bodies, raw owners, and FINAL resolved names/links/owners/PAX metadata must stay strict UTF-8. No weakening of traversal/absolute/escaping-link/duplicate/device/sparse/pin/EOF/drain/cap/fd/stdio/XZ policies. No custom tar header parser.

Output:
### Claude model/effort actually used
### Strengths (file:line)
### Issues (Critical/Important/Minor)
### Residuals
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Must-fix if any (location, repro, expected outcome)
### Accessed sdk-candidates contents? (must be no)
