# Unit identification — what to photograph (read-only)

2026-11-08 14:45 Atlantic/Reykjavik. Owner is in front of the TV and can
look at the screen. Ordinary navigation is permitted; no settings changes,
no update checks, no 401-endpoint bypass, no developer mode, no chassis
opening.

SSAP keys were **not** sent for this pass. A previous Support-category
route was non-deterministic, and the official Software Update page includes
a "Check for Updates" action. Physical navigation is safer than a blind
button sequence.

Official family guide (linked from 65NANO756PR.AEK support; options can
differ by model): hold the gear key more than one second for All Settings.
Short press is Quick Settings only.

## Photo 1 — TV Information (model)
All Settings → General → Devices → TV Management → TV Information

The guide says this screen can show Model, Serial Number, and Device
Name. Photograph the whole screen.

Please capture, if shown:
- Model, including any extra suffix after 65NANO756PR (for example .AEK
  or .AEU)
- Device name

If a serial number is visible, it is fine to photograph it, but we will
not copy the serial into the public notes. No need to type it.

This screen is not expected to show board, SoC, or panel revision.

## Photo 2 — Software Update (installed version only)
All Settings → Support → Software Update

Photograph the screen as it first appears so the current software /
webOS version is readable.

Do **not** press Check for Updates.
Do **not** change Auto Update.
Do **not** start an update.

AEK/API support pages list stock packages 03.53.45 and 03.53.46 for some
regional listings; those are not this unit's version until the on-screen
number matches.

## Photo 3 — exterior model label (no opening)
If convenient, photograph the factory label on the back or stand of the
set, showing the printed model/suffix. Do not open the chassis. Interior
board/panel silkscreen is still unauthorized.

## Still unknown after these photos
Board assembly, PCB revision, panel variant, and SoC are unlikely to
appear in the menus above. Those stay unknown unless later legitimate
documentation or separately authorized physical evidence supplies them.

## Photo 1 status — received 2026-11-08 14:59 Atlantic/Reykjavik
Owner sent the TV Information photo. Raw image not stored in git. Serial
and wired MAC were visible and are not recorded.

Recorded non-sensitive fields:
- Device Name: `[LG] webOS TV NANO756PR`
- Model: `65NANO756PR` (no extra suffix shown)
- webOS TV Version: `6.5.3-47 (kisscurl-koli)`
- Available Internal Storage: `1.07/2.03GB`

These are now in `docs/device-facts.md` and `evidence/device-identity.json`.
Mapping research: `evidence/webos-6.5.3-47-kisscurl-koli-mapping-2026-11-08.md`.

## Photo 2 status — received 2026-11-08 15:02 Atlantic/Reykjavik
Owner sent the Software Update photo. Raw image not stored in git.

Recorded:
- Software Version: `03.53.45`
- Auto Update: OFF
- Offered update: `03.53.46` / `1142MB` (Download and Install not pressed)

## Still needed
- Photo 3 (exterior factory label / suffix) remains optional.
- Do not install 03.53.46 unless a later explicit decision says to.
