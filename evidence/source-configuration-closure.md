# Source configuration / SDK closure — actual continuing off-TV research
2026-11-08T06:06:19.532050+00:00 · Atlantic/Reykjavik

## Concrete findings
### P1 Both documented PRJs explicitly configure RTD2875;B3usesBGA_27x27/TV006_27x27,B7usesBGA/TV006. DDRprofilefilenamesdiffer.
Sourceprojectconfiguration,notphysicalunitidentityoractualDDRgeometry.
### P2 Bundledproject_config.h matches B7-distinguishingpackage/board/DDRlist;Makefile regeneratesfromPRJinc.
Alignmentnotprooflastactivebuild,generationhistory,productionselectionordeployment.
### P3 ARM U-Boot build options coexistwithATF/arm64auxoptions;configured64bitkerneljumpFALSE.
DoesnotidentifyactualCPUcapabilities/livebootpolicy. k6lbuildlabelneednotcontradictRTD2875projectlabels.
### P4 Core/customerlibraryproductionMakefilesand13embeddedcore.imginputsarepresentinindex;include/rbus367filespresent.
Do not label generated libraries or matchingembeddedblobnames as missing merely becauseoutputbasenameabsent;no build/run validation.
### P5 DefaultdocumentedprjroutebuildsU-Boot;Makefilecompletionnamesuboot/u-boot.bin,whereguidebin/tmpdiffers. Separateflash_image route referencesmissinginthispackage directories.
RawU-Bootbuildcandidateisnotcompleteflashablefirmware/systemimage;mayneedsupplyfromelsewhere—notimpossibleclaim.
### P6 bin/hw_setting/realtek,tools/flash_image_maker,Aux_code,Aux_code_2nd havezeroentriesincompletebootcodeindex.
Missingfromthisinspectedpackageonly,notallLGsources/publicresources. DifferentprebuiltATF.binfilenamespresent;notrebuildclosure.
### P7 BothsourcePRJssetOTPsecurebootTRUE,rescuesourceNULL,AC-onUSBupdateDisable.
Sourceflagsnotlivefuse/securitystateorretailrecoverycapability;nochanges/bypass/keycontentreading.
### P8 Publiccommunitylistslater20191125StarfishSDK+sysrootassets,498625937Btotal;exactMarchSDKnotresolved.
Communityprovenanceclaim,notLGauthority;compatibility/license/manifest/inputclosureunverified. NoSDKdownload/install.

## Actual phase execution
Two successful new objectives,not failed-run retries orChromiumresume. Same pinnedbootinput SHA b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e checked before trustingresults. Existing reader/launcherunchanged. Eachphase3086members/117241pathnameB/106430237expandedB;project3files23455B/0.513s;helper3files11588B/0.547s. Sharedphasecaps200k/100MB/4GiB/120s/1GiBAS/16MiBpermember/64MiBplanned+postcheck/10GiBobservedreserve. ASnotRSS,noexecfalse,PAXbackstop. No originalouterreads,sourceexecution/build,SDKinstall orTVaction.
Exactcommands/checkpoints/rawlogs/results/acceptance: `evidence/project-config-execution-2026-11-08/` and `evidence/build-closure-execution-2026-11-08/`. Rawinventories/admittedfiles:corresponding `source-catalog/inspection-project-config-2026-11-08/` and `inspection-build-closure-2026-11-08/`.

## Exact source citations
### B3_A1R41.inc
`source-catalog/inspection-project-config-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bin/B3_A1R41.inc`,7987B,SHA256`4263d4c6a4a06874d4277edbb78df3e90c931a309a4a7074a49cdc3e34444849`
- Lines7–19: 'Config_Chip_Version = Ver_A\n\n##Package type [ BGA | BGA_27x27 ]\nConfig_Package_type = BGA_27x27\n\n##Board Name [ TV006 | TV006_27x27]\nConfig_Board = TV006_27x27\n\n##Bootcode type [RELEASE|DEBUG]\nConfig_Boot_Type = RELEASE\n\n## DDR SIZE config [OTP|FIXED]\nConfig_Dram_SIZE = FIXED'
- Lines27–35: 'Config_Boot_Flash_Type_is = EMMC\n\n# ********************************************************************\n# EMMC TIMING MODE (for uboot)\n# ********************************************************************\n# flag                      value\n# ********************************************************************\n##Boot Flash Type is [ HS400 | HS200 | NORMAL ]\nConfig_emmc_timing_is = HS400'
- Lines48–61: '##Target Board [ RTD2875 ]\nConfig_Target_Board = RTD2875\n\n##Target Board [ REALCHIP | FPGA ]\nConfig_IC_is = REALCHIP\n\n# ********************************************************************\n# Config\n# ********************************************************************\n# flag                      value\n# ********************************************************************\nConfig_Aux_Code_Image_File = "Aux_code_uni.img"\nConfig_Aux_Code_2nd_Image_File = "Aux_code_2nd.img"\nConfig_Extra_image_File_list =  B27_ddr4_4G4G4G4G_d1_2GB_V1 B27_ddr4_4G4G4G4G_d2_2GB_V1'
- Lines97–99: 'Config_DTE_Bootcode_Config_Value = realtek_tv006\nConfig_DTE_Bootcode_Board_name_Value = tv006\nConfig_DTE_Bootcode_SOC_Value = realtek'
- Lines115–130: '##Rescue Switch [ FLASH | USB | NULL ]\nRescue_Source =\tNULL\n##Rescue_Flash_Source =\t\t[S | K]\nRescue_Flash_Source =\t\tS\n#Rescue_File_Name =\t\tvmlinux.rescue.realtek.bin\nRescue_File_Name =\t\tvmlinux.rescue.realtek.bin.lzma\nRescue_K_File_Name =\t\tvmlinux.rescue.realtek.k.bin\n\n# ********************************************************************\n# Config\n# ********************************************************************\n# flag                      value\n# ********************************************************************\n##Usb update when AC ON feature [ Enable | Disable ]\nConfig_AC_on_Usb_Update_image = Disable\nConfig_AC_on_Usb_Update_dvrboot = Disable'
- Lines145–146: '##OTP Secure Boot [ TRUE | FALSE ]\nConfig_OTP_Secure_Boot = TRUE'
- Lines189–193: '##[ TRUE | FALSE]\nConfig_Jump_64Bit_Kernel = FALSE\n\n##Config Boot ATF [ TRUE | FALSE ]\nConfig_Boot_ATF = TRUE'
### B7_A1R62.inc
`source-catalog/inspection-project-config-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bin/B7_A1R62.inc`,8004B,SHA256`ffd6cdebc5e35300a084c82da92c9d1b3d0027a28f26bbf520473985438f5074`
- Lines7–19: 'Config_Chip_Version = Ver_A\n\n##Package type [ BGA | BGA_27x27 ]\nConfig_Package_type = BGA\n\n##Board Name [ TV006 | TV006_27x27]\nConfig_Board = TV006\n\n##Bootcode type [RELEASE|DEBUG]\nConfig_Boot_Type = RELEASE\n\n## DDR SIZE config [OTP|FIXED]\nConfig_Dram_SIZE = FIXED'
- Lines27–35: 'Config_Boot_Flash_Type_is = EMMC\n\n# ********************************************************************\n# EMMC TIMING MODE (for uboot)\n# ********************************************************************\n# flag                      value\n# ********************************************************************\n##Boot Flash Type is [ HS400 | HS200 | NORMAL ]\nConfig_emmc_timing_is = HS400'
- Lines48–61: '##Target Board [ RTD2875 ]\nConfig_Target_Board = RTD2875\n\n##Target Board [ REALCHIP | FPGA ]\nConfig_IC_is = REALCHIP\n\n# ********************************************************************\n# Config\n# ********************************************************************\n# flag                      value\n# ********************************************************************\nConfig_Aux_Code_Image_File = "Aux_code_uni.img"\nConfig_Aux_Code_2nd_Image_File = "Aux_code_2nd.img"\nConfig_Extra_image_File_list = B22_ddr3_4G4G4G_d1_1_5GB_V1 B22_ddr3_4G4G4G_d2_1_5GB_V1 B23_ddr4_4G4G4G_d1_1_5GB_V1'
- Lines97–99: 'Config_DTE_Bootcode_Config_Value = realtek_tv006\nConfig_DTE_Bootcode_Board_name_Value = tv006\nConfig_DTE_Bootcode_SOC_Value = realtek'
- Lines115–130: '##Rescue Switch [ FLASH | USB | NULL ]\nRescue_Source =\tNULL\n##Rescue_Flash_Source =\t\t[S | K]\nRescue_Flash_Source =\t\tS\n#Rescue_File_Name =\t\tvmlinux.rescue.realtek.bin\n#Rescue_File_Name =\t\tvmlinux.rescue.realtek.bin.lzma\n#Rescue_K_File_Name =\t\tvmlinux.rescue.realtek.k.bin\n\n# ********************************************************************\n# Config\n# ********************************************************************\n# flag                      value\n# ********************************************************************\n##Usb update when AC ON feature [ Enable | Disable ]\nConfig_AC_on_Usb_Update_image = Disable\nConfig_AC_on_Usb_Update_dvrboot = Disable'
- Lines145–146: '##OTP Secure Boot [ TRUE | FALSE ]\nConfig_OTP_Secure_Boot = TRUE'
- Lines189–193: '##[ TRUE | FALSE]\nConfig_Jump_64Bit_Kernel = FALSE\n\n##Config Boot ATF [ TRUE | FALSE ]\nConfig_Boot_ATF = TRUE'
### headeralignmentnotactualactivebuild
`source-catalog/inspection-project-config-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/src/include/project_config.h`,7464B,SHA256`f51c18229ae5f242f6734c406eb7bbfb0a8e67dab09500b8a7f458b8a0d3e416`
- Lines17–21: '#define Config_Chip_Version_Ver_A\n#define Config_Package_type_BGA\n#define Config_Board_TV006\n#define Config_Boot_Type_RELEASE\n#define Config_Dram_SIZE_FIXED'
- Lines43–52: '#define Config_Target_Board_RTD2875\n#define Config_IC_is_REALCHIP\n//********************************************************************\n//Config\n//********************************************************************\n//flag                      value\n//********************************************************************\n#define Config_Aux_Code_Image_File\t\t\t"Aux_code_uni___img"\n#define Config_Aux_Code_2nd_Image_File\t\t\t"Aux_code_2nd___img"\n#define Config_Extra_image_File_list\t\t\tB22_ddr3_4G4G4G_d1_1_5GB_V1 B22_ddr3_4G4G4G_d2_1_5GB_V1 B23_ddr4_4G4G4G_d1_1_5GB_V1'
- Lines93–101: '#define Rescue_Source_\tNULL\n#define Rescue_Flash_Source_\t\tS\n//********************************************************************\n//Config\n//********************************************************************\n//flag                      value\n//********************************************************************\n#define Config_AC_on_Usb_Update_image_Disable\n#define Config_AC_on_Usb_Update_dvrboot_Disable'
- Lines113–113: '#define Config_OTP_Secure_Boot_TRUE'
- Lines147–151: '#define Config_Jump_64Bit_Kernel_FALSE\n#define Config_Boot_ATF_TRUE\n\n#endif //#ifndef EXTERN_PARAM_H\t\n#define Config_Panel_'
### buildrouteandinputdirs
`source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bin/makefile`,14558B,SHA256`c6b4ee5d5e9886d8b232a8b4714dd2e1f85b548e24260c1ef60cfe1b01888b1a`
- Lines21–35: '# Note: This is LG Git. we use lg toolchain even in generic board here. \n# because We assume everyone use this bootcode is for LG project. If you need to use rtk toolchain,please change by yourself.\nTOOL_DIR      ?= $(LG_TOOLCHAIN_PATH)/sysroots/x86_64-starfishsdk-linux/usr/bin/arm-starfish-linux-gnueabi\nTARGET        ?= arm-starfish-linux-gnueabi\nTOOL_BIN      ?= $(TOOL_DIR)\n\n# Below patch is used to prevent the verify failture problem of JenkinsMK2.\n# If we branch the codebase to LGE Git, we should remove below patch first.\nTOOLCHAIN_READY = $(LG_TOOLCHAIN_PATH)\n\nexport TOOLCHAIN_READY\n\n\nTARGET_CPU    = arm\nCROSS_COMPILE = $(TARGET)-'
- Lines104–121: 'BIN_DIR          = $(TOP_DIR)/bin\nIMAGE_DIR        = $(BIN_DIR)/image\nLINK_DIR         = $(BIN_DIR)/link\nOBJ_DIR          = $(BIN_DIR)/obj\nTMP_DIR          = $(BIN_DIR)/tmp\nHW_SETTING_DIR   = $(BIN_DIR)/hw_setting\nHW_SETTING_DIR_TARGET = $(BIN_DIR)/hw_setting/realtek\n\nSRC_DIR          = $(TOP_DIR)/src\nINCLUDE_DIR      = $(SRC_DIR)/include\nU_BOOT_DIR       = $(TOP_DIR)/uboot\nK_BOOT_DIR       = $(TOP_DIR)/kboot\nAUX_CODE_UNI_DIR = $(TOP_DIR)/Aux_code\nAUX_CODE_2ND_DIR = $(TOP_DIR)/Aux_code_2nd\nTOOLS_DIR        = $(TOP_DIR)/tools\n\nCONFIGCONV_DIR              = $(TOOLS_DIR)/configconv\nFLASH_IMAGE_MAKER_DIR       = $(TOOLS_DIR)/flash_image_maker'
- Lines139–158: 'BUILD_HW_SETTING_64 = 0\nifeq ($(Config_Boot_ATF), TRUE)\n\tAUX_CODE_UNI_TARGET_EXT = _arm64_atf\n\tBUILD_HW_SETTING_64 = 1\nendif\n\nBUILD_R64=0\nAU_CODE_INFO="Aux code universal version"\nifeq ($(Config_Boot_ATF), TRUE)\n\tBUILD_R64=0\n\tDEFINE_AUXCODE_OPTS += "arm64=1"\n\tDEFINE_AUXCODE_OPTS += "CONFIG_BOOT_ATF=TRUE"\n\tAU_CODE_INFO += "(atf_arm64)"\nendif\n\nifeq ($(GCC_VERSION), GCC8)\n\t\tDEFINE_AUXCODE_OPTS += "LGE_GCC8=TRUE"\nelse\n\t\t#DEFINE_AUXCODE_OPTS += "LGE_GCC8=FALSE"\nendif'
- Lines237–241: '# DTE Bootcode default config\nConfig_DTE_Bootcode_ARCH_Value    = arm\nConfig_DTE_Bootcode_CPU_Value     = armv7\nConfig_DTE_Bootcode_Vendor_Value  = realtek\nConfig_DTE_Bootcode_Options_Value ='
- Lines264–279: 'prj: clean checkfile key configconv uboot build_done\n\n.PHONY: tool_setting hw_setting uboot otp key\n\nclean:\n\t$(RM) $(OBJ_DIR)/* $(TMP_DIR)/* dvrboot.exe.bin rescue.exe.bin dvrboot.rescue.exe.bin pgm_otp.bin bootloader.tar $(IMAGE_DIR)/$(Config_DTE_Bootcode_Image_File)\n\ncheckfile:\n\nconfigconv: key\n\t$(PERL) $(SCRIPT_DIR)/$(CONFIGCONV_SCRIPT) \\\n\t\t$(INCLUDE_DIR)/project_config.h \\\n\t\t$(BIN_DIR)/$(PRJ).inc\n\t@echo "#define Config_Panel_$(Config_Panel)" >> $(INCLUDE_DIR)/project_config.h\n\nkey: checkfile'
- Lines291–305: 'uboot:\n\t$(CD) $(TOP_DIR); \\\n\t\t./genlink_realtek.sh; \\\n\t$(CD) $(U_BOOT_DIR); \\\n\t\trm -f include/config.mk; \\\n\t\tmake distclean; \\\n\t\techo "$(Config_DTE_Bootcode_Config_Value) $(Config_DTE_Bootcode_ARCH_Value) $(Config_DTE_Bootcode_CPU_Value) $(Config_DTE_Bootcode_Board_name_Value) $(Config_DTE_Bootcode_Vendor_Value) $(Config_DTE_Bootcode_SOC_Value) $(Config_DTE_Bootcode_Options_Value)" > boards.cfg; \\\n\t\tmake $(Config_DTE_Bootcode_Config_Value) r64=$(BUILD_R64)\n\n\t$(CD) $(TMP_DIR); \\\n\t\t$(CP) $(U_BOOT_BIN) $(U_BOOT_TARGET); \\\n\t\t$(CP) $(U_BOOT_ELF) $(U_BOOT_ELF_TARGET); \\\n\t\t$(CP) $(U_BOOT_MAP) $(U_BOOT_DIS) $(U_BOOT_SREC) ./; \\\n\t\t$(CP) $(U_BOOT_TARGET) $(IMAGE_DIR)/$(Config_DTE_Bootcode_Image_File) ; \\\n\t\t$(CP) $(U_BOOT_ELF_TARGET) $(IMAGE_DIR)/$(Config_DTE_Bootcode_Image_File)_elf'
- Lines352–376: "flash_image: hw_setting check_size aux_code aux_code_2nd\nifneq ($(strip $(Rescue_Source)), NULL)\n\t$(CD) $(FLASH_IMAGE_MAKER_DIR); \\\n\tmake PRJ=$(PRJ) clean; \\\n\tmake PRJ=$(PRJ) output=rescue b2a; \\\n\tmake PRJ=$(PRJ) output=rescue dvrboot; \\\n\t$(CP) -vf dvrboot.exe.bin $(TOP_DIR)/bin/rescue.exe.bin\n\t$(CD) $(FLASH_IMAGE_MAKER_DIR); \\\n\tmake PRJ=$(PRJ) clean; \\\n\tmake PRJ=$(PRJ) b2a; \\\n\tmake PRJ=$(PRJ) dvrboot; \\\n\t$(CP) -vf dvrboot.exe.bin $(TOP_DIR)/bin/dvrboot.rescue.exe.bin\nendif\n\t$(CD) $(FLASH_IMAGE_MAKER_DIR); \\\n\tmake PRJ=$(PRJ) clean; \\\n\tmake PRJ=$(PRJ) output=bootcode b2a; \\\n\tmake PRJ=$(PRJ) output=bootcode dvrboot; \\\n\tmake PRJ=$(PRJ) package; \\\n\t$(CP) -vf dvrboot.exe.bin $(TOP_DIR)/bin/dvrboot.exe.bin; \\\n\t$(CP) -vf bootloader.tar $(TOP_DIR)/bin/bootloader.tar\n\notp: flash_image\n\nhw_setting:\n\tcd $(HW_SETTING_DIR)/realtek;make extra_image ENABLE_ARM64=1 HW_CONFIG_LIST='$(Config_Extra_image_File_list)' "
- Lines384–395: 'build_done:\n\t@echo "Build done!!!"\n\t@echo ""\n\t@echo "==========================================================================="\n\t@echo ""\n\t@echo "         Project config : $(PRJ)"\n\t@echo ""\n\t@echo "==========================================================================="\n\t@echo ""\n\t@echo "   output => uboot/u-boot.bin"\n\t@echo ""\n\t@echo "   Build date:  $(shell date)"'
### includedcorelibraryrulesandembeddedblobs
`source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/bsp/core/Makefile`,3025B,SHA256`6241bbd81aebfc81bf246486d441950b5c1e0be815eceb5fa07250b7cccc9b0c`
- Lines13–60: 'LIB\t= $(obj)librt_core.a\n\n# core lib\nCOBJS-y += src/lib/rtlib_cmd.o\nCOBJS-y += src/lib/rtlib_bdinfo.o\nCOBJS-y += src/lib/rtlib_coproc.o\nCOBJS-$(CONFIG_CMD_DSSINFO) += src/lib/rtlib_dssinfo.o\n\n# core command\nCOBJS-y += cmd/cmd_rtboot.o\nCOBJS-y += cmd/cmd_rtmmc.o\nCOBJS-$(CONFIG_CMD_DSSINFO) += cmd/cmd_rtdssinfo.o\nCOBJS-y += cmd/cmd_rtbootlogo.o\nCOBJS-y += cmd/cmd_rtsplit.o\n\n# core api\nCOBJS-y += src/api/rtapi_rtboot.o\nCOBJS-y += src/api/rtapi_rtmmc.o\nCOBJS-y += src/api/rtapi_board.o\nCOBJS-y += src/api/rtapi_main.o\nCOBJS-y += src/api/rtapi_bootlogo.o\n\n# core drivers\n\nCOBJS\t:= $(sort $(COBJS-y))\nXCOBJS\t:= $(sort $(XCOBJS-y))\nSRCS\t:= $(COBJS:.o=.c) $(XCOBJS:.o=.c)\nOBJS\t:= $(addprefix $(obj),$(COBJS))\nXOBJS\t:= $(addprefix $(obj),$(XCOBJS))\n\nCPPFLAGS += -I..\n\nall:\t$(LIB) $(XOBJS) \n\tmake -C $(MIPS_BOOTLOAD_LIB_DIR)\nifeq ($(MIPS_BOOTLOAD_IMAGE_ENABLE),y)\n\t\t$(LD) $(LDFLAGS) -r -o $(MIPS_BOOTLOAD_LIB_DIR)/$(MIPS_BOOTLOAD_LIB_NAME) $(MIPS_BOOTLOAD_LIB_DIR)/bootload.o\n\t\t$(OBJCOPY) --add-section .av_reset=$(MIPS_BOOTLOAD_IMAGE_PATH)/av_reset.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t$(OBJCOPY) --add-section .v_entry=$(MIPS_BOOTLOAD_IMAGE_PATH)/v_entry.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .v_entry_qc=$(MIPS_BOOTLOAD_IMAGE_PATH)/v_entry_qc.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .v_ddr_cal=$(MIPS_BOOTLOAD_IMAGE_PATH)/v_ddr_cal.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .v_ddr_cal_c=$(MIPS_BOOTLOAD_IMAGE_PATH)/v_ddr_cal_c.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .exc_redirect=$(MIPS_BOOTLOAD_IMAGE_PATH)/exc_redirect.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .exc_dispatch=$(MIPS_BOOTLOAD_IMAGE_PATH)/exc_dispatch.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .isrvideoimg=$(MIPS_BOOTLOAD_IMAGE_PATH)/isr_video.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .rosbootvectorimg=$(MIPS_BOOTLOAD_IMAGE_PATH)/ros_bootvector.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .a_entry=$(MIPS_BOOTLOAD_IMAGE_PATH)/a_entry.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .a_entry_qc=$(MIPS_BOOTLOAD_IMAGE_PATH)/a_entry_qc.img $(MIPS_BOOTLOAD_LIB_PATH)\n\t\t$(OBJCOPY) --add-section .a_entry_polling_0xa000000e=$(MIPS_BOOTLOAD_IMAGE_PATH)/a_entry_polling_0xa000000e.img $(MIPS_BOOTLOAD_LIB_PATH)'
### includedcustomerlibraryrules
`source-catalog/inspection-core-two-PENDING-REVIEW/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/customer/Makefile`,2777B,SHA256`fccd04fb2b913416f6cef0a079f3cdc4bebee1c09986ecaadf7e4091e3786305`
- Lines26–64: 'LIB\t= $(obj)lib_customer.o\n\n# customer command\nCOBJS-y += cmd/cmd_lg/cmd_partinfo.o\nCOBJS-y += cmd/cmd_lg/cmd_misc.o\nCOBJS-y += cmd/cmd_lg/cmd_cp2ram.o\nCOBJS-y += cmd/cmd_lg/cmd_polltimer.o\nCOBJS-y += cmd/cmd_lg/cmd_setboot.o\nCOBJS-y += cmd/cmd_lg/cmd_unlz4.o\nCOBJS-y += cmd/cmd_lg/cmd_swu.o\nCOBJS-$(CONFIG_RTK_WOV_ENABLE) += cmd/cmd_lg/cmd_wov.o\nCOBJS-y += cmd/cmd_lg/cmd_swum.o\nCOBJS-y += cmd/cmd_lg/cmd_nvm.o\nCOBJS-y += cmd/cmd_lg/cmd_micom.o\nCOBJS-y += cmd/cmd_lg/cmd_emmc.o\n\nCOBJS-y += src/lz4.o\nCOBJS-$(CONFIG_SYS_SUPPORT_MULTICORE) += src/smp.o\nCOBJS-$(CONFIG_SYS_SUPPORT_MULTICORE) += src/sched.o\nCOBJS-$(CONFIG_SYS_SUPPORT_MULTICORE) += src/sync.o\nCOBJS-y += src/CusSystem.o\nCOBJS-y += src/CusCmnio.o\nCOBJS-y += src/CusDevice.o\nCOBJS-y += src/CusUpgradeUI.o\nCOBJS-y += src/lg_bootdb.o\n\nCOBJS-y += cmd/cmd_lg/cmd_cacheinfo.o\nCOBJS-y += cmd/cmd_lg/cmd_minfo.o\nCOBJS-y += cmd/cmd_lg/cmd_mmu.o\nCOBJS-y += cmd/cmd_lg/cmd_verify.o\nCOBJS-y += cmd/cmd_lg/cmd_gpio.o\nCOBJS-y += cmd/cmd_lg/cmd_setlayout.o\nCOBJS-y += cmd/cmd_lg/cmd_loglevel.o\nCOBJS-y += cmd/cmd_lg/cmd_rtdlog.o\nCOBJS-y += cmd/cmd_lg/cmd_resume.o\nCOBJS-y += cmd/cmd_lg/cmd_snaplog.o\nCOBJS-$(CONFIG_SYS_SUPPORT_MULTICORE) += cmd/cmd_lg/cmd_thread.o\nCOBJS-y += cmd/cmd_lg/cmd_splash.o\nCOBJS-y += cmd/cmd_lg/cmd_standalone.o'
### buildtimesymlinkgeneratorreadnotrun
`source-catalog/inspection-build-closure-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/genlink_realtek.sh`,1108B,SHA256`ac1a0c1d00229dc66477447e58e67eff5bcb4fb35391e4496810b4d6d1efe22d`
- Lines1–32: '#!/bin/sh\n\n# force remove symbolic link\nrm -f ./uboot/board/realtek\nrm -f ./uboot/arch/arm/cpu/armv7/realtek\nrm -f ./uboot/arch/arm/include/asm/arch-realtek\nrm -f ./uboot/lib/rtk\nrm -rf ./uboot/include/rtk\nrm -f ./uboot/common/rtk\nrm -f ./uboot/drivers/rtk\n\nmkdir ./uboot/include/rtk\n# add symbolic link for bsp\necho "Generate link for board   ... realtek"\nln -fs ../../bsp/board/realtek/ ./uboot/board/realtek\n\necho "Generate link for arch    ... realtek"\nln -fs ../../../../../bsp/arch/realtek/ ./uboot/arch/arm/cpu/armv7/realtek\nln -fs ../../../../../bsp/arch/include/arch-realtek/ ./uboot/arch/arm/include/asm/arch-realtek\n\necho "Generate link for lib     ... rtk"\nln -fs ../../bsp/core/src/lib/ ./uboot/lib/rtk\nls bsp/core/include/* | xargs -I FILES ln -sf ../../../FILES ./uboot/include/rtk/\n\necho "Generate link for common  ... rtk"\nln -fs ../../bsp/core/cmd ./uboot/common/rtk\n\necho "Generate link for drivers  ... rtk"\nln -fs ../../bsp/core/src/drivers ./uboot/drivers/rtk\n\necho "Generate link for customer  ... rtk"\nls customer/include/* | xargs -I FILES ln -sf ../../../FILES ./uboot/include/rtk/'
### configconverterreadnotrun
`source-catalog/inspection-build-closure-2026-11-08/selected/bootcode-1.0.0-1099.7.tar.gz/bootcode/tools/script/configconv.pl`,6387B,SHA256`edce14ba3b91ea47d2ba8f61e9f459ea72ca0e0da38314a4ad32356303aa8dac`
- Lines36–61: '($ARGV[1] =~ /.*inc\\b/) || die "error!! input file is not a config file\\n";\n($ARGV[0] =~ /.*h\\b/) || die "error!! output file is not a header file\\n";\n\n#open include config file and output \n\nprint "Config convert to header file \\n\\n";\n\n\nopen (CONFIG_FILE1, "$ARGV[1]");\nprint "Input Config File     : "  . substr( $ARGV[1], rindex($ARGV[1], "/") + 1) . "\\n";\n\nif(defined $ARGV[2])\n{\n\topen (CONFIG_FILE10, "$ARGV[2]");\n\tprint "Input RSA Info File : "  . substr( $ARGV[2], rindex($ARGV[2], "/") + 1) . "\\n";\n}\n\nif(defined $ARGV[3])\n{\n\topen (CONFIG_FILE11, "$ARGV[3]");\n\tprint "Input RSA R2 Info File : "  . substr( $ARGV[3], rindex($ARGV[3], "/") + 1) . "\\n";\n}\n\nopen (HEADER_FILE, ">$ARGV[0]");\nprint "Output Header File    : "  . substr( $ARGV[0], rindex($ARGV[0], "/") + 1) . "\\n";\n'
- Lines76–130: '\t\tprint HEADER_FILE;\n\t}\n\n\t# Board, Config and USB_OTG setup segment\n\tif ((/^Board/) || (/^Config/)|| (/^USB_OTG/))\n\t{\n\t\tif (/^Board_DRAM_Block/)\n\t\t{\n\t\t\t($tmp1, $tmp2, $dram_block) = split(/ +/);\n\t\t\tchomp($dram_block);\n\t\t}\n\t\t\n\t\tif (/^Board_DRAM_Number/)\n\t\t{\n\t\t\t($tmp1, $tmp2, $dram_number) = split(/ +/);\n\t\t\tchomp($dram_number);\n\t\t}\n\t\t\n\t\tif (/^Config_HDMI/)\n\t\t{\n\t\t\ts/ *= */\t\t\t/; # replace with three TAB space\n\t\t}\n\n\t\tif (/^Config_Secure_Uart/)\n\t\t{\n\t\t\ts/ *= */\t\t\t/; # replace with three TAB space\n\t\t}\n\n\t\tif (/\\./)\n\t\t{\n\t\t\ts/\\./___/;\t# replace "." with "___"\n\t\t}\n\t\t\n\t\tif ((/Size/) || (/Number/) || (/Block/) || (/Value/) || (/_File/i) || (/Offset/i))\n\t\t{\n\t\t\ts/ *= */\t\t\t/; # replace with three TAB space\n\t\t}\n\t\telse\n\t\t{\n\t\t\ts/ *= */_/;\n\t\t}\n\n\t\tprint HEADER_FILE "#define " . $_;\n\n\n\t\tif (($dram_number != 0) && ($dram_block != 0))\n\t\t{\n\t\t\t$dram_size = $dram_block * $dram_number;\t\t\t\n\t\t\tprint HEADER_FILE "#define Board_DRAM_Size\t\t\t\t$dram_size\\n";\n\t\t\t\n\t\t\t$dram_number = ($dram_block = 0);\n\t\t}\n\t\t\n\t\tif (/Config_OTP_Secure_Boot_TRUE/)\n\t\t{'

## Directory evidence (complete bootcode index)
|Path|Indexed members|Regularfiles|
|---|---:|---:|
|bootcode/bin/hw_setting/realtek|0|0|
|bootcode/tools/flash_image_maker|0|0|
|bootcode/Aux_code|0|0|
|bootcode/Aux_code_2nd|0|0|
|bootcode/bsp/core/image|32|29|
|bootcode/bsp/core/image/src/app|3|2|
|bootcode/include/rbus|369|367|

13coreimage.imgfilenames+sizes are in JSON as metadata only;no binarycontentsread. Model suggestions that rbus/coreblobs were missing were checked:theyarepresent. Missingdirectories listedabove are literalpackageabsence,not proprietary/globalabsence assertions.

## Public SDK lead
{
  "catalogue": "https://github.com/lgstreamer/starfish-sdk-x86_64/releases/tag/04.40.20",
  "readme": "https://github.com/lgstreamer/starfish-sdk-x86_64/blob/main/README.md",
  "official_app_sdk": "https://webostv.developer.lge.com/develop/tools/sdk-introduction",
  "community_claim": "authorreportslegalLGinquiry+MR_firmware.zip+webOS5.0JO2.0/OLEDCX04.40.20;notindependentlyauthenticatedLGorigin",
  "listed_sdk": "5.0.0-20191125",
  "required_by_guides": "5.0.0-20190307",
  "interchangeable": "NOT ESTABLISHED",
  "assets": [
    {
      "name": "native_sysroot_dependencies.tar.gz",
      "size": 8017931,
      "digest": null,
      "browser_download_url": "https://github.com/lgstreamer/starfish-sdk-x86_64/releases/download/04.40.20/native_sysroot_dependencies.tar.gz",
      "state": "uploaded"
    },
    {
      "name": "starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh",
      "size": 166821312,
      "digest": null,
      "browser_download_url": "https://github.com/lgstreamer/starfish-sdk-x86_64/releases/download/04.40.20/starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh",
      "state": "uploaded"
    },
    {
      "name": "target_sysroot_dependencies.tar.gz",
      "size": 323786694,
      "digest": null,
      "browser_download_url": "https://github.com/lgstreamer/starfish-sdk-x86_64/releases/download/04.40.20/target_sysroot_dependencies.tar.gz",
      "state": "uploaded"
    }
  ],
  "assets_downloaded": false,
  "new_download_bytes": 0,
  "repo_root": "README.md only;noSDKmanifest/compilerfilesatroot",
  "bounded_search": "2webqueries+1Xquery,X0results;4documentreads;noexactMarchSDKfound\u2014notglobalabsence",
  "official_page_fact": "LGSDKIntroductiondescribesappdevelopmentCLI/Studio/Simulator/Beanviser,notfirmwarecrosscompiler"
}

## Subscription-led analysis / corrections
MainOpus5.5high128.446s reported5.5AND4.8,safety_stops2;Solactualgpt-6.1-sol/high57.068s;requestedGeminiArgonhigh64.086s (actualmodelnotseparatelyreported);newclosureOpus5.5high64.639s reportedONLY5.5,safety_stops0. All exit0,no timeout/refusal,nooperatorfallback. Primaryheavyanalysisdelegated;findingscheckedagainstexactselectedtext/index.
Rejected:activeB7/deploymentclaim (onlyheaderalignment);DDRnames→actualgeometry;PENDING-REVIEWpathname→pendingreview (historicalname);missinglibs/outputnames→missingproprietarysource;unknownrbus/blobs→absent (present);communitySDK→LG-authoritative/exactcompatible;ABI-identicalSDKasanabsoluteprerequisite (compatiblealternativecouldbevalidated,butnoneisvalidatednow). No signing/key/bypass stepsfollowed. Fullprompts/rawoutcomes:`plan-reviews/2026-11-08-project-sdk/`.

## Next concrete off-TV engineering actions
1. PreserveSDKpubliclead,thenacquire/inspectcompiler/sysrootmanifestasDATAonlyunderappropriateboundedreader;noSDKinstallerexecution. No pointpretendinglaterSDKisexactMarchversion.
2. Sourcehardwareadaptationcoveragecanadvancebyboundedinspectionofalready-indexedlibkadaptorpackage(123840909B,SHA46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25). CurrentbinarycopytoolisclosedCORETWOallowlist;doNOThackit. Parentcancoordinatea reviewed/testedproductiontooladditionunderongoingresearchscope without ownerper-filecheck-in. Noextra packagecopiedhere.
3. Identifylawfulpublicsource/supplyfortheconcretemissingpackaging/aux/hw-settingcomponents,thenbuildclosure—notmerecompiledkernel—canbereassessed.
4. Unitidentityandlegitimateboot/recoveryremainseparategates;parenthandlesanyTVactionwithadvanceviewing-impactnotice. Noarchitecturechosen orbootabilityclaimed.
