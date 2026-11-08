I couldn't do any new web research this session: WebSearch, WebFetch and the file write were all declined. Everything below comes from official LG material already saved in the repo. The main source is the webOS 6.0 family user guide `w6.0_mr10_e10`, which the exact-base-model support page links to. Online copy: http://kr.eguide.lgappstv.com/manual/w21_mr10/userguide_w6.0_mr10_e10.html; local text: `sources/official-guide-eng.txt`. Earlier support-page findings recorded in `evidence/boot-route.md` are also used.

I did not check LG help-library articles, the repair/warranty pages, or the full text of `TV_Software_Update_Guide_v3.pdf`. Those are still open, not negative findings. The guide covers a family of models ("The configurable items differ depending on model"), and AEK/API are not confirmed as this unit's suffix.

## 1. Confirmed official recovery options

- **Factory reset (settings only).** General > System > Reset to Initial Settings (p.106): "Return TV to its initial settings. This will revert all settings to their default values." Also: "Do not turn off the power during initialization." It needs the stock menu to be running, and the guide never says it restores firmware. Source: guide URL above.
- **Stock update over network or broadcast (forward only).** Support > Software Update (p.109): "you can only perform updates if an update file of a later version is available." Also: "The latest version can be obtained via digital broadcast signals or internet connections." It needs the stock OS running, and it would move the TV off 03.53.45, which conflicts with your hold. Source: guide URL.
- **Stock USB update (already known, forward only).** The pages list `Software_File(Version_03.53.45/.46).zip` and `TV_Software_Update_Guide_v3.pdf`; a lower version on USB will not work. Sources: https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/ and https://www.lg.com/it/supporto/supporto-prodotto/cs-65NANO756PR.API/
- **Quick Help and LG Remote Service** (p.112). Self-diagnosis, plus remote help that requires you to "contact the LG Electronics Customer Service Center"; "may not be available in some countries or models." Both run inside the stock OS, so they don't help a TV that won't boot.
- **Basic power checks** (p.113, "I cannot turn on the TV"): check the plug and outlet, skip any power strip, and "Try to power on using the button on your TV set."
- **Authorised service.** p.112: "If you still fail to solve the problem, please contact our Customer Service Centre." The guide doesn't say what service does (reflash, board swap, or which version it installs). Entry point: https://www.lg.com/uk/support/ (I couldn't check the repair-booking pages this session).
- **Not recovery options:**
  - LG Open Source Center (https://opensource.lge.com/product/list?keyword=65NANO756PR) gives source code only, no restore images.
  - webOS Developer Mode (https://webostv.developer.lge.com/develop/getting-started/developer-mode-app) is for installing apps, not firmware.

## 2. Explicitly not established

- No official consumer recovery mode, emergency/forced update or unbrick procedure turned up in the sources I checked.
- No documented recovery loader that works on its own, and no way to start a USB update when the stock OS or updater can't run.
- Reinstalling the same version (03.53.45 over 03.53.45) is undocumented. Only "later version works" and "lower version won't" are stated.
- It's unknown whether LG service would restore 03.53.45 or install the latest version.
- It's unknown whether the stock ZIPs rewrite every partition or only part of the system.
- Help-library wording, warranty treatment of software faults, and which packages match your unknown suffix are all unchecked.

## 3. Recovery after overwritten bootloader/kernel/system partitions

None of the official documents I checked describe it. That covers the guide, the support pages, the stock update listings and the Open Source Center. The only documented paths for a broken TV are the forward stock update, which needs a working updater, and contacting Customer Service. This is a gap in the evidence, not proof that LG or service-centre recovery doesn't exist. That kind of procedure would normally be internal and wouldn't appear in consumer documents.

## 4. Suggested inquiry wording (draft, don't send)

> I own an LG 65NANO756PR (TV Information shows no sales suffix; webOS TV 6.5.3-47, software 03.53.45). If this TV's stock software became corrupted so that it would not boot, or could not run the normal USB/network software update, what official recovery options does LG offer? Specifically: (1) is there any user-accessible recovery or emergency-update procedure; (2) can an LG or authorised service centre restore the stock firmware, and would it reinstall 03.53.45 or only the latest version; (3) can the same version be reinstalled from USB using the published Software_File package; and (4) would such a repair be covered under warranty or charged? Please also confirm which sales suffix and software packages apply to my unit if I provide the serial number privately.

**To finish this:** allow Write and I'll save this into the empty `research/ai-reviews/claude-official-recovery-2026-11-08.md`. Allow WebFetch and I can check the help-library, repair/warranty pages and the update-guide PDF.
