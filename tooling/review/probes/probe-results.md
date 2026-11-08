# Targeted synthetic probe results

No catalog archives were opened. Probes used only temporary synthetic `.tar.gz` fixtures.

## cross_archive_max_members

```json
{
  "name": "cross_archive_max_members",
  "ok": true,
  "status": "ok",
  "member_counts": [
    2,
    2
  ],
  "errors": [],
  "interpretation": "SPEC called for an invocation-level 200000-member streaming counter. Two archives with 2 members each under max_members=3 produced ok=True. Ceilings reset per archive."
}
```

## cross_archive_max_expanded

```json
{
  "name": "cross_archive_max_expanded",
  "ok": true,
  "status": "ok",
  "expanded": [
    80,
    80
  ],
  "errors": [],
  "interpretation": "Two archives each expanded 80 bytes under max_expanded_bytes=100 produced ok=True (aggregate 160). Aggregate ceiling is not cross-archive."
}
```

## continues_after_limit_and_may_select_from_later_archive

```json
{
  "name": "continues_after_limit_and_may_select_from_later_archive",
  "ok": false,
  "status": "partial",
  "archive_statuses": [
    "partial",
    "ok"
  ],
  "archive2_members": [
    "later.txt"
  ],
  "selected_later_exists": true,
  "errors": [
    "max_members exceeded"
  ],
  "interpretation": "After max_members on archive 1 the tool continued archive 2 and wrote a selected file from it."
}
```

## absolute_symlink_member_decision

```json
{
  "name": "absolute_symlink_member_decision",
  "ok": false,
  "status": "failed",
  "members": [
    {
      "raw": "/abs/link",
      "canon": null,
      "decision": "recorded_not_followed",
      "reasons": [
        "absolute_path"
      ],
      "type": "symlink"
    },
    {
      "raw": "ok.txt",
      "canon": "ok.txt",
      "decision": "accepted",
      "reasons": [],
      "type": "file"
    }
  ],
  "interpretation": "Overall status correctly failed, but the absolute-path symlink member was labeled recorded_not_followed instead of rejected because a later safe relative link target overwrote decision."
}
```

## gnu_longname_surface_as_metadata

```json
{
  "name": "gnu_longname_surface_as_metadata",
  "tarfile_next_member_count": 1,
  "surfaced_type": "regular '0'",
  "inventory_types": [
    "file"
  ],
  "pathname_bytes": 302,
  "name_len": 149,
  "interpretation": "Python 3.13 tarfile.next() does not yield GNU/PAX metadata as members. The long name appeared as a regular file; pathname_bytes 302 = name 149 + pax key 'path' 4 + pax value 149."
}
```

## pax_payload_vs_pathname_budget

```json
{
  "name": "pax_payload_vs_pathname_budget",
  "writer_pax_comment_len": 2097152,
  "reader_pax_comment_len": 2097152,
  "surfaced_type": "regular '0'",
  "surfaced_name": "small.txt",
  "ok": false,
  "status": "partial",
  "pathname_bytes": 0,
  "errors": [
    "max_pathname_bytes exceeded"
  ],
  "member_count": 0,
  "interpretation": "A 2 MiB PAX comment was fully loaded by tarfile.next() before the tool applied max_pathname_bytes=100. The tool then fail-closed (partial, member_count 0) after that allocation."
}
```

## sparse_parser_vs_helper

```json
{
  "name": "sparse_parser_vs_helper",
  "helper_on_synthetic_size10_extent10000": 10000,
  "readback": [
    {
      "name": "sparse.bin",
      "type": "b'0'",
      "size": 10,
      "sparse": null,
      "logical_helper": 10
    }
  ],
  "ok": true,
  "status": "ok",
  "expanded": 10,
  "errors": [],
  "interpretation": "logical_member_size() returns 10000 for a hand-built TarInfo with size=10 and sparse extent 10000. tarfile write/read of .sparse did not persist a sparse map (sparse=None, size=10), so inventory charged 10 and returned ok under max_expanded_bytes=100. The implementation's sparse test used size=10000, so it cannot distinguish helper-aware accounting from size-field accounting."
}
```

## output_selected_symlink_escape

```json
{
  "name": "output_selected_symlink_escape",
  "ok": false,
  "status": "failed",
  "errors": [
    "selected_write:path escapes output directory: ('selected',)"
  ],
  "leaked_outside": [],
  "dest_inside_out": false,
  "interpretation": "output_dir/selected -> outside directory was rejected; no leak."
}
```

## selected_intermediate_symlink_escape

```json
{
  "name": "selected_intermediate_symlink_escape",
  "ok": false,
  "status": "failed",
  "errors": [
    "selected_write:path escapes output directory: ('docs', 'note.txt')"
  ],
  "leaked_outside": [],
  "interpretation": "output_dir/selected/docs -> outside directory was rejected; no leak."
}
```

## r_gz_member_cache

```json
{
  "name": "r_gz_member_cache",
  "r_gz_stream_flag": false,
  "r_pipe_gz_stream_flag": false,
  "note": "On CPython 3.13, tarfile.open('r|gz') passes a _Stream as fileobj and leaves TarFile.stream=False. Both r:gz and r|gz therefore append every TarInfo to TarFile.members. open() also prefetches the first member in __init__."
}
```

## min_free_disk_can_be_lowered_below_10giB

```json
{
  "name": "min_free_disk_can_be_lowered_below_10giB",
  "allowed": true,
  "value": 1,
  "interpretation": "Limits(min_free_disk_bytes=1) is accepted. Production CLI --min-free-disk-bytes 1 would weaken the 10 GiB reserve."
}
```
