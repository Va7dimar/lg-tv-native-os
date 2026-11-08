# Independent review: bounded archive inventory tooling

Reviewed: 2026-11-08 04:45 Atlantic/Reykjavik (UTC+0)
Reviewer role: independent code review of newly implemented non-repo local tooling only.
Scope: `/workspace/lg-tv/tooling/bounded_archive_inventory.py`, `/workspace/lg-tv/tooling/isolate_inventory.py`, `/workspace/lg-tv/tooling/tests/test_bounded_archive_inventory.py`, requirements addendum, implementation report, review package. No catalog/LG originals were parsed. No production code was changed. No packages, network, TV, or repo actions.

Git range: not applicable (non-repo; `from-empty.diff` is a unified diff against `/dev/null`). No repository was created.

Method: requesting-code-review / code-reviewer template. Requirements from `docs/superpowers/plans/2026-11-08-bounded-source-inventory.md`. Existing 48-test green artifact treated as authoritative (no blind whole-suite rerun). Targeted synthetic probes written under `tooling/review/probes/` when flaws were suspected. CPython 3.13.5 `tarfile` internals were read to check allocation-before-limits. Subscribed Claude/Astra critique was not required after direct verification; no session spoofing was attempted.

Review package files listed first (`tooling/review/FILELIST.txt`):
`2026-11-08-bounded-source-inventory.md`, `FILELIST.txt`, `bounded_archive_inventory.py`, `from-empty.diff`, `implementation-report.md`, `isolate_inventory.py`, `tests_test_bounded_archive_inventory.py`.

Production files matched the review copies (`cmp` identical) for the reader, launcher, and tests.

## Verdict (requested fields)

| Gate | Result |
|---|---|
| SPEC compliance | **FAIL** |
| Code quality | **FAIL** |
| Ready to parse the three catalog originals | **NO** — pre-read checkpoint cannot truthfully pass |
| Ready to proceed without changes | **No** — with fixes (see blocking findings) |

SPEC fails because invocation-level member / pathname / expanded ceilings are implemented per-archive and a limit breach does not stop the rest of the run. Quality fails because those are real enforcement and classification bugs, not style nits; the rest of the design is otherwise careful and well tested.

---

### Strengths

- Hard maxima for members, pathname bytes, selected-text member size, expanded bytes, wall time, address space, and stdout cannot be raised (`Limits.__post_init__`, `bounded_archive_inventory.py:83-98`). Defaults match the pinned table (1 GiB AS, 120 s, 200000 members, 100000000 pathname bytes, 16 MiB selected member, 20 GiB expanded, 64 KiB stdout). Tests cover unraisable maxima (`tests/...py:61-90`).
- Path policy is solid for the cases specified: NUL, Unix absolute, Windows `X:\` / `X:/`, UNC `\\` and `//`, `..` escape, backslash/slash unification, `.` / empty-segment collapse, duplicate canonical names (`canonicalize_member_path`, lines 110-132; inventory duplicate handling 476-481). Probes did not need to contradict this.
- Link policy never dereferences or selects symlinks/hardlinks. Safe in-tree targets are `recorded_not_followed`. Devices/FIFOs/unsupported types reject and fail the run. Nested archive suffixes are listed only and not selected (`535-548`).
- Inputs are opened with `lstat` + `O_RDONLY|O_NOFOLLOW` and non-regular/symlink inputs are rejected (`258-274`, `277-296`). Duplicate resolved paths and duplicate basenames raise `InputCollisionError`.
- Selected writes fail closed on output-dir symlink escape. Probes `output_selected_symlink_escape` and `selected_intermediate_symlink_escape` planted `output/selected` and `output/selected/docs` as symlinks to an outside directory; both produced `selected_write` / `PathEscapeError` and leaked nothing.
- Inventory documents are written via temp + `fsync` + `os.replace` (`240-255`, `737-741`). `ok=true` is only set when overall status is `ok` (`731-732`). Disk-reserve and parse/limit failures persist `ok=false` documents rather than a successful-looking index.
- Isolation launcher command shape matches the addendum: `timeout --kill-after=5s`, `prlimit --as/--cpu/--core=0/--nofile=64`, `bwrap --unshare-all --die-with-parent --new-session --clearenv`, ro `/usr` + merged-usr symlinks, `--proc`, `--dev`, `--tmpfs /tmp`, explicit input/tool ro-binds, explicit output bind, no `/home`, `/root`, or `/cursor`. `noexec_output_demonstrated` is hard-coded `False` and tests assert that honesty (`isolate_inventory.py:178-188`; test line 651).
- TDD evidence exists: red-initial `ModuleNotFoundError`, red-after-stubs `48 tests` / `FAILED (failures=34, errors=10)`, green-final `Ran 48 tests in 0.101s` `OK`. Implementer residual notes (AS vs RSS, disk checked once, `r:gz` not `r|gz`, noexec not demonstrated) are accurate and were not over-claimed.
- Compensating non-exec mode bits on selected files are enforced (`os.chmod(dest, 0o644)` at `_write_selected_file` line 355). The selected-plaintext test checks mode `0o644`.

---

### Issues

#### Critical (Must Fix)

None. No sandbox escape, no execution of archive members, and no successful write outside `--output-dir` was demonstrated. The problems below break written ceilings and member classification, which is enough to fail SPEC and block a three-archive pre-read, but they are not exploits.

#### Important (Should Fix) — blocking for catalog pre-read

1. **Invocation-level ceilings are reset per archive (SPEC miss; proven)**
   - File: `bounded_archive_inventory.py:382-385` (counters local to `_process_archive`) and `716-726` (outer loop never accumulates them)
   - Evidence: probe `cross_archive_max_members` — two archives with 2 files each and `max_members=3` returned `ok=True`, `member_counts=[2, 2]`. Probe `cross_archive_max_expanded` — two archives each expanding 80 bytes under `max_expanded_bytes=100` returned `ok=True`, `expanded=[80, 80]`.
   - Why it matters: the addendum table (requirements lines 32-36) specifies a streaming member counter of 200000, **total** pathname/metadata bytes of 100000000, and **aggregate** expanded data of 20 GiB. Those words are invocation-level, and the intended later use is one run over three catalog originals (5.56 GiB compressed). Per-archive reset allows up to 3× members, 3× pathname bytes, and 3× 20 GiB logical expansion in a single command.
   - Action: keep running totals in `inventory_archives` (members, pathname bytes, expanded bytes) and pass the remaining budget into `_process_archive`. When any remaining budget is exhausted, stop and mark `partial`. Add a synthetic cross-archive test. Plan-owner alternative: rewrite the addendum to say “per archive” and accept 3× exposure — that is a requirement change, not the current text.

2. **Limit / parse stop does not stop the run (SPEC miss; proven)**
   - File: `bounded_archive_inventory.py:716-726` (no `break` after `partial` or `failed`)
   - Evidence: probe `continues_after_limit_and_may_select_from_later_archive` — archive 1 hit `max_members exceeded` (`status=partial`), archive 2 was still fully inventoried (`status=ok`) and `--select later.txt` wrote `selected/later.txt`.
   - Why it matters: the ceiling table says “exceed => stop, mark partial/failed”. Continuing later inputs after a budget breach, and still materializing selected plaintext from them, is not a stop.
   - Action: after any archive returns `partial` (limit/parse) — and likely also after `failed` security status if fail-closed stop is desired — break the outer loop. Do not select/write from subsequent archives. Test it.

3. **Absolute/escaping member names on symlinks/hardlinks can overwrite `rejected` with `recorded_not_followed` (proven)**
   - File: `bounded_archive_inventory.py:469-505`
   - Sequence: path reasons set `decision = "rejected"` (470-474); later `elif kind in {"symlink", "hardlink"}` (495-505) calls `classify_link_target(canonical or "", info.linkname)` and, if the target is a safe relative name, sets `decision = "recorded_not_followed"`.
   - Evidence: probe `absolute_symlink_member_decision` — member `raw=/abs/link` has `reasons=["absolute_path"]` but `decision="recorded_not_followed"`. Overall `status=failed` still, because `security_failed` remains True (618-620).
   - Why it matters: overall atomic status is still `ok=false` (so this is not a successful-looking index). The inventory table, however, mislabels a policy-rejected member. That will confuse any later consumer that filters on `decision`.
   - Action: only evaluate link-target policy when the member path itself was accepted; never downgrade `rejected` to `recorded_not_followed`. Add a fixture like `/abs/link` -> `relative-target`.

4. **Sparse logical-size accounting is not demonstrated against parser-surfaced members**
   - File: `bounded_archive_inventory.py:161-173`; test `tests/test_bounded_archive_inventory.py:291-311`
   - Helper behavior is correct on a hand-built `TarInfo` (`size=10`, `sparse=[(0,4),(9996,4)]` => 10000; probe `sparse_parser_vs_helper`).
   - The integration half of the official test writes `size=10000` plus a `.sparse` attribute and then asserts `"max_expanded_bytes" in errors or status in {failed, partial}`. Because `info.size` alone is already 10000, the test passes even if the sparse map is ignored.
   - Probe write/read via stdlib `tarfile` did **not** persist `.sparse` (`readback.sparse=None`, `size=10`); inventory then charged 10 bytes and returned `ok=True` under `max_expanded_bytes=100`.
   - Why it matters: GNU/PAX sparse members can advertise a small stored size and a large logical size. The helper would count the extent *if* `info.sparse` is populated after `next()`. That path is unproven with real parser output, and CPython does rewrite `size` to `origsize` for GNU sparse (`tarfile.py` `_proc_sparse` sets `self.size = origsize`). PAX sparse (`GNU.sparse.size` / `realsize`) also patches `size`. So in many real cases `info.size` after parse *is* logical — but the test does not prove it, and a member with a sparse map plus a stale small `size` would under-count if the parser left `sparse=None`.
   - Action: build a fixture the reader actually surfaces as sparse (or assert on `logical_member_size(info)` from `tf.next()`, not only a synthetic object), with stored size below the cap and logical size above it. Treat current test as non-authoritative for this requirement.

5. **`tarfile.next()` allocates PAX/GNU payloads before any tool budget runs (inherent; must be treated as a residual with isolation as the backstop)**
   - File: `bounded_archive_inventory.py:411-420` (`mode="r:gz"` then `tf.next()`); CPython `tarfile.py` `_proc_pax` / `_proc_gnulong` (`fileobj.read(self._block(self.size))` then return the *next* header, never yielding type `x`/`g`/`L`/`K` to the caller).
   - Evidence: probe `gnu_longname_surface_as_metadata` — only a regular file was surfaced. Probe `pax_payload_vs_pathname_budget` — a 2 MiB PAX `comment` was fully present on the `TarInfo` returned by `next()` (`reader_pax_comment_len=2097152`) before the tool applied `max_pathname_bytes=100`. The tool then correctly fail-closed (`partial`, `member_count=0`, `pathname_bytes=0`) *after* that allocation.
   - The metadata branch at lines 447-461 and `_pax_records_valid` (641-665) are therefore largely unreachable for headers the stdlib consumes internally. The extra PAX validator also measures record length on a UTF-8 *string*, while PAX lengths are byte lengths — dead in normal operation, and wrong if it ever ran on non-ASCII records.
   - Why it matters: this matches the addendum’s own warning that `tarfile` is a parser, not a sandbox. Semantic pathname caps cannot prevent the parser from reading a huge extended header. The compensating control is `prlimit --as=1GiB` plus 120 s wall **when the launcher is used**. Direct `inventory_archives()` / `bounded_archive_inventory.py` has only the in-process wall check (and that check runs between members, not during `next()` or `_consume_payload`).
   - Action: do not claim semantic caps contain parser allocations. Require `isolate_inventory.py` for any catalog parse. Optionally document that metadata-member handling is best-effort/unreachable under CPython 3.13. Do not write a second full tar parser (addendum forbids it). Plan-owner decision: accept AS/wall as the allocation backstop.

#### Minor (Nice to Have)

1. **`min_free_disk_bytes` has no 10 GiB floor** (`bounded_archive_inventory.py:99-100`). `Limits(min_free_disk_bytes=1)` is accepted (probe). The addendum says tests may *raise* the reserve to force failure and that the production CLI default is 10 GiB; it does not say the CLI may lower the reserve. `--min-free-disk-bytes 1` would weaken the control. Action: floor CLI values at `HARD_MIN_FREE_DISK_BYTES`; allow API override only behind an explicit test helper if needed.

2. **Disk reserve is checked once before work** (`684`, `703-710`). Matches “before work” in the addendum. Consequence: a start-of-run free amount ≥ 10 GiB can still be exhausted by selected copies (per-member cap 16 MiB, expansion budget up to 20 GiB, no separate selected aggregate cap — as the implementation report already notes). `selected_write` OSError fail-closes, but partial selected files may remain beside a `failed` inventory. Not a spec violation of the current “before work” wording.

3. **`prlimit --as` is virtual address space, not RSS** (`isolate_inventory.py:33`). Documented honestly. Consequence: it will stop large `mmap`/heap growth in the isolated process, and it can also kill a legitimate Python+gzip working set if VSZ exceeds 1 GiB; it is not `memory.max` / RSS. Adequate as a process backstop, not a cgroup guarantee.

4. **noexec output is not demonstrated; bwrap tmpfs executes.** Matches current addendum lines 100-103 and `noexec_output_demonstrated: false`. Compensating controls (never exec members; selected mode `0o644`) are implemented. **Earlier-plan vs current-requirement discrepancy:** an earlier plan proposed a non-executable output/stage directory. The current implementable addendum explicitly relaxes that because remount `noexec` failed without superuser and default tmpfs exec is allowed on this box. This review cannot “fix” noexec without relaxing the current requirement further or gaining mount privileges the addendum says are unavailable. **Plan-owner decision (already recorded in the addendum): accept compensating controls.** Residual consequence: `selected/` is untrusted plaintext on an executable filesystem; nothing in this tool should be run as code, and a later user/tool could execute a selected script that contains no NUL. That is not silently unsafe if operators treat output as data; it is not a demonstrated noexec sandbox.

5. **Mode-bit documentation mismatch.** Implementation report says selected files are created `0600` then chmod’d `0644`. Code opens with `0o644` then `chmod(..., 0o644)` (`349-355`). Final mode matches the addendum (`0o644`); the report is slightly wrong.

6. **Dead / leftover selected-read code.** `rest_hasher = hasher` is unused (`558`). After a `want` read, an extra leftover drain (`575-577`) is redundant when `_consume_payload` already ran. Harmless.

7. **In-process wall deadline is checked only at the top of the member loop** (`414-418`), not during `tf.next()` or `_consume_payload`. A single huge regular member (up to the remaining expansion cap) can run past `wall_seconds` until the launcher `timeout`/`prlimit --cpu` fires. Action: rely on the launcher for catalog work; optionally also check the deadline inside the read loop.

8. **`r:gz` retains `TarInfo` objects in `TarFile.members`.** Mode is `r:gz` (`411`), so `TarFile.stream` is False and CPython appends every member (`tarfile.py:2840-2842`). On this Python 3.13, `open(..., "r|gz")` also leaves `stream=False` (it passes a `_Stream` as `fileobj`, not `stream=True`). The tool additionally keeps its own `members` list and `json.dumps` the whole document. Consequence: peak memory is roughly two full indexes plus parser/PAX allocations, bounded in isolation by 1 GiB AS. “Streaming” is semantic (one member processed at a time for policy) rather than allocation-free.

9. **Launcher follows input symlinks** (`isolate_inventory.py:81`, `Path.resolve()` then `--ro-bind`). The inner reader would have rejected a symlink input. Consequence: `isolate_inventory.py --input some-link` binds the resolved regular file. Operator convenience, slight policy inconsistency. Minor.

10. **Cross-archive selected path collision.** Selected files from different inputs share `output/selected/<canonical>`. A second `README` with `O_EXCL` becomes `selected_write` / overall failed. Fine fail-closed; surprising if three source trees are selected by the same names. Prefixing by input stem would be clearer (and would need a spec tweak).

11. **`emit_stdout` truncation can yield invalid JSON** (`775-778`). Unlikely for the short status object.

12. **FILELIST.txt self-hash is stale** (the listed hash of `FILELIST.txt` cannot match a file that already contains that hash). Review copies of the code/tests/addendum otherwise matched production.

13. **GNU long-name pathname costing double-counts when the writer used PAX `path=`** (probe: name 149 + key `path` + value 149 = 302). Conservative, fail-closed, fine.

---

### Requirement checkpoints (requested review surfaces)

| Surface | Enforcement vs assertion |
|---|---|
| Parsing/allocation before limits (PAX/GNU long names/sparse) | Stdlib reads extended-header payloads inside `next()` before budgets. Tool then charges visible `name`/`linkname`/`pax_headers` and fail-closes if over cap. Metadata-member branch mostly unreachable. Sparse helper exists; parser-surfaced sparse unproven (see Important #4-#5). |
| Streaming read / gzip truncation / accounting | Truncation and malformed gzip tests exist and the green artifact shows they passed. Expansion is charged from declared logical size before payload read (`508-514`). `extractfile()` is size-bounded by the parser. A lying undersize header becomes the next header (stdlib behavior). `--hash-input` reads the whole file once, seeks to 0, then parses (`396-408`). |
| Cross-archive / within-archive ceilings | Within one archive: member, pathname, and expanded caps stop that archive and mark `partial` (tests exist). Across archives: **not enforced**; run continues (Important #1-#2). Wall deadline *is* shared (`712`). |
| Path / link / type / duplicate collision | Path and duplicate-canonical policy enforced. Link escape/absolute rejected overall. Member-level decision can be wrong for bad names that are also links (Important #3). Type rejects for device/fifo/unsupported present. |
| Selected text, non-execution, plaintext | Select only accepted regular non-nested files ≤ cap with no NUL; `O_CREAT\|O_EXCL`; chmod `0644`. Nested names not selected. |
| Symlink output dir / TOCTOU | `contained_path` resolve + prefix check rejected planted selected-root and intermediate symlinks. Dest open uses `O_EXCL` (rejects an existing dest symlink on Linux). No `openat`/`O_NOFOLLOW` walk of parents; risk is a hostile pre-existing output tree plus a race, not archive-created output links (dirs are not extracted). |
| Atomic status correctness | JSON/MD replaced via fsync+replace. `ok` tied to `status==ok`. Policy rejects => overall `failed` even when a member decision string is wrong. Limit mid-run => `partial`. Input/output collision raises without writing a fake-success index. Failed run after some selected writes leaves those files on disk. |
| Isolation scope / resource wrappers | Command contents match the addendum. Integration artifact and test: home hidden, net ns differs, inventory written, `noexec_output_demonstrated=false`. AS via `prlimit --as` (not RSS). Disk reserve once. bwrap tmpfs/output bind remain executable. |

---

### Recommendations

- Fix Important #1–#3 before any multi-input catalog run. Add the missing cross-archive and “stop means stop” tests, and a real sparse/parser test (#4).
- Use only `isolate_inventory.py` (not the bare reader) against large untrusted inputs, and treat AS/wall as the allocation backstop (#5).
- Ask the plan owner to reconfirm the already-written noexec relaxation if they still want a non-executable output mount; this implementation cannot demonstrate one on this box.
- Do not interpret a later SPEC-compliant inventory as board support, a boot route, or a replacement OS. This tool only indexes archives.

---

### Assessment

**Ready to merge?** No — with fixes.

**Reasoning:** The reader is a serious, fail-closed `tarfile` wrapper with good path/link/output-containment behavior, honest isolation claims, and a real red/green test trail. It does not yet implement the addendum’s aggregate ceilings or “stop on exceed” across multiple inputs, and one member-decision path is wrong even though overall `ok` stays false. Those are SPEC defects with probe evidence. The pre-read checkpoint for the three hashed catalog originals cannot truthfully pass until the aggregate/stop fixes land (or the plan owner explicitly changes the requirement to per-archive caps).

**Pre-read checkpoint can truthfully pass?** **No.**

---

### Reviewed file hashes (SHA-256)

Production / review copies (identical pairs noted):

```
ba145793ab053cd6994d5a6085cba2dba4dccf01058eb8f61d487a99c559edec  tooling/bounded_archive_inventory.py
ba145793ab053cd6994d5a6085cba2dba4dccf01058eb8f61d487a99c559edec  tooling/review/bounded_archive_inventory.py
3fd6a0ed92af40d2ac692c104a4100945aa259c944359726c60375cda8b002b5  tooling/isolate_inventory.py
3fd6a0ed92af40d2ac692c104a4100945aa259c944359726c60375cda8b002b5  tooling/review/isolate_inventory.py
789a20eeeaf500c55520b16b9db957a2bb3e1c2252e923565feeb6b38e59bd50  tooling/tests/test_bounded_archive_inventory.py
789a20eeeaf500c55520b16b9db957a2bb3e1c2252e923565feeb6b38e59bd50  tooling/review/tests_test_bounded_archive_inventory.py
6d8a9b73ed7543717a4ea7d2d577ade69b4ddfaf46ccd4774062b32a3f3a2bca  tooling/implementation-report.md
6d8a9b73ed7543717a4ea7d2d577ade69b4ddfaf46ccd4774062b32a3f3a2bca  tooling/review/implementation-report.md
05af85744c46c505473c5319eecd44d320bfdd77cf4e1b5e5676e5b1c883df51  docs/superpowers/plans/2026-11-08-bounded-source-inventory.md
05af85744c46c505473c5319eecd44d320bfdd77cf4e1b5e5676e5b1c883df51  tooling/review/2026-11-08-bounded-source-inventory.md
42e9c3acc010bc581825417f3b6a6a3e66d1e88a65241105e734fb4e91d6b3c6  tooling/review/from-empty.diff
```

Probe artifacts: `tooling/review/probes/bai_review_probes.py`, `probe-results.json`, `probe-results.md`. No catalog filenames were opened as inputs.

Existing test evidence: `tooling/artifacts/green-final.txt` (`Ran 48 tests in 0.101s` / `OK` / `EXIT:0`, 2026-11-08 04:38 Atlantic/Reykjavik). Not re-run as a whole suite.
