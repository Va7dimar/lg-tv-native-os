"""Child: close fd 0 then launch synthetic inventory with FD audit."""
import json, os, sys
sys.path.insert(0, "/workspace/lg-tv/tooling")
import isolate_sdk_inventory as isolate
import sdk_inventory_phase as sdk

args = json.loads(sys.argv[1])
os.close(0)  # free stdin slot
specs = [sdk.InputSpec(s["label"], s["path"], s["size"], s["sha256"], s["codec"], s["offset"],
                       bytes.fromhex(s["marker_hex"]))
         for s in args["specs"]]

orig = isolate._bootstrap
AUDIT = r'''
info={}
for n in (0,1,2):
 try:
  st=os.fstat(n)
  target=os.readlink('/proc/self/fd/%d'%n)
  writable=False
  try:
   w=os.open('/proc/self/fd/%d'%n, os.O_WRONLY); os.close(w); writable=True
  except OSError:
   pass
  parent=None
  try:
   p=os.open('..', os.O_RDONLY|os.O_DIRECTORY, dir_fd=n)
   parent=os.listdir(p); os.close(p)
  except OSError as e:
   parent=str(e)
  info[str(n)]=dict(target=target, writable=writable, parent=parent)
 except OSError as e:
  info[str(n)]=str(e)
open('/output/fd012-audit.json','w').write(__import__('json').dumps(info)+'\n')
'''
needle = "import sdk_inventory_phase as s;"

def wrapped(*a, **k):
    boot = orig(*a, **k)
    return boot.replace(needle, "\n" + AUDIT + "\n" + needle, 1)

isolate._bootstrap = wrapped
result = isolate.launch(specs, args["output"])
print(json.dumps({"launch_ok": result.get("ok"), "error": result.get("error")}))
