# Independent review: SDK selected-plaintext selectors

Reviewed: 2026-11-08 13:54 Atlantic/Reykjavik (UTC+0)
Authority cited by parent: owner `t77u` ongoing authorized off-TV technical review (subscriptions primary; Claude Opus 5.5 HIGH primary). No owner checkpoint. No real SDK archive run.
Scope: package `tooling/review/sdk-text-selector-2026-11-08/` (contract, RED/GREEN, diffs, `exact-command.txt`). No files under `/workspace/lg-tv/sdk-candidates/` were opened, hashed, or parsed. The proposed command was parsed only, never launched. No Page write.

Previous reviews remain immutable:
- `tooling/review/sdk-inventory-independent-review.md` SHA256 `57ac2f23882d603db7304a4ea7dd95c2579fa6f2c8e213535f20aefb67d5edb4`
- `tooling/review/sdk-fd-fix-independent-review.md` SHA256 `2acda00ef7d41373f5ad2fcb9173c9f18a04cfd42f932d69809219c990e7312b`
- `tooling/review/sdk-stdio-fix-independent-review.md` SHA256 `8ff151080819e2f6814dbeeb88f2bbc7551ba59c0dbe491234e73842adc011dd`
- `tooling/review/sdk-utf8-fix-independent-review.md` SHA256 `13ba1ab83e232c67b69c4984b6145014631603199af2db6e958024b15beb1ebc`
- `tooling/review/sdk-link-metadata-independent-review.md` SHA256 `95b21beea2373b03af8eeee2cfd3f716df8efa4c95e82f13b99559c6a05818d5`

Primary analysis: subscribed Claude Opus 5.5 HIGH. Independent synthetic probes and the full SDK suite were run here; Claude permission denials were not worked around.

Started from the package contract, report, addendum, diffs, live reader/launcher/tests, and `exact-command.txt`. Prior generated metadata evidence `evidence/sdk-inventory-links-execution-2026-11-08/verified-metadata-leads.json` was consulted only to compare the ten indexed `raw_name`/`size` pairs with the proposed selectors (no SDK asset bytes).

---

## Package and hashes

```
77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf  tooling/sdk_inventory_phase.py
c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a  tooling/isolate_sdk_inventory.py
537c33d6b8783b44e906abe5c3e071ffae4b3f4c60ed8cc5e0c6dc7a2860355b  tooling/tests/test_sdk_text_selector.py
4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7  exact-command.txt
cecbb2ac06755100d414852b91dccf8527b05321b34a96da3e0eda86b59c16c1  before/sdk_inventory_phase.py (link-metadata reader)
2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52  before/isolate_sdk_inventory.py (stdio-hardened launcher)
```

Live files `cmp`-match `current/`. Existing five SDK test modules are unchanged from the link-metadata review. `preserved-invariants.json` records unchanged AST/literals for pins, Limits, Budget, DecodedReader, tar hooks, output helpers, `canonical`/`link_*`, `_normalize_stdio`, `build_command`, and `subprocess.run` (`stdin=DEVNULL`, `pass_fds`, timeout).

Preserved RED: 23 methods, 126 errors (`TextSelector` missing), default metadata test passed, EXIT=1, against before hashes. Targeted GREEN: 22 passed + 1 nested-bwrap skip. Nested full suite: 70 methods, 11 skip entries (not counted as passes). Host durable suite: 70/70 OK, 0 skips (coordinator initially misread the word `skipped` in two passing test names; that log is retained). Host logs are evidence, not this verdict.

---

## Verdict

| Gate | Result |
|---|---|
| SPEC | **FAIL** (implementation matches the written alias rule, but that rule cannot select the six indexed SDK members the command targets) |
| QUALITY | **PASS** (tight, fail-closed, launcher isolation preserved) |
| Blocking must-fix | **Yes** — allow a maintained-parser raw name of exactly `./` + canonical selector, or the proposed command cannot succeed |
| Important remaining | Same item; fail-closed, not a follow/extract hole |

Safety properties of the new selector path itself hold on synthetic fixtures: literal-only configuration, 16 MiB/member and 64 MiB/shared configuration caps, exact indexed sizes, NUL/binary/nonprintable rejection, no symlink following, generated `selected-NNNNNN.txt` writes (`O_EXCL|O_NOFOLLOW`, mode 0600), default METADATAONLY unchanged, FD cleanup and `stdin=DEVNULL` still present. The proposed command uses a fresh `inspection-selected-text-PENDING-REVIEW` directory, the same three immutable pin paths, ten selectors summing to 50478, and `--selected-total-bytes 50478`. It was not executed.

---

### Independent verification

Probes under `tooling/review/probes-sdk-text-selector-2026-11-08/` (10/10 PASS), plus a follow-up alias reproduction:

- `ten_files_50478_exact_bound`: synthetic sdk+target members using the command’s ten canonical paths and exact sizes (printable ASCII). `ok=true`, `selected_bytes=50478`, ten `selected-000001.txt` … `selected-000010.txt` of mode 0600 whose bytes and SHA-256 match the payloads. Member names are never used as output paths.
- `shared_bound_one_byte_under_fails`: cap 50477 → `selected total exceeds shared bound`.
- `literal_selectors_rejected`: empty/`.`/`./a`/`a/`/`a//b`/`../a`/`/a`/drive/backslash/glob/control — all fail with `inputs=[]`.
- `nul_binary_rejected_no_write`: NUL, invalid UTF-8, ELF and PNG magic leave no `selected-*.txt`.
- `selected_symlink_never_followed`: selected symlink to a sentinel is not opened; no data file.
- `output_generated_name_and_freshness`: existing output dir raises `OSError`; a pre-existing `selected-000001.txt` symlink is not followed or overwritten (`ok=false`, sentinel bytes unchanged).
- `literal_command_parse_no_open`: `production_arguments` on the reconstructed argv (no `launch`, no asset open) yields 6 sdk + 4 target + 0 native selectors, total 50478, output `…/inspection-selected-text-PENDING-REVIEW`. All ten paths are already canonical.
- Launcher still contains `_normalize_stdio`, `stdin=subprocess.DEVNULL`, `pass_fds=`, and inherited-FD fail-closed cleanup.
- Follow-up synthetic: member `./version-ca9v1-starfishmllib32-linux-gnueabi` (125 `A`s) + selector `version-ca9v1-…` → `InventoryError: selected member path alias`, no data file. The `./…` *selector* form is rejected before parse as `nonliteral/noncanonical selector path`.

Full synthetic suite rerun here: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v` → `Ran 70 tests in 3.663s` `OK`, `SUITE_EXIT:0`, no unittest skips (`indep-full-suite.txt`). Includes FD, stdio, UTF-8, link-metadata, and all 23 selector tests (the nested sandbox skip did not occur on this host).

Prior inventory metadata (not archive bytes) in `verified-metadata-leads.json` records all six SDK targets with `raw_name` prefixed `./` and matching sizes (125, 4321, 13611, 97, 15721, 750). All four target targets have `raw_name == canonical_name` and matching sizes (97, 15721, 24, 11). Combined 50478.

---

### Strengths

- `validate_selectors` (`sdk_inventory_phase.py:49-73`) is literal: no glob/normalization/alias acceptance; sizes are true `int`s; duplicates and shared-bound overflow fail closed.
- CLI counts are `0|[1-9][0-9]{0,7}`; `--select-text` and `--selected-total-bytes` are required together (`:675-683`). Validation occurs in `production_arguments` and again in `launch` before opening inputs.
- `select()` runs after existing type/link/sparse/duplicate checks; `member.isreg()` is required before `extractfile` (`:605-613`). `extractfile` here reads the current regular member from the bounded stream; it does not write archive paths to disk.
- Plaintext: strict UTF-8 plus `isprintable()` with TAB/LF/CR allowed (`:91-96`).
- Writes use `selected-{n:06d}.txt` via `dir_fd`, `O_EXCL|O_NOFOLLOW`, 0600 (`:100-107`, `:615`). Full validation precedes write. `selected_bytes` is checked against the explicit shared bound before the read.
- Default empty selectors remain METADATAONLY and emit no content files.
- Launcher forwards validated `repr` literals only; descriptor cleanup and `stdin=DEVNULL` are unchanged.

---

### Issues

#### Critical (blocking for the intended ten-file command; fail-closed)

**SDK members with a maintained-parser `./` prefix cannot be selected.**

- Locations: `sdk_inventory_phase.py:603` (`member.name != selector.path` → `selected member path alias`); `validate_selectors` (`canonical(path) != path` rejects a `./…` selector) at `:62`.
- Independent synthetic repro: member `./version-ca9v1-starfishmllib32-linux-gnueabi` + canonical selector of the same basename/size → `ok=false`, error `selected member path alias`, no `selected-*.txt`. A `./…` selector is rejected before any parse.
- Prior indexed metadata (not a new SDK read) shows all six SDK command targets stored as `raw_name='./'+canonical` with the listed sizes. The four target members have no prefix and would match. Because `select()` looks up by canonical name then requires raw equality, the first matching SDK member aborts the whole selected run (`ok=false`/`partial`).
- Official `test_canonical_member_alias_is_not_selected` encodes this as intended behaviour; there is no positive test for a GNU/`./`-prefixed SDK-style archive.
- The written contract’s “alias fails” sentence collides with the stated goal of selecting those ten indexed files via canonical paths. Putting `./` into `exact-command.txt` is not a workaround, because such selectors are rejected.
- Expected fix (safety-preserving): treat `member.name in (selector.path, './' + selector.path)` as a match; keep rejecting `.//`, `././`, `x/../`, `d//`, trailing slash, and other aliases. Keep recording `raw_name` as today. Add a positive `./` synthetic test and keep the existing negative alias tests. Re-review before any real run. `exact-command.txt` can stay canonical.

#### Important

None beyond the must-fix above.

#### Minor

- `launch`’s `if selectors else _bootstrap(...)` branches are equivalent; empty-selector bootstrap text is no longer byte-identical to the previous launcher (behaviour matches: `selectors=[]`, METADATAONLY).
- The per-character plaintext scan has no inner deadline check (bounded by 16 MiB/member and the 120 s wall).
- No explicit cap on selector count (a huge argv fails closed via OSError).
- If `emit` fails after `write_selected`, a data file can remain without a JSONL row (`ok=false` is allowed as partial evidence).
- `fresh_output` still sits outside `inventory()`’s `try`, so an existing output directory raises raw `OSError` rather than a published failed manifest (pre-existing).

---

### Residuals

- No real SDK phase was executed; this review does not prove the ten files’ current bytes, only that prior metadata names/sizes plus the alias rule would prevent a successful selected run as written.
- Parent must confirm `inspection-selected-text-PENDING-REVIEW` does not already exist (`fresh_output` will refuse it). This review did not list `sdk-candidates/`.
- XZ `CHECK_NONE`, AS=VSZ not RSS, `noexec=false`, PAX allocation backstop, and private `_frombuf` hook dependency are unchanged.
- Nested-sandbox NETLINK_ROUTE skips remain in implementation logs; this host’s independent 70/70 run had zero skips.
- Any later real phase needs this must-fix, a fresh output directory, and an explicit parent handoff.

---

## Claude Opus 5.5 usage (honest)

Invocation 2026-11-08 13:51–13:54 Atlantic/Reykjavik, cwd `/workspace/lg-tv`:

`claude -p ... --model claude-opus-5-5 --effort high --output-format json`

Raw: `tooling/review/probes-sdk-text-selector-2026-11-08/claude-raw.json`.

- CLI JSON: `is_error=false`, `subtype=success`, `stop_reason=end_turn`, `num_turns=15`, `duration_api_ms=186368`, `duration_ms=186732`, session `a656a708-37d0-4377-8af2-5735636f1589`.
- `modelUsage["claude-opus-5-5"]`: canonicalModel `claude-opus-5-5`, provider `firstParty`; thinkingTokens **13055**; outputTokens 18937; inputTokens 22; cacheReadInputTokens 890291; cacheCreationInputTokens 108283; costUSD 1.4231502 list. No web search.
- Result prose said “low reasoning effort.” The invocation used `--effort high`; settings.json has `effortLevel=high`; the JSON has no separate effort field. Request, self-report, and 13055 thinking tokens are all recorded.
- Permission denials (not worked around): two Bash greps over `evidence/sdk-inventory-links-*`; one Bash `validate_selectors` snippet. Claude then read evidence files directly. This review independently read `verified-metadata-leads.json` and reproduced the `./` alias failure synthetically; the 70-test suite was run here.
- Claude verdict: SPEC FAIL, QUALITY PASS, one must-fix (`member.name` vs `./` prefix). Independent review agrees.

---

## What this review did not do

- Did not open, hash, or parse real files under `/workspace/lg-tv/sdk-candidates/`.
- Did not execute `isolate_sdk_inventory.py` or the proposed SELECTEDTEXT command.
- Did not edit production tooling or rewrite prior independent reviews / original RED logs.
- Did not write a Page.
