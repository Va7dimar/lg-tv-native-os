"""Synthetic host-FD regression. No actual SDK input accessed."""
import fcntl
import errno
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_sdk_inventory_phase as fixtures
isolate=fixtures.isolate

class BootstrapCleanupTests(unittest.TestCase):
    """Bare subprocess evidence only; these tests do not establish isolation."""
    def run_bootstrap(self, high=False, sabotage=''):
        with tempfile.TemporaryDirectory(prefix='sdk-fd-bootstrap-') as root:
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try:
                if high:
                    if resource.getrlimit(resource.RLIMIT_NOFILE)[0] < 300:
                        self.skipTest('host cannot create high descriptors')
                    duplicate=fcntl.fcntl(fd,fcntl.F_DUPFD_CLOEXEC,256)
                    os.close(fd);fd=duplicate
                boot=isolate._bootstrap([],time.monotonic()+120,False)
                audit=f'''
try:
 os.fstat({fd})
except OSError as e:
 print('FD_ERRNO',e.errno)
else:
 print('FD_STILL_OPEN')
print('READER_REACHED')
sys.exit(0)
'''
                needle='import sdk_inventory_phase as s;'
                self.assertEqual(boot.count(needle),1)
                boot=boot.replace(needle,'\n'+audit+'\n'+needle,1)
                prelude="import os,resource\nresource.setrlimit(resource.RLIMIT_NOFILE,(64,64))\n"
                return subprocess.run([sys.executable,'-I','-B','-c',prelude+sabotage+boot],
                                      pass_fds=(fd,),capture_output=True,text=True,timeout=10)
            finally:
                os.close(fd)

    def test_bare_bootstrap_closes_inherited_fd(self):
        proc=self.run_bootstrap()
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('FD_ERRNO '+str(errno.EBADF),proc.stdout)
        self.assertNotIn('FD_STILL_OPEN',proc.stdout)

    def test_bare_bootstrap_closes_fd_above_lowered_limit(self):
        proc=self.run_bootstrap(high=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('FD_ERRNO '+str(errno.EBADF),proc.stdout)
        self.assertNotIn('FD_STILL_OPEN',proc.stdout)

    def test_close_error_stops_before_reader(self):
        proc=self.run_bootstrap(sabotage="def deny(fd): raise OSError(5,'synthetic close failure')\nos.close=deny\n")
        self.assertNotEqual(proc.returncode,0)
        self.assertNotIn('READER_REACHED',proc.stdout)
        self.assertIn('synthetic close failure',proc.stderr)

    def test_enumeration_error_stops_before_reader(self):
        proc=self.run_bootstrap(sabotage="def deny(path): raise OSError(5,'synthetic enumeration failure')\nos.listdir=deny\n")
        self.assertNotEqual(proc.returncode,0)
        self.assertNotIn('READER_REACHED',proc.stdout)
        self.assertIn('synthetic enumeration failure',proc.stderr)

    def test_incomplete_cleanup_stops_before_reader(self):
        proc=self.run_bootstrap(sabotage="os.close=lambda fd: None\n")
        self.assertNotEqual(proc.returncode,0)
        self.assertNotIn('READER_REACHED',proc.stdout)

class DescriptorBoundaryTests(unittest.TestCase):
    def exercise(self, high):
        fixture=fixtures.InventoryTests('test_success_shared_three_streams');fixture.setUp()
        opened=[]
        try:
            specs=fixture.specs();out=fixture.root/'fd-output';out.mkdir()
            (fixture.root/'HOST_PARENT_SENTINEL').write_text('synthetic marker only')
            outputfd=os.open(out,os.O_RDONLY|os.O_DIRECTORY);opened.append(outputfd)
            inputs=[]
            for s in specs:
                fd=os.open(s.path,os.O_RDONLY|os.O_NOFOLLOW);opened.append(fd);inputs.append(fd)
            if high:
                if resource.getrlimit(resource.RLIMIT_NOFILE)[0] < 300:self.skipTest('host cannot create high descriptors')
                newout=fcntl.fcntl(outputfd,fcntl.F_DUPFD_CLOEXEC,256);opened.append(newout);outputfd=newout
                newin=fcntl.fcntl(inputs[0],fcntl.F_DUPFD_CLOEXEC,257);opened.append(newin);inputs[0]=newin
            boot=isolate._bootstrap(specs,time.monotonic()+120,False)
            # Observe exactly before importing the untrusted-input reader, after
            # any trusted FD cleanup. Directory enumeration's transient FD is
            # ignored only when already closed, never as a blanket exception.
            audit="""
closed=[]
for n in EXPECTED_FDS:
 try: os.fstat(n)
 except OSError as e:
  if e.errno==9: closed.append(n)
  else: raise
seen=[]
parent_walk=[]
writable=[]
for number in os.listdir('/proc/self/fd'):
 n=int(number)
 if n<3: continue
 try: target=os.readlink('/proc/self/fd/'+number)
 except FileNotFoundError: continue
 seen.append(dict(fd=n,target=target))
 try:
  parent=os.open('..',os.O_RDONLY|os.O_DIRECTORY,dir_fd=n)
  try:
   marker=os.open('HOST_PARENT_SENTINEL',os.O_RDONLY,dir_fd=parent)
   os.close(marker);parent_walk.append(n)
  finally: os.close(parent)
 except OSError: pass
 try:
  w=os.open('/proc/self/fd/'+number,os.O_WRONLY);os.close(w);writable.append(n)
 except OSError: pass
path_readonly=True
try:
 w=os.open('/input/sdk',os.O_WRONLY);os.close(w);path_readonly=False
except OSError: pass
fresh_output=os.open('/output',os.O_RDONLY|os.O_DIRECTORY)
fresh_parent=os.open('..',os.O_RDONLY|os.O_DIRECTORY,dir_fd=fresh_output)
fresh_parent_marker=False
try:
 try:
  marker=os.open('HOST_PARENT_SENTINEL',os.O_RDONLY,dir_fd=fresh_parent)
  os.close(marker);fresh_parent_marker=True
 except FileNotFoundError: pass
finally:
 os.close(fresh_parent);os.close(fresh_output)
fresh_input_writable=[]
for label in ('sdk','native','target'):
 fresh_input=os.open('/input/'+label,os.O_RDONLY)
 try:
  try:
   w=os.open('/proc/self/fd/'+str(fresh_input),os.O_WRONLY)
   os.close(w);fresh_input_writable.append(label)
  except OSError: pass
 finally: os.close(fresh_input)
with open('/output/fd-boundary.json','w') as report:
 json.dump(dict(inherited=seen,parent_walk=parent_walk,writable_reopens=writable,input_path_readonly=path_readonly,home_hidden=not os.path.exists('/home') and not os.path.exists('/root'),closed=closed,fresh_output_parent_marker=fresh_parent_marker,fresh_input_writable=fresh_input_writable),report)
""".replace('EXPECTED_FDS',repr([outputfd]+inputs))
            needle='import sdk_inventory_phase as s;'
            self.assertEqual(boot.count(needle),1)
            boot=boot.replace(needle,'\n'+audit+'\n'+needle,1)
            cmd=isolate.build_command(specs,f'/proc/self/fd/{outputfd}',[os.path.realpath('/usr/bin/python3'),'-I','-B','-c',boot],120,input_sources=[f'/proc/self/fd/{n}' for n in inputs])
            proc=subprocess.run(cmd,pass_fds=tuple([outputfd]+inputs),capture_output=True,text=True,timeout=125)
            if proc.returncode and 'bwrap:' in proc.stderr:
                self.skipTest('nested runtime blocked: '+proc.stderr)
            self.assertEqual(proc.returncode,0,proc.stderr)
            doc=json.loads((out/'fd-boundary.json').read_text())
            evidence=os.environ.get('SDK_FD_TEST_EVIDENCE_DIR')
            if evidence:
                dest=Path(evidence);dest.mkdir(exist_ok=True)
                (dest/('high.json' if high else 'normal.json')).write_text(json.dumps(dict(probe=doc,passed_fds=[outputfd]+inputs,command=cmd,exit=proc.returncode,stderr=proc.stderr),indent=2)+'\n')
            self.assertEqual(doc['inherited'],[],doc)
            self.assertEqual(doc['parent_walk'],[],doc)
            self.assertEqual(doc['writable_reopens'],[],doc)
            self.assertEqual(doc['closed'],[outputfd]+inputs,doc)
            self.assertFalse(doc['fresh_output_parent_marker'],doc)
            self.assertEqual(doc['fresh_input_writable'],[],doc)
            self.assertTrue(doc['input_path_readonly'],doc)
            self.assertTrue(doc['home_hidden'],doc)
            self.assertTrue(json.loads((out/'manifest.json').read_text())['ok'])
        finally:
            for fd in opened:os.close(fd)
            fixture.tearDown();fixture.doCleanups()
    def test_no_host_descriptors_before_reader_import(self):self.exercise(False)
    def test_no_high_host_descriptors_above_sandbox_nofile(self):self.exercise(True)
if __name__=='__main__':unittest.main()
