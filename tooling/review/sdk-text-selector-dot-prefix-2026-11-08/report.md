# SDK selected-plaintext `./` prefix match — synthetic evidence only

Narrow test-first fix after `sdk-text-selector-independent-review.md` SPEC FAIL.
No SDK asset, archive member, installer, compiler, or TV endpoint was opened.
The proposed production command was parsed only and was not launched.

## Change

In `tooling/sdk_inventory_phase.py` `select()`:

```
if member.name not in (selector.path, './' + selector.path):
    raise InventoryError('selected member path alias')
```

`tooling/isolate_sdk_inventory.py` is byte-identical to the previously reviewed
launcher `c4befa0c75267bb99e804076eda54d400edeb651151d61ea5112a4e3fd09387a`.

## Tests

`test_dot_slash_prefixed_regular_member_is_selected` accepts raw names `./a`
and `./dir/text` against canonical selectors, records `raw_name`, writes
mode-0600 generated data files, and checks payload SHA-256.

`test_canonical_member_alias_is_not_selected` now rejects `././a`, `/a`,
`x/../a`, `a/`, `d//a`, `d/./a`, `a/../x`, and `x/`. The previous negative
case `./a` was moved to the positive test.

## Results

| Run | Methods | Result | Exit |
| --- | ---: | --- | ---: |
| RED, tests first against reader `77922ceb…48cf` | 24 | 2 failures, both subtests of the new positive `./` test, error `selected member path alias`; negatives passed | 1 |
| GREEN after the one-line reader edit | 24 | OK, including `test_synthetic_selected_sandbox` | 0 |
| All `test_sdk*.py` | 71 | OK; no unittest skips (`skipped` appears only in two passing test names) | 0 |

Raw logs: `RED.*`, `GREEN.*`, `SDK-suite.*`. Hashes: `hashes.json`, `SHA256SUMS`.
Command parse-only: `command-validation.json` (6 sdk + 4 target, sum 50478,
output dir did not exist). Diffs: `diffs/`.

No actual SDK selected-text phase has run.
