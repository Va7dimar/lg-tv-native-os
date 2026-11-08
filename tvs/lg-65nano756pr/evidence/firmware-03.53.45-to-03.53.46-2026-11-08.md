# Installed 03.53.45 and offered 03.53.46

2026-11-08 15:10 Atlantic/Reykjavik. This unit is on **03.53.45** with
Auto Update OFF. The TV is offering **03.53.46 / 1142MB**. The owner was
advised not to install yet. No firmware ZIP was downloaded. No
developer-mode, homebrew, or root action was attempted or is recommended
here.

## Official public notes
LG regional support pages that list `65NANO756PR` publish both packages:

- `Software_File(Version_03.53.45).zip` — listed 30/09/2025, 1,176,144K
  on the UK `.AEK` support page.
- `Software_File(Version_03.53.46).zip` — listed 20/10/2026, 1,176,026K
  on the same page (slightly smaller file than 03.53.45).

The on-screen size `1142MB` is in the same ballpark as that 1,176,026K
listing (about 1148 MiB if K means KiB). The difference is unexplained and
is not proof the offered update is byte-identical to the support-site ZIP.

Both versions' published improvement text is the same generic sentence:
"Fixing minor bugs in software." The shared release-history table on
related NANO75/UP pages also lists `[03.53.45]` and `[03.53.46]` each as
"Fixing minor bugs in software." LG does not name the bugs, files, kernel
extraversion, or webOS string that 03.53.46 would change.

Sources:
- https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEK/
- https://www.lg.com/uk/support/product-support/cs-65NANO756PR.AEKD/
- Related regional notes repeating the same history, e.g.
  https://www.lg.com/ee/toetus/toote/lg-65NANO753PR.AEU

## Open-source catalog
The already-acquired official source set for model `65NANO756PR` is
**webOS 6.0 KLP 1.0**, sequence 510320 — a model-level snapshot, not a
drop labeled 03.53.45 or 03.53.46. A public search did not turn up a
separate LG Open Source package keyed to 03.53.46 versus 03.53.45.
Absence from this search is not proof LG never published one.

## Version pairing now confirmed on this TV
webOS TV Version `6.5.3-47 (kisscurl-koli)` plus Software Version
`03.53.45` matches several independent third-party reports of that same
pair on other 2021 webOS 6 TVs. That pairing is now a fact for *this*
unit. It still does not identify SoC, board, or the live `uname`.

A sibling-model report (`65NANO753PR` on 03.53.45 / sdk 6.5.3) published
`Linux ... 4.4.84-723.kcl4tv.20 ... armv7l`. That remains another TV.

## Community tool version lists (hypotheses only)
These are other projects' claims. They are not instructions, and they
are not authorization to root or enable developer mode.

- One third-party firmware/root helper documents a table that treats
  platform `kisscurl` (examples NANO77/NANO79, W21A) with one named
  community tool as supported **up to 03.53.45**.
  Source: https://github.com/TheLord83/CleanFrame-webos/blob/main/docs/ROOTING.md
- User issue titles later report the same family of tool working on
  **03.53.46** for some UP77/UP77xx models that share LG's official
  03.53.46 applicable-model list with `65NANO756PR`
  (e.g. 60UP7750PSB, 75UP77006LB).
  Sources: https://github.com/throwaway96/slopbro/issues/77
  and https://github.com/throwaway96/slopbro/issues/94
- Those later reports are unverified here. The written "up to 03.53.45"
  ceiling and the later 03.53.46 success claims disagree, so a 03.53.46
  install is not proven safe or unsafe for any community tool.

No exploit steps are recorded. None should be run on this TV without a
separate explicit owner decision, which has not been given.

## Does this change SDK / BSP facts?
No. Official guides still name SDK **20190307**. The inventoried
community SDK is still **20191125**. The catalog kernel Makefile is still
Linux **4.4.84**. Confirming 03.53.45 only strengthens the documentary
link between this installed userspace string and the 03.53.45 stock
package family already listed for the model.

## Recommendation
**Stay on 03.53.45 for now. Leave Auto Update OFF. Do not press Download
and Install.**

Reasons:
1. The current combination (`6.5.3-47 (kisscurl-koli)` + `03.53.45`) is
   now photographically documented and should be kept as the research
   baseline until there is a reason to change it.
2. Official notes for 03.53.46 disclose only unspecified minor bug
   fixes. They do not claim a needed panel, HDMI, security, or recovery
   improvement we can verify.
3. Updating is not required for the current source/SDK work and would
   change the installed software we just recorded. Whether 03.53.46
   keeps webOS `6.5.3-47` is unknown.
4. Official consumer downgrade paths are not established. Installing
   03.53.46 should be treated as hard to undo.
5. Community version tables are inconsistent about 03.53.46. Staying
   preserves the documented state without depending on those tools, and
   without taking any root/developer-mode action.

Revisit only if the owner later makes an explicit decision to update
(for a stated official fix) or separately authorizes a different line of
stock-OS investigation.
## Subscription cross-checks (2026-11-08 Atlantic/Reykjavik)
- Claude Opus 5.5 high reviewed the webOS-string mapping before the Software
  Update photo arrived and treated 03.53.45 as the most likely dotted
  version. That guess is now confirmed. Raw:
  `research/ai-reviews/claude-kisscurl-koli-2026-11-08.md`.
- Codex (read-only, exit 0) agreed to stay on 03.53.45 to preserve the
  documented baseline, and cautioned that “minor bugs” neither proves nor
  disproves a security fix. It also noted that 1,176,026K as KiB is about
  1148 MiB, not 1142. Raw:
  `research/ai-reviews/codex-firmware-03.53.45-2026-11-08.md`.
- Gemini 4 Argon high (second attempt, no tools; first headless run
  produced no answer because it requested a shell command) also agreed to
  stay on 03.53.45. Some of its extra claims are **unverified hypotheses**
  and are not adopted as facts: that `koli` historically maps to `k7lp` /
  KLP 1.0; that webOS will enforce anti-rollback after 03.53.46; and that
  a boot modal will still offer the update. Raw:
  `research/ai-reviews/gemini-firmware-03.53.45-2026-11-08.md`.

AI agreement is not independent hardware evidence.
