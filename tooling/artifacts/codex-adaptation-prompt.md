You are implementing a new NARROW hardware-adaptation phase for an existing non-repo local Python tooling tree at /workspace/lg-tv/tooling. The user authorized local tooling edits. Do NOT use --dangerously-skip-permissions or any security/usage evasion.

Do not read, parse, hash, or open any original LG catalog archives (nothing under source-catalog/archives/, no filenames beginning with "webOS 6.0 KLP"). Synthetic fixtures only. No TV actions, no builds, no package installs, no git, no Page edits.

Already written (do not rewrite into a weaker contract): /workspace/lg-tv/docs/superpowers/plans/2026-11-08-adaptation-libkadaptor-phase.md

DO NOT modify these reviewed files (their hashes must stay identical):
- tooling/bounded_archive_inventory.py
- tooling/isolate_inventory.py
- tooling/targeted_core_two_phase.py
- tooling/isolate_targeted_phase.py
- tooling/tests/test_bounded_archive_inventory.py
- tooling/tests/test_review_regressions.py
- tooling/tests/test_targeted_core_two_phase.py

Reuse policy/isolation helpers from bounded_archive_inventory.py (canonicalize_member_path, classify_link_target, logical_member_size, open_untrusted_tar_gz, open_regular_nofollow, contained_path, atomic_write_bytes, isolation_observation, member_kind, metadata_byte_cost, is_nested_archive_name, _write_selected_file). You may import them. Do NOT copy-paste the whole CORE TWO phase into a generic framework. Do NOT import targeted_core_two_phase if that would force the isolate launcher to bind extra modules; prefer using only bounded_archive_inventory helpers plus new focused code.

Create:
- tooling/adaptation_libkadaptor_phase.py
- tooling/isolate_adaptation_phase.py
- tooling/tests/test_adaptation_libkadaptor_phase.py

Pinned production constants (hardcoded; CLI without synthetic mode cannot swap them):
- OUTER name webOS 6.0 KLP_1.0_2.tar.gz, 511945894 bytes, SHA256 95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832
- TARGET member EXACTLY soc/libkadaptor-1.0.0-908.3.tar.gz, 123840909 bytes, SHA256 46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25
- Do not copy kernel, bootcode, Chromium, or any other package.

Hard ceilings (PhaseLimits; cannot raise; tests may lower via PhaseLimits.for_tests like the existing reader). Do not soften:
- wall 120s TOTAL shared (hash+copy+inner), no per-package reset
- AS 1GiB
- members 200000 shared
- pathname/metadata 100000000 shared
- phase expanded+materialized 4GiB = outer logical regular payload + staged copy bytes + inner logical + selected copies (double-charge copies)
- outer compressed <= 512MiB (536870912)
- outer decoded = SUM of logical sizes of regular FILE members only (NOT tar headers, directories, or metadata members). Cap 640MiB (671088640)
- target copy <= 128MiB (134217728); total materialized binary <= 128MiB
- admitted compressed = outer file bytes + copied target bytes <= 1GiB
- selected text 16MiB each, 64MiB combined
- disk >= 10GiB observed before phase and before writes; not a reservation
- one inner level only; nested archives inside are listed/metadata-only, never expanded

Mechanism:
1. Disk check; open outer O_NOFOLLOW; verify size+sha256 BEFORE tar parse.
2. Forward-read with existing path/link/type/duplicate policy; fail-closed.
3. Stream-copy ONLY the pinned member to staged/<basename> while hashing (NUL allowed in binary copy). Do NOT buffer the whole member or unclaimed payloads in memory; discard unclaimed member data in chunks.
4. Verify copied size+hash. Re-hash staged file BEFORE any inner inventory.
5. One inner inventory; select NUL-free evidence: README/build/config/license/manifest PLUS hardware API headers (e.g. .h/.hpp under include/api/hardware/adaptor/hal/kadaptor or names containing api). Never execute scripts. Mode 0644. Do not claim noexec mount (noexec_output_demonstrated=false).
6. Collision/path errors (existing phase.json/phase.md, write escape, OSError) become document status=failed, ok=false — catch them honestly, do not crash without a failed index when possible.
7. Stop on failed/partial/timeout; never mark ok=true then.
8. Shared budgets and a single deadline; do not reset when starting the inner package.

CLI:
- Production: python3 adaptation_libkadaptor_phase.py --outer PATH --output-dir DIR
  (and isolate_adaptation_phase.py with the same two flags)
- Pins are hardcoded. No --expected-outer-sha256 / --test-target / --allow-test-spec flags that can swap production pins.
- Optional explicit isolated synthetic mode ONLY: --synthetic-fixture-mode SPEC.json
  SPEC may provide outer_bytes, outer_sha256, target_size, target_sha256 for the SAME pinned member name soc/libkadaptor-1.0.0-908.3.tar.gz and a synthetic outer file. If SPEC tries to change the member path, fail closed. Production proposed command must never include this flag.
- CLI cannot lower the 10GiB disk floor except via PhaseLimits.for_tests in-process.

Isolation launcher: timeout --kill-after=5s, prlimit --as/--cpu/--core=0/--nofile=64, bwrap --unshare-all --die-with-parent --new-session --clearenv, ro-bind /usr + merged-usr symlinks, bind only the explicit outer file and writable output, ro-bind this new module AND bounded_archive_inventory.py, PYTHONPATH=/tool, no /home /root /cursor, no --share-net. Reject symlink outer inputs (O_NOFOLLOW). Do not claim noexec.

TDD (mandatory):
1. Write tests first (synthetic fixtures using the exact pinned member name with small payloads).
2. If you need a stub so failures are assertion failures (not just ImportError), do that.
3. Run: python3 -m unittest /workspace/lg-tv/tooling/tests/test_adaptation_libkadaptor_phase.py -v
   Save full output to /workspace/lg-tv/tooling/artifacts/red-adaptation-phase.txt (must show assertion FAILs for missing behavior).
4. Implement until tests pass.
5. Save green new tests to /workspace/lg-tv/tooling/artifacts/green-adaptation-phase.txt
6. Run full suite: python3 -m unittest discover -s /workspace/lg-tv/tooling/tests -v
   Save to /workspace/lg-tv/tooling/artifacts/green-adaptation-full-suite.txt
   All old tests must still pass (expect 85 prior + your new ones).

Required tests: exact copy of pinned member; NUL allowed only in binary; unallowlisted kernel/bootcode/other not copied; oversize binary; wrong hash/size; missing target; symlink/type; duplicates; path traversal; nested inner archive not expanded; combined/shared budgets (members, pathname, outer decoded regular-only, phase expanded, binary 128MiB, admitted compressed); sparse logical size if practical; global deadline not reset; disk reserve failure; output collision => failed status; isolation command shape; isolation integration using --synthetic-fixture-mode only; evidence names including a hardware API header; limits cannot be raised; production CLI cannot swap pins; controls document noexec false, isolation required, parser allocation backstop, disk observation, outer_decoded_regular_files_only.

Do NOT run any command against real catalog archives after green. Do not write a Page. Do not create a review package directory unless asked; I will package after verifying.

Write a short note to /workspace/lg-tv/tooling/adaptation-phase-notes.md with: files created, test commands and result lines (Ran N / OK or FAILED), any residuals.

When done, print a brief summary of tests and file paths.
