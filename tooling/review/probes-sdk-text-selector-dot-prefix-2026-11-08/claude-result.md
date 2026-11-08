# Independent review: SDK selected-plaintext `./` prefix fix

Reviewed 2026-11-08, reading files only. My two attempts to run synthetic code were not approved (details in the last section), so I ran no tests. The verdict rests on reading the code and the supplied logs.

## Verified hashes (`sha256sum` on the live files)

| File | SHA256 | Matches |
|---|---|---|
| `tooling/sdk_inventory_phase.py` (reader) | `3598007632b1c13790d16cad9f6a68c23e5f4b35a4996948a3917bef2d8f8168` | stated hash, `current/`, hashes.json, SHA256SUMS |
| `tooling/isolate_sdk_inventory.py` (launcher) | `c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a` | stated hash; `cmp` byte-identical to `before/` |
| `tooling/tests/test_sdk_text_selector.py` | `8b78078ef48c8cad3e0d9091c244336c8450cc74bb8c5d0e55ed8339f76d6681` | stated hash, `current/` |
| `exact-command.txt` (package copy and original) | `4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7` | identical, unchanged |
| `before/sdk_inventory_phase.py` | `77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf` | stated before-reader hash |
| `before/test_sdk_text_selector.py` | `537c33d6…355b` | prior review's test hash |
| Prior review `sdk-text-selector-independent-review.md` | `8740357586f1…5ece` | unchanged |

I diffed `before/` against `current/` directly. The reader changes in exactly one line (`:603`). The tests add one positive method and widen the negative cases. Nothing else changed.

## Verdict

| Gate | Result | Reason |
|---|---|---|
| **SPEC** | **PASS** | A member now matches only if its name is exactly the selector path or exactly `'./' + path`. Every other alias is still rejected, all previous safety checks are untouched, and the unchanged ten-selector command can now in principle succeed against the indexed member names. |
| **QUALITY** | **PASS** | It is a minimal one-line change that adds no normalization, follows no links, keeps the order of checks, and fails closed. |
| **Blocking must-fix** | **None** | |

### SPEC reasoning

**The accepted set is exactly two strings.**
- `select()` (`sdk_inventory_phase.py:598-621`) looks up the selector by `(input, canonical(member.name))`. It is only reached after `canonical()` has already rejected a leading `/`, `..`, backslashes, drive letters and NUL (`:361-369`, `:466`).
- Selector paths themselves must already be canonical (`validate_selectors`, `:60-63`). So the path has no empty, `.` or `..` parts, and `'./' + path` canonicalizes back to the same path.
- Any other raw name that canonicalizes to the selector differs from both accepted strings and fails with `selected member path alias`. Examples: `././a`, `.//a`, `./a/`, `d//a`, `d/./a`, and `a/` when it is a regular file.
- A directory entry such as `./a/` comes back from tarfile as `./a`, but it then fails `isreg()`. That is still fail-closed.

**Safety ordering is unchanged.** The name check still comes before the regular-file check, the exact-size check, the duplicate check, the shared cap, `extractfile`, the plaintext check, and the generated-name write.

**`a` and `./a` in the same archive can't both be selected.** They are rejected earlier as `duplicate canonical name` (`:469`), and the `found` set (`:609`) also guards against it.

**Everything else is preserved:**
- `raw_name` is still recorded verbatim.
- Output files are named `selected-NNNNNN.txt` and opened with `O_EXCL|O_NOFOLLOW`, mode 0600. Member names never become output paths.
- 16 MiB per member and 64 MiB shared caps.
- METADATAONLY is still the default.
- The launcher is unchanged, so FD cleanup and `stdin=DEVNULL` are unchanged.

**The command can now succeed on names and sizes.** I checked the prior metadata evidence `evidence/sdk-inventory-links-execution-2026-11-08/verified-metadata-leads.json`, which is not under `sdk-candidates/`:
- The six SDK targets are recorded with `raw_name` exactly `'./' + selector`, type `regular`, sizes 125, 4321, 13611, 97, 15721 and 750.
- That includes the 131-character GNU longname README (line 132).
- The four target-archive members have `raw_name` equal to the selector, type `regular`, sizes 97, 15721, 24 and 11.
- Total 50478, which equals `--selected-total-bytes`.

This proves name, type and size compatibility only. It says nothing about the actual bytes (see Residuals).

**TDD evidence holds up:**
- RED: exit 1, 24 tests, two failures, both from the new positive test with `selected member path alias`. The negative cases passed.
- GREEN: exit 0, 24 tests OK.
- Full suite: exit 0, `Ran 71 tests`, `OK`. A grep found no `skipped '` or FAIL/ERROR lines.

## Important issues

None.

## Minor issues

1. **The negative test doesn't check why each case fails.** `test_canonical_member_alias_is_not_selected` only asserts `ok=false`.
   - `/a`, `x/../a` and `a/../x` fail inside `canonical()` (`unsafe path` / `unsafe parent path`), so they never reach the new alias line.
   - Only `././a`, `a/`, `d//a`, `d/./a` and `x/` actually exercise it.
   - The closest neighbours of the accepted form, `.//a` and `./a/`, appear only in the coordinator's probe, not in the committed tests.
   - Suggestion: assert `'selected member path alias'` for the cases that reach `select()`, and add `.//a` and `./a/`.
2. **The positive test uses PAX-format fixtures only.** The default `tar_bytes(fmt=PAX_FORMAT)` puts short names in the ustar name field. The GNU `././@LongLink` path that the real README uses is not tested synthetically. The risk is low: the earlier metadata-only run used the same parser and recorded exactly that `./…README` string, and `select()` compares that same `member.name`.
3. **The amendment's wording is narrower than the code.** It calls the accepted form one "produced by the maintained tar parser for GNU-style archives." The check doesn't depend on archive format: `./`+path is accepted from PAX, ustar or GNU, including after PAX `path` substitution. That's harmless, but the text should say "decoded `member.name`, any format."
4. **The probe results can't be reproduced or re-run.**
   - `probes-sdk-text-selector-dot-prefix-2026-11-08/` holds only results and the Claude raw output, with no probe source.
   - One entry is mislabeled: `x/../a` is listed with requested `x`. It's harmless because `canonical()` fails first.
   - The results agree with my reading of the code (aliases reach the right error, `./` selectors are rejected before parsing), but they are coordinator evidence, not independently reproduced.
5. **Minors from the prior review are still open, all pre-existing:**
   - `fresh_output` sits outside the `try`.
   - If `emit` fails after `write_selected`, a data file can be left behind without a JSONL row.
   - There is no cap on the number of selectors.
   - The per-character plaintext scan has no inner deadline check.

## Residuals

- **The actual bytes are unverified.** The plaintext rule allows strict UTF-8, printable characters, TAB, LF and CR, so it would reject form feeds (`\x0c`, common in GNU sources), ESC, or other control characters. Any of these in the six SDK files or four target files would abort the run with `partial`. That is fail-closed but would mean no success.
- **Selected files already written stay behind on failure.** Selection follows stream order (sdk, then native, then target). If a later member fails, earlier `selected-*.txt` files remain as partial evidence with `ok=false`.
- **The output directory must be absent at launch time.** `command-validation.json` says `inspection-selected-text-PENDING-REVIEW` did not exist at package time. I did not list `sdk-candidates/`. The parent should confirm it is still absent immediately before launching; `fresh_output` would refuse it anyway.
- **The metadata leads came from the earlier link-metadata reader.** Per the prior review's preserved-invariants record, its parsing and canonicalization code is unchanged, and the input pins prevent the assets from drifting.
- **Unchanged platform residuals:** XZ `CHECK_NONE`, the address-space limit (AS) rather than an RSS limit, `noexec=false`, the private `_frombuf` hook, and the PAX allocation backstop.

## Gating

With SPEC PASS and QUALITY PASS, the one authorized post-PASS selected-text run is technically gated, provided that:
- reader `3598…8168`, launcher `c4be…387a` and `exact-command.txt` `4856…63d7` still match at launch;
- the output directory is still absent;
- it is invoked only through the launcher as written.

I did not run it.

## What I did and did not do

**Did:**
- Ran `sha256sum` on the live files, `current/`, `before/` and `exact-command.txt`.
- Diffed `before/` against `current/` and ran `cmp` on the launcher.
- Read the reader source (`select`, `validate_selectors`, `canonical`, `parse_archive`, writers), the tests, the fixtures, the amendment, the report, the RED/GREEN/full-suite logs and exit files, `command-validation.json` and the probe results.
- Read the prior metadata evidence `evidence/.../verified-metadata-leads.json` to cross-check the ten names and sizes.

**Did not:**
- **No SDK asset opened.** I did not open, hash, parse or list anything under `/workspace/lg-tv/sdk-candidates/`.
- **No production command run.** I did not execute `isolate_sdk_inventory.py` or `exact-command.txt`.
- No SDK installer, compile step or TV action.
- No edits to production tooling or prior reviews.

**Permission denials (not worked around):**
- Writing a synthetic probe script to `/tmp` (it would have covered GNU longname `./`, PAX-substituted `./a`, `a` plus `./a` duplicates, `./a` symlinks and hardlinks, and the ten-selector shape) was denied.
- Running the targeted `unittest` methods needed approval that wasn't granted.
- Listing `/usr/lib` to read the stdlib `tarfile` source was blocked.

I stopped each of those and relied on the supplied logs, the prior metadata evidence, and reading the code.