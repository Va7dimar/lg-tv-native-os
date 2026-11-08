# Owner-run root result — 2026-11-08 (Atlantic/Reykjavik)

Status: **confirmed on this unit.** Owner ran a community client on the home LAN.
This agent did **not** run it, did **not** write a procedure, and did **not**
reach the TV. Raw photographs are not in this repository. Serial, MAC, and
pairing material are not recorded.

This is an outcome record, not a reproduction guide. It does not include
commands, script flags, payloads, launcher identities, or button-by-button
steps.

Project goal is unchanged: an **internal custom/native OS**, not Homebrew
Channel apps as the end state. Root plus Homebrew Channel is userspace
progress on stock webOS. It is **not** custom-OS readiness, a bootloader
unlock, or a recovery path. See `boot-route.md` and `recovery-case.md`.

## Confirmed (owner photos, this session)

| When (Atlantic/Reykjavik) | What |
| --- | --- |
| ~17:43 | TV showed SlopBro (by throwaway96) with green status “service launched successfully”. Dialog: “Rooting complete. You may need to reboot for Homebrew Channel to appear. Would you like to reboot now?” Buttons: Reboot now / Don’t reboot. Owner chose **Reboot now**. |
| ~17:46 | After reboot, Homebrew Channel was open. Title **HOMEBREW CHANNEL**, subtitle **webosbrew.org**, showing the installable third-party catalog. |

Unit identity already photo-confirmed earlier the same day (unchanged by these
screens):

- Model: `65NANO756PR` (no extra suffix on TV Information)
- Device Name: `[LG] webOS TV NANO756PR`
- webOS TV Version: `6.5.3-47 (kisscurl-koli)`
- Software Version: `03.53.45` (last Software Update photo 15:02)
- Auto Update: OFF (same photo)
- Offered update `03.53.46` / `1142MB`: not installed

See `tv-information-photo-2026-11-08.md` and
`software-update-photo-2026-11-08.md`.

## What the Homebrew Channel photo does and does not show

**Does show:** the Homebrew Channel app itself, branded webosbrew.org, with a
scrollable catalog of installable titles. That is the usual post-root
userspace marker described at a high level in `root-plan.md`.

**Does not show:** that any catalog title was installed; that remote-admin
services are on; that updates are blocked; that persistence will survive a
factory reset; that picture/HDMI/audio/power were re-measured; or that the
TV will accept a custom boot image.

Catalog titles visible in the photo are third-party listings, not a project
install list. None are recorded as installed.

## Not re-checked after reboot (unknown until a later photo or note)

- Software Version still `03.53.45`
- Auto Update still OFF
- Whether `03.53.46` is still offered
- Sales suffix, board, PCB revision, panel variant, SoC
- Storage layout, boot policy, recovery entry
- HDMI / AppleTV / audio / standby behaviour beyond “the panel can show
  Homebrew Channel”

**Standing hold (unchanged):** keep Auto Update **OFF**. Do **not** install
`03.53.46` until that update is separately checked against this project’s
baseline. Last Software Update photo is still the 15:02 shot.

## Agent vs owner

| Actor | What happened |
| --- | --- |
| Owner | Ran the community client from a machine on the TV LAN; accepted reboot; opened Homebrew Channel. |
| This agent / research box | Did not download or execute the client in this session; did not send SSAP, pairing, or TV commands. Earlier research in `root-plan.md` stayed no-go for *agent* execution. |

Earlier compatibility notes treated `65NANO756PR` as unconfirmed. That exact
sales model is now confirmed rooted at webOS `6.5.3-47 (kisscurl-koli)` /
Software `03.53.45` by the owner photos above.

## Provenance

Fields transcribed from the owner’s attached photographs in this session
(Atlantic/Reykjavik). JPEGs were visible to this executor and are not
committed. No new TV API call, no USB image, no flash.

## Relation to custom OS gates

Root and Homebrew Channel do **not** move U0 / G3-D / G3-V. Those stay
no-go / blocked until new **public, verified, legitimate** custom-boot and
independent-recovery evidence exists for this board. Next research-only
frontiers: `../handoff/post-root-research-2026-11-08.md`.
