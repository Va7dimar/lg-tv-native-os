# Post-root next steps — research, not an install guide

2026-11-08 ~17:50 Atlantic/Reykjavik. Owner-run root and Homebrew Channel
are confirmed on this `65NANO756PR` (`../evidence/root-result-2026-11-08.md`).
This handoff is for **safe research toward an internal custom/native OS**.
It is not a flashing, shell, Homebrew-app, or exploit runbook.

## Current gates (unchanged by root)

| Gate | Status | Why root does not pass it |
| --- | --- | --- |
| G1-record | Partial (unknowns explicit) | Model / webOS / software version sourced; suffix, board, PCB, panel, SoC still unknown. |
| G1-target | **BLOCKED** | No live board/SoC/panel mapping to a candidate boot/driver branch. |
| U0 / custom boot | **DEPLOYMENT NO-GO** | Homebrew Channel runs on stock webOS. No verified legitimate custom-image acceptance (`../evidence/boot-route.md`). |
| G3-D documentary recovery | **BLOCKED** | No independent recovery entry, failure coverage, or certified restore media (`../evidence/recovery-case.md`). |
| G3-V validated recovery | **BLOCKED** | Nothing tested; no primary-unit write is authorized to “prove” recovery. |
| Architecture / PhaseB / PhaseT | Not selected / not approved | Root is not architecture freeze and not a deploy go. |

Project goal stays **OS inside the TV** (panel / HDMI AppleTV display /
audio / power / remote). Sideloaded apps and a replacement launcher on
otherwise-stock webOS are explicitly not that goal.

## Evidence that would move boot / recovery (documentary only)

Do not invent partitions, keys, boot modes, or image headers. A later
pass may reconsider U0 / G3-D **only** if public sources supply all of:

1. **Exact-board (or exact-revision) legitimate custom-OS boot route** —
   publisher, applicable hardware revision, artifact class/format, and
   stated limits. Must be ordinary public manufacturer or exact-target
   project documentation, not a bypass. Cite URLs; stay conservative.
2. **Independent recovery entry** that can run when stock userspace,
   kernel, or display cannot — not Homebrew Channel, not SSAP, not
   factory-reset-as-firmware-restore.
3. **Failure coverage** for interrupted write / affected boot regions,
   plus a legitimately obtainable matching stock restore artifact.
   Official consumer USB packages currently documented here are
   **forward-only stock updates** when the stock updater can still run
   (`03.53.45` cannot be reinstalled over itself from the published
   guide wording).
4. **Independent early log/diagnostic channel** when stock OS/display
   are unavailable.
5. **Unique calibration/provisioning** preservation or authoritative
   non-impact evidence for the proposed operation — never key extraction.

G3-V additionally needs a separately approved validation route (spare or
other non-destructive method) covering the exact proposed artifact.
Documentation alone is not G3-V. No flash or USB custom image until
those gates actually pass.

## Research-safe now (read-only / observation)

These collect evidence. They do not write boot/system regions.

**Ordinary UI / owner eyes (no new privileges required):**

- Re-photograph Support → Software Update: Software Version, Auto Update,
  whether `03.53.46` / `1142MB` is still offered. Do not press Download
  and Install. Last shot is 15:02, before root.
- Optional: rear product ID label for sales suffix (official update guide
  already tells consumers to read that label). Photograph only; redact
  serial. Suffix still unknown.
- Functional observation, not a write: does HDMI AppleTV, audio, remote,
  and standby still behave as before? Panel can already show Homebrew
  Channel; that is not an HDMI baseline.

**Off-TV / already-approved desk work:**

- Continue public boot/recovery documentary search (same U0 rules:
  bounded, cite URLs, no how-to, no service-menu entry methods).
- Continue source/SDK identity mapping already in this repo (Linux
  4.4.84 Makefile, rtk_kdriver index, source labels RTK2875 / RTK287O /
  k6l / A0 / tv006 / B3 / B7). Those remain **source** labels until a
  live string from this unit matches them.
- Unsent LG open-source inquiry draft stays a draft
  (`lg-opensource-inquiry-draft.md`) until the owner decides to send it.

**If the owner later authorizes a read-only running-OS identity session**
(separate decision; not implied by root success):

- Collect identity **strings** that this project already treats as G1
  fields: running kernel version, platform/board/SoC labels if they
  appear on allowed surfaces, webOS/build strings already used in
  device identity.
- Compare those strings to the SOURCE labels above. A match would help
  G1-target. It would **not** by itself pass U0, G3-D, or G3-V.
- Record unknowns as unknown. Do not infer a partition map, OTP/rescue
  mode, or boot policy from source Makefiles or from root success.
- Do not enable optional remote-admin services for this. If a shell is
  already listening, that is a security exposure (community Homebrew
  SSH has historically used a well-known default password); harden or
  leave it off; never expose it beyond the intended LAN; never commit
  credentials.

## Still needs an explicit owner decision (do not do from this handoff)

Destructive or privilege-expanding work stays gated:

- Any flash, USB custom image, or write to boot/system regions
- Installing `03.53.46`
- Factory reset (undo claim is unverified here and wipes the baseline)
- Service menu, chassis opening, serial wiring, spare-board purchase
- Enabling remote-admin services
- Installing Homebrew catalog apps (not the project goal)
- Architecture freeze, PhaseB box build, PhaseR recovery tests, PhaseT
  target boot

## Explicit non-goals for the next pass

- Reproduce or document how rooting was done
- Treat Homebrew Channel as the destination
- Claim a custom boot route exists
- Prepare recovery media “just in case” from unofficial images

## Pointers

- Outcome: `../evidence/root-result-2026-11-08.md`
- Earlier assessment (historical, agent no-go): `../evidence/root-plan.md`
- Boot: `../evidence/boot-route.md`
- Recovery: `../evidence/recovery-case.md`
- Identity: `../evidence/device-identity.json`
- Source labels: `../evidence/kernel-bootcode-inspection.md`
