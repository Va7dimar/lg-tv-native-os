# Native Bootable TV OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**STATUS: PLAN READY FOR APPROVAL — DISCOVERY/EVIDENCE SCOPE ONLY; TARGET IMPLEMENTATION AND DEPLOYMENT BLOCKED.** The sub-skill execution directive above is INACTIVE until written, phase-specific owner approval. Tasks describe future authorized work, not instructions to start. Planning creates no execution authority.

**Goal:** Establish and, only if evidence gates pass and separately approved, build an internal replacement OS for LG65NANO756PR with working panel, HDMI input, audio, remote and safe power behavior.

**Architecture:** Conditional choice between vendor-kernel/BSP reuse with replacement userspace (partial-stack replacement) and rebuilt kernel/vendor BSP with replacement userspace (kernel replacement). An independent full-stack hardware port is a third, currently unsupported branch. No architecture is selected or bootable recipe established yet.

**Tech Stack:** Initial evidence records are Markdown/JSON/SHA256 and read-only archive metadata analysis on the box; no target-language, CPU architecture, toolchain, kernel release, partitioning or deployment technology selected. Target stack is selected only from inspected exact-board source/build documentation.

## Global Constraints
- PLAN ONLY. No implementation, source archive download/execution, code scaffold, repository creation, TV commands, account changes, enrollment, inquiries, purchasing, disassembly, flashing or resets in this planning task.
- Full internal replacement is goal; HDMI external OS and app/launcher-only substitutions are excluded.
- Preserve native panel/backlight, HDMI input, audio, power/thermal and remote functionality as first acceptance; LG apps expendable; HDR currently untouched.
- Exact SoC/board/suffix/live version remain unknown; candidates and KLP catalog/notice labels are not measurements of this unit.
- No401 retries, security bypass, private APIs, copied signatures/provisioning, DRM/HDCP circumvention or invented image layouts.
- All future operations gated by evidence plus specific approval. A broad owner go cannot silently authorize hardware access, purchases or destructive writes.
- Do not assume A/B slots, USB/external boot, serial recovery, writable boot chain or independently recoverable partitions.
- No target code tasks are execution-ready until a platform addendum supplies verified APIs, target, build commands and tests. Explicit blocked tasks below are discovery contracts, not fictitious implementation instructions.

---

## Document authority and handoff
Design: `docs/superpowers/specs/2026-11-08-native-bootable-os-design.md`; detailed evidence: `native-os-feasibility.md`; chronology: `project-log.md`; live facts: `device-facts.md`; notice audit: `source-catalog/notice-inventory.json` and `.md`. All paths relative to `/workspace/lg-tv`. Update existing Page6d983eed-3554-42ac-b292-cb8e606eadfe only. No git repo currently created; do not run commits now. A later approved coding phase can use isolated source control and task reviews, but not repurpose TV helper/NOTES as an OS repository.

## Proposed future artifact map (not created by this plan)
|Path|Responsibility / interface|
|---|---|
|evidence/device-identity.json|Fields model,suffix,installedSoftware,webOSBuild,boardAssembly,pcbRevision,panelVariant,SoC; each value carries source,timestamp,confidence; unresolved fields use explicit unknown state, never guessed strings.|
|evidence/catalog-manifest.json|Catalog URL,sequence510320,display label,exact archive filename,size,download timestamp,SHA256,source association and notice hash; not installation manifest.|
|evidence/archive-members.json|Per archive:normalized path,type,size,link target,rejected reason; no extraction/write effects on TV.|
|evidence/source-coverage.json|Per required capability:source path/version,source-vs-binary,license,ABI/toolchain,board association,evidence citation,status; missing is a blocker.|
|evidence/boot-route.md|Manufacturer/public supported exact-board deployment mechanism, scope and limitations; no bypass directions.|
|evidence/recovery-case.md|Independent recovery entry prerequisites,failure coverage,unit-data preservation and tested evidence; no invented addresses.|
|evidence/decision-record.md|Owner-selected A/B/C architecture, approvals, reasons, risk acceptance and next permitted action.|
|validation/baseline.md|Existing SDR/HDR/HDMI/audio/remote/power observations with source modes, permitted UI settings and evidence.|
|validation/matrix.csv|Test ID,preconditions,input,expected result,measured result,evidence,pass/fail; no fabricated pass.|
|platform/target-contract.md|After source gate only:actual board/toolchain/ABI/interfaces/build outputs and target-specific test commands.|
|build/reproducibility.md|Pinned source/toolchain/dependencies,isolated build process,output manifests and explained nondeterminism.|
|handoff/approval-checklist.md|Stage status,hashes,review findings,rollback scope and approval boundary.|

Source/tooling code paths and function signatures will be specified in a separate executable platform/tooling addendum only after owner go and relevant inputs exist. This document intentionally adds no speculative system implementation code.

## Unknown registry: exact proof contracts
|ID / unknown|Safe acquisition and required artifact|Pass criterion|Fail/stop criterion|
|---|---|---|---|
|U0 cheap boot/recovery feasibility screen|Desk-only public manufacturer/exact-target project documentation before heavy source audit; evidence/boot-route.md with dated search scope and legitimate entry/recovery findings.|At least a credible exact-target route to investigate; no exploit requirement.|If none, record deployment-no-go. Source work already inside a later approved E1 scope may complete for learning; beyond-scope work needs new approval.|
|U1 suffix/version/build|Normal UI: General>Devices>TV Management>TV Information; Support>Software Update VIEW ONLY. Record photos/text with sensitive serial redacted in device-identity.|Exact visible strings/provenance, never catalog label substituted.|Unavailable stays unknown; do not retry denied API.|
|U2 actual board/SoC/panel|Existing service documents/photos or manufacturer parts cross-reference keyed to suffix; identity mapping document.|Assembly,PCB,panel and SoC mapping tied to unit or authoritative exact variant.|Seller lists/UD15D/RTK label alone insufficient; no opening TV silently.|
|U3 catalog/source match|Normal public UI source archive download after approval; catalog-manifest and member list.|Exactnames/sizes/checksums,release association and board-relevant source references reconciled.|Catalog entry alone does not prove matching installed release/BSP.|
|U4 reproducible build inputs|Read-only source inventory/readmes/config/toolchain documentation.|Complete build dependency/rights manifest and actual target recipe.|Missing toolchain/generated files/vendor dependencies block build stage.|
|U5 hardware coverage|Inspect source/interfaces/licenses and board docs; source-coverage.|Panel/HDMI-IN/audio/power/remote path accounted for with usable compatible components.|Output-only HDMI or generic video service is not receiver support.|
|U6 legitimate custom boot|Published manufacturer-supported route or lawful documented project route for exact board that does not require bypass; boot-route.|Target acceptance method and failure behavior documented and independently reviewed.|No route means STOP boot/deploy; never fill gap with exploit.|
|U7 independent recovery|Manufacturer/exact-board recovery docs; recovery-case with separate risk-approved validation.|Recovery does not depend on overwritten system; covers contemplated failures,unitdata and locked/licensed state.|Factoryreset/ordinary update alone or untested backup is insufficient.|
|U8 owner boundary choice|decision-record comparing designA/B/C.|Owner explicitly accepts retained-kernel boundary or chooses full kernel replacement.|No implicit downgrade to partial userspace or launcher.|

## Task 0: Cheap boot/recovery screen before source audit (U0)
**Files:** evidence/boot-route.md; evidence/recovery-case.md; evidence/decision-record.md.
**Consumes:** exact-model source register and candidate identity caveats; desk-only research approval.
**Produces:** documented route lead or dated deployment-no-go finding.
- [ ] Review only ordinary public manufacturer/exact-target project documentation for custom boot acceptance and recovery scope. Preserve exact citations and evidence limitations.
- [ ] Record whether stock restore media is legitimately obtainable and any approved diagnostic/log channel exists when display/userspace fail. Do not acquire credentials,wire serial,open TV or send inquiries.
- [ ] If no credible route exists, stop deployment preparation; complete a no-go report listing searched sources,missing proof and reconsideration trigger. A later E1 approval explicitly includes its bounded source learning regardless of U0 outcome; finish those evidence outputs without another approval, but do not advance deployment preparation or expand E1.
**Acceptance:** evidence report has value even on a no-go; no inference that source download implies future deployment. This desk screen does not replace full G3.

## Task 1: Evidence identity and original operating baseline (G1)
**Files:** future evidence/device-identity.json; validation/baseline.md; evidence/decision-record.md.
**Consumes:** design confidence table and existing device-facts.md/NOTES.md for G1-record; separately approved owner-performed read-only UI session for additional unit facts.
**Produces:** evidence-addressable identity and baseline, no target changes.
- [ ] Copy confirmed model into identity record with worker/source reference; leave suffix/version/SoC/board/panel unknown.
- [ ] During separately authorized normal-UI session capture exact suffix/software/build; do not press Check/Install/Reset, enroll devmode or expose serial/MAC.
- [ ] Record known SDR HDMI2 Filmmaker settings from NOTES:panel40,contrast80,brightness50,colour50,sharpness0; copy existing evidence rather than claim new measurements.
- [ ] Capture actual AppleTV HDMI input mode, audio path, volume/remote power behavior and current supported HDR mode using normal playback only after approval. Existing HDR calibration remains untouched.
- [ ] Reconcile candidate service parts with authoritative exact-variant documentation; if unresolved, mark U2 blocked.
**Authorization split:** Task1 information readout is owner-performed E-TV-info, not E-box. Playback/audio/CEC/power baseline is E-TV-baseline with its own approval; no automated TV commands. AEK and AEU references conflict at suffix level; no candidate mapping applies to this unit until reconciled. An installed firmware,board,panel or source change invalidates affected G1–G4 evidence and requires re-review; do not change auto-update settings to enforce a freeze.
If ordinary UI and lawful exact-variant documents cannot resolve identity without prohibited hardware access, U2 remains blocked under the current non-invasive scope; do not call it universally or permanently impossible.
**Acceptance/review:** independent reader can distinguish measured facts, catalog association and seller claims. G1-record passes when every field has provenance/confidence or explicit unknown, feeding desk source triage now. G1-target passes only when identity needed by an explicitly described candidate boot/driver branch is resolved and matched to this unit; it does not require architecture freeze first. Unknown board/panel fields do not prevent unit-independent source learning, but block exact-board claims and G1-target. Fail closed if the unit cannot be matched.

## Task 2: Source acquisition and safe member inventory (G2a)
**Files:** evidence/catalog-manifest.json; evidence/archive-members.json; source-catalog/ originals retained unchanged.
**Consumes:** confirmed catalog URL and sequence510320,notice SHA256,public UI and later E1-box approval. Parsing additionally requires the recorded pre-read safety checks below; no extra owner approval for each in-bounds file.
**Produces:** independently verifiable archive provenance and safe read-only member index.
- [ ] Normal public UI: capture three exact displayed filenames and sizes. Prior names KLP_1.0_1/_2/_3 are reported labels, not checked raw filenames.
- [ ] Download only published source archives to box; record URL/context/time/size/SHA256. Do not generate hidden URLs or invoke internal APIs; if UI fails, stop and record reason.
- [ ] Before extraction list member metadata with a maintained archive reader. Reject absolute paths, traversal including normalized parent escape, unsafe symlink/hardlink targets, device nodes,FIFOs and unbounded expansion; set approved disk/member/expanded-size limits after observing sizes and free disk.
- [ ] Set conservative initial parser ceilings before reading archives: metadata listing in an isolated process with1GiB memory,120-second wall limit,200,000 members,100,000,000 total path-name bytes,16MiB maximum selected text member; no nested archive expansion by default. Keep at least10GiB box disk reserve and stage no more than20GiB expanded data. These are proposed tooling limits,not measured package requirements; if exceeded stop and review limits instead of bypassing them. Readers must enforce streaming/bounded allocation; a maintained parser is not itself sandboxing.
- [ ] For read-only selected-text extraction, use an isolated non-executable staging directory and reject dangerous entries first; do not source scripts, install packages from archive or run builds. Archive contents remain untrusted data.
- [ ] Cross-check duplicate member names, collisions and encoding; retain member-level origin archive and byte ranges/hash where practical. Partial/truncated download is fail.
If source requires a request/contact, stop; draft only and obtain specific external-message approval. Do not treat contact-only availability as missing source or send automatically.
**Pre-read checkpoint:** record available maintained general-purpose archive utility/version, streaming/resource isolation and enforcement evidence, observed source sizes/free disk, rejection rules and ceilings in handoff/approval-checklist.md before parsing. Existing project scripts are not implicitly trusted utilities. If enforcement cannot be demonstrated, stop archive reading and report the specific missing control; no custom reader or limit increase is silently authorized.
**Acceptance/review:** all three sources accounted for, original hashes stable, no writes outside staging,no executed downloaded code. Future evidence-tool implementation requires tests for traversal,links,duplicate names,expansion limit and deterministic index; actual code/test commands belong to approved tooling addendum, not this plan-only output. G2a does not establish source completeness.

## Task 3: Exact-board BSP and rights coverage audit (G2b)
**Files:** evidence/source-coverage.json; platform/target-contract.md (document only); evidence/decision-record.md.
**Consumes:** G2a member index/verified text; G1-record with unknowns explicit. E1 may triage READMEs, target/config identifiers, licenses and dependency gaps without a resolved installed board. G2b exact-board pass requires G1-target and reconciled source mapping; preliminary triage is not that pass.
**Produces:** capability/source/ABI map with missing pieces, not a bootable image.
- [ ] Locate real READMEs/build manifests/licenses; record exact release/toolchain versions,patch order,config and target identifiers with paths and hashes.
- [ ] Search actual source for kernel configuration/platform/device-tree equivalents,kdriver and referenced kernel modules; compare4.4.84-711.kalaupapa.4 notice label without asserting it is current runtime.
- [ ] Trace panel/backlight,HDMI RECEIVER/input and EDID/control,audio,memory/storage,power/thermal,IR/MagicRemote/CEC and network; mark generic services separately from real hardware drivers.
- [ ] Inventory external-to-main-CPU dependencies as separate capabilities:standby/power controller,watchdog,TCON/panel firmware,HDMI receiver,MagicRemote pairing/radio,Wi-Fi/Bluetooth firmware,calibration and unit provisioning. Labels do not prove any particular topology. Retain certified radio firmware/config where lawfully usable; otherwise radios disabled and not claimed supported.
- [ ] For each required retained binary identify its lawful source and availability,not merely a notice name:kernel/modules,firmware,hardware daemons and libraries. If absent from inspected public source,do not infer it exists elsewhere or obtain it through bypass/exploit/decryption. Missing supply is a branch blocker.
- [ ] For each retained vendor binary record permitted use/distribution,compatible kernel/userspace ABI and required provisioning. Do not copy unique credentials or infer licenses from notice name alone.
- [ ] Produce a retained/replaced component ledger covering kernel,modules,firmware,hardware userspace services,init/system manager,compositor,app framework,UI and licensed services. Owner must explicitly accept this ledger; replacing only launcher on stock init/system manager/app stack remains excluded. A-K keeps kernel/modules only; A-H also retains specifically enumerated vendor hardware services but must replace init/system management/UI under approved boundary. B-same rebuilds same compatible kernel/config; B-new requires fresh driver/ABI validation and may approach full-portC. No evidence currently establishes an easier boot route for A than B.
- [ ] Produce architecture A/B/C comparison using actual inventory. A needs alternate-userspace boot and compatible driver stack; B also needs rebuilt-kernel compatibility; C requires public hardware documentation not currently present. For Task4 desk evaluation, describe each plausible candidate branch and retained/replaced ledger explicitly; this is not owner selection, build approval or a deployable artifact. Do not require an owner choice merely to compare documentary boot/recovery evidence. Task5 later freezes the owner-selected viable boundary.
**Protected-input gate:** selected stack must legitimately use compatible HDCP services and this unit’s own provisioning for normal protected AppleTV playback. Legal-use evidence plus later functional verification both required; unprotected picture alone fails first acceptance. No key extraction/transplant or circumvention proposed.
**Acceptance/review:** every first-acceptance capability has a concrete usable implementation/dependency chain or explicit blocker. Packagegroup names or a successful kernel compilation cannot satisfy this gate. If required proprietary components unavailable/incompatible, stop selected branch; no secret launcher fallback.

## Task 4: Boot authorization and independent recovery case (G3-D / G3-V — currently BLOCKED)
**Files:** evidence/boot-route.md; evidence/recovery-case.md; handoff/approval-checklist.md.
**Consumes:** earlyU0 lead, resolved G1-target and G2b mapping plus candidate branch descriptions and published exact-board boot/recovery documentation. General documentary research may start earlier, but cannot pass an exact-target gate. No speculative steps.
**Produces:** reviewed deployment/recovery design or explicit no-go.
- [ ] For each explicitly described candidate branch, identify a documented route that accepts its required artifact class on the actual retail board without bypass/impersonation. Record publisher,target revisions,formats,constraints and evidence; do not invent image headers,keys,addresses or flash commands. Final built-artifact compatibility is checked again before any target action.
- [ ] Record which boot components/regions the proposed change would affect from verified documentation. If unknown, do not schedule writes.
- [ ] Establish independent recovery entry and failure coverage:failed image,interrupted install,failed userspace,kernel unable to boot and lost display. State which cases the method cannot recover.
- [ ] Establish ordinary authorized backup access and restore semantics for stock code/config and unique calibration/provisioning; hashes,private encrypted storage,restricted access,no Page exposure. If backup access itself needs prohibited methods, mark blocked rather than attempt.
- [ ] Require recovery validation on an exact compatible development target or approved non-destructive route; buying/opening/wiring hardware needs separate approval. If no safe validation environment exists, recovery remains unproven and target experiments stop.
A matched spare does not prove recovery of the primary unit’s unique calibration/provisioning. Before any primary-unit write, require an authorized non-invasive preservation-and-restore route for its own unique data or authoritative evidence that the documented operation cannot alter or invalidate that data. No key extraction or transplantation is authorized. If neither can be established,the primary-unit deployment is blocked.
**Recovery proof levels:** distinguish documentary route,validation evidence and coverage of this exact proposed operation. Compatibility argument must explicitly cover board revision,panel variant,boot policy,storage layout,unit provisioning and intended changed regions. An ordinary source manifest does not establish storage layout. Legitimately obtainable matching stock restore artifact and authorized independent log/diagnostic path are required. Validation on a spare board/unit needs separate purchase/hardware/test approvals and cannot be silently bundled into PhaseT; if no compatible recoverable validation route exists,G3 remains FAIL. Documentation alone is not tested recovery.
**Two stop/go decisions, not a build/test cycle:** G3-D is documentary build eligibility: exact-target legitimate artifact acceptance, credible independent recovery design with failure coverage and unit-data preservation, legitimately obtainable restore inputs, and an authorized validation route. It is not tested recovery. With G1-target/G2b, G3-D can support owner-approved box-only build work; G3-V need not exist before producing an artifact. G3-V is validated recovery plus coverage of the exact proposed operation/artifact and primary-unit data, independently reviewed before ANY custom target boot/write. Recovery validation itself still needs PhaseR approval; it cannot use an unapproved custom boot on the primary to prove safety. If a safe independent validation route cannot be established, stop target work. A backup file without tested restore or factory reset is not G3-V. Source availability waives neither gate.

## Task 5: Architecture freeze and executable platform addendum (G4)
**Files:** evidence/decision-record.md; platform/target-contract.md; handoff/approval-checklist.md; a new target-specific executable plan after evidence.
**Consumes:** G1-target, G2b exact-board pass and G3-D documentary artifacts, plus owner boundary selection. G3-V validated operation-specific recovery remains mandatory before target boot/write, not a precondition to box-only build.
**Produces:** exact implementation target and separately approved phase scope.
- [ ] Owner explicitly selects partial-stack vendor-kernel routeA or kernel-replacement routeB; routeC only if its evidence supports it. Record limitations; retaining kernel must remain visible in project title/claims.
- [ ] Freeze an owner-approved operating profile:required HDMI modes/colour range,protected playback,audio route,physical remote minimum versus MagicRemote pointer/pairing,CEC actions,AppleTV sleep/wake,input reconnect,TV standby and permissible outages/latency. Proposed cycle/soak values below are acceptance proposals,not a reliability certification. Quantitative tolerances need a named measurement method and approved baseline before testing.
- [ ] Define minimal hardware contract,actual source paths/APIs/toolchain/license inputs and image outputs from inspected docs.
- [ ] Write target-specific TDD steps with complete code/test commands only now that interface and target are real. Document mock versus hardware test coverage; mocks never satisfy panel/HDMI tests.
- [ ] Obtain approval for box-only isolated build first. Source build scripts are untrusted; inspect then execute only in approved isolated environment without TV/network credentials or registered-machine access.
**Acceptance/review:** no unknown required interface or required deployment operation is disguised as executable task. Cursor target coding begins only after this addendum and PhaseB approval; target operations additionally await G3-V/G5 and PhaseT. Evidence-tool coding may begin earlier ONLY under separate narrow tooling approval. No cloud agent/repo launched now.

## Pre-boot hardware safety gate (G5 — BLOCKED)
Before ANY custom boot,including minimal init or purported RAM-only tests:document safe startup panel/backlight defaults,power/standby/TCON/watchdog requirements and thermal limits from exact-board documentation. Require a stop method independent of replacement userspace and a permitted observation/log channel even if display fails. Loss of these controls is a no-boot condition,not something to diagnose after energizing an unknown stack. No electrical timing guesses or casual mains intervention. Recovery proof is necessary but not a substitute for preventing panel damage.

## Conditional future milestones — not currently executable
Each milestone requires a concrete platform addendum with verified file paths/commands. These are engineering requirements and exit tests, NOT a fabricated recipe.

|Milestone / dependencies|Required artifact and first test|Exit / stop condition|
|---|---|---|
|M1 isolated reproducible build;G4|Pinned sources/toolchain/config;two clean builds;output hashes/logs;explain timestamps or deterministic normalization.|Reproduce defined artifacts or document/approve bounded nondeterminism;no unexplained downloads/secrets;no TV deployment.|
|M2 smallest boot;M1 + G5 + specific target-test approval|Minimal init/health instrumentation using documented route;logs captured through authorized interface;known rollback available.|No custom boot or image write until G3-V. Stable boot/liveness and bounded resource use;stop at any unknown power/panel behavior.|
|M3 panel/backlight + HDMI input;M2|Correct panel timing/backlight limits from exact hardware docs;input receiver path,EDID and normal HDCP compatibility.|Visible stable SDR input without unsafe drive/timing; licensed HDCP works or fail—not bypass. Do not guess electrical parameters.|
|M4 audio/remote/CEC;M3|Target adapters,volume/mute/routing,power button,input switching,CEC behavior,network handling tests.|Core AppleTV operation works without hidden service calls or loss of physical power control;network unavailable must not block basic display. Optional network support requires minimal exposed services,no undocumented listeners and a maintenance/update policy; leave network disabled if unsupported.|
|M5 HDR/4K and power/thermal;M4|Documented mode handling,colour-range/HDR metadata/audio sync,resume/standby and monitored load.|Only baseline-supported modes are mandatory;new capabilities not promised. No power-loss trial during write;unsafe thermal/power behavior stops tests.|
|M6 internal UI;M4 + owner feature selection|Small native UI for inputs/status/settings using documented adapters;no external HDMI compute dependency.|Usable with remote,clear unsupported states;not replacing goal with app-on-stockwebOS.|
|M7 maintenance/update/rollback;M5/M6|Documented hardware-supported update model,integrity verification,dependency/rollback test matrix.|A/B only if actual hardware/layout supports it;otherwise approved alternative or no update feature. No unsafe field-update claims.|

## Validation matrix — proposed acceptance, not measured capabilities
All target tests wait for approvals and gates; initial baseline is not proof target supports same mode. No automated button-send success is treated as UI-state acknowledgment.
|Test|Proposed acceptance|Evidence / backout|
|---|---|---|
|V01 identity/source association|Every required target field tied to artifact and source;no inferred SoC/board.|Identity/coverage review;block build/deploy if mismatch.|
|V02 SDR baseline|HDMI2 AppleTV stable picture and input selection at the actually observed baseline mode;no accidental stock HDR changes.|Before/after settings and observed mode;preserve original baseline record. Acceptance is stable correct-range SDR,not numeric setting equivalence or vendor Filmmaker picture-quality parity. Instrumented picture-quality parity is out of scope unless separately specified.|
|V03 panel safety|Documented panel/backlight settings only;no abnormal flicker,loss of sync,unsafe power/thermal indication.|Approved display observation +telemetry;immediate controlled shutdown/verified recovery on anomaly.|
|V04 HDMI/EDID/HDCP|AppleTV negotiates documented baseline SDR modes normally;no link training loops/blank content;normal authorized protected AppleTV playback required.|Mode/EDID capability evidence and playback observation;no circumvention.|
|V05 audio|Baseline route audible withmute/volume reliable;no persistent desync/dropouts;lip-sync tolerance specified from baseline before target comparison.|Record audio path and agreed observation method,not fabricated millisecond pass.|
|V06 remote/CEC|Physical power/input/navigation and required AppleTV CEC functions repeatable;no stuck keys/wrong-device actions.|Action/result trace and manual fallback.|
|V07 4K/HDR|Test only modes confirmed in baseline and exact-target specs;correct HDR signalling/colour range,with no claimed calibration equivalence.|Mode metadata and suitable test content;revert to verified SDR on failure. HDR calibration unchanged unless separately approved.|
|V08 reboot/suspend|Proposed20reboot and20standby/resume cycles with no failed wake/input/audio loss;owner approves cycle count before trial.|Cycle logs;stop at first failure and preserve logs. Count is proposed criterion,not measured reliability.|
|V09 sustained operation|Proposed2-hour normal-use soak with no crash,unbounded memory or documented thermal-limit breach.|Runtime/thermal observations;if sensors/limits absent,block unattended/loaded test. Duration is proposed,not performance estimate.|
|V10 loss-of-power handling|Only after independent recovery proof:controlled normal-state power-loss/restart test,never during write unless expressly approved on recoverable target.|Recovery/known-good artifacts available;failure freezes further target tests.|
|V11 updates/rollback|Only supported update scheme:failed candidate does not prevent recovery;unit data preserved.|Failure-case evidence on approved recovery target. No assumed A/B.|
|V12 source-tool safety|Malicious archive traversal,links,collision,oversize and malformed metadata rejected;hash changes detected.|Box-only fixture tests;never execute downloaded code to test metadata parser.|

## Approval scopes and stop/go summary
**Requestable first go (not yet granted): E1-box ONLY — desk-only boot/recovery research; normal public source metadata/download and SHA256; then bounded member listing and selected read-only text inspection using existing maintained general-purpose tools, only after Task2 pre-read safety checks pass. Local evidence records and this same Page are updated.** U0 deployment-no-go does not stop this explicitly proposed learning scope. Deliver a dated U0 finding, catalog manifest, bounded member index, README/config/license/dependency triage and updated unknown registry, not a complete BSP/coverage claim. No new owner permission per in-bounds file. Excluded: custom inventory code, nested expansion, raised ceilings, build/script/downloaded-code execution, TV actions, accounts, inquiries, hardware access, purchases or deployment. This edits the proposal, not the record of consent; nothing in E1 is executed during planning.
**Beyond-E1 archive work (formerly E2-box):** new scope/risk review only if needed for raised ceilings, nested expansion or broader extraction; do not request another approval merely to complete bounded E1 reading. No build/script execution. A failed safety checkpoint is a stop, not permission to weaken controls.
**E-tooling:** separate reviewed test-first executable addendum before custom inventory code; evidence code must implement rejection/limit tests before untrusted archive processing. It is box-only and does not select the OS architecture.
**E-TV-info:** separately authorized owner-performed normal information readout only; not automated TV navigation or playback tests.
**E-TV-baseline:** separately approved owner-operated AppleTV playback/audio/remote/CEC/power observations with exact profile; no resets/updates/calibration changes.
**PhaseB:** isolated box-only build after G1-target/G2b/G3-D and Task5 addendum/owner boundary approval; no TV action. G3-V validation may depend on the resulting artifact, but must pass before any target boot/write.
**PhaseR:** any recovery validation needing a matched spare target,purchase,hardware access or failure injection requires its own specific approval and risk case. No dependency loop authorizes tests on the primary TV to establish recovery.
**PhaseT:** target boot/deploy only after G3-V exact-operation recovery, G5 safety and specific operation/risk approval; broad go is insufficient. PhaseR validation cannot silently authorize primary-unit experiments.
Current blocked reasons:unknown actualboard/SoC/suffix/liveversion;sourcecontents/BSP/ABI uninspected;no lawful documented custom-boot route or independent recovery. None is resolved by AI confidence or catalog availability.

## Self-review and handoff requirements
- [x] Check design requirements map to tasks1–5,M1–M7,V01–V12; record uncovereditems as stop conditions.
- [x] Challenge architecture scope,identity assumptions,archive safety,licensing,boot/recovery independence and power/HDMI hazards with independent reviewers.
- [x] Reconcile advice against actual notice/official sources; do not promote reviewer memory to facts.
- [x] Save prompts/rawoutputs/outcomes and response-to-review; update same Page and chronological audit.
- [x] Report PLAN READY FOR APPROVAL, NOT FLASH READY; owner's go remains pending before implementation.

No schedule/cost estimates are asserted. Successful plan review cannot guarantee a compatible boot route exists.

## Review reconciliation (2026-11-08, Atlantic/Reykjavik)
Claude Opus5.5 high and Codex high independently reviewed the ORIGINAL staged plan,not a generic prompt. Raw prompts and outputs preserved in plan-reviews/. Accepted corrections:explicit inactive execution header;earlyU0 no-go screen;retained/replaced ledger and A-K/A-H/B-same/B-new distinctions;no unproven A boot advantage;protected playback mandatory;source/parser limits;split approvals;pre-M2 safety gate;external-controller/radio dependencies;separate recovery proof levels,equivalence,restore/log prerequisites;picture-quality baseline scope;networksecurity;identity/source-change invalidation. No new hardware/source fact is inferred from AI reviews. Specific technical claims remain tied to design sources/notice. Gemini high-tier focused review completed exit0 in112.59 seconds (330-second bound),actual result captured. Accepted:new binary-supply evidence ledger;E1 download/hash separated from E2 parsing;a secondary-board recovery test cannot waive primary-unit unique-data preservation;early safe non-invasive telemetry required. Rejected as unverified hardware claims:actual secureboot/dm-verity/TEE/RPMB arrangement;actual private-driver interfaces;guaranteed absence of vendor components from UNINSPECTED archives;universal impossibility or permanent identity failure. Treat these only as dependency questions,not facts. All three reviews challenged original revision;no claim of unanimous approval of final edits.

### Exact proposed first approval text
“Approve E1-box evidence research only: public source metadata/download and hashes; desk-only boot/recovery research; and, after recorded pre-read safety checks pass, bounded member listing and selected read-only text inspection with existing maintained tools. Complete this learning scope even if deployment is no-go; update local records and this same Page. No custom code, raised ceilings, nested expansion, builds, downloaded-code execution, TV actions, hardware access, purchases, inquiries or deployment.”
This is a proposed request,not recorded consent. Normal TV information can be supplied in a separately authorized owner-performed E-TV-info session. An architecture preference may be recorded now,but no architecture is selected by approving E1.

## Enhancement review — 2026-11-08, Atlantic/Reykjavik
Supersedes prior E1/E2 split as a PROPOSAL ONLY: bounded reading is now inside E1 after recorded safety checks; no owner go has been granted. Historical review entries above remain unchanged as chronology, not current authority. Current review artifacts: `plan-reviews/2026-11-08-0400-opus-astra/`. Opus5.5 high full technical review returned a refusal despite CLI exit0; it did not supply findings. A genuinely narrower editorial-only Opus5.5 high review succeeded and led approval/coherence corrections. Astra gpt-6-astra high independently reviewed the same original full revision, reported that exact model/effort and supplied two findings. Neither establishes hardware feasibility. Candidate adjudication and final hashes are recorded separately in that review folder.
