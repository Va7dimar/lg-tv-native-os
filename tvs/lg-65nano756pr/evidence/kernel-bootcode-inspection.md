# CORE TWO actual source inspection

Recorded 2026-11-08T05:20:01.229430+00:00 · Atlantic/Reykjavik (UTC+0).

## Outcome
Single exact reviewed isolated invocation: **exit0 / statusOK**, 11.368s. Kernel61088 members /4498 selected; bootcode3086 members /304 selected. Outer6 + inner64174 =64180 members total;4802 selected plaintext files. Prior all-three inventory remains PARTIAL at200000 (Chromium); no resume/retry/reset. No source execution, build or TV action. libkadaptor excluded.

## Provenance and controls
Official exact-model catalog: https://opensource.lge.com/product/list?keyword=65NANO756PR. Original2:511945894B, SHA256 95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832. Original checked INSIDE phase. See `evidence/catalog-manifest.json` and `evidence/core-two-execution-2026-11-08/checkpoint.json`, `command.txt`, `result.json`, stdout/stderr and isolated launcher logs under phase output.
Output: `source-catalog/inspection-core-two-PENDING-REVIEW`. PENDING-REVIEW is an exact historical pathname, not current review status; independent PASS preceded execution. Original → exact outer-member path → staged SHA verified before inner → canonical inner path → selected plaintext SHA/line quotes below. No physical offsets invented.
- `soc/kernel-1.0.0-711..4.tar.gz` → `staged/kernel-1.0.0-711..4.tar.gz`: 170350960B; SHA256 `110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962`; verified before inner.
- `soc/bootcode-1.0.0-1099.7.tar.gz` → `staged/bootcode-1.0.0-1099.7.tar.gz`: 12014324B; SHA256 `b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e`; verified before inner.

| Counter | Actual | Cap |
|---|---:|---:|
|member_count|64180|200000|
|pathname_bytes|2961886|100000000|
|expanded_bytes|1701645860|4294967296|
|selected_text_bytes|12467926|67108864|
|outer_decoded_bytes|522047300|671088640|
|binary_copy_bytes|182365284|335544320|
|admitted_compressed_bytes|694311178|1073741824|

120s complete-phase wall;1GiB AS (not RSS);16MiB selected/member,64MiB total;10GiB free-disk observation,not reservation. Post-phase available 117542842368B. Outer decoded counts logical regular payload, NOT tarheaders/padding/EOA. ROinputs,home/root/cursor hidden,separate network namespace. noexec=false;0644 is not noexec; source never executed. PAX pre-semantic allocations rely on AS/wall backstop; peak RSS not measured. No ceilings changed.

## Material findings

### K1 · Bundled kernel top Makefile declares Linux4.4.84 although directory is named linux-4.4.3.
EXTRAVERSION is empty here; full notice suffix and running-kernel version are not established.
- Inner `linux-4.4.3/Makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/Makefile`; 57250B; SHA256 `92f1690a977d2e3bad752991f1a94ff85f9648dbba891c24f51c4e6bba2887e7`.
  - Lines1–5: 'VERSION = 4\nPATCHLEVEL = 4\nSUBLEVEL = 84\nEXTRAVERSION =\nNAME = Blurry Fish Butt'

### K2 · Vendor RTK modifications default SUBARCH to arm if ARCH unset; commented compiler paths mention LG115x,ASDK and Starfish.
Comments are not a supplied compiler, tested build recipe or identification of installed CPU.
- Inner `linux-4.4.3/Makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/Makefile`; 57250B; SHA256 `92f1690a977d2e3bad752991f1a94ff85f9648dbba891c24f51c4e6bba2887e7`.
  - Lines235–240: '# RTK_patch: default use arch/arm\nifeq ($(ARCH),)\nSUBARCH\t:= arm\nelse\nSUBARCH\t:= $(ARCH)\nendif'
  - Lines262–272: 'ARCH\t\t?= $(SUBARCH)\n# RTK_patch: change toolchain path\n#CROSS_COMPILE\t?= $(CONFIG_CROSS_COMPILE:"%"=%)\n#CROSS_COMPILE\t?= ../../system/tmp/toolchain/asdk-4.9.2-a53-EL-3.10-g2.19-a32n-141121/bin/asdk-linux-\n#CROSS_COMPILE\t?= ../../system/tmp/toolchain/arm-lg115x-linux-gnueabi-4.8-2014.08-1-i686/bin/arm-linux-\n#CROSS_COMPILE\t?= /usr/local/arm-lg115x-linux-gnueabi-4.8-2014.08-1-i686/bin/arm-linux-\n\nifeq ($(ARCH),arm64)\n#CROSS_COMPILE\t:= ../../system/tmp/toolchain/asdk64-4.9.2-a53-EL-3.10-g2.19-a32n-141121/bin/asdk64-linux-\n#CROSS_COMPILE   := ../../system/tmp/toolchain/starfish-sdk-x86_64_4.5.0-20180321/sysroots/x86_64-starfishsdk-linux/usr/bin/aarch64-starfish-linux/aarch64-starfish-linux-\nendif'

### K3 · Both ARM RTK2875/tv006 and ARM64 RTK287O/tv006 development defconfigs are present. ARM64 config names aarch64-starfish-linux-. LG1K configurations also occur in index.
Multiple platform candidates, not selection of this TV board or its live config. The .old_defconfig name matters.
- Inner `linux-4.4.3/arch/arm/configs/realtek/config.develop.rtd2875.tv006.emmc.old_defconfig` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/arch/arm/configs/realtek/config.develop.rtd2875.tv006.emmc.old_defconfig`; 10177B; SHA256 `fe85a3e1c39165889d293f6bc9338e79e1267d7ec3cb07272f1d05e2de698676`.
  - Lines45–45: 'CONFIG_ARCH_RTK2875=y'
  - Lines118–118: 'CONFIG_CUSTOMER_TV006=y'
- Inner `linux-4.4.3/arch/arm64/configs/realtek/config.develop.rtd287o64.tv006.emmc.old_defconfig` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/arch/arm64/configs/realtek/config.develop.rtd287o64.tv006.emmc.old_defconfig`; 9775B; SHA256 `5ff806370033f1accd43d08a113c344d768eabc981e509cf9030680671dff50e`.
  - Lines3–3: 'CONFIG_CROSS_COMPILE="aarch64-starfish-linux-"'
  - Lines42–42: 'CONFIG_ARCH_RTK287O=y'
  - Lines116–116: 'CONFIG_CUSTOMER_TV006=y'
  - Lines373–374: 'CONFIG_KDRIVER_USE_NEW_COMMON=y\nCONFIG_RTK_KDRIVER_SUPPORT=y'

### K4 · Actual kernel index includes drivers/rtk_kdriver and conditional build integration, including HDMI RX,scaler,audio HW,CEC,IR and thermal driver paths.
Metadata presence and Makefile integration do not prove implementations complete, enabled for this TV, buildable, licensable as a whole, or working HDMI/HDCP/panel/audio. Source .c bodies generally not admitted/read.
- Inner `linux-4.4.3/drivers/Makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/drivers/Makefile`; 5278B; SHA256 `467a8d7d6945d5e2cc704a8663fe24c2f4b2f74c29264ffa9d3682303d3c68ff`.
  - Lines179–184: 'ifdef CONFIG_LG_BUILTIN_KDRIVER\n#obj-y\t\t\t\t+= lg_kdriver/core/\nendif\n\nobj-$(CONFIG_RTK_KDRIVER)       += rtk_kdriver/\nobj-$(CONFIG_TEE)               += tee/'
- Inner `linux-4.4.3/drivers/rtk_kdriver/Makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/drivers/rtk_kdriver/Makefile`; 6821B; SHA256 `42b86eb1b21a2a682a8688cac3a6bd2fcaa1d0504532fd71a8858e164acd1a8b`.
  - Lines100–106: 'obj-$(CONFIG_RTK_KDRV_SMARTCARD) += smartcard/\n\n# CEC\nobj-$(CONFIG_RTK_KDRV_CEC) += rtk_cec/\n\n# DDC\nobj-$(CONFIG_RTK_KDRV_DDC) += ddc/'
  - Lines139–142: 'obj-$(CONFIG_RTK_KDRV_WATCHDOG) += rtk_watchdog.o\n\n# Thermal Sensor\nobj-$(CONFIG_RTK_KDRV_THERMAL_SENSOR) += thermal/'
  - Lines167–170: 'obj-$(CONFIG_RTK_KDRV_IR) += ir/\n\n#IRTX Driver\nobj-$(CONFIG_RTK_KDRV_IRTX) += irtx/'
  - Lines189–196: '# SCALER\nobj-$(CONFIG_SUPPORT_SCALER) += tvscalercontrol/\n\n# HDMI RX\nobj-$(CONFIG_RTK_HDMI_RX) += tvscalercontrol/hdmirx/\n\n# LG BOARD\nobj-$(CONFIG_RTK_KDRV_LG_BOARD) += rtk_lg_board.o'
  - Lines217–218: '# Audio HW Driver\nobj-$(CONFIG_RTK_KDRV_AUDIO_HW) += audio_hw/'
  - Lines262–268: 'obj-$(CONFIG_RTK_KDRV_AUDIO) += audio/\nobj-$(CONFIG_RTK_KDRV_VDEC) += vdec/\nobj-$(CONFIG_RTK_KDRV_VUTILS) += vutils/\nobj-$(CONFIG_RTK_KDRV_V4L2_VCODEC) += v4l2_vcodec/\n\nobj-$(CONFIG_RTK_KDRV_TEEPROXY) += teeproxy/\nobj-$(CONFIG_RTK_KDRV_DVO) += directvo/'
- Inner `linux-4.4.3/drivers/rtk_kdriver/Kconfig` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/drivers/rtk_kdriver/Kconfig`; 10890B; SHA256 `19aa6aa6a6f5e9431e86c0a2b253737d289e20e42e01c9637eb38e4f8ed2c9e2`.
  - Lines25–29: '#SCALER\nsource "drivers/rtk_kdriver/tvscalercontrol/Kconfig"\n\n#HDMI RX\nsource "drivers/rtk_kdriver/tvscalercontrol/hdmirx/Kconfig"'
  - Lines60–71: 'config RTK_KDRV_RPC\n\tbool "Use RPC to communicate with Audio & Video."\n\tdefault y\n\thelp\n\t  Use RPC mechanism\n\n# AVCPU\nconfig RTK_KDRV_AVCPU\n\tbool "AVCPU Driver"\n\tdefault n\n\thelp\n\t  Driver used to control Audio & Video cpu.'

### B1 · Bootcode contains U-Boot top Makefile identifying2012.07 and an LG toolchain-dependent bootcode build file.
Bundled source version is not the installed bootloader version, complete boot firmware or custom-image acceptance.
- Inner `bootcode/uboot/Makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/uboot/Makefile`; 34004B; SHA256 `27623ea8faaf185b341f8d30e280af5f5bbbe03b076932ae90d2849e90f270e0`.
  - Lines24–27: 'VERSION = 2012\nPATCHLEVEL = 07\nSUBLEVEL =\nEXTRAVERSION ='
  - Lines182–194: 'ARCH = arm\nexport\tARCH CPU BOARD VENDOR SOC\n\n\n#########################################################################\n# Build MIPS Image Related Setting\n\nMIPS_BOOTLOAD_LIB_NAME\t\t= libbootload.a\nMIPS_BOOTLOAD_LIB_DIR\t\t= $(TOPDIR)/../bsp/core/image/src/app\nMIPS_BOOTLOAD_LIB_PATH\t\t= $(MIPS_BOOTLOAD_LIB_DIR)/$(MIPS_BOOTLOAD_LIB_NAME)\n\n\nCFLAGS += --sysroot=$(TOOLCHAIN_READY)/sysroots/ca9v1-starfishmllib32-linux-gnueabi'
- Inner `bootcode/bin/makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bin/makefile`; 14558B; SHA256 `c6b4ee5d5e9886d8b232a8b4714dd2e1f85b548e24260c1ef60cfe1b01888b1a`.
  - Lines1–1: 'include $(PRJ).inc'
  - Lines21–35: '# Note: This is LG Git. we use lg toolchain even in generic board here. \n# because We assume everyone use this bootcode is for LG project. If you need to use rtk toolchain,please change by yourself.\nTOOL_DIR      ?= $(LG_TOOLCHAIN_PATH)/sysroots/x86_64-starfishsdk-linux/usr/bin/arm-starfish-linux-gnueabi\nTARGET        ?= arm-starfish-linux-gnueabi\nTOOL_BIN      ?= $(TOOL_DIR)\n\n# Below patch is used to prevent the verify failture problem of JenkinsMK2.\n# If we branch the codebase to LGE Git, we should remove below patch first.\nTOOLCHAIN_READY = $(LG_TOOLCHAIN_PATH)\n\nexport TOOLCHAIN_READY\n\n\nTARGET_CPU    = arm\nCROSS_COMPILE = $(TARGET)-'

### B2 · Bootcode/bin/makefile hardcodes PLATFORM_CHIP/NAME=k6l and revision A0; tv006 board files and B3_A1R41.inc/B7_A1R62.inc are indexed.
k6l,A0,tv006,B3/B7 are source labels, NOT verified TV hardware/chassis/SoC. Project .inc files were not selected, so active selection is unresolved.
- Inner `bootcode/bin/makefile` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bin/makefile`; 14558B; SHA256 `c6b4ee5d5e9886d8b232a8b4714dd2e1f85b548e24260c1ef60cfe1b01888b1a`.
  - Lines37–51: '# common SOC platform defination\n#\n#PROJECT_NAME=GP4-L9\nPLATFORM_CHIP=k6l\nPLATFORM_NAME=k6l\nPLATFORM=$(PLATFORM_NAME)\nPLATFORM_ALLOW="k6l:"\nUSE_CITRIX_SERVER=YES\n\n# current SOC platform definition\n#\nPLATFORM_CHIP_VER=k6l\nPLATFORM_CHIP_REV=A0\n\nUSE_EMMC="YES"'

### L1 · Actual selected COPYING files identify GPLv2 kernel terms and U-Boot GPLv2/later-exception wording.
Not a complete per-file license audit, a grant over missing binaries or a warranty of buildability.
- Inner `linux-4.4.3/COPYING` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/kernel-1.0.0-711..4.tar.gz/linux-4.4.3/COPYING`; 18693B; SHA256 `af8067302947c01fd9eee72befa54c7e3ef8a48fecde7fd71277f2290b2bf0f7`.
  - Lines2–11: '   NOTE! This copyright does *not* cover user programs that use kernel\n services by normal system calls - this is merely considered normal use\n of the kernel, and does *not* fall under the heading of "derived work".\n Also note that the GPL below is copyrighted by the Free Software\n Foundation, but the instance of code that it refers to (the Linux\n kernel) is copyrighted by me and others who actually wrote it.\n\n Also note that the only valid version of the GPL as far as the kernel\n is concerned is _this_ particular version of the license (ie v2, not\n v2.2 or v3.x or whatever), unless explicitly otherwise stated.'
- Inner `bootcode/uboot/COPYING` → `source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/uboot/COPYING`; 16398B; SHA256 `73e8f71e4179f55824f57a003cbe815caa157e7e42219029a7814bfd95d627e1`.
  - Lines1–7: '  U-Boot is Free Software.  It is copyrighted by Wolfgang Denk and\nmany others who contributed code (see the actual source code for\ndetails).  You can redistribute U-Boot and/or modify it under the\nterms of version 2 of the GNU General Public License as published by\nthe Free Software Foundation.  Most of it can also be distributed,\nat your option, under any later version of the GNU General Public\nLicense -- see individual files for exceptions.'

## Physically indexed driver coverage
Counts are metadata,not read/executed implementation bodies. HDMI is within scaler: do not sum overlapping rows.
|Path below drivers/rtk_kdriver|Indexed entries|C filenames|Selected text files|
|---|---:|---:|---:|
|tvscalercontrol/hdmirx|77|34|5|
|tvscalercontrol|497|183|31|
|audio|38|24|2|
|audio_hw|30|13|2|
|rtk_cec|15|5|2|
|ir|52|24|3|
|thermal|9|4|2|

Kernel rtk_kdriver:2763 entries including root;2548 regular files;784 C filenames. This is actual vendor-driver-tree evidence, no longer notice-only. Makefile references do not prove HDMI/HDCP/panel/audio completeness. No lg_kdriver path found in this complete kernel index; a commented reference exists. This is not a claim that no required proprietary component exists anywhere.

## Concrete missing evidence / next viable stage
Three small build-guide names are physically indexed but **were not selected by current admission policy**, so their contents/hash are unknown:
- `linux-4.4.3/README_HowToMake.txt` in `kernel-1.0.0-711..4.tar.gz`: 1217B; not read.
- `bootcode/README_Make_Boot.txt` in `bootcode-1.0.0-1099.7.tar.gz`: 1149B; not read.
- `bootcode/README-bootcode.txt` in `bootcode-1.0.0-1099.7.tar.gz`: 1076B; not read.
Combined guide size3442B. This exposes an actionable selector gap, not a claim that build documentation is absent. Future focused allowance/review would be needed to read exactly these files from staged/pinned packages within documented bounds; no automatic rerun or new source reads performed.

Boot project B3_A1R41.inc (7987B) and B7_A1R62.inc (8004B) indexed,unread; project build begins include $(PRJ).inc, so active target/toolchain selection unresolved. Root kernel .config not present in the indexed root; provided development defconfigs are not this unit’s active config.

No exact65NANO756PR occurrence in selected text; this limited negative search is not proof that other source bodies contain no model mapping. Source base4.4.84 corroborates the notice base version only; no explicit matching full711.kalaupapa.4 suffix established here. U-Boot2012.07 and k6l/tv006 source labels do not measure installed bootloader/SoC/board. KernelCOPYING and U-BootCOPYING are actual license text,not complete BSP licensing.

## Decision
Source-learning stage materially advanced: vendor-modified kernel, vendor driver subtree and U-Boot source/build dependencies are confirmed. Complete BSP/buildability, exact-unit mapping, lawful custom boot acceptance and independent recovery remain **NOT PASSED**. Full native OS replacement has not run. No architecture selected; vendor-kernel/userspace reuse stays partial-stack,not complete kernel replacement. HDMI substitute/launcher remain excluded. Protected AppleTV HDMI/audio/power/remote remain acceptance requirements.

Next proof sequence: exact identity/source mapping plus the named documentation gap → supplied compiler/sysroot/config/dependency coverage → legitimate boot and independent recovery design/preservation/logging → separately approved build/target phases. Stock reset/update is not established overwritten-boot recovery. No new authorization or hardware operation inferred.
