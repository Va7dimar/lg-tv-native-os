# Root research and decision — 2026-11-08

Status: **SUPERSEDED — owner rooted this unit on 2026-11-08 via SlopBro.** Homebrew Channel 0.7.3 and root SSH are available. See the [post-root plan](../plan-2026-11-08-post-root.md), [live inventory](live-system-inventory-2026-11-08.md) and [SSH evidence](ssh-access-2026-11-08.md). No exploit reproduction steps are added here.

The assessment below is historical, pre-root research; its “STOPPED”, “no-go from this session” and network-access statements are not the present state. Root access does not establish custom boot or independent recovery. Original status: **STOPPED before any TV change.** No apps were installed, no exploit was run, no USB payload was prepared, no settings were changed, and the offered `03.53.46` update was not started.

This file is a compatibility and risk assessment, not a reproduction procedure. It does not include commands, script flags, payloads, launcher app identities, or button-by-button steps.

## Recommendation

**No-go for proceeding from this session.**

Two separate questions were asked. They have different answers:

1. **Is a current community method *reported* to apply to firmware `03.53.45` / webOS `6.5.3-47 (kisscurl-koli)`?** Yes, as unverified third-party reports plus the author's claimed webOS 4–11 range. It is **not** confirmed on this exact sales model `65NANO756PR`.
2. **Should this agent now run a community root tool against the TV?** **No.** This agent will not write or execute unofficial exploit procedures. The research box also has no useful network path to the living-room TV.

This is **not** a "no applicable method" finding, and it is **not** a finding of a documented hard-brick pattern for a failed software attempt. webOS Homebrew's public rooting guide and the current-method author's README both describe failed software attempts as usually uneventful; they also warn that later privileged system changes can damage a TV, that warranty may be affected, and that remote shells (if enabled) are a security exposure.

Residual risks of a *successful* persist remain: Homebrew Channel and boot-time privileged hooks, optional remote-admin services, community "block updates" behaviour, and factory-reset undo that older docs say *should* remove root configuration but is not independently proven for this tool on this unit. A factory reset would also wipe picture, accounts, and the documented software baseline.

Keep Auto Update **OFF** and do **not** install the offered `03.53.46` / `1142MB` update. That recommendation from the earlier firmware note is unchanged.

## Photo-confirmed unit (no serial or MAC)

Recorded from owner photos on 2026-11-08 (Atlantic/Reykjavik):

- Device Name: `[LG] webOS TV NANO756PR`
- Model: `65NANO756PR` (no further suffix shown)
- webOS TV Version: `6.5.3-47 (kisscurl-koli)`
- Software Version: `03.53.45`
- Auto Update: OFF
- Offered update: `03.53.46` / `1142MB` (not installed)
- Available Internal Storage (TV Information): `1.07/2.03GB`

See `evidence/tv-information-photo-2026-11-08.md` and `evidence/software-update-photo-2026-11-08.md`.

## Methods surveyed (high level)

Primary pages fetched or consulted on 2026-11-08:

- [webOS Homebrew exploit summary](https://www.webosbrew.org/rooting/exploits/)
- [webOS Homebrew rooting risks](https://www.webosbrew.org/guides/rooting/)
- [throwaway96/slopbro](https://github.com/throwaway96/slopbro) README at observed `main`
- [throwaway96/faultmanager-autoroot](https://github.com/throwaway96/faultmanager-autoroot) public README (patch-status text)
- Community issue threads on that current-method repo, plus older RootMyTV / caniroot user reports that DejaVuln / older procedures failed on `03.53.45`

| Method (public name) | Reported relevance to this unit | Notes |
| --- | --- | --- |
| RootMyTV v1 / v2 | Unlikely | webosbrew lists both as mitigated years ago |
| crashd | Unlikely | webosbrew: mitigated in a developer-mode jail-config update around 2024-04-02 |
| WTA / asm / DejaVuln | Unlikely on current firmware | webosbrew lists them as mitigated in firmware; users reported DejaVuln failure on `03.53.45` |
| faultmanager-autoroot | Unlikely as the current path for latest webOS 5+ images | webosbrew table still shows no patched date; the project's own README warned that latest webOS 5+ firmware was almost all patched as of 2025-08-24, and that path starts from official Developer Mode |
| NVM / hardware debug flag | Not applicable / out of scope | webosbrew: older platforms and a hardware modification; not authorized here |
| SlopBro (2026 public project) | **Best-supported reported method for this firmware generation** | Author claims webOS 4–11 use; community comments report success on the same webOS string and `03.53.45` on other 2021 models |

The webosbrew exploit table fetched on 2026-11-08 does **not** yet list SlopBro. Compatibility evidence for this firmware therefore comes from that project's README and issue comments, not from the older webosbrew table.

## Compatibility evidence (hypothesis vs source)

**Primary-source author claims** (README at observed `main` commit `d7e6d4e4653a1d997c55b1e131be1cd255122a6f`, commit author date 2026-11-04 23:24:53 UTC / 2026-11-04 23:24:53 Atlantic/Reykjavik; committer 2026-11-05 00:04:46 UTC):

- Has been used successfully against webOS 4–11, including a workaround for an earlier vendor patch attempt.
- Not expected to work on webOS 10 and 11 firmware released since about 2026-10-10. That cutoff does **not** apply to this webOS 6 unit.
- Author statement: a failed attempt is not going to harm the TV. Treat as an author claim, not independent proof.

**Unverified community reports** (issue comments; not independently reproduced here):

- OLED C1-class sets with Software Version `03.53.45` and webOS `6.5.3-47 (kisscurl-koli)` — same webOS string as this unit.
- Other `03.53.45` / webOS 6 reports, including `55NANO796PC` and a comment "Works on NANO756PA, WebOS6" (close sales-family cousin; not this exact `65NANO756PR`).
- At least one later `03.53.46` success comment on a different model, which is **not** a reason to install `03.53.46` here.
- A G1 comment reporting `03.53.45` / webOS 6.5.3 success (issue 109, created 2026-11-06).

**Not found in this pass:** a confirmation specifically naming `65NANO756PR`. Transfer to this exact model remains a hypothesis.

**Older-method failure reports:** RootMyTV issue 164 and webosbrew/caniroot issue 100 describe DejaVuln / "standard procedures" failing on webOS 6.5.3 / firmware `03.53.45`.

## Pinned identifiers (no local download of the tool)

Nothing from the project was downloaded into this repo or executed on the box. Identifiers were read from the public GitHub API on 2026-11-08:

- Repository: https://github.com/throwaway96/slopbro
- Observed `main` commit: `d7e6d4e4653a1d997c55b1e131be1cd255122a6f` (message: "update patch status")
- Latest GitHub release tag: `v0.1.0` (published 2026-09-28 00:13:03 UTC / 2026-09-28 00:13:03 Atlantic/Reykjavik)
- Release asset named `slopbro_packed.py`, size 78142 bytes, publisher-stated digest `sha256:b0a7cb1294daf37d0f6eac404604dab468af700462de7a7ed41a0ed8df7f1ad8` (from the GitHub releases API `digest` field; **not** re-hashed locally because the file was not fetched)
- Important version note: `v0.1.0` is older than the observed `main` commit. Community success comments cite various later revisions. A tagged release and current `main` are **not** proven identical.

## What a successful persist typically writes (high level)

From the current-method author's own overview, not from running it: the client talks to the TV over the LAN using the same family of app-control pairing already used for ordinary remote control, then arranges privileged execution and installs Homebrew Channel with persistence.

Older Homebrew / RootMyTV public docs describe typical post-root state in general terms (not proven identical for this 2026 tool):

- Homebrew Channel appears as an installed app
- Persistence hooks that survive ordinary reboots
- Optional remote-admin services (SSH and/or an unauthenticated telnet-style service if someone turns those on)
- A community option to block system updates
- Factory reset is the commonly cited way to remove root-related configuration; it is not independently verified here for this tool, and it is destructive to settings and accounts

Do not treat "block updates" as a reason to install `03.53.46` first or later.

## Network / already-paired control

The current method is described by its author as a LAN client that can show a **new pairing prompt** on the TV. An existing pairing for a different remote-control client does not automatically authorize a new unofficial tool, and pairing material must not be copied, committed, or reused for that purpose.

The research box is on `172.30.0.2/24`. A route lookup for the previously recorded TV address `192.168.0.2` only showed the box default gateway (`via 172.30.0.1`). That is not evidence of LAN reachability to the living-room TV. No SSAP, pairing, or TV command was sent from the box during this research. **The box cannot reliably trigger anything on the TV.** Any future network action would have to originate on a machine that is actually on the home LAN (for example the owner's already-used Windows client). That is a topology fact, not permission to proceed.

## What would need the owner's hands and eyes (if anyone later proceeded)

This is presence and consent, not a how-to:

- Stay in front of the TV and watch the screen the whole time.
- Leave Auto Update OFF; do not press Download and Install for `03.53.46`.
- Be ready to accept or refuse a pairing / consent prompt if a new client appears — that decision is the owner's.
- Photograph any unexpected error, reboot loop, or settings change.
- Do not open the TV, do not use a service menu, and do not flash firmware.

What the box can do (and did): read public documentation, pin published identifiers, write this assessment, and commit it. The box cannot reach the TV and will not run a root client.

## Risks and undo

**Author / webosbrew claims (not independent tests):**

- Failed software attempts are usually uneventful.
- Later uninformed system changes can brick a TV.
- Rooting may affect warranty.
- Enabling remote shells is a security issue if the TV is reachable beyond the intended LAN. Community Homebrew SSH has historically shipped with a well-known default password; if a shell were ever enabled it would need immediate hardening and must not be exposed to the internet.
- Factory reset may remove root configuration; after a reset, re-rooting may no longer be possible if the relevant issue has been patched.

**Residual risks that remain even if those claims are accurate:**

- Success installs persistent privileged software, which is a larger change than a failed attempt.
- Partial success (app installed, hook only half-applied, extra service left listening) is not the same as "no change."
- Transfer from other `03.53.45` / kisscurl-koli models to `65NANO756PR` is unproven.
- Picture, HDMI, audio, and power behaviour matter for this project; they are not what community "root worked" comments usually verify in depth.
- Undo via factory reset destroys the carefully recorded settings baseline.

No widespread "this tool hard-bricked 03.53.45 sets" pattern was found in this pass. Absence of such reports is not proof of safety.

## AI cross-checks (hypothesis only)

Prompts asked only for compatibility and residual-risk review and forbade how-to content.

- Codex (`gpt-6.1-sol` / high, 2026-11-08): agreed that an applicable method is *reported* for this firmware/webOS string, that `65NANO756PR` itself is unconfirmed, that there is no documented hard-brick pattern in the reviewed notes, and that declining remains reasonable because of residual risk. Raw: `research/ai-reviews/codex-root-compatibility-2026-11-08.md`.
- Gemini (`gemini-4-argon-high`, no tools, 2026-11-08): same classification — reported compatible on same firmware / sibling models, exact model unconfirmed, no-go-for-execution not required by "no method" or "hard-brick pattern," residual risk only. Raw: `research/ai-reviews/gemini-root-compatibility-2026-11-08.md`.
- Claude Opus: the subscribed CLI refused the prompt under its cyber safeguard (`Request ID: req_011CgqhEqTb4bvYbFNkTneCx`). Not retried. Note: `research/ai-reviews/claude-root-compatibility-2026-11-08.md`.

Agreement among reviewers is still hypothesis.

## Explicit stop

No further action toward rooting will be taken by this agent unless a later owner decision asks for something that does **not** require writing or running an exploit (for example more public documentation research, or reading kernel/chip facts by some other already-permitted path). Installing Homebrew, launching unofficial clients at the TV, changing developer-mode state, or plugging a prepared USB stick are all out of scope for this stop point.

## Addendum: README-focused CLI reviews and local hash check (same day, Atlantic/Reykjavik)

After the first decision note, reading and interpretation of the pinned SlopBro README and the two webosbrew pages were pushed to the subscribed CLIs. This agent only did the hash check, wrote the files, and committed.

Local hash check of the published `v0.1.0` asset `slopbro_packed.py` (downloaded to a temp path, hashed, then deleted; not executed, not added to git):

- size: 78142 bytes
- SHA-256: `b0a7cb1294daf37d0f6eac404604dab468af700462de7a7ed41a0ed8df7f1ad8`
- matches the GitHub releases API publisher digest recorded earlier: yes

README-focused reviews (still no how-to in this repo):

- Codex fetched the pages itself: `research/ai-reviews/codex-slopbro-readme-2026-11-08.md`
- Gemini reviewed pasted public text: `research/ai-reviews/gemini-slopbro-readme-2026-11-08.md`
- Claude did not complete a review: `research/ai-reviews/claude-slopbro-readme-2026-11-08.md`

Both completed reviews agree on the same conceptual usage picture from the README: a pairing prompt is stated as required; USB, Developer Mode app, LG account, and settings toggles are not stated as requirements; success is described as installing Homebrew Channel and enabling persistence; a failed attempt is claimed by the author to be harmless (no warranty); the README gives no undo procedure; webosbrew separately mentions factory reset as losing root and possibly preventing later re-rooting; the client runs on a LAN computer and privileged work then happens on the TV. webOS 6 is inside the author's 4–11 claim; `65NANO756PR`, `03.53.45`, and `kisscurl-koli` are not named in that README.

Session recommendation is unchanged: **no-go for this agent proceeding to change the TV.**
