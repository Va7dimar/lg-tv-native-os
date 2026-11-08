# Re-review targeted synthetic probes (2026-11-08)

No catalog archives were opened.

## cross_archive_max_members

```json
{
  "name": "cross_archive_max_members",
  "ok": false,
  "status": "partial",
  "member_counts": [
    2,
    1
  ],
  "totals": {
    "member_count": 3,
    "pathname_bytes": 15,
    "expanded_bytes": 3,
    "selected_text_bytes": 0
  },
  "skipped": [],
  "errors": [
    "max_members exceeded"
  ],
  "fixed": true
}
```

## cross_archive_max_expanded

```json
{
  "name": "cross_archive_max_expanded",
  "ok": false,
  "status": "partial",
  "expanded": [
    80,
    0
  ],
  "totals": {
    "member_count": 1,
    "pathname_bytes": 10,
    "expanded_bytes": 80,
    "selected_text_bytes": 0
  },
  "errors": [
    "max_expanded_bytes exceeded"
  ],
  "fixed": true
}
```

## stop_after_partial_no_later_select

```json
{
  "name": "stop_after_partial_no_later_select",
  "ok": false,
  "status": "partial",
  "n_archives": 1,
  "skipped": [
    "/tmp/rr-stop-hzn_nfbv/second.tar.gz"
  ],
  "later_exists": false,
  "fixed": true
}
```

## stop_after_failed

```json
{
  "name": "stop_after_failed",
  "ok": false,
  "status": "failed",
  "n_archives": 1,
  "skipped": [
    "/tmp/rr-fail-kg6mlggk/after.tar.gz"
  ],
  "fixed": true
}
```

## absolute_symlink_stays_rejected

```json
{
  "name": "absolute_symlink_stays_rejected",
  "decision": "rejected",
  "reasons": [
    "absolute_path"
  ],
  "status": "failed",
  "fixed": true
}
```

## namespaced_selected

```json
{
  "name": "namespaced_selected",
  "ok": true,
  "left": "b'one'",
  "right": "b'two'",
  "fixed": true
}
```

## isolate_rejects_symlink_input

```json
{
  "name": "isolate_rejects_symlink_input",
  "raised_input_error": true,
  "error": "symlink input rejected: /tmp/rr-isl-vegdzegc/link.tar.gz",
  "fixed": true
}
```

## stream_true_no_tarinfo_cache

```json
{
  "name": "stream_true_no_tarinfo_cache",
  "stream": true,
  "counted": 2,
  "members_during": [
    [],
    []
  ],
  "fixed": true
}
```

## cli_disk_floor

```json
{
  "name": "cli_disk_floor",
  "rc": 2,
  "inventory_exists": false,
  "production_limits_rejects_low": true
}
```

## api_disk_floor_without_for_tests

```json
{
  "name": "api_disk_floor_without_for_tests",
  "accepted": false,
  "fixed": true
}
```

## emit_stdout_valid_json

```json
{
  "name": "emit_stdout_valid_json",
  "valid": true,
  "parsed": {
    "status": "ok",
    "ok": false,
    "truncated": true,
    "error": "stdout_truncated"
  },
  "text": "{\"status\":\"ok\",\"ok\":false,\"truncated\":true,\"error\":\"stdout_truncated\"}",
  "fixed": true
}
```

## exact_member_cap_complete_archive

```json
{
  "name": "exact_member_cap_complete_archive",
  "ok": false,
  "status": "partial",
  "member_count": 2,
  "errors": [
    "max_members exceeded"
  ],
  "totals": {
    "member_count": 2,
    "pathname_bytes": 10,
    "expanded_bytes": 2,
    "selected_text_bytes": 0
  },
  "note": "If status=partial after exactly max_members and no leftover members, exhausted() uses >= after the last increment.",
  "is_false_partial": true
}
```

## hash_input_with_stream_open

```json
{
  "name": "hash_input_with_stream_open",
  "ok": true,
  "expected": "8b3aac3c16437093c3610639cc91374947093433399a4a91f9d598676c4cda1b",
  "got": "8b3aac3c16437093c3610639cc91374947093433399a4a91f9d598676c4cda1b",
  "matched": true,
  "members": 1
}
```

## gnu_sparse_parser_surfaced

```json
{
  "name": "gnu_sparse_parser_surfaced",
  "parser_size": 10000,
  "parser_sparse": true,
  "logical": 10000,
  "inventory_ok": false,
  "inventory_status": "partial",
  "member": {
    "index": 0,
    "raw_name": "sparse.bin",
    "canonical_name": "sparse.bin",
    "type": "file",
    "size": 10000,
    "link_target": null,
    "decision": "accepted",
    "reasons": [
      "max_expanded_bytes"
    ],
    "selected": false,
    "selected_output": null,
    "sha256": null,
    "nested_archive_not_expanded": false,
    "sparse": true
  },
  "errors": [
    "max_expanded_bytes exceeded"
  ],
  "fixed": true
}
```

## ceilings_unchanged

```json
{
  "name": "ceilings_unchanged",
  "members": true,
  "pathname": true,
  "selected": true,
  "disk": true,
  "expanded": true,
  "as_bytes": true,
  "wall": true,
  "stdout": true,
  "fixed": true
}
```

## controls_honesty

```json
{
  "name": "controls_honesty",
  "isolation_required": true,
  "parser_before_limits": true,
  "stream": true,
  "noexec_ctl": false,
  "noexec_obs": false,
  "selected_not_noexec": true,
  "never_exec": true
}
```

## for_tests_cannot_raise_maxima

```json
{
  "name": "for_tests_cannot_raise_maxima",
  "rejected": true,
  "fixed": true
}
```
