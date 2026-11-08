# SDK selected plaintext implementation — synthetic evidence only

Implemented optional literal selectors in `tooling/sdk_inventory_phase.py` and
passed their configuration through `tooling/isolate_sdk_inventory.py`. Added
`tooling/tests/test_sdk_text_selector.py`; no existing test or unrelated helper,
adaptation file, repository configuration, or SDK asset was modified. No repository
was created. No actual SDK input was opened, hashed, parsed, or executed. No actual
selected member was read, and the proposed production command was not executed.

The preimplementation [contract](contract.md) defines the exact interface and
plaintext policy. Each selector carries input ID, canonical literal member path,
and exact indexed byte count. Selected regular files must match that count and
pass strict UTF-8/printable-Unicode validation (TAB/LF/CR allowed). Bytes are
validated completely before exclusive/nofollow creation of generated mode-0600
data files. Selected JSONL rows retain original input ID, resolved original member
name, size, SHA-256, and generated output data path. No archive path is extracted.
Missing selectors, aliases, links/nonregular members, duplicate selectors, bad
sizes, invalid text, or stream failures cannot produce an ok=true manifest.
Previously validated data may remain in a failed/partial output directory.

The one selected-byte budget covers all three inputs. Limits remain at most
16 MiB/member and 64 MiB/shared total. Existing shared inventory limits, immutable
input pins, full pin verification before parsing, bounded decoders, complete EOF
draining, corruption checks, link metadata classification, and output confinement
remain in place. Default mode is still METADATAONLY. In selected mode, unselected
content is neither emitted nor content-hashed; complete decompression/integrity
validation still occurs. Absolute unselected symlinks remain metadata-only and
are never followed. Nested expansion is absent.

The launcher changes only configuration forwarding, validation, and truthful
failure-mode labeling. [preserved-invariants.json](preserved-invariants.json)
records 24 equal AST/literal comparisons, including unchanged input pins, Limits,
Budget, DecodedReader, tar header hooks, output traversal/publication helpers,
build_command, standard descriptor normalization, high-FD cleanup, and the exact
subprocess.run call with stdin=DEVNULL, pass_fds, and timeout. This is local
implementation evidence, not independent review or proof of sandbox execution.

| Run | Test methods | Result | Process exit |
| --- | ---: | --- | ---: |
| RED, before production edits | 23 | Expected 126 error entries from missing selector API/CLI; default metadata test passed | 1 |
| First GREEN | 23 | No failures/errors; 1 sandbox skip | 0 |
| Final targeted GREEN | 23 | 22 passed; 1 sandbox skip | 0 |
| All SDK tests (`test_sdk*.py`) | 70 | No failures/errors; 11 skip entries | 0 |

All runs use ordinary Python unittest and synthetic temporary fixtures. RED
production hashes equal the supplied before snapshots. The original RED test
source is retained as `RED.test_sdk_text_selector.py`; the final test source adds
only whitespace cleanup and persistence of synthetic sandbox evidence. The full
suite contains all 47 existing SDK test methods plus the 23 new methods. Its 11
skip entries comprise four whole test methods and seven closed-stdio subtests;
subtracting eleven from seventy is not a valid passed-method count. Raw stdout,
stderr, exit files, commands, timestamps, and counts are in
[test-results.json](test-results.json) and the corresponding RED/GREEN/SDK-suite
logs. Unrelated test suites were not run.

The new suite covers success and byte/hash equality across inputs, exact/mismatched
sizes, multiple/duplicate/missing selectors, unknown IDs, negative/overflow sizes,
glob/path aliases/traversal/control characters, member aliases, selected links
and nonregular types, strict UTF-8/NUL/control/binary rejection, exact shared caps,
16 MiB actual-member boundary, 64 MiB configuration boundary, empty text,
unselected content, default metadata mode, output freshness/symlinks, all pins
before parsing, later-input corruption, tar EOF, unchanged shared caps, launcher
forwarding/DEVNULL, and lack of nested expansion.

Sandbox integration was attempted through the unchanged bwrap command. The
runtime returned `bwrap: loopback: Failed to create NETLINK_ROUTE socket:
Operation not permitted` before starting the reader. Raw launcher stderr,
launcher-result.json, and failed manifests are retained in `sandbox-targeted/`
and `sandbox-full-suite/`; all seven closed-stdio failure records are retained in
`stdio-full-suite/`. Consequently, this package does not establish successful
end-to-end sandboxed selected-text execution or new runtime FD isolation proof.
Bare bootstrap cleanup tests passed, including the inherited descriptor above
RLIMIT_NOFILE and fail-closed cleanup tests. No sandbox bypass, permission flags,
host FD reopening, weakened isolation, network access, TV action, installer,
compiler, source execution, or other-model invocation was used.

[exact-command.txt](exact-command.txt) is a proposal only, derived from the prior
links-inventory command. It keeps all three input paths and immutable pins,
changes the output to the requested fresh
`inspection-selected-text-PENDING-REVIEW` directory, and adds exactly the ten
handoff selectors with their indexed sizes plus `--selected-total-bytes 50478`.
There are six SDK and four target selectors; the native input remains fully
pinned and inventoried. No other bound changes. Argument validation only was
performed, with input opening guarded against; see
[command-validation.json](command-validation.json). The command file SHA-256 is
`4856e812ece17229f0872f22ae66921bca78c80fb97fe9ae465c5dd3749963d7`.

| Current file | SHA-256 |
| --- | --- |
| sdk_inventory_phase.py | `77922ceb9757797055a42feeebc7e1da702bbca3c0f677fb87a00f58f3b048cf` |
| isolate_sdk_inventory.py | `c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a` |
| test_sdk_text_selector.py | `537c33d6b8783b44e906abe5c3e071ffae4b3f4c60ed8cc5e0c6dc7a2860355b` |

Whole-file before/current snapshots and unified diffs are under `before/`,
`current/`, and `diffs/`; a marker records the new test's prior absence.
[hashes.json](hashes.json) records byte sizes and hashes, and `SHA256SUMS` verifies
the review artifacts. Actively written, harness-owned codex event/stderr/prompt
files are explicitly excluded from that stable artifact index. The standard
library `prepare_review.py` reproduces packaging and literal command validation;
it never launches the SDK phase.

Requested model: no exact model identifier was specified in the request visible
to this worker; requested role was primary implementation worker. Observed
serving model/revision: not exposed and unverified. The developer describes
Codex as based on GPT-6; that description is not observed serving-model metadata.
No model identity or independent reviewer PASS is inferred or claimed.

Remaining work belongs to independent SPEC/QUALITY review and the parent: assess
the contract/diffs and command, rerun the unchanged synthetic sandbox tests on a
host that permits bwrap, and decide the actual-run handoff. No actual SDK phase
or new owner approval was attempted in this implementation task.
