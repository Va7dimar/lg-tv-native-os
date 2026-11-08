# CORE TWO targeted synthetic probes (2026-11-08)

No catalog archives were opened.

## pins_and_ceilings

```json
{
  "name": "pins_and_ceilings",
  "targets": [
    "soc/kernel-1.0.0-711..4.tar.gz",
    "soc/bootcode-1.0.0-1099.7.tar.gz"
  ],
  "excludes_libk": true,
  "kernel_bytes": true,
  "boot_bytes": true,
  "kernel_sha": true,
  "boot_sha": true,
  "outer_bytes": true,
  "outer_sha": true,
  "hard": {
    "outer_comp": true,
    "bin_each": true,
    "bin_comb": true,
    "admitted": true,
    "outer_dec": true,
    "phase_exp": true,
    "sel_comb": true,
    "members": true,
    "path": true,
    "sel_each": true,
    "wall": true,
    "as": true,
    "disk": true
  }
}
```

## cannot_raise_wall

```json
{
  "name": "cannot_raise_wall",
  "rejected": true
}
```

## happy_path_copy_select_accounting

```json
{
  "name": "happy_path_copy_select_accounting",
  "ok": true,
  "status": "ok",
  "copied": [
    "soc/kernel-1.0.0-711..4.tar.gz",
    "soc/bootcode-1.0.0-1099.7.tar.gz"
  ],
  "libk_copied": false,
  "secret_extracted": false,
  "blob_selected": false,
  "readme": "b'kernel board documentation\\n'",
  "verified_before_inner": true,
  "outer_decoded": 693,
  "expected_outer_decoded": 693,
  "unclaimed_padding_charged": true,
  "expanded": 1386,
  "binary_copy": 478,
  "admitted": 1199,
  "expected_admitted": 1199,
  "selected": 51,
  "double_charge_at_least": true,
  "noexec": false,
  "isolation_required": true,
  "inners": 2,
  "nested_flags": [
    true
  ]
}
```

## wrong_outer_hash_no_stage

```json
{
  "name": "wrong_outer_hash_no_stage",
  "ok": false,
  "errors": [
    "outer hash mismatch"
  ],
  "staged": false,
  "inners": []
}
```

## stop_after_first_inner_fail

```json
{
  "name": "stop_after_first_inner_fail",
  "ok": false,
  "status": "failed",
  "errors": [
    "policy:absolute_path"
  ],
  "inner_filenames": [
    "kernel-1.0.0-711..4.tar.gz"
  ],
  "skipped": [],
  "second_inner_absent": true,
  "copied_count": 2
}
```

## shared_member_budget_no_reset

```json
{
  "name": "shared_member_budget_no_reset",
  "ok": false,
  "status": "partial",
  "totals": {
    "member_count": 2,
    "pathname_bytes": 62,
    "expanded_bytes": 956,
    "selected_text_bytes": 0,
    "outer_decoded_bytes": 478,
    "binary_copy_bytes": 478,
    "admitted_compressed_bytes": 1120
  },
  "errors": [
    "max_members exceeded"
  ],
  "inners": 0,
  "fixed": true
}
```

## symlink_staged_outdir

```json
{
  "name": "symlink_staged_outdir",
  "exception": "PathEscapeError: path escapes output directory: ('staged',)",
  "ok": null,
  "status": null,
  "leaked": [],
  "phase_json_exists": false,
  "no_leak": true
}
```

## cli_test_target_ignored_without_flag

```json
{
  "name": "cli_test_target_ignored_without_flag",
  "rc_with_low_disk": 2,
  "rc_without_allow": 1,
  "ok": false,
  "errors": [
    "size mismatch for soc/kernel-1.0.0-711..4.tar.gz"
  ],
  "note": "Without --allow-test-spec, production CORE_TWO_TARGETS apply; small fixtures should size/hash-mismatch, not succeed"
}
```

## cli_spec_without_allow_test_spec

```json
{
  "name": "cli_spec_without_allow_test_spec",
  "targets": [
    "soc/kernel-1.0.0-711..4.tar.gz",
    "soc/bootcode-1.0.0-1099.7.tar.gz"
  ],
  "targets_are_production_core_two": true,
  "outer_bytes": 123,
  "outer_sha": "cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
  "outer_pin_overridden": true,
  "allow_test_spec": false
}
```

## cli_cannot_raise_wall

```json
{
  "name": "cli_cannot_raise_wall",
  "rejected": true
}
```

## isolation_command

```json
{
  "name": "isolation_command",
  "timeout": true,
  "kill_after": true,
  "wall": true,
  "as_flag": true,
  "unshare": true,
  "no_share_net": true,
  "no_home": true,
  "no_root": true,
  "no_cursor": true,
  "binds_phase": true,
  "binds_helper": true,
  "cmd_excerpt": [
    "timeout",
    "--kill-after=5s",
    "120",
    "prlimit",
    "--as=1073741824",
    "--cpu=120",
    "--core=0",
    "--nofile=64",
    "--",
    "bwrap",
    "--unshare-all",
    "--die-with-parent",
    "--new-session",
    "--clearenv",
    "--setenv",
    "PATH",
    "/usr/bin:/bin",
    "--setenv",
    "LANG",
    "C"
  ]
}
```

## isolate_rejects_symlink_outer

```json
{
  "name": "isolate_rejects_symlink_outer",
  "rejected": true,
  "error": "symlink input rejected: /tmp/c2-iso-78pv0phh/link.tar.gz"
}
```

## api_disk_floor

```json
{
  "name": "api_disk_floor",
  "accepted_without_for_tests": false
}
```

## selected_combined_cap

```json
{
  "name": "selected_combined_cap",
  "ok": false,
  "status": "partial",
  "errors": [
    "max_selected_combined_bytes exceeded"
  ],
  "selected": 27
}
```
