# Adaptation inspection (libkadaptor) — admitted evidence only

Timezone: Atlantic/Reykjavik (UTC+0). This is not a successful complete phase. The isolated tool exited 1 with `phase.json` `ok=false`, `status=partial`, error `max_selected_combined_bytes exceeded`. No ceiling was raised and the command was not retried.

Copied pin (required checks held even though the phase is partial): `soc/libkadaptor-1.0.0-908.3.tar.gz` → `staged/libkadaptor-1.0.0-908.3.tar.gz`, 123840909 bytes, SHA256 `46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25`, `verified_before_inner=true`. An independent SHA-256 of that staged regular file matched; the staged tarball was not parsed again.

Inner metadata lists 1434 members (77 dirs, 1357 files). 796 files were selected (65,599,808 bytes), 391 of them under `.../rbus/`. The last listed member is `libkadaptor/system/optee/optee_os_64bits/optee_os_prebuilt/arm-plat-rtk/export-ta_arm64/include/rbus/rtk_dtv_demod_isdbt_reg.h` (1,717,085 bytes, not selected). The phase aborted while charging that file against the 64 MiB combined-text cap, so any later archive members were not recorded. Arm32 `include/rbus` lists 302 files vs 90 under arm64 `include/rbus`; that asymmetry is consistent with a mid-directory stop and is not proof of how many files remain unread. “Absent” below means absent from the admitted listing, not proven absent from the unread tail.

Selected evidence is almost entirely generated OP-TEE/rbus headers plus `libkadaptor/Makefile`. Presence of an adapter or register name is not proof of complete functional drivers or of TV model 65NANO756PR.

## License / confidentiality

No member name contains LICENSE, README, COPYING, or NOTICE.

`libkadaptor/Makefile` (3100 B, SHA256 `53802315af59e91b864830acef88d69145c7f6f025aa4d5b9232f2aedfadfdf2`, selected output `selected/libkadaptor-1.0.0-908.3.tar.gz/libkadaptor/Makefile`) has no license block in lines 1–85.

`libkadaptor/system/optee/export/export-ta_arm32/include/drivers/hdcp2/hdcp2_hal.h` (2897 B, SHA256 `fe44680a829a232db581b6e491a68fdc6a15413cf5ea7cd7cada413c8d67c310`):

- lines 4–5: `INTEL CONFIDENTIAL` / `Copyright 2010-2011 Intel Corporation All Rights Reserved.`
- line 18: `No license under any patent, copyright, trade secret or other intellectual`
- lines 27–28: `#define NEWBASE_FUNC` and `#define TEST_HDCP2_2_RX_DRIVER`
- lines 47–50: named AES key macros are present; values are not reproduced here
- lines 71–74: `extern` HDCP 2.2 prototypes `lib_hdmi_hdcp22_init`, `newbase_msg_hander`, `newbase_hdmi_hdcp22_write_data_to_tx`, `lib_ks_setting`

`.../drivers/hdcp2/hdmi.h` (361 B, SHA256 `6fdab9b6f8e6c370cbced2a057a1c565e4583b87493f62c9d9250293509db51a`) lines 7 and 10–13: author `Brad Bitterman <bitter@vtilt.com>`; prototypes `hdmi_init`, `hdmi_CheckHdcp1x`, `hdmi_policeEnable`, `hdmi_task`. No license text.

Rbus banners cite `RS_MM2_SD` / `mm_mm2_rd_sw_kernel@realtek.com` and no SPDX/license block. `HDCPTX22_TestKey.h` was selected in arm32 and arm64 trees; it was not opened for quotation.

## Source completeness and binaries

Makefile references that are **not** in the listed members:

- line 1 `SRC_DIR=./system/src`
- line 2 `CONFIG_FILE =./system/include/MakeConfig`
- line 5 `KADP_AUDIO_DIR=./src/audio` and line 26 `cd ./src/audio/; sh build_binary.sh`
- lines 76/82 `ta_64bits_v3` / `ta_32bits_v3` (only `ta_32bits/` and `ta_64bits/` prebuilt `.ta` files are listed)

Listed but not selected: `libkadaptor/kadaptor.mk` (2474 B), `libkadaptor/common.setting` (6000 B), `libkadaptor/files/pkgconfig/kadaptor.pc` (305 B, SHA256 `7a4c6c236f797313bdf1d1df066d8d31d6af6b94b14ccaf5997b738b3941ebd7` from phase metadata). Makefile line 25 copies `./output/*.so*` to `../hal/output/` (HAL output lives outside this package).

Only `.c`/`.s` names listed are OP-TEE TA boilerplate `user_ta_header.c` and `ta.ld.S` (not selected). Metadata lists 25 `.a`, 12 `.so`, 13 `.ta`, 8 `.pem`, plus `tee-supplicant` binaries. Prebuilt DRM/TEE libraries named in `system/optee/output_v3/lib/` include oemcrypto, oemsvp, playreadypk30/40, fairplay, nrd416/503/510/520, skb, jpmarlin (`.so` and `_static.a`, not selected). Also `system/third_party/Sockeye/libSkbStatic.a` (962596 B). `.pem` TA signing keys were not opened.

## Target identifiers

Makefile lines 7 and 9–15: default `all` is `ADD_OPTIMIZE_OPTION_OFF optee_V3_4k package_optee`; options for OPTEE V2/V3 and 2K/4K platforms. Lines 66, 72, 78, 84 package `optee-k6lp_64bit.tar.bz2`, `optee-k6lp_32bit.tar.bz2`, `optee-V3-k6lp_64bit.tar.bz2`, `optee-V3-k6lp_32bit.tar.bz2`.

`hdcp2_interface.h` (14580 B, SHA256 `51393f74475fc30a18c418b1acc418e41672e66644c73c88c471643738f8e1b5`) lines 63–64: `#if defined(NEWBASE_FUNC)` / `#define HDMI_MAX_PORT_NUM 4`.

Rbus file banners (line 2), hashes verified against both the selected file bytes and `phase.json` member SHA-256:

| Banner (line 2) | Path under `.../export-ta_arm32/include/rbus/` | SHA256 |
|---|---|---|
| Merlin3-DesignSpec-P0_HDMI_RX_MAC | hdmi_p0_reg.h (618533 B) | `9fb8d5bbc78fad7b0550b1702168ec4bc8d3da9b38f97778ad2c90762f0ceb3e` |
| Merlin3-DesignSpec-DFE_HDMI_RX_PHY | dfe_hdmi_rx_phy_reg.h (429474 B) | `3f18c9629bf22c0ff2753f59385fb05e00622b7775d6f2fa8b23a24e937d6983` |
| Merlin3-DesignSpec-AUDIO | audio_reg.h (1102068 B) | `5ed69ee98fef184ec0a50c6370ae9b57600c3f7847cdf591edb78e3e459b7633` |
| Merlin3-DesignSpec-CEC | cec_reg.h (130425 B) | `2e7e57a9c6a54e32d7d806cb2169c25a801d0d27e93d3b71994bb7b69628f1e8` |
| Merlin3-DesignSpec-ISO_MISC_IRDA | irda_reg.h | `babcac77d846cc82da1433812bfbcbf9d7358e1523eaccbf3a3388588af168ba` |
| Merlin3-DesignSpec-D_Domain_TCON | tcon_reg.h | `6a54f41b31fa6854d6823649dc9cd22e68f25de2ef9a5c772861ba9f092574f1` |
| Merlin3-DesignSpec-Display_Timing_Generator | ppoverlay_reg.h | `6c5f65ddc635c5d292cc885c4756ba1da3b0364f8083c5ea2917c5ef4d84043c` |
| Merlin3_DesignSpec_Vby1 | vby1_reg.h | `24a33629f7d21ad021efc0a93682f609392b4c9b9f01c50152a20112172d9b60` |
| Merlin3-DesignSpec-EMCU | emcu_reg.h | `615c747486f9c5dd2540c16a6ff588cb9bd3d874f8fdb92c22aef45343960e9c` |
| Merlin3-DesignSpec-ISO_MISC_arch_spec | iso_misc_reg.h | `3d79cdd2a6a0990e2f9aaa27f1f373d698f6db0a7bea46c0cf02010ab40164ac` |
| Merlin3-DesignSpec-D-Domain_LGD_M_plus | lg_m_plus_reg.h | `b217af7b247738c3d3e5aa957312e61e35fea82e9e7e3349916ee1c9629a2cd8` |
| Merlin3-DesignSpec-CRT | sys_reg_reg.h | `57e1e4067946c903293b8f2d8c79017df42538d0a38d2e72eca2ac986641389f` |

k6lp / Merlin3 / HDMI_MAX_PORT_NUM=4 are SoC/package identifiers in this tree, not a demonstration that this dump is a complete board support package for a specific LG TV SKU.

## Domain notes (API vs register map)

- HDMI RX: HDCP-in-TEE prototypes (`hdmi.h`, `hdcp2_hal.h` 71–74, `hdcp2_rcp_api.h` 10–20 `RCP_HDCP2_*`). Register maps `hdmi_p0`–`p3_reg.h`, `dfe_hdmi_rx_phy_reg.h` (P0–P3 LDO select fields at lines 41–45 of the selected arm32 header), DDC `iso_misc_ddc0`–`4`. No HDMI RX driver `.c` listed.
- Display/panel: register maps `tcon_reg.h`, `ppoverlay_reg.h`, `vby1_reg.h`, `pinmux_lvdsphy_reg.h`, `lg_m_plus_reg.h`, `lg_hcic_reg.h`, `color_*`. No panel timing/driver source listed.
- Audio: `audio_reg.h` line 20 `AUDIO_global_ctrl_0` at `0x18006000`, including ARC-related field names (`div_arcdma_r_512fs`, `play_r_adc_512fs_sel_arc`). Makefile’s `./src/audio` tree is not listed.
- Power/standby: no power/PMU API headers by name. Register maps include `emcu_reg.h`, `sys_reg_reg.h` (CRT), `iso_misc_off_reg.h`, `stb_reg.h`, `wdog_reg.h`, PWM maps. Purpose of PWM maps is not established from names alone.
- Remote: `irda_reg.h` line 20 `IRDA_IR_PSR` at `0x18061400`; also `misc_off_irda_reg.h`, `cec_reg.h` (`CEC_CEC_CR0` at `0x18061E00`). No keymap or IR protocol implementation listed.
- Thermal: no member name contains `thermal`. `color_temp_reg.h` is display white-balance, not a thermal sensor API.

## Analysis worker

Subscribed Claude CLI, requested `--model claude-opus-5-5 --effort high`. JSON result `canonicalModel=claude-opus-5-5`, session `7cae6b7b-d602-4243-927b-9f8cdc756598`, 152560 ms, `is_error=false`. Seven Bash tool calls were permission-denied; quotes above were independently re-read from selected files and matched `phase.json` SHA-256 values. No original catalog archive was opened for analysis.
