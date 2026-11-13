# LG TV live device facts (read-only, 2026-11-08 03:37 Atlantic/Reykjavik)
Verified (SSAP ssap://system/getSystemInfo, saved remote key):
- modelName: 65NANO756PR ; receiverType: DVB ; features.dvr: false ; programMode: true ; serial present (redacted)
Verified other:
- LAN IP 192.168.0.2 (DHCP, previously .8), MAC [MAC redacted] ; SSAP ws://:3000 open, wss://:3001 fails from this client
- Ports seen open: 3000, 3001, 18181, 36866
From LG official spec pages (not live): webOS 6.0, Quad Core Processor 4K, 2021, EU variant (.AEK suffix in a retailer PDF, not confirmed on device)
UNAVAILABLE:
- Firmware/software version, webOS build, board/SoC id: ssap://com.webos.service.update/getCurrentSWInformation -> 401 insufficient permissions (not bypassed)
- Exact sales suffix (e.g. .AEK) not reported by device
How user can get them: TV Settings > General/Support > About This TV (shows software version, webOS TV version, model).

# 2026-11-08 14:59 Atlantic/Reykjavik — TV Information photo
Owner photographed All Settings → General → Devices → TV Management → TV Information.
The raw JPEG was not copied into the repository. Serial number and wired MAC were
visible on the screen and are not recorded here.

User-photo-confirmed (non-sensitive fields):
- Device Name: `[LG] webOS TV NANO756PR`
- Model: `65NANO756PR` (no extra sales suffix such as `.AEK` or `.AEU` shown on this screen)
- webOS TV Version: `6.5.3-47 (kisscurl-koli)`
- Available Internal Storage: `1.07/2.03GB`

This webOS TV Version is not the dotted Software Version (for example 03.53.xx)
shown under Support → Software Update. That photo is still pending.
Sales suffix, board, PCB revision, panel variant, and SoC remain unknown.
No new SSAP calls, no 401 bypass, no update check.

# 2026-11-08 15:02 Atlantic/Reykjavik — Software Update photo
Owner photographed All Settings → Support → Software Update. Raw JPEG not
copied into the repository. No Download and Install, and no update check,
was performed.

User-photo-confirmed:
- Software Version: `03.53.45`
- Auto Update: OFF
- Banner: an important software update is available `03.53.46` / `1142MB`
- Download and Install was visible and not pressed

This is the dotted software/firmware number. It is distinct from the
already-recorded webOS TV Version `6.5.3-47 (kisscurl-koli)`.

# Standing hold — 2026-11-08 later Atlantic/Reykjavik
Keep Software Version `03.53.45`. Leave Auto Update OFF. Do not install the
offered `03.53.46` / `1142MB` update. Sales suffix, board, PCB revision, panel
variant, and SoC remain unknown. No serial or MAC recorded in later notes.

# 2026-11-08 ~17:43–17:46 Atlantic/Reykjavik — owner-run root + Homebrew Channel
Owner photographed (1) a SlopBro “Rooting complete” reboot prompt and (2)
Homebrew Channel after choosing Reboot now. Raw JPEGs are not in the
repository. This agent did not run the client.

User-photo-confirmed:
- SlopBro by throwaway96: “Rooting complete. You may need to reboot for
  Homebrew Channel to appear.” Owner chose Reboot now.
- Homebrew Channel open, branded webosbrew.org, catalog visible. No catalog
  title is recorded as installed.

Not re-photographed after reboot: Software Version, Auto Update, offered
`03.53.46`. Last those values are still the 15:02 Software Update photo.
Standing hold above is unchanged.

This does not identify board/SoC/suffix, does not document a custom-OS boot
route, and does not fill recovery gates. Goal remains an internal OS, not
Homebrew apps. See `evidence/root-result-2026-11-08.md`.

# 2026-11-08 later Atlantic/Reykjavik — sales suffix research
Official firmware applicable-model lists use the base name
`65NANO756PR` with no dotted suffix. Regional support pages publish
`.AEK` (UK; URL slug also `.AEKD`), `.AEU` (Sweden/Portugal/Greece URL),
and `.API` (Italy; also a Greece URL heading). This unit’s on-screen
model is still `65NANO756PR` only. Rear ID-label suffix remains unknown.
See `evidence/sales-suffix-firmware-mapping-2026-11-08.md`.
