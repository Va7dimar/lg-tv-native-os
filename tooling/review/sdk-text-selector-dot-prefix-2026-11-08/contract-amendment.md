# Contract amendment: GNU/PAX `./` raw-name match

This amends `tooling/review/sdk-text-selector-2026-11-08/contract.md` after
independent review `tooling/review/sdk-text-selector-independent-review.md`
(SHA256 `8740357586f1b2fe558a3321a20934fe5e52f992f86c0add8d553295c40f5ece`)
returned SPEC FAIL / QUALITY PASS.

The original sentence "A selected member whose maintained-parser name is an
alias of its selector fails" remains true for every alias except one explicit
stored-name form produced by the maintained tar parser for GNU-style archives:

- A member matches a selector only if `member.name` is exactly `selector.path`
  or exactly `'./' + selector.path`.
- Selectors themselves remain strictly canonical. A selector of `./…` is still
  rejected by `validate_selectors` (`canonical(path) != path`).
- All other raw names remain aliases and fail closed, including `././x`,
  `.//x`, `/x`, `a/../x`, `x/`, `d//a`, `d/./a`, trailing slashes, doubled
  slashes, and parent-directory forms.
- `raw_name` continues to record the maintained-parser name unchanged.
- No other path normalization, glob, regex, link resolution, or nested
  expansion is introduced.

All other contract clauses are unchanged: 16 MiB/member and 64 MiB/shared
configuration caps; exact indexed sizes; regular files only; plaintext is
strict UTF-8 with printable Unicode plus TAB/LF/CR; NUL/binary/nonprintable
rejection; selected symlinks and other nonregular types fail and are never
followed; generated `selected-NNNNNN.txt` writes use `O_EXCL|O_NOFOLLOW` and
mode 0600; default empty selectors remain METADATAONLY; FD cleanup and
`stdin=DEVNULL` are unchanged; no SDK asset, installer, compiler, or TV action
is part of this amendment.

The proposed production command is unchanged (canonical selectors, shared bound
50478, fresh output `inspection-selected-text-PENDING-REVIEW`). It must not be
executed until this amendment receives independent SPEC/QUALITY PASS.
