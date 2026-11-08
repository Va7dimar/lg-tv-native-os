# Independent review handoff — candidate only

The reader now records absolute and escaping SYMLINK targets as lexical metadata, without opening, following, resolving, or extracting targets. Such rows have `decision=recorded_not_followed_nonextractable`, `link_target_classification=absolute|out_of_tree`, `extractable=false`, `selected=false`, and an explicit reason. Safe links retain their existing decision and metadata-only reason. HARDLINK targets retain strict rejection. The strict `link_safe` helper remains a documented nonreuse guard; a future extractor MUST reject unsafe targets. No extractor exists and no future extraction behavior is claimed tested.

Failed manifests retain at most four rejected-link records (the inventory stops at the first failure). Name/target each retain a prefix capped at 512 bytes after JSON ASCII escaping, with full original byte counts and truncation flags. Type, target classification when known, and a reason capped at 160 characters accompany each record. Counting uses bounded chunks and does not retain a full diagnostic copy. Values remain dictionary strings serialized with `ensure_ascii=True`; this is JSON escaping, not HTML escaping, interpretation of paths, or permission to use member names for output files. Member names never choose output filenames. The existing error field cap remains 2000 characters; link/path failures do not interpolate names or targets into it.

Existing header/resolved string accounting still charges full metadata before semantic acceptance; diagnostic prefixes never feed counters. The added control-character budget fixture has 90 name bytes and 91 target bytes charged twice: 362 bytes, exceeding its 350-byte cap even though both diagnostic fields truncate. Budget failures remain partial, and later inputs remain skipped.

## Existing assertion changes

| Existing test | Prior expectation | Candidate expectation | Contract basis and retained checks |
| --- | --- | --- | --- |
| `test_sdk_inventory_phase.py::test_links_pax_gnu_longnames_metadata_only` | `../../escape` SYMLINK aborts | Successful metadata record, out_of_tree classification, explicit nonextractable decision, no selection | Contract item 2 explicitly broadens only absolute/escaping SYMLINK metadata. Existing safe links, PAX/GNU and full accounting assertions remain. |
| `test_sdk_utf8_boundary.py::test_extended_paths_links_duplicates_and_types_fail_closed` | Absolute/escaping extended SYMLINK targets raise (eight codec/format subcases) | Those same targets roundtrip with classification/nonextractable assertions, selected zero, integrity/tar EOF | Contract item 2. Every HARDLINK case remains rejected. Drive/backslash SYMLINK cases, unsafe names, duplicates, sparse/device/unknown types remain rejected. No hidden failures suppressed. |

The intermediate full-suite log preserves all nine failures before these explicit expectation changes. Whole existing test files were snapshotted before edits. FD and stdio tests and launcher are byte-identical to their snapshots.

## Evidence

- `logs/RED.log`: six new tests, six expected baseline assertion failures, exit 1; reader baseline SHA256 verified as `e70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4` before production edits.
- `before/test_sdk_link_metadata.RED.py`: exact new test version used for RED. Final version strengthens the budget fixture with truncating control characters while retaining its independently derived 362-byte expectation.
- `logs/GREEN-final.log`: six new tests, exit 0.
- `logs/full-SDK-final.log`: `python3 -B -m unittest discover -s tooling/tests -p 'test_sdk*.py' -v`, 47 tests, exit 0, 10 skips caused by nested bwrap NETLINK_ROUTE EPERM. These skips are unresolved, honest and unbypassed; parent normal-box verification remains necessary.
- `test-results.json`: all preserved runs, exit codes and counts. No prior RED output was overwritten.
- `before/`, `current/`, `diffs/`, `before-hashes.txt`, `current-hashes.txt`: whole snapshots, exact file diffs and SHA256s; unchanged files have empty diffs.
- `unchanged-checks.txt`: AST comparisons for pins' data structures, limits, decoder, file/publication boundaries, canonical member policy and closed CLI helpers. Production pin constants/offsets are untouched in the exact diff.
- `requested-model-metadata.json`: requested PRIMARY/subscribed Codex/gpt-6.1-sol/HIGH. Actual backend routing is not independently attested. No external providers or agents used.

## Remaining limits

Synthetic stdlib fixtures only; no SDK/source-catalog content was opened, hashed, parsed, downloaded, executed or rerun. Synthetic target sentinel content was never read; guarded target access and resolution cause the metadata success test to fail. No source/installer/compiler/build/TV action occurred. The actual unsafe-link offender is unknown; this candidate is not claimed to match that field case.

Tarfile still owns archive parsing. Failures occurring before a link TarInfo can be identified (for example malformed extension decoding) may have only the existing bounded error, not a rejected-link record. Invalid final UTF8 remains fail closed; diagnostics preserve surrogateescaped bytes as JSON-safe escaped strings. Diagnostic `not_evaluated` means a preceding failure prevented target policy evaluation, not that the target is safe. Current selection is always zero, and extraction is unimplemented. Header/decode/full-string caps and AS/wall backstops retain their existing limits; this change does not claim new hard RSS guarantees or fix XZ check-none behavior.

Independent parent review must judge the new reader and policy before any real SDK command. This is not self-approval or runtime authorization.
