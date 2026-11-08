# LG paired control research
2026-11-08 Atlantic/Reykjavik. Read-only consultation; no machine/TV commands or shared helper/NOTES edits.

## Verified against public source
- aiopylgtv button(): type:button\nname:NAME\n\n; move(): type:move\ndx:X\ndy:Y\ndown:0\n\n. BOTH end with two LF bytes. lgtv2 SpecializedSocket independently appends two LF to every command. Do not change terminators based on pointer/button differences.
- Button send has no correlated acknowledgment in either implementation; successful send is not successful UI action. ENTER is aiopylgtv ok_button(), while click is a separate pointer-location event.
- aiopylgtv subscribe_picture_settings() uses SSAP envelope type:subscribe, URI ssap://settings/getSystemSettings, payload {category:"picture",keys:["contrast","backlight","brightness","color"]}. Its SSAP payload does NOT add subscribe:true. Keep a receiver routing by id after initial response. Merge partial setting updates into cached state, do not replace the whole cache with a changed-key event. Subscription not yet tested on this TV; existing successful reads support trying the same allowed keys.
- Official LG Settings Service documents payload subscribe:true, initial whole-key response and later changed-key events, BUT this is the ON-DEVICE luna://com.webos.settingsservice API, not the external SSAP contract. Public documented keys are locale/country/audioGuidance/captions; not arbitrary picture keys. Do not treat official Luna docs as proof of permission for arbitrary SSAP settings.
- No reliable generic screen/menu/focus observation method found through ordinary paired public API. Foreground-app/input/power/audio subscriptions do not reveal focused menu rows; local evidence hdmi2 while menus visible disproves foreground app as a reliable menu detector. Picture reads verify specific numeric effects only. Screenshot401 is a boundary, not a reason to try internal routes.

## QMENU vs MENU
Community search result maps MENU139 and QMENU793 distinctly. Official Magic Remote browser keycodes are a DIFFERENT namespace (OK13 vs named ENTER), not SSAP codes. aiopylgtv buttons.py lists neither MENU nor QMENU; historical lgtv2 issue40 uses MENU. QMENU remains a plausible SINGLE observed test, not proven gear behavior on webOS6 or a verified fix. No source independently confirms this model's mapping. Do not use numeric keycodes in named frames.

## Launch
aiopylgtv public launch_app_with_params uses system.launcher/launch {id,params}. Community remote-me reports com.palm.app.settings + params.target picture/sound/etc, but explicitly tested on webOS3/B6, not this TV and not an official stable webOS6 deep link. Launch already401 here: DO NOT retry alternate launcher endpoints/app ids to route around refusal.

## Minimal actionable path
1. Existing worker owns QMENU observation; do not duplicate commands. Preserve ordinary saved pairing key/permissions, no re-pairing or privileged manifest changes.
2. One persistent SSAP plus pointer socket, serialized button commands and one receiver routing replies/events by id. Persistent transport reduces variables; it does not prove UI behavior.
3. Read allowed four picture keys; optionally subscribe using exact library envelope above. If denied stop subscription, retain already-successful read snapshots (no alternative endpoint).
4. Only when Panel Brightness focus is known: record original input/mode/value; LEFT once; bounded await readback. If100->99, RIGHT once and verify100. If no change, stop rather than assume focus or send unconditional rollback RIGHT, which might change a different setting.
5. Document each route with known starting UI state, actual opener, keys/delays, input/picture mode context, before/after values and observation status. Historical MENU>All Settings>Picture route not independently verified here; focus memory/timeouts mean blind scripts cannot establish a map of all settings.
6. Normal permanent pairing means saved client-key reuse, not disabling TV security. Reset/revocation may invalidate it. No supported way found to promise autonomous arbitrary menu learning without observation.

## Directly checked sources
https://raw.githubusercontent.com/bendavid/aiopylgtv/master/aiopylgtv/webos_client.py
https://raw.githubusercontent.com/hobbyquaker/lgtv2/master/index.js
https://raw.githubusercontent.com/bendavid/aiopylgtv/master/aiopylgtv/buttons.py
https://webostv.developer.lge.com/develop/references/settings-service
Search-result corroboration only:
https://github.com/hobbyquaker/lgtv2/issues/40
https://github.com/jxgedouard/remote-me/blob/main/docs/lg-webos.md
https://webostv.developer.lge.com/develop/guides/magic-remote
https://www.reddit.com/r/webos/comments/1swdcgv/if_you_want_to_remap_your_remote_keycodes/ (community name mapping only; no internal/decompiled code accessed)

## Claude
Signed-in subscription verified. Bounded Opus5.5 high-effort sanitized consultation output in claude-control-research.txt; verification appended below when complete.

## Claude conclusion, independently checked
Opus5.5 high-effort consultation completed successfully using the signed-in subscription. Full output: /workspace/lg-tv/claude-control-research.txt. It ran no tools and labeled its source recall as unverified. Its double-LF/button-send/ENTER-vs-click conclusions match fetched aiopylgtv and lgtv2 source. Its lack of known public menu/focus API agrees with this limited research, but is not proof of universal nonexistence. QMENU=gear, HDMI-CEC routing and bscpylgtv QMENU listing remain unverified guesses; do NOT change SIMPLINK or present these as fixes. Its mention of subscribe:true must be corrected for external SSAP: use library envelope type:subscribe, not blindly the on-device Luna payload convention. Its suggested volume-button positive control can be useful only with a meaningful TV-volume readback (external soundbar/ARC can invalidate it); restore only if initial change was observed. It recommends no blind ENTER/arrows. No new TV tests were performed by this researcher.
