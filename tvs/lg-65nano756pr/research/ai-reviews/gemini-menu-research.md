# Exact-model LG menu research
2026-11-08 Atlantic/Reykjavik. No TV commands, user-machine access, shared NOTES/helper edits or security changes.

## Primary-source breakthrough
Exact model regional support page https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/ links this online manual:
http://kr.eguide.lgappstv.com/manual/w21_mr10/userguide_w6.0_mr10_e10.html
and downloadable archive:
https://gscs-b2c.lge.com/downloadFile?fileId=xTNMAXUHlxmsjAmsx9LVw
Downloaded archive successfully. It contains English AND Icelandic PDFs, among other languages. English original is /workspace/lg-tv/tvs/lg-65nano756pr/sources/official-guide-extracted/w6.0_mr10_e10_eng.pdf; searchable text /workspace/lg-tv/tvs/lg-65nano756pr/sources/official-guide-eng.txt. Icelandic: w6.0_mr10_e10_ice.pdf. This is an official manual explicitly linked from exact 65NANO756PR.AEK support, NOT merely a similar-model search result. It is still a family guide: explicitly says options differ by model/input/mode. Its OLED/Dolby Vision/local dimming entries do not establish those features on this NanoCell. Regional suffix AEK may differ from owner's exact suffix, which is unknown. Support page lists manual revision 14/10/2026; actual TV firmware/menu can differ.
HTTPS online guide fetch failed500; curl identified hostname/certificate mismatch. Did NOT disable TLS checking. Original LG-linked HTTP page fetched via WebFetch. Official HTTPS archive worked and is the substantive source.

## Official physical remote operations (PDF pp13,65)
Visually checked PDF p13 icons in /workspace/lg-tv/tvs/lg-65nano756pr/sources/web-snapshots/manual-remote-page.png:
- Short press gear = Quick Settings.
- Hold gear >1 second = All Settings directly.
- BACK = previous step; hold BACK = closes menu.
- Wheel(OK) selects pointed item.
- Quick Settings entries can be added/deleted/reordered (p65). Therefore blind QMENU,ENTER depends on current focus/configuration, not universal All Settings location.
These physical long-press facts do NOT establish that repeating SSAP button messages emulates a hold. No documented SSAP duration/key-down/key-up mechanism verified; do not invent one. No documented operation guarantees focus resets to first Picture row. Closing/reopening menus is not a guaranteed focus reset. Docs cannot reveal live focus.

## Complete documented Picture tree (family guide pp66–76)
All Settings > Picture
  Select Mode
    SDR family: Vivid, Standard, Basic, APS, Cinema, Sports/Football/Cricket,
      Game Optimiser, FILMMAKER MODE, Expert(Bright space,daytime), Expert(Dark space,night)
    HDR family: Vivid, Standard, Cinema Home, Cinema, Game Optimiser, FILMMAKER MODE
    Availability conditional; guide mentions Dolby Vision for other models, not a claim for this TV.
  Aspect Ratio
    User Selection:16:9,Original,Full Wide,4:3,Vertical Zoom,4-Way Zoom
      Zoom controls:Adjust Zoom Ratio,Adjust Screen Position
    Just Scan:On/Off/Auto
  Advanced Settings
    Brightness
      Panel Brightness [LCD backlight,0..100]
      OLED Pixel Brightness [OLED only: EXCLUDE this NanoCell]
      Adjust Contrast
      Screen Brightness
      Auto Dynamic Contrast
      HDR Tone Mapping [HDR/model conditional]
      Peak Brightness [model conditional]
      Gamma(Adjust Brightness) [includes BT.1886]
      Black Level:Auto/Limited/Full [external input]
      LED Local Dimming [model conditional; not proved supported]:Off/Low/Medium/High
      Motion Eye Care
    Colour
      Colour Depth [toward100=deeper]
      Tint [Red50..Green50]
      Colour Gamut:Auto Detect/Native
      Fine Tune
        Colour Upgrade
        Select Colour:Red/Green/Blue/Cyan/Magenta/Yellow
        Adjust Saturation / Adjust Tint / Adjust Luminance [-30..30]
      White Balance
        Colour Temperature [cooler/warmer]
        Method:2 Points / 10 Points Signal Level(%) / 22 Points Signal Level(%)
        Point:Low/High for2 Points; level selection otherwise
        Signal Level(%) [10/22 point modes]
        Show brightness level at the maximum signal level(%)
        Adjust brightness level at the selected signal level(%)
          [multi-point modes + Cinema/Expert restriction]
        Red / Green / Blue [-50..50,for selected Point]
    Clarity
      Adjust Sharpness [toward50=sharper]
      Super Resolution
      Noise Reduction
      MPEG Noise Reduction
      Smooth Gradation
      Cinema Screen
      TruMotion:Off/Cinematic Movement/Natural/Smooth Movement/User Selection
        User Selection:De-Judder / De-Blur /
          OLED Motion / OLED Motion Pro / Motion Pro / NanoCell Motion Pro
          [conditional family list, NOT promise NANO75 supports all]
    Apply to all inputs [deliberately copies settings beyond current input; do not invoke casually]
    Reset [resets each image mode, NOT a focus reset; do not invoke]
    FILMMAKER MODE Auto Start
    Reduce Blue light [model conditional]

## Important manual evidence
Panel Brightness may lock when Energy Saving Auto/Maximum. LCD route: Support > Energy Saving > Energy Saving Step > Off or Minimum (p70). This is a diagnosis/path, NOT a request to change power settings now.
Available settings differ by selected mode/input/model. Select Mode can alter Energy Saving and Motion Eye Care. Current picture settings normally apply only to selected input (p75). Thus cache values/routes with input/mode/HDR context, not universal TV state.

## Photo-confirmed vs documentation vs unknown
Photo-confirmed per current NOTES (read-only): QMENU then ENTER opened full Picture settings; RIGHT,DOWN,DOWN,ENTER entered Advanced; Brightness/Colour/Clarity categories. Clarity seven-row order exactly matches guide. Colour Depth,Tint,Gamut,FineTune,WhiteBalance order matches. White Balance Warm50,2Points,High,RGB0 confirmed. Sharpness10->0 and other Clarity values confirmed.
Actual key semantics are USER-OBSERVED, not specified by manual: LEFT on selected row returns to category column; ENTER opens vertical slider; DOWN decreases. Do not assume LEFT decrements or every numeric slider uses identical orientation.
Manual confirms hierarchy/labels/purpose and physical remote opening operations. It does NOT establish current selected row, exact index when conditional entries hide, or navigation timing. No screenshot/private API attempts made.

## Gemini subscription consultation
agy models succeeded and listed gemini-4-argon-high. Sequential bounded command: timeout160 agy -p <sanitized exact-model read-only research prompt> --model gemini-4-argon-high. No lower-tier fallback. Output /workspace/lg-tv/tvs/lg-65nano756pr/research/ai-reviews/gemini-menu-output.txt. Actual result appended below.

### Actual Gemini outcome
Model-list retrieval authenticated sufficiently to list available models; research inference did NOT complete. Exact high-tier command timed out after160 seconds, exit124, with empty output. No auth error reported, but no generated answer either. Therefore no Gemini conclusions to verify and no claim Gemini found the manual. Independent official LG manual research above succeeded during that bounded attempt. Do not retry through another tier or CLI as a workaround.
