# LG 65NANO756PR remote via AC-009 (machine a60120fb-0764-4ced-812e-6326f8b62577)
Canonical notes + menu map live on AC-009: %LOCALAPPDATA%\LGTVRemote\README.md
- Helper: lgtv.ps1 (saved key client-key-remote.txt; LGKEYS, LGREAD=1, LGPAIR=1 only for deliberate pairing)
- Allowed: buttons, read backlight/contrast/brightness/color/energySaving, foreground app. Denied: picture writes, screenshots, launch.
- Menu path: MENU > All Settings > Picture > (RIGHT,DOWN,DOWN,ENTER) Advanced Settings > Brightness > Panel Brightness/Adjust Contrast/Screen Brightness/Auto Dynamic Contrast/Gamma/Black Level
- 02:39: ENTER,LEFT on Panel Brightness gave no readback change (100). Unverified.
- 02:45: Claude Opus 5.5 review in /workspace/lg-tv/claude-review.md. Framing/ENTER correct. FG can't see menus (always hdmi2). Trim/whitelist fix applied. Next test: LEFT alone on Panel Brightness with LGREAD=1.
- 02:45: sent MENU via saved key; awaiting photo.
- 02:59: sent MENU again via saved key; awaiting confirmation.
- 03:01 CORRECTION: no TV ack exists for buttons; no automated button effect proven. Framing correct. Sent pointer-move test (8 moves, no click); awaiting user observation.
- 03:03:30 repeated pointer-move test (8 right, no click/buttons); awaiting user.
- 03:04 CONFIRMED pointer moves reach TV (user). MENU(139) vs QMENU(793) distinct; gear likely QMENU on webOS6 (hypothesis). QMENU whitelisted. Next test: one QMENU.
- 03:09:35 sent QMENU once via saved key; sliders 100/80/50/50; awaiting user.
- QMENU user-verified (03:09:35 opened sidebar). 03:10:48 sent ENTER once; awaiting user.
- user-verified path QMENU,ENTER -> full Settings (Picture). 03:12:00 sent RIGHT,DOWN,DOWN,ENTER; awaiting Advanced Settings confirmation.
- 03:12:19 sent DOWN,DOWN,ENTER (expect Clarity); awaiting photo.
- user-verified: Picture > RIGHT,DOWN,DOWN,ENTER -> Advanced Settings. Clarity sequence sent 03:12:19 once.
- user-verified Clarity screen (Sharpness 10, SuperRes Off, NR Off, MPEG NR Off, Smooth Grad Off, Cinema Screen On). 03:12:51 single LEFT on Sharpness; no API readback for sharpness.
- user-verified: LEFT on row -> back to sidebar (no adjust). 03:14:06 sent RIGHT,ENTER to open Sharpness slider; awaiting photo.
- user-verified RIGHT,ENTER opens Sharpness slider (vertical, DOWN decreases). 03:14:56 sent 10x DOWN (target 0).
- USER CONFIRMED Sharpness 10->0. 03:15:41 sent BACK + 6x DOWN toward TruMotion; awaiting photo.
- USER CONFIRMED Clarity complete (Sharp 0, SuperRes/NR/MPEG NR/SmoothGrad Off, Cinema Screen On, TruMotion Off). 03:17:42 sent BACK,UP,ENTER toward Colour; awaiting photo.

## MENU MAP (03:19) - canonical copy in AC-009 README.md
QMENU (sidebar, All Settings) > ENTER (Picture) > RIGHT,DOWN,DOWN,ENTER (Advanced: Brightness/Colour/Clarity/...) 
Advanced: ENTER=Brightness; DOWN,ENTER=Colour; DOWN,DOWN,ENTER=Clarity.
Clarity rows: Sharpness, SuperRes, NR, MPEG NR, SmoothGrad, CinemaScreen, TruMotion. Colour rows: Depth, Tint, Gamut, FineTune, WhiteBalance.
Semantics: ENTER opens slider; DOWN -1; BACK up a level; LEFT on row -> category column (no value change).
Confirmed: Sharp 0 (changed), SuperRes/NR/MPEG/SmoothGrad Off, CinemaScreen On, TruMotion Off, Depth 50, Tint 0, Gamut Auto Detect.
03:19:02 sent DOWN x4,ENTER -> White Balance (awaiting photo).
- USER CONFIRMED White Balance: Warm 50, 2 Points, High, R0 G0 B0 (leave). 03:19:38 sent BACK,BACK,UP,ENTER toward Brightness; sliders 100/80/50/50.
- 03:21 Panel Brightness 100->40 verified by API readback (ENTER,DOWN=99; batches 30+29). BACK closes slider.
- White Balance route: Colour > DOWN x4,ENTER; return BACK,BACK,UP,ENTER -> Brightness page. WB Warm50/2pt/R0G0B0 untouched.
- FINAL SDR Filmmaker HDMI2: BL40 C80 B50 Col50, DynContrast Off, Gamma BT.1886, Black Auto, Sharp0, SuperRes/NR/MPEG/SmoothGrad Off, CinemaScreen On, TruMotion Off, Depth50 Tint0 Gamut Auto. HDR untouched.


## Official guide added 2026-11-08
Exact-model support: https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/
Official English PDF: /workspace/lg-tv/official-guide-extracted/w6.0_mr10_e10_eng.pdf
Full source-checked Picture tree and limitations: /workspace/lg-tv/gemini-menu-research.md
This is the webOS6 family guide linked from model65NANO756PR.AEK; regional suffix of owner's unit unknown. Conditional OLED/DolbyVision/local-dimming features do not establish support on this NanoCell. Quick Settings can be reordered: QMENU,ENTER is confirmed for current layout, not a universal focus reset. Numeric controls and live focus need observed confirmation. Gemini high-tier subscription attempt timed out with no generated answer; official-manual research succeeded independently.
User photo additionally confirms PanelBrightness40; sharpness0 already confirmed. SDR only; HDR untouched.
- 03:37 device facts in /workspace/lg-tv/device-facts.md (model 65NANO756PR, DVB; firmware version 401-unavailable).
- 03:42:56 sent EXIT,QMENU,ENTER,LEFT,UPx4,DOWNx3 aiming Support category (unverified).
- 03:43 prior Support route landed on General (non-deterministic, don't reuse). 03:43:44 sent DOWN -> Support (awaiting photo).
