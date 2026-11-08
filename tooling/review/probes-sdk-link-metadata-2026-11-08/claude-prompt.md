Read-only SPEC+QUALITY independent review of a deliberate SDK reader metadata-only symlink-policy candidate.

Do NOT access/hash/parse anything under /workspace/lg-tv/sdk-candidates/. Do NOT edit files or run any production inventory command. Do not work around permission-denied reads; note them and continue.

Previous reviews are IMMUTABLE:
- tooling/review/sdk-inventory-independent-review.md
- tooling/review/sdk-fd-fix-independent-review.md
- tooling/review/sdk-stdio-fix-independent-review.md
- tooling/review/sdk-utf8-fix-independent-review.md

Start with:
/workspace/lg-tv/tooling/review/sdk-link-metadata-2026-11-08/HOST-VERIFICATION-ADDENDUM.md
Also read contract.md, report.md, diffs/sdk_inventory_phase.py.diff, live
/workspace/lg-tv/tooling/sdk_inventory_phase.py
Expected reader SHA256: cecbb2ac06755100d414852b91dccf8527b05321b34a96da3e0eda86b59c16c1
Launcher must remain: 2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52
New tests: tooling/tests/test_sdk_link_metadata.py SHA256 1c31fd5d2af306f54c050cc39b62077fb6c1f12ee2e6db536c54d27f79d8ee26

Policy: METADATAONLY may record absolute/out-of-tree SYMLINK targets as classified metadata (recorded_not_followed_nonextractable, extractable=false, selected=false) without following/resolving/opening/extracting. Hardlinks, traversal/absolute/drive/backslash member names, duplicates, types/sparse, UTF8, caps remain fail-closed. Diagnostics: max 4 rejected-link records; name/target JSON-ASCII prefixes <=512 bytes with original_bytes+truncated; rule <=160 chars; full strings still charged; error field must not interpolate unbounded names. link_safe remains strict nonreuse guard. Assertion changes in two existing tests must be justified by this policy only.

Output:
### Claude model/effort actually used
### Strengths (file:line)
### Issues (Critical/Important/Minor)
### Residuals
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Must-fix if any (location, repro, expected outcome)
### Accessed sdk-candidates contents? (must be no)
