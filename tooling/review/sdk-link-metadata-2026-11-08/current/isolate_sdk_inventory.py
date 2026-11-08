"""Mandatory closed production launcher; synthetic injection is library-only.

The outside launcher owns launcher-result.json, which is authoritative even if a
worker is killed after publishing its own manifest. No production test flags.
"""
from __future__ import annotations
import dataclasses
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import time
# -I excludes the script directory; add only this explicit trusted tool path.
sys.path.insert(0, str(Path(__file__).absolute().parent))
import sdk_inventory_phase as sdk

TOOL = str(Path(__file__).absolute().with_name('sdk_inventory_phase.py'))


def argument_parser():
    return sdk.argument_parser()


def build_command(specs, output_source, worker_command, remaining, *, input_sources=None):
    python = os.path.realpath('/usr/bin/python3')
    version = f'{sys.version_info.major}.{sys.version_info.minor}'
    cmd = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=1s', str(remaining),
           '/usr/bin/prlimit', '--as=1073741824', '--cpu=120', '--core=0',
           '--nofile=64', '--fsize=1073741824', '--', '/usr/bin/bwrap',
           '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
           '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
           '--dir', '/usr', '--dir', '/usr/bin', '--dir', '/usr/lib',
           '--ro-bind', python, python,
           '--ro-bind', '/usr/lib/python' + version, '/usr/lib/python' + version,
           '--ro-bind', '/usr/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu',
           '--ro-bind', '/usr/lib64', '/usr/lib64',
           '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
           '--proc', '/proc', '--remount-ro', '/proc', '--dev', '/dev',
           '--remount-ro', '/dev', '--dir', '/tmp', '--dir', '/input',
           '--dir', '/tool', '--ro-bind', TOOL, '/tool/sdk_inventory_phase.py']
    for i, spec in enumerate(specs):
        source = input_sources[i] if input_sources is not None else spec.path
        cmd += ['--ro-bind', source, '/input/' + spec.label]
    cmd += ['--bind', output_source, '/output', '--chdir', '/output',
            '--remount-ro', '/', '--'] + list(worker_command)
    return cmd


def _read_json(fd, name):
    src = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    with os.fdopen(src, 'rb') as f:
        raw = f.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise sdk.InventoryError('worker manifest oversized')
    return json.loads(raw)


def _bootstrap(specs, deadline, probe):
    # Literal trusted configuration from the closed CLI, or synthetic library
    # fixtures; never read an external spec/configuration file.
    mapped = [dataclasses.replace(s, path='/input/' + s.label) for s in specs]
    values = repr([dataclasses.asdict(s) for s in mapped])
    # bwrap has finished the descriptor-backed binds before this runs. Close
    # every host descriptor, including numbers above the lowered RLIMIT_NOFILE,
    # and fail closed before reader imports. /proc enumeration briefly opens a
    # descriptor of its own; only EBADF (already closed) is harmless.
    code = '''import sys,os,errno
for name in os.listdir('/proc/self/fd'):
 n=int(name)
 if n<3: continue
 try: os.close(n)
 except OSError as e:
  if e.errno!=errno.EBADF: raise
for name in os.listdir('/proc/self/fd'):
 n=int(name)
 if n<3: continue
 try: os.fstat(n)
 except OSError as e:
  if e.errno!=errno.EBADF: raise
 else: raise RuntimeError('inherited descriptor survived cleanup')
'''
    code += ('import json,time,socket;sys.path.insert(0,"/tool");'
            'import sdk_inventory_phase as s;'
            f'specs=[s.InputSpec(**x) for x in {values}];'
            'fd=s.directory_fd("/output");'
            f'doc=s.inventory(specs,"/output",output_fd=fd,deadline={deadline!r});')
    if probe:
        code += '''
readonly=True
try:
 f=os.open('/input/sdk',os.O_WRONLY);os.close(f);readonly=False
except OSError: pass
sock=socket.socket();network_unavailable=False
try: sock.connect(('127.0.0.1',9))
except OSError: network_unavailable=True
finally: sock.close()
s.atomic_json(fd,'isolation-probe.json',dict(home_hidden=not os.path.exists('/home') and not os.path.exists('/root') and 'HOME' not in os.environ,input_readonly=readonly,net_ns=os.readlink('/proc/self/ns/net'),network_unavailable=network_unavailable))
'''
    return code + '\nos.close(fd)\nsys.exit(0 if doc["ok"] else 1)\n'


def _normalize_stdio():
    # Reserve standard slots before allocating any host bind descriptors.
    for n in range(3):
        try:
            os.fstat(n)
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
            fd = os.open(os.devnull, os.O_RDWR)
            if fd != n:
                try:
                    os.dup2(fd, n)
                finally:
                    os.close(fd)


def launch(specs, output_dir, *, synthetic_probe=False):
    started = time.monotonic()
    deadline = started + 120
    _normalize_stdio()
    outfd = sdk.fresh_output(output_dir)
    inputs = []
    handles = []
    result = dict(ok=False, status='failed', exit_code=None, error=None,
                  sandbox_unavailable=False, noexec=False, disk_reserved=False,
                  address_space_bytes=1024**3, hard_rss_limit=False,
                  wall_seconds=120, host_net_ns=os.readlink('/proc/self/ns/net'),
                  worker_manifest='manifest.json')
    doc = None
    try:
        sdk.disk_check(outfd)
        for spec in specs:
            sdk.check_deadline(deadline)
            fd, identity = sdk.open_regular(spec.path)
            inputs.append((fd, identity))
        remaining = deadline - time.monotonic()
        sdk.check_deadline(deadline)
        bootstrap = _bootstrap(specs, deadline, synthetic_probe)
        worker = [os.path.realpath('/usr/bin/python3'), '-I', '-B', '-c', bootstrap]
        cmd = build_command(specs, f'/proc/self/fd/{outfd}', worker, remaining,
                            input_sources=[f'/proc/self/fd/{fd}' for fd, _ in inputs])
        # Retain nofollow descriptors through bwrap's bind creation.
        result['command'] = cmd
        for name in ('launcher-stdout.txt', 'launcher-stderr.txt'):
            sdk.disk_check(outfd)
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=outfd)
            handles.append(os.fdopen(fd, 'wb'))
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL,
                              stdout=handles[0], stderr=handles[1],
                              pass_fds=tuple([outfd] + [fd for fd, _ in inputs]),
                              timeout=max(0.001, deadline - time.monotonic()))
        result['exit_code'] = proc.returncode
        for f in handles:
            f.flush()
        for fd, identity in inputs:
            if sdk.signature(os.fstat(fd)) != identity:
                raise sdk.InventoryError('input mutation during sandbox')
        sdk.check_deadline(deadline)
        try:
            doc = _read_json(outfd, 'manifest.json')
        except FileNotFoundError:
            errfd = os.open('launcher-stderr.txt', os.O_RDONLY | os.O_NOFOLLOW, dir_fd=outfd)
            try:
                error = os.read(errfd, 4096).decode('utf-8', 'replace')
            finally:
                os.close(errfd)
            result['sandbox_unavailable'] = 'bwrap:' in error
            raise sdk.InventoryError('worker did not publish manifest: ' + error)
        result['ok'] = proc.returncode == 0 and doc.get('ok') is True
        result['status'] = 'ok' if result['ok'] else 'failed'
        if not result['ok']:
            result['error'] = doc.get('error') or 'worker failed'
    except Exception as e:
        result.update(ok=False, status='failed', error=type(e).__name__ + ': ' + str(e)[:4096])
    finally:
        for f in handles:
            f.close()
        for fd, _ in inputs:
            os.close(fd)
        try:
            if doc is None:
                doc = dict(ok=False, status='failed', error=result['error'],
                           mode='METADATAONLY', worker_completed=False,
                           totals=None, members_jsonl_may_be_partial=True)
                # Never overwrite a worker result, including after timeout.
                try:
                    sdk.atomic_json(outfd, 'manifest.json', doc)
                except FileExistsError:
                    pass
            result['elapsed_seconds'] = time.monotonic() - started
            sdk.atomic_json(outfd, 'launcher-result.json', result)
        finally:
            os.close(outfd)
    return result


def main(argv=None):
    try:
        args = sdk.production_arguments(argv)
        result = launch(sdk.PRODUCTION_SPECS, args.output_dir)
        print(json.dumps(dict(ok=result['ok'], status=result['status'],
                              launcher_result=str(Path(args.output_dir) / 'launcher-result.json'))))
        return 0 if result['ok'] else 1
    except (OSError, sdk.InventoryError) as e:
        print(json.dumps(dict(ok=False, status='failed', error=str(e)[:2000])))
        return 2


if __name__ == '__main__':
    sys.exit(main())
