# Independent re-review: SDK reader UTF-8 boundary fix

Reviewed: 2026-11-08 13:13 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t77u` resume of already-authorized off-TV technical review (subscriptions primary; no owner checkpoint; no policy/ceiling changes).
Scope: reader UTF-8 package starting at `tooling/review/sdk-utf8-fix-2026-11-08/package/HOST-VERIFICATION-ADDENDUM.md`. No SDK/candidate asset contents were read, hashed, or parsed. No production command, installer execution, TV action, or Page write.

Previous reviews remain immutable:
- `tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4` — V1 SPEC FAIL / QUALITY PASS for launcher `488e34d3…f7f0`.
- `tooling/review/sdk-fd-fix-independent-review.md` SHA256 `2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b` — FD≥3 SPEC PASS for launcher `35b6dd2c…4771`.
- `tooling/review/sdk-stdio-fix-independent-review.md` SHA256 `8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd` — stdio SPEC PASS for launcher `2a6638e3…ca52`.

This document reviews the new reader hash only. It does not rewrite those verdicts.

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent adversarial probes and the full synthetic SDK suite were run here; Claude permission denials were not worked around.

Started from `package/HOST-VERIFICATION-ADDENDUM.md`; also read `contract.md`, `package/review-packet.md`, `package/change.diff`, live reader/tests, red/green/host logs.

---

## Package and hashes

```
e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4  tooling/sdk_inventory_phase.py
2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52  tooling/isolate_sdk_inventory.py
aaba6c1cc6fd799c02ea62d2a0a3b8103790af97bd6a4dea7a0c6496d48f0ba0  tooling/tests/test_sdk_inventory_phase.py
f0b0e69c9b69b4e2122494b0104a791b108009b15b20dfc7a26d2d951126bd10  tooling/tests/test_sdk_fd_boundary.py
15fe10e33a5c49c3fa879c0e5dda2b56e9f15d77caabcdd3de25f3c253ddf065  tooling/tests/test_sdk_stdio_boundary.py
746defc12bdcfa73f211eaad30ba8e349bb70eda8a40e9ed5bbb9ab12a4c3d58  tooling/tests/test_sdk_utf8_boundary.py
c04fe95faf8346741d18de8cdef4814beb520d47d079d7f1a702997ca026fd7f  package/before/sdk_inventory_phase.py (stdio-era reader)
```

Live reader, launcher, and new UTF-8 tests `cmp`-match `package/current/`. Launcher is byte-identical to the stdio-fix hash. Existing three SDK test modules are unchanged. Before-reader hash is the previous reviewed reader `c04fe95f…fd7f`. Production delta is only: `Budget.text(..., errors='strict')` default with optional `surrogateescape`; `ObservedInfo._frombuf` hardcodes `'surrogateescape'`; `_proc_member` charges raw name/link with surrogateescape and owners strictly; the yielded-member loop validates final owners strictly (no second owner charge) then charges final name/link and PAX keys/values strictly.

Preserved RED: `package/red.log` — 6 methods, 18 `UnicodeDecodeError`s at `tarfile.nts` / `_frombuf` byte `0xc4` position 99 (`FAILED (errors=18)`, EXIT=1). These are production decode errors, not fixture-construction typos. `package/green.log` 6/6 PASS. Nested Codex suite logged 10 EPERM skips; host `../host-sdk-suite.txt` is 41/41 OK, 0 skips, 2.000s. Host FD `normal.json`/`high.json` still `inherited=[]`, `parent_walk=[]`, `writable_reopens=[]` (256/257 closed). Host stdio masks 1–7 remain green. Those host logs are evidence, not this independent verdict.

The actual SDK failing field/offset remains unknown. This is a synthetic compatibility hypothesis, not a diagnosis of real archive bytes.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** |
| QUALITY | **PASS** |
| Blocking must-fix | **None** |
| Important remaining | **None** for the reviewed UTF-8 boundary |

Transient fixed name/link bytes may be surrogate-escaped only until maintained GNU/PAX substitution. Extension-body decoding stays `tarfile.open(..., encoding='utf-8', errors='strict')`. Raw owners remain strict inside `_proc_member` (before `_apply_pax_info`). Final resolved names/links are strict-charged before `canonical` / duplicate checks / `link_safe` / emit, so leftover surrogates cannot become inventory paths. Unresolved malformed UTF-8 fails closed. Traversal, absolute/drive/backslash paths, escaping links, duplicates, devices, FIFO, sparse, and unknown types still raise `InventoryError`. Pins, EOF/drain, caps, FD cleanup, and stdio hardening are unchanged. No custom header parser.

---

### Independent verification

Probes (synthetic only) under `tooling/review/probes-sdk-utf8-fix-2026-11-08/`:

- `gnu_split_roundtrip_both_codecs`: name-only, link-only, and both; gzip and XZ. Writer base header ends with `0xc4` at name `[0:100]` and/or link `[157:257]`. Resolved `raw_name`/`link_target` match `99*'a'+U+0100+'-suffix'`. No surrogate code points in emitted rows. `integrity_eof` and `tar_eof` true. Members 2 (one extension) or 3 (name+link extensions).
- `unresolved_invalid_utf8_fails_closed`: 12 cases (short name/link, long name/link bodies, uname, gname × both codecs). Fail closed via `InventoryError` or raw `UnicodeDecodeError` (the latter from strict `nts()` of a malformed GNU extension body — fail-closed, type not wrapped).
- `extended_unsafe_still_inventoryerror`: 74 GNU+PAX unsafe cases all raise `InventoryError`.
- `policy_uses_final_not_discarded_raw_traversal_bytes`: GNU longname `'s'*120` whose following 100-byte field was patched to `b'../'+b'x'*96+b'\\xc4'` (checksum fixed) is accepted as `canonical_name='s'*120`. Policy sees the substituted name, not the discarded raw field.
- `final_gnu_traversal_rejected`: final GNU name `'../'+LONG` still `unsafe parent path`.
- `raw_invalid_uname_rejected_despite_pax`: PAX `uname=validowner` plus a patched ustar uname field starting `0xc4` → `InventoryError: invalid UTF8 metadata` (raw owners checked before `_apply_pax_info`).
- `pax_valid_path_replaces_truncated_raw_name`: explicit PAX `path=good-final.txt` plus patched ustar name `99*'a'+0xc4` → emitted name `good-final.txt`.
- `ustar_malformed_prefix_fails_closed`: lone prefix `0xc4` joined into the name → `invalid UTF8 metadata`.
- `exact_gnu_metadata_budget`: 1466 bytes (`2*(13+512)+200+2*len(LONG.encode())`); cap 1465 rejects.
- `regular_multibyte_charge`: USTAR `Ā` + `é` + `ö` still exactly 8 bytes.
- `json_roundtrip_no_surrogates`, preexisting `nts()` NUL-termination note, hashes/prior reviews, and source-order (`surrogateescape` in `_frombuf` → raw charge → final strict owners/names → `canonical` → `link_safe`).

Full synthetic suite rerun here: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 41 tests in 2.334s` `OK`, `SUITE_EXIT:0` (`indep-full-suite.txt`). No skips.

---

### Strengths

- Hook remains `super()._frombuf(...)` (`sdk_inventory_phase.py:288`); field bounds, checksum, and GNU/PAX substitution stay in maintained CPython 3.13 tarfile.
- `surrogateescape` recovers original raw name/link bytes for charging (the stray `0xc4` counts as one byte, not replacement/loss). Final strings are still charged as strict UTF-8.
- Owner strictness is preserved and happens in `_proc_member` (`:299`) before `_proc_builtin`/`_proc_pax` apply overrides; an extra final-owner encode (`:318-322`) does not double-charge.
- Path policy is unchanged and runs only after the final strict name/link charge (`:323` then `:328` / `:341`).
- New tests assert the writer actually produced the split `0xc4` field, pin the 1466-byte GNU budget and hidden-header count, cover gzip and XZ, and keep PAX/USTAR/ASCII GNU baselines.

---

### Issues

#### Critical

None.

#### Important

None.

#### Minor

1. Official unsafe-path fixtures (`test_sdk_utf8_boundary.py:91-96`) use `'../'+LONG` (and similar), which pushes U+0100 past the 100-byte fixed field, so many of the 74 cases never hit the split-UTF-8 boundary. Production order still rejects after substitution (and independent probes did exercise patched `0xc4` raw fields plus final traversal). Tightening those fixtures would make the packet's “split then still reject” claim directly tested.
2. `test_unresolved_invalid_utf8_fails_closed` builds the archive inside `assertRaises` and accepts bare `UnicodeError`. A malformed GNU longname *body* surfaces as `UnicodeDecodeError` from `nts(..., 'strict')` rather than `InventoryError`. It is still fail-closed (and `inventory()` already catches `Exception`); the type is just inconsistent.
3. `_frombuf` applies surrogateescape to every `nts()` field, including the USTAR prefix and hidden-header names, not only the documented name/link slots. Unresolved prefix junk still fails at the final strict charge (independent probe). Prefix bytes that a later GNU/PAX path replaces used to fail in `_frombuf` and now survive only as a charged raw string — within the contract, slightly broader than the packet wording.
4. The hook ignores its `errors` argument (intentional while TarFile stays `errors='strict'`). An assert that the incoming handler is `strict` would catch future tarfile drift.

---

### Residuals (unchanged or outside this fix)

- The real SDK error is consistent with a truncated 100-byte name/link (or possibly prefix) but is not proven. If the bad field is unresolved, a future real phase will still fail closed — correct, and not a successful inventory.
- XZ `CHECK_NONE` labeling, absolute-symlink fail-closed, AS=VSZ not RSS, `noexec=false`, private `_frombuf` hook dependency, and launcher AS/wall backstops are unchanged.
- Passing 41 synthetic tests does not prove SDK compatibility, compiler/ABI/license fitness, or boot/recovery.
- Any later real phase needs a fresh output directory (`inspection-metadata-utf8-PENDING-REVIEW`) and an explicit parent handoff. Old partial output must not be reused.
- Prior independent reviews remain the record for their respective hashes.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 13:09–13:13 Atlantic/Reykjavik, cwd `/workspace/lg-tv`:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

Raw: `tooling/review/probes-sdk-utf8-fix-2026-11-08/claude-raw.json` (prompt `claude-prompt.md`).

- CLI JSON: `is_error=false`, `subtype=success`, `stop_reason=end_turn`, `num_turns=16`, `duration_api_ms=222973`, `duration_ms=223481`, session `7eb825c7-2ad5-4e5e-9635-ae52dcfadd92`.
- `modelUsage["claude-opus-5-5"]`: canonicalModel `claude-opus-5-5`, provider `firstParty`; thinkingTokens **17287**; outputTokens 22781; inputTokens 26; cacheReadInputTokens 1016405; cacheCreationInputTokens 96773; costUSD 1.433189 list. No web search. `fast_mode_state=off`.
- Result prose said reasoning effort was “set by the harness at a low setting.” The invocation used `--effort high`; settings.json has `effortLevel=high`; the JSON has no separate effort field. Request, self-report, and 17287 thinking tokens are all recorded.
- Permission denials (not worked around): Bash to diff/read production tests; Bash to inspect live `tarfile` hooks; Bash to run `test_sdk_utf8_boundary.py`. Claude therefore did not execute tests; this review did, independently, along with extra adversarial crafts.
- Claude verdict: SPEC PASS, QUALITY PASS, no must-fix, hashes match, did not access `sdk-candidates` contents. Independent review agrees after running the 41-test suite and the probes above. Claude’s two test-quality notes are recorded as Minors 1–2.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute any production METADATAONLY command or reuse old SDK output.
- Did not edit production tooling or rewrite prior independent reviews / original RED logs.
- Did not write a Page.
- Did not change isolation policy or resource ceilings.
