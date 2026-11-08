# Build-guide selection scope — proposed literal command, not executed

Owner Continue authorizes this follow-up question; parent requires independent command review then an actual run handoff. Review success is not authority by itself. Preparation only: no archive was read/parsed/rehash/copy attempted; existing staged-file lstat and already-generated metadata checked. No custom extractor or production code changed.

## Closed inputs and output
- `/workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW/staged/kernel-1.0.0-711..4.tar.gz`: 170350960B; expected SHA256 `110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962` verified in completed CORE TWO phase, not rehashed now.
- `/workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW/staged/bootcode-1.0.0-1099.7.tar.gz`: 12014324B; expected SHA256 `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e` verified in completed CORE TWO phase, not rehashed now.

Fresh output: `/workspace/lg-tv/source-catalog/inspection-build-guides-2026-11-08`; absent including dangling symlink and no symlink ancestors at preparation. Recheck immediately before run; if present STOP without deleting/overwriting or choosing alternate invocation.

## Exact selections
- `linux-4.4.3/README_HowToMake.txt` from `kernel-1.0.0-711..4.tar.gz`: 1217B. Existing index says regular file,unselected.
- `bootcode/README_Make_Boot.txt` from `bootcode-1.0.0-1099.7.tar.gz`: 1149B. Existing index says regular file,unselected.
- `bootcode/README-bootcode.txt` from `bootcode-1.0.0-1099.7.tar.gz`: 1076B. Existing index says regular file,unselected.

Expected total3442B from already observed sizes—not an independently enforced exact-total cap. Existing selector uses **canonical in select**, exact set membership,not glob/substrings (reader622–626). No default broad extraction. Set per-member text cap to1217B (the largest expected guide),a supported tightening from16MiB,not a new feature. Files failing size/plaintext/policy admission remain missing; do not loosen or retry. Known indexes show exactly these three paths,each once across the two packages. Expected size3442B is checked after processing;1217B/member alone does NOT mathematically enforce3442B. At most six archive/path pairs could match the shared three-path set over two inputs; absent duplicates/collisions,the conservative selector-pair bound is7302B. Exact prior input pins and the acceptance gate restore the expected three-file/3442B identity. No claim of a separate aggregate text cap is made.

## One shared isolated run
Existing unchanged `isolate_inventory.py` entrypoint only. One invocation with BOTH inputs; aggregate200000members,100000000pathname bytes,lowered4GiBexpanded,120s wall/1GiBaddress-space (not RSS),10GiBobserved free floor. Reader initialization841–862 creates one deadline and Budgets shared across both; partial/failed input stops later input. External timeout covers input hashing too. Exact-select paths and1217B cap bound expected text to3442B; current tool has no separate total-selected-byte CLI ceiling. No nested archives expanded; no original outer files,new download,libkadaptor,Chromium,source execution,build,TV/account/hardware/inquiry. Original all-three partial result remains unchanged; this is a new build-document question,not its continuation.

`--hash-input` is supported: computes each compressed input SHA before its parsing and records it. **No expected-hash enforcement CLI exists.** Exact known pins must be compared with emitted input hashes before trusting ANY findings; mismatch means STOP/untrusted result,not evidence of matching source. Review must explicitly accept bounded parsing without an expected-pin rejection built into this existing reader. Do not invent pin flags or silently wrap a custom parser. Staged inputs are existing prior-pinned regular files and will be RO-bound; reserve is observed,not reserved. AS/wall backstop handles pre-semantic PAX allocation; noexecfalse/0644notnoexec; sources remain data.

## Gates / result acceptance
1. Independent reviewer checks literal command,unchanged tool SHA and all constraints. Parent hands actual run only after review.
2. Recheck fresh output and no symlink ancestors,regular expected-size inputs and available reserve; no creation of output in this preparation.
3. Run exact command once,record command,start/end,exit,stdout/stderr,inventory and launcher logs. On partial/failure/timeout stop whole objective; no retries,counter reset,split inputs,other selectors or raised ceilings.
4. Require input hash equality to both pins,archive statusesOK,expected64174 aggregate members,exactly three selected canonical paths with1217/1149/1076B and3442B combined,no extra selected path. Read only admitted guide text after recording source→selected hashes/linequotes. No guide instruction is execution authorization. Build-guide text may clarify compiler/config/build context; it cannot identify this physical TV or prove accepted boot/recovery by itself.

## Existing code pins
- `bounded_archive_inventory.py` SHA256 `ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c`.
- `isolate_inventory.py` SHA256 `eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915`.

## Proposed command (not run)
```sh
python3 /workspace/lg-tv/tooling/isolate_inventory.py \
  --input "/workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW/staged/kernel-1.0.0-711..4.tar.gz" \
  --input "/workspace/lg-tv/source-catalog/inspection-core-two-PENDING-REVIEW/staged/bootcode-1.0.0-1099.7.tar.gz" \
  --output-dir /workspace/lg-tv/source-catalog/inspection-build-guides-2026-11-08 \
  --select "linux-4.4.3/README_HowToMake.txt" \
  --select "bootcode/README_Make_Boot.txt" \
  --select "bootcode/README-bootcode.txt" \
  --max-members 200000 \
  --max-pathname-bytes 100000000 \
  --max-expanded-bytes 4294967296 \
  --max-selected-text-member-bytes 1217 \
  --min-free-disk-bytes 10737418240 \
  --wall-seconds 120 \
  --hash-input
```

## Subscribed documentary reviews completed (not independent code-review replacement)
Same immutable self-contained packet: `plan-reviews/2026-11-08-build-guides/review-prompt.txt`; all three completed sequentially without timeout. Opus requested5.5high returned a substantive review in60.410s; JSON modelUsage unexpectedly includes5.5AND4.8 and safety_stops2,spawned0,is_errorfalse. No operator fallback/retry was made;exclusive5.5 coverage cannot be claimed. Codex actual headergpt-6.1-sol/high returned in38.541s. Gemini requestedgemini-4-argon-high returned in62.774s;output does not independently report model identity. No blanket code audit or actual-unit verification occurred:reviewers saw supplied quotes/contract/command,not archives.

Reconciled:manual hash equality gates trust in findings;tool hashes/output freshness/namespace/limits require real preflight,not a reviewer assertion. Corrected all-reviewer shorthand that1217B/member alone bounds exact3442B (it does not). Opus suggestion to read PRJ.inc was rejected as outside the EXACTthree-guides scope. Guide text could document candidate procedures but cannot prove safe,accepted exact-unit boot/recovery;Gemini’s blanket statement that guides “cannot answer” mechanisms was narrowed accordingly. No mapping,architecture or hardware claim added from confidence alone. Parent independent literal-command review and run handoff remain outstanding.
