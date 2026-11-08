"""Launch the bounded inventory reader under timeout, prlimit, and bwrap."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import bounded_archive_inventory as bai


def build_isolation_command(
    inputs,
    output_dir,
    limits: bai.Limits,
    tool_path,
    forwarded_args=None,
) -> list[str]:
    if limits.address_space_bytes > bai.HARD_MAX_ADDRESS_SPACE_BYTES:
        raise bai.LimitError("address_space_bytes exceeds hard maximum")
    if limits.wall_seconds > bai.HARD_MAX_WALL_SECONDS:
        raise bai.LimitError("wall_seconds exceeds hard maximum")
    forwarded_args = list(forwarded_args or [])
    output_dir = Path(output_dir).resolve()
    tool_path = Path(tool_path).resolve()
    cmd: list[str] = [
        "timeout",
        "--kill-after=5s",
        str(limits.wall_seconds),
        "prlimit",
        f"--as={limits.address_space_bytes}",
        f"--cpu={limits.wall_seconds}",
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
        "C",
        "--setenv",
        "PYTHONDONTWRITEBYTECODE",
        "1",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib64",
        "/lib64",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/input",
        "--dir",
        "/tool",
        "--ro-bind",
        str(tool_path),
        "/tool/bounded_archive_inventory.py",
    ]
    used_names: set[str] = set()
    inner_inputs: list[str] = []
    for index, raw in enumerate(inputs):
        path = Path(raw)
        fd, _st = bai.open_regular_nofollow(path)
        os.close(fd)
        src = path.resolve()
        name = src.name
        if name in used_names:
            name = f"{index}-{name}"
        used_names.add(name)
        dest = f"/input/{name}"
        cmd += ["--ro-bind", str(src), dest]
        inner_inputs.append(dest)
    cmd += [
        "--bind",
        str(output_dir),
        "/output",
        "--chdir",
        "/output",
        "--",
        "python3",
        "/tool/bounded_archive_inventory.py",
        "--output-dir",
        "/output",
    ]
    for dest in inner_inputs:
        cmd += ["--input", dest]
    cmd += forwarded_args
    return cmd


def _write_launcher_result(output_dir: Path, payload: dict) -> None:
    data = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    dest = output_dir / "launcher-result.json"
    tmp = output_dir / f".launcher-result.json.tmp.{os.getpid()}"
    tmp.write_bytes(data)
    os.replace(tmp, dest)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = bai.build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        limits = bai.limits_from_args(args)
    except bai.LimitError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    forwarded: list[str] = []
    if args.select:
        for item in args.select:
            forwarded += ["--select", item]
    if args.max_members is not None:
        forwarded += ["--max-members", str(args.max_members)]
    if args.max_pathname_bytes is not None:
        forwarded += ["--max-pathname-bytes", str(args.max_pathname_bytes)]
    if args.max_selected_text_member_bytes is not None:
        forwarded += ["--max-selected-text-member-bytes", str(args.max_selected_text_member_bytes)]
    if args.max_expanded_bytes is not None:
        forwarded += ["--max-expanded-bytes", str(args.max_expanded_bytes)]
    if args.min_free_disk_bytes is not None:
        forwarded += ["--min-free-disk-bytes", str(args.min_free_disk_bytes)]
    if args.wall_seconds is not None:
        forwarded += ["--wall-seconds", str(args.wall_seconds)]
    if args.hash_input:
        forwarded.append("--hash-input")

    tool_path = Path(__file__).with_name("bounded_archive_inventory.py")
    try:
        cmd = build_isolation_command(
            args.inputs,
            output_dir,
            limits=limits,
            tool_path=tool_path,
            forwarded_args=forwarded,
        )
    except (bai.InputError, bai.InputCollisionError, bai.LimitError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    host_net = None
    try:
        host_net = os.readlink("/proc/self/ns/net")
    except OSError:
        host_net = None

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout[: limits.max_stdout_bytes]
    stderr = proc.stderr[: 256 * 1024]
    (output_dir / "launcher-stdout.txt").write_bytes(stdout)
    (output_dir / "launcher-stderr.txt").write_bytes(stderr)

    sandbox_net = None
    inventory_path = output_dir / "inventory.json"
    if inventory_path.is_file():
        try:
            document = json.loads(inventory_path.read_text(encoding="utf-8"))
            sandbox_net = (document.get("isolation_observation") or {}).get("sandbox_net_ns")
        except (OSError, json.JSONDecodeError):
            sandbox_net = None

    result = {
        "unshare_all": "--unshare-all" in cmd,
        "share_net": "--share-net" in cmd,
        "noexec_output_demonstrated": False,
        "exit_code": proc.returncode,
        "host_net_ns": host_net,
        "sandbox_net_ns": sandbox_net,
        "timeout_wall_seconds": limits.wall_seconds,
        "prlimit_as_bytes": limits.address_space_bytes,
        "command": cmd,
    }
    _write_launcher_result(output_dir, result)
    if stdout:
        sys.stdout.buffer.write(stdout if stdout.endswith(b"\n") else stdout + b"\n")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
