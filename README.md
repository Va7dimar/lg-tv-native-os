# LG TV native OS research: native Wayland apps on rooted webOS (LG 65NANO756PR)

**Run your own native, full-screen app on an LG webOS TV, and document how far a custom LG TV OS can actually go.**

This repo holds a working native Wayland client (`wayland-hello`) for a rooted LG NanoCell 65NANO756PR on webOS 6.5.3, the SAM / luna-service2 findings that make it launch and register properly, and a careful, evidence-first research record on whether an LG TV's OS could ever be replaced. Every claim is tagged with what it is: TV-validated, host-tested only, or still a hypothesis.

> [!WARNING]
> **NEVER overwrite `kernel`, `rootfs`, or `tvservice` system partitions: doing so will brick the TV.**
> This project uses userspace and developer installation only, with files in `/tmp` and app directories. No flashing or system-partition writes. One prototype, [Impetus Home](prototypes/impetus-home/), goes further once the owner approves it at the TV: its scenes change picture settings through the TV's own settings service (saved first, put back after), and its boot hook is one file in Homebrew Channel's start-up folder.
> An independent recovery route is unknown; a power cycle is not proven recovery because of snapshot boot.
> **Not affiliated with LG. Use at your own risk.**

## Status

Results through **2026-11-14**, on the LG 65NANO756PR below.

| Group | Result | Limits |
|---|---|---|
| **Works today (TV-validated)** | Native Wayland SHM surface drew full screen; remote arrows moved a square. | Initial display probe lasted 10 seconds. |
| **Works today (TV-validated)** | Script-built IPK installed through `dev/install` and launched through SAM with full screen and keyboard focus. | Home reclaimed the screen after about 31 seconds. |
| **Works today (TV-validated)** | Setting `appinfo.json` `main` to the ELF fixed LS2 `-1027 Invalid permissions`; lifecycle-2 `registerApp` succeeded. | Registration alone did not prevent Home reclaim. |
| **Experimental** | v0.8 lifecycle-2 + `wl_webos_shell` OVERLAY: logs show the process/overlay stayed up for the full 90-second safety cap. | **On-screen visibility is not yet confirmed.** Buffer was 640×360; no keyboard focus-enter was logged. See [the 90 s run note](tvs/lg-65nano756pr/evidence/persist-90s-tv-run-2026-11-13.md). |
| **Experimental** | v0.9 opt-in `--menu` tile launcher: Demo / About / Exit. | Host-tested only; without buffer release, the spare-buffer cap allows roughly eight key presses. |
| **Works today (TV-validated)** | Native gate closed on 2026-11-14: `wl_shell` fullscreen is shown for about 31 seconds; `wl_webos_shell` (OVERLAY and CARD) is never shown on this firmware. Verdict: hybrid, a web app is the Home. | See the [mode A/B](tvs/lg-65nano756pr/evidence/photo-frame-tv-run-2026-11-14.md) and [mode C](tvs/lg-65nano756pr/evidence/photo-frame-c-tv-run-2026-11-14.md) run notes. |
| **Experimental** | [Impetus Home](prototypes/impetus-home/) 1.2.0, a web-app Home: a living room (the sun's path, clock), a control room (Apple TV door with a live still, shortcuts, apps, scenes) and an engine room (vitals, connections, log, an LG ad and tracking shield). | **Host-tested only** (stand-in TV). 1.0.0 ran on the TV as an ordinary app; everything newer waits for the [TV session](prototypes/impetus-home/TV-SESSION.md). |
| **Not done** | Custom boot or replacement OS built or booted. | Nothing flashed; internal OS replacement remains a research goal. |
| **Not done** | Independent recovery route established. | Unknown. |

## Hardware

| Item | Observed value |
|---|---|
| TV | LG 65NANO756PR, NanoCell NANO75 series, 2021, 65-inch |
| webOS | TV Version `6.5.3-47` (`kisscurl-koli`); LG open-source catalog: “webOS 6.0 KLP 1.0” |
| Firmware | `03.53.45`, photographed 2026-11-08; `03.53.46` offered but not installed; auto-update off |
| SoC / board | Kernel reports Realtek RTD2875; `board_type K7LP_DVB`; chip label `K7LPA0` |
| Kernel | Linux `4.4.84`, `armv7l` |
| Graphics | ARM Mali (`mali_kbase`); `/dev/dri/card0`, `fb0` / `fb1` |
| Compositor | `surface-manager`, Qt5Compositor `5.6.3` |
| Wayland | `/tmp/xdg/wayland-0`; advertises `wl_shell` v1 and `wl_webos_shell` v1 |
| Target ABI | ELF32 ARM EABI5 soft-float, `e_flags 0x05000200` |
| Unknown | Exact sales suffix, PCB revision, panel variant |

These results establish behavior on this TV, not compatibility with other models.

## Quick start

### 1. Build and test off-TV

Run on your development machine, from the repository root. Host tests need GCC and Python 3 and use a mock compositor; no TV is needed.

```sh
cd prototypes/wayland-hello
make test

python3 -I scripts/fetch_openlgtv_sdk.py
make sdk-abi
```

The SDK fetch uses pinned inputs and fails closed on digest/signature verification failure. `make sdk-abi` builds the ARM binary and produces an ABI report.

### 2. Package an IPK

For the basic native demo:

```sh
python3 -I scripts/build_ipk.py \
  --binary build/sdk/wayland-hello \
  --out build/ipk/wayland-hello.ipk
```

For the experimental lifecycle-2 overlay:

```sh
python3 -I scripts/build_ipk.py \
  --binary build/sdk/wayland-hello \
  --lifecycle 2 \
  --out build/ipk/wayland-hello-overlay.ipk
```

Add `--menu` to opt into the host-tested tile launcher. It has not been run on the TV.

### 3. Install and launch on an already rooted TV

**Prerequisite:** an already rooted TV with Homebrew Channel and root SSH access. See [webOS Homebrew](https://www.webosbrew.org/) for community information. **This repository deliberately contains no rooting or exploit steps.**

Copy your chosen IPK to `/tmp/wayland-hello.ipk` on the TV. In the TV’s root SSH session, install it:

```sh
luna-send-pub -n 1 \
  luna://com.webos.appInstallService/dev/install \
  '{"id":"org.va7dimar.waylandhello","ipkUrl":"/tmp/wayland-hello.ipk","subscribe":true}' \
  </dev/null
```

Launch through SAM:

```sh
luna-send-pub -n 1 \
  luna://com.webos.service.applicationmanager/launch \
  '{"id":"org.va7dimar.waylandhello"}' \
  </dev/null
```

Inspect `/tmp/wh6.log`. The basic path is expected to lose the screen to Home after about 31 seconds. The overlay experiment has log evidence beyond that point, but visible rendering and keyboard focus remain unconfirmed.

Remove the app:

```sh
luna-send-pub -n 1 \
  luna://com.webos.appInstallService/dev/remove \
  '{"id":"org.va7dimar.waylandhello","subscribe":true}' \
  </dev/null
```

## How it works

The reusable finding is the relationship between SAM launch, the executable, and LS2 permissions:

1. **Launch through SAM.** The packaged app has type `native`. On this TV, the SAM-launched `wl_shell` path held full screen and keyboard focus for about 30 seconds.
2. **Make `appinfo.json` `main` point directly to the ELF.** `dev/install` generates the app’s LS2 role from `main`, while `ls-hubd` identifies the executable through `/proc/self/exe`. Pointing `main` at a wrapper script caused `-1027 Invalid permissions`. Pointing it at `wayland-hello` made lifecycle-2 `registerApp` succeed.
3. **Registration does not prevent reclaim.** Around 31 seconds after launch, SAM’s `last_input_handler` relaunches Home and hides the app. This also happened after successful registration.
4. **Lifecycle-2 overlay is the current experiment.** v0.8 combines lifecycle-2 registration with a `wl_webos_shell` OVERLAY window. Logs show it stayed up for 90 seconds, but that does not yet prove a visible, interactive full-screen experience ([run note](tvs/lg-65nano756pr/evidence/persist-90s-tv-run-2026-11-13.md)).

## Repo layout

| Path | Contents |
|---|---|
| [`prototypes/wayland-hello/`](prototypes/wayland-hello/) | Native client, host tests, SDK build and IPK packaging |
| [`prototypes/impetus-home/`](prototypes/impetus-home/) | Impetus Home: the web-app Home, its root helper, host tests, IPK build, design and TV-session checklist |
| [`tvs/`](tvs/) | TV index and per-device research |
| [`tvs/lg-65nano756pr/`](tvs/lg-65nano756pr/) | Device docs, evidence, sources, SSAP remote helper and handoff |
| [`tvs/_template/`](tvs/_template/) | Starting point for another TV |
| [`tooling/`](tooling/) | Bounded, read-only archive/SDK inspection tools and tests |
| [`REPRODUCING.md`](REPRODUCING.md) | Research method and how to repeat it on another TV |
| [`SOURCES.md`](SOURCES.md) | Source records |
| [`docs/superpowers/`](docs/superpowers/) | Tool plans |

Large or vendor-licensed inputs are gitignored and tracked by URL and SHA-256. Device identifiers such as the TV's MAC address and serial number are redacted, and no pairing keys or credentials are stored.

## Add your TV

Copy [`tvs/_template/`](tvs/_template/) to `tvs/<vendor>-<model>/`. Record hardware/software facts, sources, evidence, decisions and unknowns, then add it to the [TV index](tvs/README.md).

Keep identifiers out of public evidence: no real names, serials, device IDs, MACs, IPs, emails or credentials.

## Contributing

Useful contributions include sanitized TV evidence, native lifecycle findings, build fixes and host-test improvements.

Include the model, firmware, commands used, observed behavior and limits of the evidence. Distinguish host tests, TV logs and results confirmed on screen. Keep changes within the userspace/dev-install scope; do not add rooting or exploit instructions.

## FAQ

### Can you install a custom OS on an LG TV?

This repository has not achieved that. No custom boot or replacement OS has been built or booted, and nothing has been flashed. Current work runs a native app on top of stock webOS; internal OS replacement feasibility and independent recovery remain unresolved.

### How do I run a native app on webOS 6?

On the tested, already rooted TV: build for its ARM soft-float ABI, package a native IPK, install through `appInstallService/dev/install`, and launch through SAM. Follow the quick start above. Results apply to the listed TV and software versions.

### Why does my webOS native app get -1027 Invalid permissions?

On this TV, `appinfo.json` `main` pointed to a wrapper script while `/proc/self/exe` identified the ELF. The installer-generated LS2 role therefore did not match. Setting `main` directly to the ELF fixed registration. This is a verified cause here, not a diagnosis of every permissions failure.

### Why does Home take over after ~30 seconds?

SAM’s `last_input_handler` relaunches Home at about 31 seconds and hides the app. Successful lifecycle-2 registration alone did not stop it. The lifecycle-2 overlay experiment stayed up for 90 seconds according to logs; on-screen visibility is still unconfirmed.

## Related projects

- [webOS Homebrew Project (webosbrew.org)](https://www.webosbrew.org/): Homebrew Channel, rooting information, app catalog
- [openlgtv/buildroot-nc4](https://github.com/openlgtv/buildroot-nc4): community LG TV toolchain/SDK (the pinned SDK fetched for `make sdk-abi`)
- [webOS Open Source Edition docs](https://www.webosose.org/): SAM, luna-service2 and Wayland extension references used throughout

Keywords: LG TV OS, custom LG TV OS, LG webOS native app, webOS 6 native app, rooted LG TV, LG NANO756 / NANO75 root, Homebrew Channel, Wayland on webOS, Realtek RTD2875, luna-send, SAM registerApp.

## License

[MIT](LICENSE) © 2026 Va7dimar.

The vendored `third_party/webos-wayland-extensions` XML is Apache-2.0 licensed. See also [SECURITY.md](SECURITY.md) for the safety and disclosure policy.
