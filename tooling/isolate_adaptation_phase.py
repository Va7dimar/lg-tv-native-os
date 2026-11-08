"""Narrow timeout/prlimit/bwrap launcher for the pinned adaptation phase."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import bounded_archive_inventory as bai
import adaptation_libkadaptor_phase as ap


def build_isolation_command(outer, output_dir, *, synthetic_fixture_mode=None,
                            wall_seconds=120, address_space_bytes=1073741824):
    limits = ap.PhaseLimits(wall_seconds=wall_seconds, address_space_bytes=address_space_bytes)
    outer = Path(outer).absolute()
    fd, _ = bai.open_regular_nofollow(outer)
    os.close(fd)
    output = Path(output_dir).absolute()
    if output.is_symlink():
        raise ap.PhaseError("symlink output directory rejected")
    tool_dir = Path(__file__).resolve().parent
    cmd = [
        "timeout", "--kill-after=5s", str(limits.wall_seconds), "prlimit",
        f"--as={limits.address_space_bytes}", f"--cpu={limits.wall_seconds}",
        "--core=0", "--nofile=64", "--", "bwrap",
        "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LANG", "C",
        "--setenv", "PYTHONDONTWRITEBYTECODE", "1", "--setenv", "PYTHONPATH", "/tool",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
        "--dir", "/input", "--dir", "/tool",
        "--ro-bind", str(tool_dir / "adaptation_libkadaptor_phase.py"), "/tool/adaptation_libkadaptor_phase.py",
        "--ro-bind", str(tool_dir / "bounded_archive_inventory.py"), "/tool/bounded_archive_inventory.py",
        "--ro-bind", str(outer), f"/input/{outer.name}",
        "--bind", str(output.resolve()), "/output", "--chdir", "/output",
    ]
    if synthetic_fixture_mode is not None:
        fixture = Path(synthetic_fixture_mode).absolute()
        ap.load_synthetic_spec(fixture)  # Reject retargeting before launching.
        cmd += ["--ro-bind", str(fixture), "/input/synthetic-spec.json"]
    cmd += ["--", "python3", "/tool/adaptation_libkadaptor_phase.py",
            "--outer", f"/input/{outer.name}", "--output-dir", "/output"]
    if synthetic_fixture_mode is not None:
        cmd += ["--synthetic-fixture-mode", "/input/synthetic-spec.json"]
    return cmd


def _namespace():
    try:
        return os.readlink("/proc/self/ns/net")
    except OSError:
        return None


def _write_log(output, name, data):
    free = ap.shutil.disk_usage(output).free
    if free < bai.HARD_MIN_FREE_DISK_BYTES:
        raise ap.PhaseError(f"disk free {free} below 10GiB floor before launcher write")
    bai.atomic_write_bytes(bai.contained_path(output, name), data)


def main(argv=None):
    try:
        args = ap.build_arg_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code
    output = Path(args.output_dir).absolute()
    held = []
    try:
        if output.is_symlink():
            raise ap.PhaseError("symlink output directory rejected")
        output.mkdir(parents=True, exist_ok=True)
        # Build rejects input symlinks. Hold O_NOFOLLOW descriptors through bwrap
        # setup so a subsequent path replacement cannot redirect the input bind.
        cmd = build_isolation_command(args.outer, output,
                                      synthetic_fixture_mode=args.synthetic_fixture_mode)
        sources = [Path(args.outer).absolute()]
        if args.synthetic_fixture_mode:
            sources.append(Path(args.synthetic_fixture_mode).absolute())
        for source in sources:
            fd, _ = bai.open_regular_nofollow(source)
            held.append(fd)
            for index, value in enumerate(cmd):
                if value == "--ro-bind" and cmd[index + 1] == str(source):
                    cmd[index + 1] = f"/proc/self/fd/{fd}"
        host_ns = _namespace()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=tuple(held))
        _write_log(output, "launcher-stdout.txt", proc.stdout[:bai.HARD_MAX_STDOUT_BYTES])
        _write_log(output, "launcher-stderr.txt", proc.stderr[:256 * 1024])
        document = {}
        path = bai.contained_path(output, "phase.json")
        if path.is_file():
            fd, st = bai.open_regular_nofollow(path)
            with os.fdopen(fd, "rb") as src:
                if st.st_size <= 64 * 1024 * 1024:
                    document = json.load(src)
        result = dict(exit_code=proc.returncode, command=cmd,
                      unshare_all=True, share_net=False, noexec_output_demonstrated=False,
                      host_net_ns=host_ns,
                      sandbox_net_ns=document.get("isolation_observation", {}).get("sandbox_net_ns"),
                      timeout_wall_seconds=120, prlimit_as_bytes=1073741824)
        _write_log(output, "launcher-result.json", (json.dumps(result, indent=2) + "\n").encode())
        if proc.stdout:
            sys.stdout.buffer.write(proc.stdout[:bai.HARD_MAX_STDOUT_BYTES])
        if proc.stderr:
            sys.stderr.buffer.write(proc.stderr[:256 * 1024])
        return proc.returncode
    except (ap.PhaseError, bai.InputError, bai.PathEscapeError, OSError, ValueError) as exc:
        ap.record_failed_phase(output, str(exc))
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        for fd in held:
            os.close(fd)


if __name__ == "__main__":
    sys.exit(main())
