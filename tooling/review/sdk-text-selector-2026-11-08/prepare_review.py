"""Prepare review artifacts from tool code and handoff metadata; NEVER launch SDK.

This script uses only the standard library. It neither opens nor hashes assets.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import shlex
import sys
from unittest import mock

PACKAGE = Path(__file__).absolute().parent
ROOT = PACKAGE.parents[2]
sys.path.insert(0, str(ROOT / 'tooling'))
import sdk_inventory_phase as sdk


def json_file(name, value):
    (PACKAGE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def prepare_command():
    plan = json.loads((ROOT / 'handoff/sdk-selected-text-next-plan.json').read_text())
    evidence = ROOT / 'evidence/sdk-inventory-links-execution-2026-11-08/exact-command.txt'
    # Shell line continuations are removed before shlex tokenization. No shell
    # invocation, command substitution, or production subprocess is performed.
    old = shlex.split(evidence.read_text().replace('\\\n', ''), comments=True)
    assert old[:4] == ['/usr/bin/python3', '-I', '-B',
                       '/workspace/lg-tv/tooling/isolate_sdk_inventory.py']
    command = old.copy()
    command[command.index('--output-dir') + 1] = (
        '/workspace/lg-tv/sdk-candidates/20191125/inspection-selected-text-PENDING-REVIEW')
    for item in plan['candidates']:
        command += ['--select-text', item['input'], item['exact_path'], str(item['indexed_bytes'])]
    total = sum(x['indexed_bytes'] for x in plan['candidates'])
    assert len(plan['candidates']) == 10 and total == 50478
    command += ['--selected-total-bytes', str(total)]
    with mock.patch.object(sdk, 'open_regular', side_effect=AssertionError('input opening forbidden')):
        args = sdk.production_arguments(command[4:])
    assert len(args.selectors) == 10 and args.selected_total_bytes == 50478
    assert [(s.input, s.path, s.size) for s in args.selectors] == [
        (s['input'], s['exact_path'], s['indexed_bytes']) for s in plan['candidates']]
    assert command[:command.index('--output-dir')] == old[:old.index('--output-dir')]
    lines = ['# PROPOSED ONLY — SELECTEDTEXT — DO NOT EXECUTE during implementation.',
             '# Requires independent SPEC/QUALITY review, sandbox evidence, and parent handoff.',
             '# Prepared from handoff metadata only; no SDK asset or member opened.',
             shlex.join(command[:4]) + ' \\']
    for label in ('sdk', 'native', 'target'):
        spec = next(s for s in sdk.PRODUCTION_SPECS if s.label == label)
        lines.append('  --' + label + ' ' + shlex.quote(spec.path) + ' \\')
    lines.append('  --output-dir ' + shlex.quote(args.output_dir) + ' \\')
    for s in args.selectors:
        lines.append('  --select-text ' + shlex.join([s.input, s.path, str(s.size)]) + ' \\')
    lines.append('  --selected-total-bytes 50478')
    raw = ('\n'.join(lines) + '\n').encode()
    assert shlex.split(raw.decode().replace('\\\n', ''), comments=True) == command
    (PACKAGE / 'exact-command.txt').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (PACKAGE / 'exact-command.sha256').write_text(digest + '  exact-command.txt\n')
    json_file('command-validation.json', dict(
        executed=False, validation='production_arguments only, guarded against input opening',
        source_command=str(evidence.relative_to(ROOT)), selectors=[sdk.asdict(s) for s in args.selectors],
        selected_total_bytes=total, output_dir=args.output_dir,
        input_pins=[dict(label=s.label, path=s.path, size=s.size, sha256=s.sha256,
                         codec=s.codec, offset=s.offset, marker_hex=s.marker.hex())
                    for s in sdk.PRODUCTION_SPECS],
        unchanged_limits=sdk.asdict(sdk.Limits()), selected_member_hard_max=sdk.SELECTED_MEMBER_MAX,
        selected_total_hard_max=sdk.SELECTED_TOTAL_MAX, exact_command_file_sha256=digest))
    return digest


def snapshots():
    for folder in ('current', 'diffs'):
        (PACKAGE / folder).mkdir(exist_ok=True)
    for name in ('sdk_inventory_phase.py', 'isolate_sdk_inventory.py', 'test_sdk_text_selector.py'):
        source = ROOT / 'tooling' / ('tests' if name.startswith('test_') else '') / name
        current = source.read_bytes()
        (PACKAGE / 'current' / name).write_bytes(current)
        before = PACKAGE / 'before' / name
        original = before.read_bytes() if before.exists() else b''
        diff = ''.join(difflib.unified_diff(
            original.decode().splitlines(True), current.decode().splitlines(True),
            fromfile='before/' + name if before.exists() else '/dev/null', tofile='current/' + name))
        (PACKAGE / 'diffs' / (name + '.diff')).write_text(diff)
    (PACKAGE / 'before/test_sdk_text_selector.py.ABSENT.txt').write_text(
        'New file: test_sdk_text_selector.py did not exist before this task.\n')


def preserved_boundaries():
    def tree(path):
        return ast.parse(path.read_text())
    def node(t, name):
        return next(n for n in t.body if getattr(n, 'name', None) == name)
    def dump(n):
        return ast.dump(n, include_attributes=False)
    checks = {}
    old = tree(PACKAGE / 'before/sdk_inventory_phase.py')
    new = tree(ROOT / 'tooling/sdk_inventory_phase.py')
    for name in ('InputSpec', 'Limits', 'check_deadline', 'signature', 'directory_fd',
                 'open_regular', 'fresh_output', 'disk_check', 'atomic_json', 'diagnostic_text',
                 'Budget', 'DecodedReader', 'canonical', 'link_classification', 'link_safe'):
        checks['reader.' + name] = dump(node(old, name)) == dump(node(new, name))
    for name in ('PRODUCTION_SPECS', '_BASE'):
        def assignment(t):
            return next(n for n in t.body if isinstance(n, ast.Assign) and
                        any(isinstance(x, ast.Name) and x.id == name for x in n.targets))
        checks['reader.' + name] = dump(assignment(old)) == dump(assignment(new))
    def nested(t):
        return next(n for n in node(t, 'parse_archive').body
                    if isinstance(n, ast.ClassDef) and n.name == 'ObservedInfo')
    checks['reader.parse_archive.ObservedInfo'] = dump(nested(old)) == dump(nested(new))
    old = tree(PACKAGE / 'before/isolate_sdk_inventory.py')
    new = tree(ROOT / 'tooling/isolate_sdk_inventory.py')
    for name in ('build_command', '_read_json', '_normalize_stdio', 'argument_parser'):
        checks['launcher.' + name] = dump(node(old, name)) == dump(node(new, name))
    def cleanup_literal(t):
        return next(n.value.value for n in node(t, '_bootstrap').body
                    if isinstance(n, ast.Assign) and
                    any(isinstance(x, ast.Name) and x.id == 'code' for x in n.targets))
    checks['launcher.host_descriptor_cleanup_literal'] = cleanup_literal(old) == cleanup_literal(new)
    def run_call(t):
        return next(n for n in ast.walk(node(t, 'launch')) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == 'subprocess' and n.func.attr == 'run')
    checks['launcher.subprocess_run_stdio_pass_fds_timeout'] = dump(run_call(old)) == dump(run_call(new))
    assert all(checks.values()), checks
    json_file('preserved-invariants.json', checks)


def test_results():
    runs = {}
    for label in ('RED', 'GREEN-attempt-1', 'GREEN', 'SDK-suite'):
        result = json.loads((PACKAGE / (label + '.result.json')).read_text())
        stderr = (PACKAGE / (label + '.stderr.log')).read_text()
        count = re.search(r'^Ran (\d+) tests? in ([0-9.]+)s$', stderr, re.M)
        skip_lines = [x for x in stderr.splitlines() if ' ... skipped ' in x]
        error_count = re.search(r'^FAILED \(errors=(\d+)\)', stderr, re.M)
        result.update(test_methods=int(count[1]), duration_seconds=float(count[2]),
                      failure_entries=0, error_entries=int(error_count[1]) if error_count else 0,
                      skipped_entries=len(skip_lines),
                      skipped_whole_methods=sum(not x.startswith('  ') for x in skip_lines),
                      skipped_subtests=sum(x.startswith('  ') for x in skip_lines),
                      raw_stdout=label + '.stdout.log', raw_stderr=label + '.stderr.log',
                      raw_exit=label + '.exit.txt')
        runs[label] = result
    red = runs['RED']
    for name, expected in red['production_sha256'].items():
        assert hashlib.sha256((PACKAGE / 'before' / name).read_bytes()).hexdigest() == expected
    assert runs['RED']['exit_code'] == 1
    assert runs['GREEN']['exit_code'] == runs['SDK-suite']['exit_code'] == 0
    json_file('test-results.json', dict(
        synthetic_only=True, actual_sdk_phase_executed=False, independent_review_status='not performed',
        counts_note='unittest counts test methods; skip entries include seven stdio subtests, so do not subtract eleven from seventy to infer passes.',
        sandbox_limitation='bwrap loopback NETLINK_ROUTE socket: Operation not permitted; no bypass attempted',
        requested_model=None, requested_role='primary implementation worker',
        requested_model_note='No exact model identifier specified in the user request available to this worker.',
        observed_serving_model=None,
        observed_serving_model_note='Exact serving model/revision metadata is not exposed to this worker; cannot verify. Developer identifies Codex based on GPT-6, which is not observed serving metadata.',
        other_models_invoked=False, runs=runs))


def hashes():
    # These harness-owned logs are actively written during this turn. Exclude
    # them explicitly instead of publishing immediately stale self-hashes.
    exclusions = {'SHA256SUMS', 'hashes.json', 'codex-events.jsonl', 'codex-stderr.txt', 'codex-prompt.txt'}
    paths = sorted(x for x in PACKAGE.rglob('*') if x.is_file() and x.name not in exclusions)
    records = {str(x.relative_to(PACKAGE)): dict(bytes=x.stat().st_size,
               sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in paths}
    json_file('hashes.json', dict(algorithm='SHA256', files=records,
              exclusions=sorted(exclusions), note='SDK assets are never read or hashed.'))
    lines = [v['sha256'] + '  ' + k for k, v in records.items()]
    lines.append(hashlib.sha256((PACKAGE / 'hashes.json').read_bytes()).hexdigest() + '  hashes.json')
    (PACKAGE / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    command_hash = prepare_command()
    snapshots()
    preserved_boundaries()
    test_results()
    hashes()
    print(json.dumps(dict(command_sha256=command_hash, selectors=10, selected_total_bytes=50478)))
