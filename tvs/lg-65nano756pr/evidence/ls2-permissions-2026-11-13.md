# LS2 role/client-permission grant for wayland-hello — 2026-11-13

Off-TV research and packaging only. No files were written on the TV in this
step. Serial, nduid, and MAC are not recorded here.

## Why this exists

The PR #8 lifecycle-2 IPK (`888e96b0e705bec22c4852dd7e1d7eea2b54ea8ff2b2d4cfcbcfe6735a7cf7b1`,
binary `673dfb9b98a8d170bb1be328af426afa4e966e06393b05b6c4beeb70359f1c30`,
head `8aa820a`) was installed and launched on this 65NANO756PR on 2026-11-13.
SAM passed a native lifecycle-2 launch document (`interfaceMethod registerApp`,
`interfaceVersion` 2, `@system_native_app` true). The client then failed closed:

```
t=12 luna: register name=org.va7dimar.waylandhello source=app-id
t=16 luna: LSRegister failed code=-1027 message=Invalid permissions for org.va7dimar.waylandhello. Failing closed.
```

Full log: `tvs/lg-65nano756pr/evidence/luna-register-live-2026-11-13.md`
(copied from main). No surface was created. The 31 s Home-reclaim hypothesis
is still untested.

`Invalid permissions for <name>` on LSRegister is a hub denial of **claiming
that bus name**, not an ACG denial of a later method call. Public description:
ls-hubd `_LSTransportRequestNameLocal` rejects the name when the calling
binary has no matching role / `allowedNames` entry
([webos-mcp LS2 roles note](https://cdn.jsdelivr.net/npm/webos-mcp@0.1.13/knowledge/ls2-roles.md)).

## Verified on this TV (already on file)

- webOS TV 6.5.3-47 (Rockhopper), rooted, Homebrew Channel, developer apps
  under `/media/developer`.
- `/` is squashfs read-only. `/var` is writable ext4 (p58). `/media` is
  writable ext4 (p59). Do not write kernel, rootfs, tvservice, or squashfs
  `/var/palm` system roles
  (`tvs/lg-65nano756pr/evidence/live-system-inventory-2026-11-08.md`).
- A SAM-launched native IPK of this id runs `wayland-hello-launch.sh` as
  `main`, with `APPID=org.va7dimar.waylandhello` and `HOME=<app dir>`
  (`tvs/lg-65nano756pr/evidence/sam-launch-success-2026-11-08.md`).
- The lifecycle-2 client `exec`s `wayland-hello` and then calls `LSRegister`
  as `org.va7dimar.waylandhello` (live log above). `/proc/self/exe` at that
  point is the ELF, not the shell script. **Not yet logged on the TV;** the
  client now prints `luna: exe=`.
- `libluna-service2.so.3` and `libglib-2.0.so.0` exist under `/usr/lib`.

## Mechanism (public sources; this TV's ls-hubd conf was not dumped)

webOS 4+ / 6 (this TV is 6.5) reads LS2 security files from:

| Tree | Role | Client permissions | Manifests |
| --- | --- | --- | --- |
| `/var/luna-service2` | `roles.d/` | `client-permissions.d/` | `manifests.d/` |
| `/var/luna-service2-dev` | same | same | same |

Developer-mode / `dev/install` apps use the `-dev` suffix
([OSE security guide](https://www.webosose.org/docs/guides/development/configuration-files/security-guide/),
[webosose `webos_filesystem_paths.bbclass`](https://github.com/webosose/meta-webosose/blob/warrior/meta-webos/classes/webos_filesystem_paths.bbclass)).
`/usr/share/luna-service2` is the built-in (read-only) copy; this work does
not write it.

A native-app role uses `exeName` = absolute path of `appinfo.json` `main`,
`type` `regular`, `allowedNames` `[<id>*]`, `trustLevel` `oem`
([`webos_app_generate_security_files.bbclass`](https://github.com/webosose/meta-webosose/blob/master/meta-webos/classes/webos_app_generate_security_files.bbclass);
the comment there says keep it in sync with appinstalld). This package's
`main` is the launcher script, so an installer-generated role would name
`…/wayland-hello-launch.sh` and would **not** match the ELF that calls
`LSRegister`. That mismatch is the working explanation of `-1027`. It is
**hypothesis** until `/var/luna-service2-dev/roles.d/` is listed on the TV
after a PR #8 install.

Client permissions for a native app are keyed by the exact app id and are
filled from `requiredPermissions`
(same bbclass). OSE `registerApp` is ACG `application.operation`
([applicationmanager docs](https://www.webosose.org/docs/reference/ls2-api/com-webos-service-applicationmanager/)).
The OSE nativeqt sample sets `"requiredPermissions": ["application.operation"]`
and `"nativeLifeCycleInterfaceVersion": 2`
([nativeqt appinfo.json](https://github.com/webosose/samples/blob/master/native-apps/built-in/com.example.app.nativeqt/appinfo.json)).

After files in those directories change, ls-hubd must rescan.
`ls-control scan-services` is what Homebrew Channel runs
([`elevate-service.ts`](https://github.com/webosbrew/webos-homebrew-channel/blob/master/services/elevate-service.ts)).
An older librolegen note renamed the installed-app-only scan to
`scan-volatile-dirs`
([openwebos/meta-webos 865a0f8](https://github.com/openwebos/meta-webos/commit/865a0f8e22bfdecaa60b07e41326fecc0899f193)).
The OSE security guide still documents `ls-control scan-services`.

Homebrew Channel, for an already-installed **service**, patches
`/var/luna-service2` and `/var/luna-service2-dev` (and legacy
`/var/palm/ls2*`), creates `client-permissions.d/<service>.root.json` as
`{ "<service>*": ["all"] }`, and rescans. It does not write `/usr`.
`/var/luna-service2-dev` is the developer tree HBC itself leaves behind
([webosbrew/webos-homebrew-channel#11](https://github.com/webosbrew/webos-homebrew-channel/issues/11)).

This app is a SAM-launched native GUI client, not a hub-spawned service, so
no `.service` file and no api-permissions file are shipped.

## What this package does

Templates (placeholders `__EXE_NAME__` / `__LUNA_ROOT__`) are in the IPK at
`usr/palm/applications/org.va7dimar.waylandhello/sysbus/`. They are not
unpacked into `/usr/share/luna-service2`.

On `nativeLifeCycleInterfaceVersion` 2, `wayland-hello-launch.sh`:

1. Picks `/var/luna-service2-dev` if that directory exists, else
   `/var/luna-service2`. Refuses `/usr`, `/etc`, `/overlay`, `/var/palm`,
   and other system prefixes.
2. Writes `roles.d/<id>.app.json` with `exeName` = realpath of the ELF,
   `allowedNames` the exact id plus `id*` and `id-*`, inbound/outbound `*`,
   `trustLevel` `oem`.
3. Writes `client-permissions.d/<id>.app.json` granting
   `application.operation`, `public`, and `all` on those names (`all` is
   the HBC token; `application.operation` is the documented registerApp
   ACG).
4. Writes `manifests.d/<id>.json` listing those two files.
5. Runs `ls-control scan-services`, falling back to `scan-volatile-dirs`.
6. Fails closed (exit 10, log `ls2: … Failing closed.`) if the root is
   missing, not writable, forbidden, or the scan fails. Unchanged files
   skip the scan.
7. `exec`s `wayland-hello --demo --luna-register …`.

The default (lifecycle omitted) IPK does not write LS2 files.

No api-permissions file: we do not export methods.

## Hypothesis vs verified (still open on this TV)

| Claim | Status |
| --- | --- |
| `-1027` is a missing/mismatched role for this ELF + name | Strong, from the live log + public hub behaviour. Not proven by listing the TV's role dir. |
| `/var/luna-service2-dev` exists and is writable by a SAM-launched native app | **Hypothesis.** Expected on a Homebrew Channel / developer-mode image; not listed in the 2026-11-08 inventory. If the process is jailed, the write fails closed and the log says so. |
| ls-hubd on this image loads `manifests.d` and needs a rescan | **Hypothesis** (webOS 4+ / HBC pattern). |
| `trustLevel` `oem` is accepted for a `dev/install` native app | **Hypothesis.** OSE says downloadable apps get OEM automatically; the generator hard-codes `oem`. |
| `all` is a valid ACG group on this TV | **Hypothesis.** HBC uses it on rooted TVs. `application.operation` is the documented registerApp group (OSE). |
| `ls-control scan-services` exists at `/usr/sbin/ls-control` | **Hypothesis.** HBC calls that binary by name after putting `/usr/sbin` on PATH. |
| Installer-generated role used `main` = the `.sh` | **Hypothesis.** Fits `-1027` after exec. |

If the launcher cannot write the luna root, fail-closed is the intended
result. Do not work around it by writing `/usr` or `/var/palm`.

## New IPK build recipe (host)

```sh
python3 -I scripts/fetch_openlgtv_sdk.py
make sdk-abi
python3 -I scripts/build_ipk.py --binary build/sdk/wayland-hello \
  --out build/ipk/org.va7dimar.waylandhello_0.7.0_arm.ipk
python3 -I scripts/build_ipk.py --binary build/sdk/wayland-hello --lifecycle 2 \
  --out build/ipk/org.va7dimar.waylandhello_0.7.0_arm-lifecycle2.ipk
```

Recorded hashes (not committed):

- SDK binary `a4fa3165822002a4989acaea2c4b0997e4c855e4036c8c0a9cf75636f3f96220`
- default IPK `dc2340822e7554b52f702f8781355923cafb61ca609fc31771380f95714f6e95`
- lifecycle-2 IPK `0452e5e3956f38aa4f2edad529e0b4804230add8059d2da3ecd5cf555d2b9890`

`e_flags 0x5000200`, max `GLIBC_2.4`, NEEDED `libc.so.6` `libdl.so.2`
`librt.so.1`. Member names are space-padded with no GNU `/`.

## On-TV verification (lifecycle-2 IPK `0452e5e3…`)

**NEEDS OWNER NOTICE.** Same install/launch shape as the 2026-11-13 run.
Uninstall the previous id first; wait for the app to be gone. Copy the IPK
to `/tmp` and hash it on the TV. `luna-send-pub` needs `</dev/null`.

```sh
sha256sum /tmp/org.va7dimar.waylandhello_0.7.0_arm-lifecycle2.ipk
luna-send-pub -n 1 luna://com.webos.appInstallService/dev/remove '{"id":"org.va7dimar.waylandhello","subscribe":true}' </dev/null
# wait until the app dir is gone
luna-send-pub -n 1 luna://com.webos.appInstallService/dev/install '{"id":"org.va7dimar.waylandhello","ipkUrl":"/tmp/org.va7dimar.waylandhello_0.7.0_arm-lifecycle2.ipk","subscribe":true}' </dev/null
luna-send-pub -n 1 luna://com.webos.service.applicationmanager/launch '{"id":"org.va7dimar.waylandhello"}' </dev/null
```

Then read `/tmp/wh6.log`. Success looks like:

- `ls2: root=/var/luna-service2-dev` (or `/var/luna-service2` if `-dev` is absent)
- `ls2: scan-services ok` or `ls2: scan-volatile-dirs ok`
- `luna: register name=org.va7dimar.waylandhello`
- `luna: exe=` equal to the installed role `exeName` (the ELF under the app dir)
- no `LSRegister failed` / no `Invalid permissions`
- `luna: event=registered`

If the launcher failed closed before exec, the log names the reason
(`luna root does not exist`, `refusing to write system path`,
`ls-control not found`, `hub rescan failed`, `cannot create .d dirs`).

Read-only confirmation of what the launcher wrote (no system-partition
writes). Paths only; do not dump serial/nduid/MAC:

```sh
ls -ld /var/luna-service2-dev /var/luna-service2
ls /var/luna-service2-dev/roles.d /var/luna-service2-dev/client-permissions.d /var/luna-service2-dev/manifests.d
# if -dev is absent, the same names under /var/luna-service2
```

Compare `exeName` in `org.va7dimar.waylandhello.app.json` with `luna: exe=`
in the log. They must be the same path.

Still not shown by a passing `LSRegister`: whether `registerApp` then
stops the ~31 s Home reclaim. That remains a separate observation.
