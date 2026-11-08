"""Closed-standard-stream launch regressions; only synthetic fixture assets."""
import dataclasses,json,os
from pathlib import Path
import subprocess,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_sdk_inventory_phase as fixtures
CHILD = r"""
import sys,os,json,dataclasses
sys.path.insert(0,sys.argv[1])
import isolate_sdk_inventory as launch
import sdk_inventory_phase as sdk
specs=[sdk.InputSpec(**dict(x,marker=bytes.fromhex(x['marker']))) for x in json.loads(sys.argv[2])]
out=sys.argv[3];result=sys.argv[4];mask=int(sys.argv[5])
original=launch._bootstrap
def boot(*args):
 code=original(*args)
 audit="\nstdio={}\nfor n in range(3):\n try: stdio[str(n)]=os.readlink('/proc/self/fd/'+str(n))\n except OSError as e: stdio[str(n)]='ERROR:'+str(e)\nwith open('/output/stdio-audit.json','w') as report: json.dump(stdio,report)\n"
 return code.replace('import sdk_inventory_phase as s;',audit+'import sdk_inventory_phase as s;',1)
launch._bootstrap=boot
for n in range(3):
 if mask&(1<<n): os.close(n)
doc=launch.launch(specs,out)
with open(result,'w') as report:json.dump(doc,report)
"""
class StandardStreamBoundaryTests(unittest.TestCase):
 def test_all_seven_closed_stdio_combinations(self):
  for mask in range(1,8):
   with self.subTest(closed_mask=mask):
    fixture=fixtures.InventoryTests('test_success_shared_three_streams');fixture.setUp()
    try:
     specs=fixture.specs();encoded=[]
     for spec in specs:
      v=dataclasses.asdict(spec);v['marker']=spec.marker.hex();encoded.append(v)
     out=fixture.root/'stdio-output';result=fixture.root/'child-result.json'
     cmd=[sys.executable,'-I','-B','-c',CHILD,str(Path(__file__).resolve().parents[1]),json.dumps(encoded),str(out),str(result),str(mask)]
     proc=subprocess.run(cmd,capture_output=True,text=True,timeout=135)
     self.assertEqual(proc.returncode,0,proc.stderr)
     doc=json.loads(result.read_text());evidence=os.environ.get('SDK_STDIO_TEST_EVIDENCE_DIR')
     audit=json.loads((out/'stdio-audit.json').read_text()) if (out/'stdio-audit.json').exists() else None
     if evidence:
      dest=Path(evidence);dest.mkdir(exist_ok=True);(dest/f'mask-{mask}.json').write_text(json.dumps(dict(mask=mask,launcher=doc,audit=audit,exit_code=proc.returncode,stderr=proc.stderr),indent=2)+'\n')
     error=str(doc.get('error'))
     if doc.get('sandbox_unavailable') and 'NETLINK_ROUTE' in error and ('Operation not permitted' in error or 'EPERM' in error):self.skipTest('nested bwrap blocked:'+error)
     self.assertTrue(doc['ok'],doc)
     self.assertIsNotNone(audit)
     self.assertEqual(audit['0'],'/dev/null',audit)
     for n,target in audit.items():
      self.assertNotIn(target,[str(x.path) for x in specs]+[str(out)],audit)
      self.assertFalse(target.startswith('ERROR:'),audit)
    finally:fixture.tearDown();fixture.doCleanups()
if __name__=='__main__':unittest.main()
