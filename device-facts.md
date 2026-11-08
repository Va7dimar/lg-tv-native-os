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
