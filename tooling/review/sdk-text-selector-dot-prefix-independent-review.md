# Independent re-review: SDK selected-plaintext `./` prefix match

Reviewed: 2026-11-08 14:02 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t77u` ongoing authorized off-TV technical review (subscriptions primary; Claude Opus 5.5 HIGH primary). No owner checkpoint. No real SDK archive run during this review.
Scope: package `tooling/review/sdk-text-selector-dot-prefix-2026-11-08/` (contract amendment, RED/GREEN/suite logs, diffs, `exact-command.txt`). No files under `/workspace/lg-tv/sdk-candidates/` were opened, hashed, parsed, or listed for assets. The proposed command was parsed only, never launched. No Page write during review.

Previous reviews remain immutable:
- `tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4`
- `tooling/review/sdk-fd-fix-independent-review.md` SHA256 `2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b`
- `tooling/review/sdk-stdio-fix-independent-review.md` SHA256 `8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd`
- `tooling/review/sdk-utf8-fix-independent-review.md` SHA256 `13ba1ab83e232c67b69c4984b6145014631603199af2db6e958024b15beb1ebc`
- `tooling/review/sdk-link-metadata-independent-review.md` SHA256 `95b21beea2373b03af8eeee2cfd3f716df8efa4c95e82f13b99559c6a05818d5`
- `tooling/review/sdk-text-selector-independent-review.md` SHA256 `8740357586f1b2fe558a3321a20934fe5e52f992f86c0add8d553295c40f5ece` — SPEC FAIL / QUALITY PASS; must-fix was the `./` stored-name mismatch

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent synthetic probes and the full SDK suite were run here; Claude permission denials were not worked around.

Started from the package contract amendment, report, diffs, live reader/launcher/tests, RED/GREEN/suite logs, and `exact-command.txt`. Prior generated metadata evidence `evidence/sdk-inventory-links-execution-2026-11-08/verified-metadata-leads.json` was consulted only to compare the ten indexed `raw_name`/`size` pairs with the proposed selectors (no SDK asset bytes).

---

## Package and hashes

```
3598007632b1c13790d16cad9f6a68c23e5f4b35a4996948a3917bef2d8f8168  tooling/sdk_inventory_phase.py
c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a  tooling/isolate_sdk_inventory.py
8b78078ef48c8cad3e0d9091c244336c8450cc74bb8c5d0e55ed8339f76d6681  tooling/tests/test_sdk_text_selector.py
4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7  exact-command.txt
77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf  before/sdk_inventory_phase.py (selector-era reader)
537c33d6b8783b44e906abe5c3e071ffae4b3f4c60ed8cc5e0c6dc7a2860355b  before/test_sdk_text_selector.py
```

Live files `cmp`-match `current/`. Launcher is byte-identical to the previous reviewed launcher. Reader delta is exactly one line in `select()`: `member.name not in (selector.path, './' + selector.path)`. Tests add `test_dot_slash_prefixed_regular_member_is_selected` (`./a` and `./dir/text`) and expand negatives to `././a`, `/a`, `x/../a`, `a/`, `d//a`, `d/./a`, `a/../x`, and `x/`.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **PASS** (accepted raw names are exactly the canonical selector or `'./' + selector`; other aliases still fail closed; unchanged ten-selector command can in principle match the six indexed SDK `./`+canonical names and four exact target names) |
| QUALITY | **PASS** (one-line, no extra normalization, no link following, prior safety order preserved) |
| Blocking must-fix | **None** |

Safety properties remain: literal-only selector configuration, 16 MiB/member and 64 MiB/shared configuration caps, exact indexed sizes, NUL/binary/nonprintable rejection, no symlink following, generated `selected-NNNNNN.txt` writes (`O_EXCL|O_NOFOLLOW`, mode 0600), default METADATAONLY unchanged, FD cleanup and `stdin=DEVNULL` still present. The proposed command is unchanged: fresh `inspection-selected-text-PENDING-REVIEW`, the same three immutable pin paths, ten selectors summing to 50478, `--selected-total-bytes 50478`. It was not executed during this review. The output directory did not exist at package time or at review close (14:02 Atlantic/Reykjavik).

---

### Independent verification (coordinator)

Probes under `tooling/review/probes-sdk-text-selector-dot-prefix-2026-11-08/` (10/10 PASS):

- `dot_slash_version_like_selected`: member `./version-ca9v1-starfishmllib32-linux-gnueabi` (125 `A`s) + canonical selector → `ok=true`, `raw_name` preserved, mode 0600, bytes match.
- `exact_canonical_still_selected`: member `a` still matches selector `a`.
- `other_aliases_rejected_no_write`: `././a`, `/a`, `x/../a`, `a/`, `d//a`, `d/./a`, `a/../x`, `x/`, `.//a`, `./a/` all `ok=false` with no `selected-*.txt`. `/a` fails as `unsafe path`; `x/../a` and `a/../x` as `unsafe parent path`; the rest as `selected member path alias`. A follow-up confirmed `x/../a` vs selector `a` is also `unsafe parent path` with no data file (the automated probe had mislabeled that case's requested path as `x`; the official unit test and the follow-up use `a`).
- `dot_slash_selector_rejected`: selector `./a` fails before parse (`nonliteral/noncanonical selector path`, `inputs=[]`).
- `selected_symlink_never_followed`: sentinel not opened; `selected member not regular`.
- `binary_rejected_no_write`: `\x7fELF` → `nonplaintext selected content`, no data file.
- `shared_bound_one_byte_over_fails_with_dot_slash`: three `./a` members, cap 14 → `selected total exceeds shared bound`.
- `literal_command_parse_no_open`: reconstructed argv → 6 sdk + 4 target + 0 native, total 50478, output `…/inspection-selected-text-PENDING-REVIEW`, directory absent.
- `launcher_isolation_literals_present`: `_normalize_stdio`, `stdin=subprocess.DEVNULL`, `pass_fds=`.
- `default_metadata_only`: empty selectors still METADATAONLY, no content files.

Full synthetic suite rerun here before review close: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 71 tests in 3.959s` `OK`, `SUITE_EXIT:0`, no unittest skips (`skipped` occurs only in two passing test names). RED against the previous reader: 24 methods, 2 failures, both new positive `./` subtests, error `selected member path alias`, exit 1. GREEN after the one-line edit: 24/24 OK, exit 0, including `test_synthetic_selected_sandbox`.

Prior inventory metadata (not archive bytes) still records all six SDK targets with `raw_name` prefixed `./` and matching sizes (125, 4321, 13611, 97, 15721, 750). All four target targets have `raw_name == canonical_name` and matching sizes (97, 15721, 24, 11). Combined 50478.

---

### Strengths

- The accepted set is two exact strings; `validate_selectors` still rejects a `./…` selector.
- `canonical()` still rejects leading `/`, `..`, backslash, drive, and NUL before `select()` runs.
- No glob, regex, extra normalization, or link resolution was added.
- `raw_name` is still the maintained-parser name.
- TDD order is documented: tests first (RED), then the one-line reader change (GREEN), then the full suite.

---

### Issues

#### Critical

None.

#### Important

None.

#### Minor

- Several negative cases (`/a`, `x/../a`, `a/../x`) fail inside `canonical()` rather than at the new alias comparison; the test only asserts `ok=false`. Closest neighbours `.//a` and `./a/` were covered by coordinator probes, not the committed unit test.
- Positive tests use PAX fixtures; the long GNU `././@LongLink` README path is not re-created synthetically. Risk is low because the earlier metadata run recorded that exact `member.name` through the same parser.
- The amendment text says "GNU-style archives"; the code accepts `'./'+path` from any format after parser substitution.
- Coordinator probe `x/../a` was initially requested as `x` due to a labeling bug; follow-up and the unit test use selector `a`.
- Pre-existing minors from the prior selector review remain: `fresh_output` outside `inventory()`'s `try`; possible data file without a JSONL row if `emit` fails after `write_selected`; no explicit selector-count cap; plaintext scan has no inner deadline.

---

### Residuals

- No real SDK selected-text phase was executed during this review. Name/type/size compatibility with prior metadata is not proof of the ten files' current bytes or of plaintext acceptance (form-feed or other controls would fail closed as `partial`).
- Parent must confirm `inspection-selected-text-PENDING-REVIEW` is still absent immediately before launch (`fresh_output` will refuse it).
- XZ `CHECK_NONE`, AS=VSZ not RSS, `noexec=false`, PAX allocation backstop, and private `_frombuf` hook dependency are unchanged.
- Any later real phase needs this PASS, a still-fresh output directory, matching reader/launcher/command hashes, and the existing parent handoff. Selected files written before a later failure would remain as partial evidence.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 13:58–14:02 Atlantic/Reykjavik, cwd `/workspace/lg-tv`:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

Raw: `tooling/review/probes-sdk-text-selector-dot-prefix-2026-11-08/claude-raw.json`.
Result prose: `tooling/review/probes-sdk-text-selector-dot-prefix-2026-11-08/claude-result.md`.

- CLI JSON: `is_error=false`, `subtype=success`, `stop_reason=end_turn`, `num_turns=38`, `duration_api_ms=219767`, `duration_ms=220363`, session `41c4ce1a-4758-4588-be23-d861387dc97f`.
- `modelUsage["claude-opus-5-5"]`: canonicalModel `claude-opus-5-5`, provider `firstParty`; thinkingTokens **6787**; outputTokens 20434; inputTokens 42; cacheReadInputTokens 1892526; cacheCreationInputTokens 103575; costUSD 1.6159532 list. No web search.
- Permission denials (not worked around): a bundled Bash hash/read command; writing a synthetic probe script under `/tmp`; running targeted unittest methods; listing `/usr/lib` for stdlib `tarfile` source. Claude then hashed and read files directly and relied on supplied logs plus `verified-metadata-leads.json`.
- Claude verdict: SPEC PASS, QUALITY PASS, no blocking must-fix. Independent review agrees.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute `isolate_sdk_inventory.py` or the proposed SELECTEDTEXT command.
- Did not edit production tooling or rewrite prior independent reviews / original RED logs after the documented GREEN.
- Did not write a Page.
