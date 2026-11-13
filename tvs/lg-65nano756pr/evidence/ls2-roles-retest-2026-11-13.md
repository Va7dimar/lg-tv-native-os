# PR #11 (LS2 roles) live retest on 65NANO756PR — 2026-11-13 ~19:22Z

## Build (reproduced on box, hash-matched box→laptop→TV)
- SDK binary sha256 `a4fa3165822002a4989acaea2c4b0997e4c855e4036c8c0a9cf75636f3f96220`
- lifecycle-2 IPK sha256 `0452e5e3956f38aa4f2edad529e0b4804230add8059d2da3ecd5cf555d2b9890`
- branch cursor/wayland-hello-ls2-roles-aaf7, head a68926e (PR #11 onto PR #8).

## Result: still fails closed, nothing drew. New, more precise cause.
remove returnValue true (REMOVED), install returnValue true (INSTALLED),
launch returnValue true. ~40 s later no wayland-hello process; screen unchanged.

`/tmp/wh6.log` (lifecycle 2, APPID correct, SAM passed the registerApp doc):
```
ls2: exe=/media/developer/apps/usr/palm/applications/org.va7dimar.waylandhello/wayland-hello
ls2: no writable luna-service2 root (/var/luna-service2-dev or /var/luna-service2). Failing closed.
ls2: could not grant LS2 identity. Failing closed.
```
The launcher's self-install never reached LSRegister this time: `ls2_pick_root`
found neither `/var/luna-service2-dev` nor `/var/luna-service2` from inside the
SAM-launched app process, so it failed closed before registering.

## Key finding: the SAM app is sandboxed away from the LS2 config tree
Over root SSH, BOTH `/var/luna-service2-dev` (drwxr-xr-x, Nov 8) and
`/var/luna-service2` exist and are writable by root. The jailed app process does
not see them. A dev-installed native app therefore cannot self-install its own
LS2 role at launch — chicken/egg: it has no permission to write LS2 config.

## What DID get registered (by dev/install, not the launcher)
After install, these appeared in the real tree (install honored the IPK's
`sysbus/` manifest; the launcher had already failed closed):
- `client-permissions.d/org.va7dimar.waylandhello.app.json` = `{"org.va7dimar.waylandhello":["public"]}`
- `manifests.d/org.va7dimar.waylandhello.json` with
  `roleFilesPub=/var/palm/ls2-dev/roles/pub/...`, `roleFilesPrv=/var/palm/ls2-dev/roles/prv/...`,
  `clientPermissionFiles=/var/luna-service2-dev/client-permissions.d/...`
- NO role file in `roles.d` (absent). The manifest declares role files under
  `/var/palm/ls2-dev/roles/{pub,prv}` but nothing copied the shipped
  `sysbus/*.role.json` there, and `/var/palm` is on the launcher's forbidden list.

IPK ships `sysbus/{role,perm,manifest}.json` in the app dir as designed.

## Conclusion / next direction (not yet authorized)
The permission grant must be installed OUT OF BAND of the jailed app — either
by relying on dev/install to also place the role file (fix the manifest's role
path to a writable, install-reachable location), or by a root/elevated step
(the owner's SSH, or an hbchannel-style elevated helper) that writes the role
and rescans; the launcher should then just LSRegister, not self-install.
Whether a valid role actually clears -1027 AND whether registration stops the
~31 s Home reclaim both remain untested.
