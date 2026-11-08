"""Launch the CORE TWO phase under timeout, prlimit, and bwrap."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import bounded_archive_inventory as bai
import targeted_core_two_phase as tcp


def build_isolation_command(
    outer,
    output_dir,
    wall_seconds: int = 120,
    address_space_bytes: int = 1073741824,
    forwarded_args=None,
    tool_path=None,
    helper_path=None,
) -> list[str]:
    if wall_seconds > bai.HARD_MAX_WALL_SECONDS:
        raise tcp.PhaseLimitError("wall_seconds exceeds hard maximum")
    if address_space_bytes > bai.HARD_MAX_ADDRESS_SPACE_BYTES:
        raise tcp.PhaseLimitError("address_space_bytes exceeds hard maximum")
    outer_path = Path(outer)
    fd, _st = bai.open_regular_nofollow(outer_path)
    os.close(fd)
    outer_path = outer_path.resolve()
    output_dir = Path(output_dir).resolve()
    tool_path = Path(tool_path or Path(__file__).with_name("targeted_core_two_phase.py")).resolve()
    helper_path = Path(helper_path or Path(__file__).with_name("bounded_archive_inventory.py")).resolve()
    forwarded_args = list(forwarded_args or [])
    dest_name = outer_path.name
    cmd = [
        "timeout",
        "--kill-after=5s",
        str(wall_seconds),
        "prlimit",
        f"--as={address_space_bytes}",
        f"--cpu={wall_seconds}",
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
        "--setenv",
        "PYTHONPATH",
        "/tool",
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
        "/tool/targeted_core_two_phase.py",
        "--ro-bind",
        str(helper_path),
        "/tool/bounded_archive_inventory.py",
        "--ro-bind",
        str(outer_path),
        f"/input/{dest_name}",
        "--bind",
        str(output_dir),
        "/output",
        "--chdir",
        "/output",
        "--",
        "python3",
        "/tool/targeted_core_two_phase.py",
        "--outer",
        f"/input/{dest_name}",
        "--output-dir",
        "/output",
    ]
    cmd += forwarded_args
    return cmd


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = tcp.build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        limits = tcp.limits_from_args(args)
    except tcp.PhaseLimitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    forwarded: list[str] = [
        "--expected-outer-bytes",
        str(args.expected_outer_bytes),
        "--expected-outer-sha256",
        args.expected_outer_sha256,
    ]
    if args.allow_test_spec:
        forwarded.append("--allow-test-spec")
        for item in args.test_target:
            forwarded += ["--test-target", item]
    if args.min_free_disk_bytes is not None:
        forwarded += ["--min-free-disk-bytes", str(args.min_free_disk_bytes)]
    if args.wall_seconds is not None:
        forwarded += ["--wall-seconds", str(args.wall_seconds)]
    try:
        cmd = build_isolation_command(
            args.outer,
            output_dir,
            wall_seconds=limits.wall_seconds,
            address_space_bytes=limits.address_space_bytes,
            forwarded_args=forwarded,
        )
    except (tcp.PhaseLimitError, bai.InputError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    host_net = None
    try:
        host_net = os.readlink("/proc/self/ns/net")
    except OSError:
        host_net = None
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output_dir / "launcher-stdout.txt").write_bytes(proc.stdout[: limits.max_stdout_bytes])
    (output_dir / "launcher-stderr.txt").write_bytes(proc.stderr[: 256 * 1024])
    sandbox_net = None
    phase_path = output_dir / "phase.json"
    if phase_path.is_file():
        try:
            document = json.loads(phase_path.read_text(encoding="utf-8"))
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
    tmp = output_dir / f".launcher-result.json.tmp.{os.getpid()}"
    tmp.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, output_dir / "launcher-result.json")
    if proc.stdout:
        sys.stdout.buffer.write(proc.stdout[: limits.max_stdout_bytes])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
