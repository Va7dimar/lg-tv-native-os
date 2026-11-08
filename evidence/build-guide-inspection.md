# Actual three-guide inspection — complete closed scope

8 November2026,05:47–05:48 Atlantic/Reykjavik (UTC+0).

## Execution and acceptance
Parent literal-command reviewPASS was coordination approval under ownerContinue,not a fresh independent code audit. Exact commandSHA256d40686fb2d51964980ef50300cdab9530433b86c71adae520ed39d43af211476 executed ONCE;exit0 in6.089s. Inputs only prior-pinned staged kernel170350960B and bootcode12014324B. No original outer read,newdownload,libkadaptor/Chromium/deepernesting,sourceexecution/build,TV/hardware/account action.

Both emitted compressed input hashes matched expected pins BEFORE guide findings were trusted;both archive statusesOK;64174members;2961727pathnamebytes;984765350expandedbytes;exactthreeguides3442B. Shared caps200000members/100000000pathbytes/4294967296expandedbytes/120s/1GiBAS (notRSS),10GiBdiskfloor;1217B/member.3442B is postvalidated,not an intrinsic aggregate selected cap. Code unchanged. Diskreserve observed,not reserved;noexecfalse,0644notnoexec;PAX allocations rely on AS/wall backstop. No peakRSS measurement.

Run/checkpoint/command/stdout/stderr/result/acceptance-before-analysis: `evidence/build-guide-execution-2026-11-08/`. Reader inventory and launcherlogs: `source-catalog/inspection-build-guides-2026-11-08/`. Reader --hash-input records hashes but does NOT reject expected mismatch before parse;this known residual was explicitly accepted for bounded research and fingerprints were checked before evidence analysis.

## Source provenance and exact raw line citations
Official catalog https://opensource.lge.com/product/list?keyword=65NANO756PR → originalarchive2(hashcatalog-manifest.json) → CORE TWO exactoutermembers and stagedhashes(verifiedpreviousphase) → currentinputhashmatches → exactinnerguide→selectedplaintextSHA below. No physical offsets inferred;memberordinal is not compressedseekoffset. Entire guide text below is quoted DATA,not execution permission.

### linux-4.4.3/README_HowToMake.txt
Package `kernel-1.0.0-711..4.tar.gz` compressed inputSHA256 `110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962`. Selected `source-catalog/inspection-build-guides-2026-11-08/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/README_HowToMake.txt`, 1217B, SHA256 `2c2227082b356f3cd40a93b718489a3d68d6e33424f86004cbf6166cc0b034a7`.
```text
01: #========================================
02: # How to compile the Linux kernel/rtk_driver/common
03: #========================================
04: 
05: #----------------------------------------
06: @@. Elements in the package
07: #----------------------------------------
08: + kernel-1.0.0-711.kalaupapa.4.tar.gz
09: - README_HowToMake.txt : describe how to compile source codes using toolchain
10: 
11: #----------------------------------------
12: @@. The order to compile codes
13: #----------------------------------------
14: 1)./starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh
15: - Enter target directory for SDK (default: /opt/starfish-sdk-x86_64/5.0.0-20190307): /HOME/USERNAME/TOOLCHAIN
16: - You are about to install the SDK to "DIRECTORY". Proceed[Y/n]? y
17: - You need remember you toolchain install path.
18: 2) export toolchain PATH:
19: - PATH=/HOME/USERNAME/TOOLCHAIN/sysroots/x86_64-starfishsdk-linux/usr/bin/arm-starfish-linux:$PATH
20: 3) make config and make
21: - make realtek/config.develop.rtd2875.tv006.emmc.old_defconfig
22: - CROSS_COMPILE=arm-starfish-linux- make KALLSYMS_EXTRA_PASS=1
23: 
24: #----------------------------------------
25: @@. Output path and file
26: #----------------------------------------
27: - .:
28: -- vmlinux.bin : linux binary file
```

### bootcode/README_Make_Boot.txt
Package `bootcode-1.0.0-1099.7.tar.gz` compressed inputSHA256 `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e`. Selected `source-catalog/inspection-build-guides-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/README_Make_Boot.txt`, 1149B, SHA256 `b0cb2f0ba58ec6c369776724b432e2b44553145351856baab541c47bfe9fb354`.
```text
01: INTRODUCTION
02: ===============================================================================
03: Source code path:
04: download source with below path:					
05: checkout wall.lge.com/bsp/realtek/boot to 
06: 	boot/
07: 
08: 
09: HOW TO SET TOOLCHAIN
10: ===============================================================================
11: For 64bit toolchain
12: 1. Get toolchain file
13: 2. Run toolchain script and remember your install SDK path.
14: 	$ ./starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh
15: 	webOS TV SDK installer version 5.0.0-20190307
16: 	=============================================
17: 	Enter target directory for SDK (default: /opt/starfish-sdk-x86_64/5.0.0-20190307): .
18: 	You are about to install the SDK to "/opt/starfish-sdk-x86_64/5.0.0-20190307". Proceed[Y/n]? Y
19: 	Extracting SDK..........................done
20: 	Setting it up...done
21: 	SDK has been successfully set up and is ready to be used.
22: 	
23: 	
24: HOW TO BUILD
25: ===============================================================================
26: For 64bit toolchain
27: 1. Setup toolchain path
28: 	export LG_TOOLCHAIN_PATH=/opt/starfish-sdk-x86_64/5.0.0-20190307
29: 2. Build Boot
30: 	- make -C bin PRJ=B3_A1R41 
31: 	or
32: 	- make -C bin PRJ=B7_A1R62
33: 
```

### bootcode/README-bootcode.txt
Package `bootcode-1.0.0-1099.7.tar.gz` compressed inputSHA256 `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e`. Selected `source-catalog/inspection-build-guides-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/README-bootcode.txt`, 1076B, SHA256 `e42fad809ed711810d51bb3d41f0d2b513e404ee0af3e582f94f4a9b11d3fb65`.
```text
01: #========================================
02: # How to compile the bootcode
03: #========================================
04: 
05: #----------------------------------------
06: @@. Elements in the package
07: #----------------------------------------
08: + bootcode-1.0.0-1099.kalaupapa.7.tar.gz
09: - README : describe how to compile source codes using toolchain
10: 
11: #----------------------------------------
12: @@. The order to compile codes
13: #----------------------------------------
14: 1)./starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh
15: - Enter target directory for SDK (default: /opt/starfish-sdk-x86_64/5.0.0-20190307): /HOME/USERNAME/TOOLCHAIN
16: - You are about to install the SDK to "DIRECTORY". Proceed[Y/n]? y
17: - You need remember you toolchain install path.
18: 2) export toolchain PATH:
19: - export LG_TOOLCHAIN_PATH=/HOME/USERNAME/TOOLCHAIN
20: 3) make config and make
21: - make -C bin PRJ=B3_A1R41 
22: or
23: - make -C bin PRJ=B7_A1R62
24: 
25: #----------------------------------------
26: @@. Output path and file
27: #----------------------------------------
28: - bin/tmp:
29: -- u-boot.bin : bootcode binary file
```

## Material new facts and exact limits
1. Kernel guide8 names component `kernel-1.0.0-711.kalaupapa.4.tar.gz`;guide21–22 documents the RTK2875/tv006/emmc old_defconfig,arm-starfish-linux- prefix and KALLSYMS_EXTRA_PASS=1. Root output is documented as vmlinux.bin (27–28). This is a provided build candidate,not proof this TV uses it. Sourcebase4.4.84 from priorMakefile remains distinct from componentversion/liveuname.
2. Allthree guides name `starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20190307.sh`. Exact installer basename absent from both complete CORE TWO member indexes. This does NOT prove absence from other unopened packages or public availability. Installer/version requirements are named;SDK is not obtained or installed. Filename date is not installed TV firmware/date.
3. Both boot guides specify LG_TOOLCHAIN_PATH and alternative PRJ=B3_A1R41 or B7_A1R62 (README_Make_Boot28–32;README-bootcode19–23). Those .inc filenames are indexed,but their contents remain UNREAD and no selection is authorized here. Neither project is selected automatically.
4. Boot output documented as bin/tmp/u-boot.bin (README-bootcode28–29);component filename1099.kalaupapa.7 at8 differs from outer package1099.7. Documentary component naming is not installedbootloaderversion,retailupdateimageformat or imageacceptance.
5. README_Make_Boot11/26 says64bittoolchain,while previously admitted boot makefile has ARCH=arm,arm-starfish-linux-gnueabi- default and ca9v1-starfishmllib32 sysroot. Kernel guide uses arm-starfish-linux-. Host64bit wording is not proof of targetARM64;prefix/sysroot compatibility and host/target meaning needSDKmanifest/PRJcontext. Do not resolve by guessed architecture.
6. README_Make_Boot3–6 names a vendor checkout and workingrootboot/;we did not access it. Catalog payload rootbootcode/ exists,includingbsp/uboot. Different path/convention needs build-layout reconciliation;not proof missing source or authority for privateaccess.
7. None of these three complete guide texts provides an exact65NANO756PR board/panel/suffix link,manufacturer custom-image boot/install route,independent recovery procedure,calibration/provisioning backup or protectedHDMI/panel safety validation. Their build steps do not establish these properties.

## Dependency closure and next documentary frontier
See `evidence/build-dependency-ledger.json` / `.md`. Remaining:lawful matchingSDK/compiler/sysroot supply+manifest;project.inc contents/choice;build-layout,input,patch/dependency/license closure;exact physicalunit/source mapping;documented accepted boot and independent recovery/logging/preservation. Future scoped research may target these gaps;current exactthree-guide objective is EXHAUSTED,not permission to inspect PRJ.inc,fetch SDK,build or touchTV. No fullreplacement or partial-stack architecture selected.

## Review status
Allthree focused subscribed documentary reviews completed:Opusrequested5.5/high50.209s reported5.5AND4.8+safety_stops2;Codexactualgpt-6.1-sol/high27.635s;Geminirequestedgemini-4-argon-high55.367s,actualmodelnotseparatelyreported.All exit0,no timeout/refusal. Fullreconciliation:`plan-reviews/2026-11-08-build-guide-findings/reconciliation.md`. No operatorfallback/retry;notexclusiveOpus5.5coverage. Earlier mixedOpus review remainsretained.

Reviewer-confirmednewdirectdiscrepancy:README_Make_Boot17–18 enters . then echoes /opt/...;this is sampletranscript inconsistency,not tested installerbehavior. Corrected packagecount:135total first-two nestedpackages minus2coretwo =133uninspected siblings;no SDKclaim beyond exactbasenamenotfoundincoretwo. Differences ink6l/RTKprojectlabels,prefixes anddirectoryversions are unresolvedrelationships,notprovedincompatibility. Recoveryisunknown,notprovedimpossible.
