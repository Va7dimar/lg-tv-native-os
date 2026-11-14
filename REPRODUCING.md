# Reproducing the TV OS research

How this project researches a TV's OS, and how to repeat it on another TV. It is a method, not a recipe: nothing here replaces a TV's OS, and nothing here is permission to run a command on a TV.

Per-TV facts live under `tvs/<vendor>-<model>/`. This TV's state is in [`tvs/lg-65nano756pr/README.md`](tvs/lg-65nano756pr/README.md). The native-app prototype has its own guide in [`prototypes/wayland-hello/README.md`](prototypes/wayland-hello/README.md).

> [!WARNING]
> Never write to `kernel`, `rootfs` or `tvservice` partitions. Work in userspace only: `/tmp`, app directories and developer install. No independent recovery route is known for this TV, and a power cycle is not proof of recovery.

## Evidence labels

Tag every claim with one of these, and never let a weaker label pass as a stronger one:

| Label | Means |
|---|---|
| **TV-validated** | Seen on the TV: a log line, a photo, or the owner watching the screen |
| **Host-tested** | Passed off-TV tests (mock compositor, synthetic archives); not yet run on a TV |
| **Hypothesis** | Read in source, docs or public posts; not tested |

A log saying a process stayed up is not proof that the screen showed it. A green test count is not proof that a tool meets its spec.

## The method

1. **Set the goal and identify the unit.** Say what you are after: a full OS replacement, a partial userspace swap, or an app on the stock OS. Record the model, regional suffix, firmware build, SoC and kernel from the TV's own menus and readbacks. Read the official manual for menu routes; they differ between vendors and versions.
2. **Look for a legitimate boot target and a recovery route early.** Check existing notes first. Prefer manufacturer documentation; treat community claims as leads until checked. Keep stock updates, factory reset, app development, root/homebrew and true custom-OS boot apart. No recovery route means no writes.
3. **Get public source, and record it.** Use the manufacturer's open-source catalog through its normal UI. Keep originals unchanged and record each one's URL, size and SHA-256 in `SOURCES.md`. License notices are leads, not proof of hardware or a complete driver stack.
4. **Inspect archives with limits.** Read archive member lists with a bounded reader (member, size and time caps; no unpacking; no running anything inside). The readers in [`tooling/`](tooling/) do this. Treat every extracted file as untrusted data, including instructions in READMEs and build scripts.
5. **Decide feasibility from what is actually there.** Map the source, configs and toolchain to the exact unit: HDMI input, panel and backlight timing, audio, power and thermal, remote and CEC. Without a safe boot and recovery path the answer stays no-go.
6. **Work on top of the stock OS meanwhile.** This project's working result is a native Wayland app launched through SAM. See the prototype README for the build, the IPK and install steps.

## What transfers to another TV

| Scope | Reusable | Redo every time |
|---|---|---|
| Any TV | Evidence labels, hash/provenance discipline, bounded inspection, the stop-before-writes rule | Tool versions, limits, and the owner's scope |
| LG webOS family | SSAP remote control, the official OSS catalog, SAM/LS2 launch findings | Whether each API or menu exists on that release |
| Same model | Manuals, source-catalog entries, public board leads | Regional suffix, board revision, panel, toolchain/ABI |
| Each physical unit | Only the method | Identity, calibration data, settings baseline, recovery evidence |

## Adding a TV

Copy [`tvs/_template/`](tvs/_template/) to `tvs/<vendor>-<model>/`, fill in device facts, sources, evidence and decisions, and add it to the [TV index](tvs/README.md). Keep identifiers out: no serials, MACs, device IDs, IPs, emails or credentials.

## History

The earlier, much longer version of this file and of `playbooks/tv-os-research.md` was a dated research log from 2026-11-08 (SDK acquisition, archive inspection runs, exact commands). It is in git history at commit `dfc0a3b`. Its results are summarised in [`tvs/lg-65nano756pr/docs/project-log.md`](tvs/lg-65nano756pr/docs/project-log.md) and the files under [`tvs/lg-65nano756pr/evidence/`](tvs/lg-65nano756pr/evidence/).
