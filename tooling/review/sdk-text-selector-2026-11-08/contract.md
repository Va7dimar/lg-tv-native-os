# Narrow SDK selected plaintext contract

Written before production implementation. Synthetic TDD only. No SDK asset,
archive, selected source member, or actual SDK output is opened by this work.

The default remains METADATAONLY. The optional CLI is repeatable
`--select-text INPUT EXACT_PATH INDEXED_BYTES`, with an explicit
`--selected-total-bytes BYTES` whenever selectors are present. Library calls use
`TextSelector(input, path, size)` and `inventory(..., selectors=...,
selected_total_bytes=...)`; the launcher forwards this literal configuration.
Only sdk/native/target input IDs are valid. No external selector file is loaded.

Selectors are literal canonical relative paths, with no empty/dot/parent
components, leading/trailing/doubled slash, backslash, drive prefix, glob
characters (`*?[]`), NUL, or control/nonprintable characters. No normalization,
regex, glob, alias, link resolution, or nested archive expansion selects content.
A selected member whose maintained-parser name is an alias of its selector fails.
Duplicate input/path selector pairs, unknown inputs, noninteger/negative/overflow
sizes, and bounds above 16 MiB/member or 64 MiB/shared total fail closed. Zero-byte
regular text is allowed. Every file must match its exact indexed size, and the
sum across ALL inputs must fit the one shared bound. The proposed ten selectors
sum to 50478 bytes and use a 50478-byte shared bound, superseding the handoff's
looser proposed bounds. Existing metadata/member/logical/decoder/memory/wall/disk
ceilings and all three immutable input pins remain unchanged.

All input pins are verified before any archive parsing. Existing full stream,
compression integrity EOF, tar zero tail, corruption, link metadata, duplicate
member, and mutation rules remain in force. Selected links (including hardlinks),
directories, sparse files, devices, and every other nonregular type fail; no link
target is followed. Unselected absolute symlinks retain their existing metadata
classification. All requested selectors must be found before success is possible.

Plaintext means strict UTF-8 with only printable Unicode characters plus TAB,
LF, and CR. NUL, other C0 controls, DEL, C1 controls, Unicode format controls,
surrogates, private-use/unassigned characters, and nonprintable separators are
rejected. This is a conservative syntactic policy, not a semantic file-format
detector: printable text that resembles code is still inert data.

Selected bytes are read through the bounded maintained tar stream, completely
validated before writing, hashed with SHA-256, and written unchanged as flat
generated `.txt` data filenames under the already confined output directory.
No member name becomes an output path; no archive extraction or executable mode
is used. Files use exclusive/nofollow creation and mode 0600. Each selected JSONL
record includes original input/path/size, content_sha256, and output_data_path.
Fresh-output, ancestor-symlink refusal, and atomic manifest publication persist.
Any selection or stream failure publishes only ok=false, failed/partial state;
previous validated data may remain as partial evidence, never a successful run.

Verification order: write this contract and synthetic tests; save raw RED stdout,
stderr, and exit against unchanged production; only then implement; run targeted
GREEN followed by all test_sdk*.py tests. Sandbox tests use unchanged isolation;
runtime refusal is recorded honestly, without bypass. No actual SDK phase runs.
Independent SPEC/QUALITY review and any parent execution remain outstanding.
