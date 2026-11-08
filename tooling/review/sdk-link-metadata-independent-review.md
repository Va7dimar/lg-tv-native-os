# Independent re-review: SDK reader metadata-only link policy

Reviewed: 2026-11-08 13:29 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t77u` ongoing authorized off-TV technical review (subscriptions primary; no owner checkpoint; no policy/ceiling changes beyond this explicit METADATAONLY symlink-recording candidate).
Scope: package starting at `tooling/review/sdk-link-metadata-2026-11-08/HOST-VERIFICATION-ADDENDUM.md`. No SDK/candidate asset contents were read, hashed, or parsed. No production command, installer execution, TV action, or Page write.

Previous reviews remain immutable:
- `tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4`
- `tooling/review/sdk-fd-fix-independent-review.md` SHA256 `2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b`
- `tooling/review/sdk-stdio-fix-independent-review.md` SHA256 `8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd`
- `tooling/review/sdk-utf8-fix-independent-review.md` SHA256 `13ba1ab83e232c67b69c4984b6145014631603199af2db6e958024b15beb1ebc`

This document reviews the new reader hash only. It does not rewrite those verdicts.

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent adversarial probes and the full synthetic SDK suite were run here; Claude permission denials were not worked around.

Started from `HOST-VERIFICATION-ADDENDUM.md`; also read `contract.md`, `report.md`, diffs, live reader/tests, RED/GREEN/host logs.

This is a deliberate METADATAONLY policy candidate, not a bug-compatible fix. The actual SDK offending link remains unknown.

---

## Package and hashes

```
cecbb2ac06755100d414852b91dccf8527b05321b34a96da3e0eda86b59c16c1  tooling/sdk_inventory_phase.py
2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52  tooling/isolate_sdk_inventory.py
03962a2ca74afbe1446afd9ee87ba9dd6bf6d6cacbc7c24f11f68e93407b5749  tooling/tests/test_sdk_inventory_phase.py
6278c8353a118a695e5512a1968eeae8c5eb49536dd5335b0091db23703f655e  tooling/tests/test_sdk_utf8_boundary.py
1c31fd5d2af306f54c050cc39b62077fb6c1f12ee2e6db536c54d27f79d8ee26  tooling/tests/test_sdk_link_metadata.py
f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10  tooling/tests/test_sdk_fd_boundary.py
15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065  tooling/tests/test_sdk_stdio_boundary.py
e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4  before/sdk_inventory_phase.py (UTF-8-era reader)
```

Live reader, launcher, and new link tests `cmp`-match `current/`. Launcher and FD/stdio tests are byte-identical to `before/` (empty diffs). Reader baseline before this change is the UTF-8-reviewed hash `e70f683a…7ba4`.

Production delta: `diagnostic_text` / `Budget.reject_link` (cap 4); `link_classification` lexical helper; `link_safe` now wraps it and still raises on absolute/out_of_tree; parse loop records absolute/out-of-tree *symlinks* as nonextractable metadata; hardlinks still call `link_safe` first; `rejected_links` attached to the manifest; `extractable=False` on every emitted row. `extraction_implemented=False` was already present. Pins, decoder, EOF/drain, FD/stdio, and UTF-8 strict-final rules are unchanged.

Preserved RED: `logs/RED.log` — 6/6 new-test assertion failures (EXIT=1) before production edit. Intermediate `logs/full-SDK-before-assertion-updates.log` — 9 failures (1 `test_links_pax_gnu_longnames_metadata_only` + 8 `test_extended_paths_links_duplicates_and_types_fail_closed` subcases: cases 5 and 7 × gz/xz × two formats). Nested Codex suite 47 methods with 10 EPERM skips (not counted as passes). Host `host-sdk-suite.txt` 47/47 OK, 0 skips, 2.098s. Host FD/stdio evidence remains green. Those host logs are evidence, not this independent verdict.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** |
| QUALITY | **PASS** |
| Blocking must-fix | **None** |
| Important remaining | **None** for the reviewed metadata-only link policy |

Absolute and escaping SYMLINK targets are classified lexically and recorded as `decision=recorded_not_followed_nonextractable`, `link_target_classification=absolute|out_of_tree`, `extractable=false`, `selected=false`, plus an explicit `absolute_target` / `out_of_tree_target` reason. Nothing opens, follows, `readlink`s, `realpath`s, or extracts a target. Safe symlinks keep `recorded_not_followed`. Hardlink absolute/escape, unsafe member names (traversal/absolute/drive/backslash), empty/NUL/backslash/drive *symlink targets*, duplicates, devices/FIFO/sparse/unknown types, and unresolved UTF-8 remain fail-closed. Failed-manifest diagnostics are capped (4 records; name/target JSON-ASCII prefixes ≤512 bytes with `original_bytes` and `truncated`; rule ≤160 characters). Full names/targets still charge the existing metadata budget; truncated diagnostics do not. The first failure still yields `ok=false` / `status=partial` and skips later inputs. `link_safe` remains a strict nonreuse guard and still rejects `/abs` and `../../escape`.

The two existing-test assertion updates are justified by this explicit contract item only: they cover exactly the 9 preserved pre-update failures (one old escaping-symlink abort plus eight codec/format absolute/escaping symlink subcases). Hardlink, drive/backslash symlink-target, unsafe-name, duplicate, and type/sparse cases were kept as rejections.

---

### Independent verification

Probes (synthetic only) under `tooling/review/probes-sdk-link-metadata-2026-11-08/` (12/12 PASS):

- `symlink_metadata_no_follow`: absolute (existing sentinel path used only as archive *text*), escaping, and safe relative symlinks. `os.open`/`os.pread`/`builtins.open`/`Path.resolve` guards fire if the sentinel inode or path is touched. Inventory `ok=true`; classifications `absolute`, `out_of_tree`, `relative`; decisions and `extractable`/`selected` as specified; `selected_bytes=0`; `extraction_implemented=false`.
- `hardlink_fail_closed_skips_later`: `/abs` and `../../escape` hardlinks → `partial`, `skipped_inputs=['native','target']`, empty `members.jsonl`, one `rejected_links` row classified `absolute` / `out_of_tree`.
- `unsafe_names_and_malformed_targets_fail_closed`: `../sym`, `/sym`, `C:/sym`, `dir\\sym`, empty/drive/backslash targets, and duplicate canonical names still fail.
- `diagnostics_bounded_and_not_in_error`: 1000-repeat unicode/control name and target; each diagnostic prefix ≤512 JSON-ASCII bytes; `original_bytes` match full UTF-8 length; `truncated=true`; serialized records <2000 bytes; `doc['error']` contains neither full string and is <200 characters.
- `full_charge_before_reject_not_truncated_diag`: 90+91 control-character bytes charged twice = 362 > 350 cap; diagnostics truncated.
- `rejected_links_capped_at_4`: 100 collector calls retain 4.
- `link_safe_still_rejects_unsafe`; `invalid_utf8_symlink_target_fail_closed`; `gnu_long_absolute_symlink_recorded` (`/`+LONG).
- `assertion_updates_match_preserved_nine_failures`; hashes/prior reviews; no `extract`/`readlink`/`realpath` in the reader.

Full synthetic suite rerun here: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 47 tests in 2.302s` `OK`, `SUITE_EXIT:0` (`indep-full-suite.txt`). No skips.

---

### Strengths

- Classification is lexical (`sdk_inventory_phase.py:302-322`): empty/NUL/backslash/drive still raise; only `/…` and depth-crossing `..` become recordable symlink classes.
- Hardlinks call `link_safe` before classification (`:410-411`). Member `canonical()` / duplicate checks run first (`:396-401`).
- Every emit sets `extractable=False` and `selected=False` (`:420-423`). Safe links keep `recorded_not_followed`.
- `diagnostic_text` (`:152-174`) caps the escaped prefix, counts original bytes in `CHUNK` slices, and never feeds counters. `reject_link` (`:184-196`) caps at 4 and slices the rule to 160 characters.
- Link/path `InventoryError` messages are fixed strings (no interpolated names). Manifest `error` remains `type + ': ' + str(e)[:2000]` (`:537`).
- `doc['rejected_links']` aliases `budget.rejected_links`, so records added during parse appear in the written manifest. A diagnostic record does not flip `ok`.

---

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. `reject_link` guesses `target_classification` from the error text and a leading `/` (`:189-192`), not from a completed `link_classification`. A failure whose *name* is unsafe (`../sym` → `/abs`) or a metadata-budget miss on an absolute target is labelled `absolute` even though the target policy was not the abort reason. Report.md’s `not_evaluated` wording is tighter than the implementation. Safety is unaffected (the run still fails).
2. If `emit()` later raises (deadline / disk floor) after a link row was accepted, the loop `except` will also append that member to `rejected_links`.
3. Official tests do not assert `target_classification` on rejection records, nor the 160-character rule slice. The 4-record cap is unit-tested on the collector only (a live inventory stops at the first failure).
4. Older plan/report prose elsewhere may still say absolute/escaping links abort; that documentation would need a later update if this candidate is adopted. Not a reader defect.

---

### Residuals (unchanged or outside this fix)

- `relative` is lexical only; symlink chains are not walked because nothing is extracted. A future extractor must not trust this label and must reject absolute/out-of-tree targets (`link_safe` plus its own resolution policy). No extractor exists and none was tested.
- Failures before a link TarInfo is identified may have only the existing bounded `error` field.
- The real SDK unsafe-link offender is still unknown; this is not a successful actual inventory.
- XZ `CHECK_NONE`, AS=VSZ not RSS, `noexec=false`, PAX allocation backstop, observed disk floor, and private `_frombuf` hook dependency are unchanged.
- Any later real phase needs a fresh output directory and an explicit parent handoff. Old partial output must not be reused.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 13:26–13:29 Atlantic/Reykjavik, cwd `/workspace/lg-tv`:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

Raw: `tooling/review/probes-sdk-link-metadata-2026-11-08/claude-raw.json` (prompt `claude-prompt.md`).

- CLI JSON: `is_error=false`, `subtype=success`, `stop_reason=end_turn`, `num_turns=17`, `duration_api_ms=178530`, `duration_ms=179048`, session `c4673c72-4afa-4f0b-914c-6a88d5838302`.
- `modelUsage["claude-opus-5-5"]`: canonicalModel `claude-opus-5-5`, provider `firstParty`; thinkingTokens **10131**; outputTokens 16141; inputTokens 28; cacheReadInputTokens 1076532; cacheCreationInputTokens 101507; costUSD 1.3502944 list. No web search.
- Result prose said “low reasoning effort.” The invocation used `--effort high`; settings.json has `effortLevel=high`; the JSON has no separate effort field. Request, self-report, and 10131 thinking tokens are all recorded.
- Permission denials (not worked around): Bash to cat package docs; two attempts to run the SDK suite; Bash to inspect host/RED logs; Bash to confirm the recorded diff. Claude therefore did not execute tests; this review did, independently, including extra follow/skip/bound probes.
- Claude verdict: SPEC PASS, QUALITY PASS, no must-fix, hashes match, did not access `sdk-candidates`. Independent review agrees. Claude’s diagnostic-labelling and emit-failure notes are recorded as Minors 1–2.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute any production METADATAONLY command or reuse old SDK output.
- Did not edit production tooling or rewrite prior independent reviews / original RED logs.
- Did not write a Page.
- Did not change isolation policy or resource ceilings.
