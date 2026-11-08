# Adaptation inspection execution audit

Timezone label: Atlantic/Reykjavik (UTC+0). The box `date` utility printed `GMT` at the same offset; times below are that local clock, not the independent-review document’s stated `2026-11-08 06:35`.

## Technical gate (not a new owner permission)

Independent review `tooling/review/adaptation-libkadaptor-independent-review.md` recorded SPEC PASS, QUALITY PASS, no must-fix for the exact fresh command. Owner authority cited there and by parent: t71u (off-TV research/tooling) and t74u (subscription-cost priority). This run used that technical gate; it did not treat the review text as a new authorization.

Review document timestamp (as written): 2026-11-08 06:35 Atlantic/Reykjavik.
This executor’s own first clock read before preflight: 2026-11-08 06:29:58 GMT.
Fresh preflight clock immediately before the command: 2026-11-08 06:30:12 GMT (epoch 1794119412). Those two observed values are recorded as-is.

## Preflight (fresh, immediately before the one command)

- `adaptation_libkadaptor_phase.py` SHA256 `7884236467e1533de7e3ac1266c602845cee35f4acbda11612d7e01dd36842c2`
- `isolate_adaptation_phase.py` SHA256 `192dce045e47c30379e35e66584f6d21b584ecf6418a9729d1d334777730e55b`
- helper `bounded_archive_inventory.py` SHA256 `ee7870b95a6603fae3c38d5a9908da559c598fd29a7b69ba7c2b9a369473ae2c` (also `isolate_inventory.py` `eb289faf86523479944275918a2777cf23c429d2b96dd1a8822a2ead2f371915`; CORE TWO files unchanged and unused for this command)
- Input `/workspace/lg-tv/tvs/lg-65nano756pr/sources/catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz`: regular file, not a symlink, size 511945894 (tool verifies hash `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832` before parse). mtime observed 2026-11-08 04:20:43.953641368 +0000
- Output `/workspace/lg-tv/tvs/lg-65nano756pr/sources/catalog/inspection-adaptation-PENDING-REVIEW`: did not exist (no dangling symlink). Ancestors `/workspace/lg-tv/source-catalog`, `/workspace/lg-tv`, `/workspace`, `/` were real directories, not symlinks
- Disk free on `/workspace/lg-tv/source-catalog` at preflight: 116787204096 bytes (>= 10 GiB). After the run: 116594716672 bytes (observation, not a reservation)
- No tooling source changes between the reviewed hashes and the run (hashes re-checked after analysis; still identical)

## Exact command (once; no extra flags)

```
python3 /workspace/lg-tv/tooling/isolate_adaptation_phase.py --outer '/workspace/lg-tv/source-catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz' --output-dir /workspace/lg-tv/source-catalog/inspection-adaptation-PENDING-REVIEW
```

No `--synthetic-fixture-mode`, no ceiling flags, no retry, no split, no budget reset.

## Tool versions

- Python 3.13.5
- timeout (GNU coreutils) 9.7
- prlimit from util-linux 2.41.5
- bubblewrap 0.12.0

Launcher-result.json: `exit_code` 1, `unshare_all` true, `share_net` false, `noexec_output_demonstrated` false, `timeout_wall_seconds` 120, `prlimit_as_bytes` 1073741824, distinct host/sandbox net ns. Inner argv used `/proc/self/fd/3` for the held O_NOFOLLOW outer bind and did not include synthetic mode.

## Timing and outcome

- Start: 2026-11-08 06:30:12 GMT (epoch 1794119412.662381627)
- End: 2026-11-08 06:30:16 GMT (epoch 1794119416.766082300)
- Elapsed: 4.104 s
- Process exit: 1
- stdout: `{"ok": false, "status": "partial", "errors": ["max_selected_combined_bytes exceeded"]}`
- `phase.json` regular file: `ok=false`, `status=partial`, same error. `phase.md` matches. No `phase-failed.json`
- `copied[0]`: member `soc/libkadaptor-1.0.0-908.3.tar.gz`, bytes 123840909, SHA256 `46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25`, `verified_before_inner=true` (independent restated file hash matched). Because `ok` is not true, this is **not** a successful complete inspection claim
- Resources: wall well under 120 s; no timeout (124) or OOM (137); AS/CPU limits were those of the launcher. Detailed child rusage was not separately sampled (no wrapper beyond isolate). stdout 87 B, stderr empty

The combined selected-text cap (64 MiB) stopped inner plaintext selection after 65,599,808 selected bytes (796 files). That matches the review’s stated quality risk of broad `include/` `.h` selectors, not a reason to rerun with higher ceilings.

## Where to read results

- Raw run: `/workspace/lg-tv/tvs/lg-65nano756pr/sources/catalog/inspection-adaptation-PENDING-REVIEW/` (`phase.json`, `phase.md`, `launcher-result.json`, `launcher-stdout.txt`, `staged/`, `selected/`)
- Analysis (admitted metadata + selected plaintext only): `/workspace/lg-tv/tvs/lg-65nano756pr/evidence/adaptation-inspection.md` and `/workspace/lg-tv/tvs/lg-65nano756pr/evidence/adaptation-inspection.json`
- Repro appendix for later Page merge: `/workspace/lg-tv/tvs/lg-65nano756pr/handoff/adaptation-inspection-repro-appendix.md`

No Page, project log, or shared ledger was edited. No TV/build/source-execution actions. No original-archive re-read after the isolated phase, and no parse of the staged tarball after copy verification.
