# LG65NANO756PR native bootable OS — proposed design

Status: proposed for owner review; NOT approved, implemented, flash-ready or known bootable. 2026-11-08, Atlantic/Reykjavik.

## Goal and boundary
Replace the operating environment INSIDE the TV. First functional acceptance is the TV as a reliable AppleTV display: native panel/backlight, HDMI input including normal licensed HDCP negotiation, audio, power/thermal control and remote input. LG streaming apps are expendable. An HDMI-attached computer, sideloaded app or replacement launcher on otherwise-stock webOS does not fulfill this goal. No boot recipe, SoC, kernel architecture, partition map, addresses or unlock method is known.

## Architectures to choose explicitly
|Architecture|Replacement boundary|Conditional feasibility|Decision|
|---|---|---|---|
|A. Vendor-kernel/BSP reuse + replacement root filesystem/userspace|New internal userspace/init/UI; retain compatible vendor kernel/modules and licensed hardware support. This is PARTIAL-STACK OS replacement, not complete kernel replacement; not merely an app.|Requires a documented legitimate way to boot alternate userspace, compatible available kernel interfaces/binaries, redistribution/use rights and independent recovery. No such route verified.|Hypothesis only; no evidence it has an easier boot route than B. Owner must accept explicit retained-kernel and enumerated vendor-service boundary before selection.|
|B. Rebuilt kernel + vendor BSP + replacement userspace|Replace kernel and userspace while reusing compatible board-specific sources/firmware/driver interfaces.|Requires exact-board source/config/toolchain, legal usable firmware, display/HDMI/audio/power coverage, approved custom boot route and recovery. Kernel source alone insufficient.|Preferred boundary if owner means kernel replacement; remain blocked until evidence supports it.|
|C. Independent kernel/full hardware stack port|Replace kernel/userspace and reimplement hardware integration from public documentation.|Requires lawful hardware documentation and maintainable drivers for TV receiver/display/power path. No evidence package establishes this.|Not first route; stop rather than silently downscope if A/B unavailable.|

No selection is made on the owner's behalf. Recommendation does not authorize preserving stock webOS userspace under a launcher and calling it replacement. A/B must be revisited after source inspection, not promised today.

## Verified inputs and source confidence
|Fact|Evidence|Confidence / limitation|
|---|---|---|
|Model65NANO756PR|Parallel worker ordinary SSAP system/getSystemInfo, device-facts.md|Live model confirmed; no suffix/board/SoC.|
|2021/webOS6 product generation|Official model documentation [S1,S2]|Product specification, not current installed version.|
|Exact-model OSS catalog entry|Public browser worker [S3], release sequence510320, labelwebOS6.0 KLP1.0, three source archive entries|Catalog confirmed; filenames spacing/sizes and archive contents not inspected. Label not live firmware; notice filename210204 not release date.|
|Notice components|Local SHA2563e7a13e14f6cd328c9b5483c25c416e735da67dc5cd08131b61804a9b06fbf8f; notice-inventory.json/md|317notice groups,923unique labels,41license strings. Legal attribution inventory only.|
|Kernel/kdriver leads|Notice id103/104, GPL-2.0; labels include4.4.84-711.kalaupapa.4|Not running-kernel measurement or source content proof.|
|BSP/video/audio leads|Notice packagegroup-starfish-bsp,id227; video adaptation/id294; videooutputd/id295; audiooutputd/id14; omx-il-rtk/id222|Names do not prove complete drivers or actual SoC.|
|Candidate board trail|[S4] EBU66527491/replacementCRB38659901,65NANO75_F_BOE_EU_SVC BOM LG UD15D for65NANO756PR.AEU; [S5] EAX69581701(1.1)/EBT66830203 seller claim|Separate parts listings, not installed-board facts or reconciled identities.|
|SDR configuration baseline|NOTES.md/photo/API observations|HDMI2 Filmmaker: panel40,contrast80,brightness50,colour50,sharpness0; dynamiccontrastOff,gammaBT.1886,blackAuto,processingOff,CinemaScreenOn. HDR untouched; these are settings not calibrated measurements.|
|Installed version/SoC/board/suffix|Not obtained; firmware-info API401|Unknown; no denied-endpoint retry.|
|Custom boot/recovery|None verified|Blocking, not proof universal impossibility.|

## Source register
S1 https://www.lg.com/uk/tvs/nanocell-tvs/65nano756pr/
S2 https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/ and official linked guide http://kr.eguide.lgappstv.com/manual/w21_mr10/userguide_w6.0_mr10_e10.html ; local official English PDF official-guide-extracted/w6.0_mr10_e10_eng.pdf.
S3 https://opensource.lge.com/product/list?keyword=65NANO756PR ; public product source disclaimer https://opensource.lge.com/product . Exact browser download of notice retained in source-catalog/. No hidden/download APIs authorized.
S4 https://lgdelar.se/lg-reservdelar/tv/kretskort/ebu66527491-mainboard/
S5 https://www.toutvendre.fr/p/motherboard-tv-lg-65nano756pr-75nano756pr-eax69581701-1-1-e/984312608
S6 https://webostv.developer.lge.com/develop/getting-started/developer-mode-app ; app testing is not system replacement.
S7 https://www.webosose.org/docs/guides/setup/system-requirements/ and https://www.webosose.org/about/governance-licensing/faq/ ; OSE sources do not make this retail TV a supported target.

## Proposed system boundaries and interfaces
Hardware adapter layer must expose internal panel/backlight, HDMI receiver/input selection/status (distinct from HDMI display output), audio route/mute, physical/Magic Remote events, CEC, standby/resume and health/thermal telemetry. Actual APIs and ABIs must be derived from inspected compatible sources/documentation, not invented here. UI/services consume a documented adapter contract after platform selection; unsupported functions must report unavailable, never silently fall back to private calls. Stock calibration/provisioning remains unit-specific data, not a redistributable fixture. No DRM/HDCP circumvention or copied device credentials.

## Safety invariants
No TV commands or changes during planning. Ordinary UI version discovery later requires a specific read-only session; no update/reset action. No service menu, chassis opening, serial console wiring, buying parts, root/secureboot bypass, account changes, dev enrollment, privileged API, flash or destructive write is included in a general approval. A hardware-dependent step needs its own documented method/risk authorization. If normal source access fails, report it; do not mint URLs, use internal APIs or change identity.

## Approval and readiness
Plan readiness means tasks/evidence/acceptance are reviewable. Flash readiness additionally requires exact hardware mapping, selected architecture, complete usable dependency inventory, legitimate custom-boot route, proven independent recovery and specific risk consent. Presently neither boot nor recovery gate passes. Proposed first approval is BOX-ONLY evidence tooling/source inspection and approved normal UI readout, not any TV OS implementation. A later design revision must enumerate concrete build target, artifact hashes and permitted deploy operation before target code/deployment.

## Review-driven design clarifications
A-K retains kernel/modules; A-H also retains only enumerated necessary hardware services. Neither may quietly retain stock init/system manager/compositor/app stack and call a launcher OS replacement. B-same versus B-new must distinguish rebuilt compatible kernel/config from a different kernel needing new driver/ABI proof. Owner approves a complete retained/replaced ledger rather than a letter alone. Core boot/control,licensed hardware services and component availability are unverified dependencies,not facts about this unit.
Architecture selection requires normal protected AppleTV playback through lawfully usable stack and unit-owned provisioning;an unprotected HDMI picture is not sufficient. No HDCP circumvention or provisioning-copying route is proposed.
Pre-bootG5 requires documented startup,panel/backlight,power/watchdog/thermal safety plus independent stop/observation. Documentary recovery,validated recovery and coverage for this operation are different;compatible-target proof explicitly covers board,panel,boot policy,storage and provisioning. Recovery-test hardware/failure injection needs separate approval,not a broadgo.
First proposed approval is E1-box metadata/download/hash/desk-research only; E2 archive parsing needs a reviewed safety/test addendum and separate approval. E-tooling,E-TV-info,E-TV-baseline,isolatedbuild,recoveryvalidation and deployment are separate scopes. Early desk-onlyU0 may yield deployment-no-go;source research can remain valuable but continuing for learning needs explicit scope. AEK/AEU candidate conflict is unresolved;hardware/source/firmware changes invalidate affected evidence.

Gemini plan review succeeded. Its useful dependency challenges were accepted,not its unsupported assertions about this unit’s secureboot,dm-verity,TEE/RPMB or exact driver interfaces. Required binary supply must be evidenced lawfully. A spare-target recovery demonstration cannot waive preserving the primary unit’s unique data; documented non-impact or authorized preservation/restore proof is required. No claim archives contain or lack proprietary components until read-only audit.
