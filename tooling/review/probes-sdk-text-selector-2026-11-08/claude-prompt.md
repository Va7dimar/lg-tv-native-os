Read-only SPEC+QUALITY independent review of optional SDK plaintext selector support.

Do NOT access/hash/parse anything under /workspace/lg-tv/sdk-candidates/. Do NOT edit files or execute isolate_sdk_inventory.py / any production inventory command. Do not work around permission-denied reads; note them and continue.

Previous reviews are IMMUTABLE:
- tooling/review/sdk-inventory-independent-review.md
- tooling/review/sdk-fd-fix-independent-review.md
- tooling/review/sdk-stdio-fix-independent-review.md
- tooling/review/sdk-utf8-fix-independent-review.md
- tooling/review/sdk-link-metadata-independent-review.md

Start with package /workspace/lg-tv/tooling/review/sdk-text-selector-2026-11-08/ : contract.md, report.md, HOST-VERIFICATION-ADDENDUM.md, exact-command.txt, diffs/, live
/workspace/lg-tv/tooling/sdk_inventory_phase.py SHA256 77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf
/workspace/lg-tv/tooling/isolate_sdk_inventory.py SHA256 c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a
tests: tooling/tests/test_sdk_text_selector.py SHA256 537c33d6b8783b44e906abe5c3e071ffae4b3f4c60ed8cc5e0c6dc7a2860355b
exact-command.txt SHA256 4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7

Verify: literal-only selectors; 10 indexed files summing to 50478 bytes with matching shared bound; per-file 16MiB and combined 64MiB caps; NUL/binary/nonprintable rejection; no symlink following; output writes use generated selected-NNNNNN.txt via exclusive/nofollow 0600, never member names; launcher changes do not regress FD cleanup or stdin=DEVNULL; default remains METADATAONLY; proposed command uses fresh inspection-selected-text-PENDING-REVIEW and same caps, and must not be executed.

Output:
### Claude model/effort actually used
### Strengths (file:line)
### Issues (Critical/Important/Minor)
### Residuals
### SPEC: PASS or FAIL
### QUALITY: PASS or FAIL
### Must-fix if any (location, repro, expected outcome)
### Accessed sdk-candidates contents? (must be no)
