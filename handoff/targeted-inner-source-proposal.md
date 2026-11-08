# Targeted inner-source proposal — HISTORICAL DECISION ARTIFACT

**Status (2026-11-08 05:06 Atlantic/Reykjavik):** retained as the written proposal that framed this work. It is **not** the executable contract and must not be read as authorizing libkadaptor or a three-package inner scan.

Owner t68u (quoted in full): `Continue`

Parent adopted **CORE TWO ONLY** (kernel + bootcode) after stating that targeted kernel/bootcode/adaptor inspection required a reviewed new scope and was paused. Optional `soc/libkadaptor-1.0.0-908.3.tar.gz` is **not** in the approved allowlist.

Executable contract: `docs/superpowers/plans/2026-11-08-targeted-core-two-phase.md`.
The Chromium/all-three outer inventory PARTIAL at 200000 members remains recorded and is not retried by this phase.

Original proposal text follows unchanged for provenance.

---

# Targeted inner-source proposal — FUTURE / UNAPPROVED

2026-11-08 05:03 Atlantic/Reykjavik. Plan/documentation only. No new source-processing authority is inferred or used. No code, binary copy, inner listing or extraction created/performed by this proposal. Parent handles any owner scope decision.

## Decision proposed
Approve a separately bounded, reviewed **targeted kernel/boot-code evidence investigation**, NOT a retry/resume of the capped all-three outer inventory. Core targets are exactly the kernel and bootcode paths named below (table order does not select scope); optionally include exactly `libkadaptor` in the same explicitly chosen scope. Do not include Chromium,otherpackages or automaticrecursive dependencies. No prompts per in-bounds member once that whole targeted phase is approved and its reader passes review.

## Why a new objective and feature are necessary
The prior single all-three invocation is permanently recorded PARTIAL at200,000members; its incomplete Chromium inventory stays incomplete. Archives1/2 outer lists completed, revealing kernel/bootcode candidates. The new question is “what build/platform/license documentation is physically inside these specifically identified packages?”,not “finish the remainingChromium tree with freshcounters”. This proposal does not authorize dropping/rescanninginputs to evade that original aggregate stop. It requires explicit new authorization for a distinct binary-materialization + single-level inner metadata task, separately budgeted and reviewed. If not granted, only generatedmetadata analysis continues.

All identified targets reside in completed archive2 `webOS 6.0 KLP_1.0_2.tar.gz`,511,945,894bytes, originalSHA256 `95894dd81e2bb32fd1ced1eb119698f2e1464e6b9b5b5879ea51528d7d5e8832`. Existingindex has names,ordinals,sizes,payloadhashes—not physical or gzip offsets. Any future materialization therefore needs one verified forward outer read,not invented randomaccess coordinates.

|Exact target member|Observed compressed payload bytes|Already observed payload SHA256|
|---|---|---|
|`soc/libkadaptor-1.0.0-908.3.tar.gz`|123,840,909|`46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25`|
|`soc/kernel-1.0.0-711..4.tar.gz`|170,350,960|`110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962`|
|`soc/bootcode-1.0.0-1099.7.tar.gz`|12,014,324|`b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e`|

Core kernel+bootcode total182,365,284bytes. Including optional libkadaptor totals306,206,193bytes. Current safe-plaintext selector is NOT a binary copier: kernel170,350,960bytes exceeds16MiB;libkadaptor123,840,909bytes also exceeds16MiB;bootcode12,014,324bytes is below16MiB but is a nested compressedbinary,not admitted plaintext. Neither the extension nor its size makes it eligible for the current selector. No existing flag or README example is an authorized way to copy them.

## Proposed narrow limits (NOT adopted current limits)
The future executable addendum must specify and test these as a closed-phase contract before it runs. It may tighten limits; it must not silently increase them if realinputdoesn'tfit.

|Control|Proposed bound and meaning|
|---|---|
|Outer source input|Exactly the one archive2 above; regular/no-follow RO input,compressedsize<=512MiB(536870912bytes),expectedhashmatch. No archive1/3 rescan.|
|Binary-copy allowlist|Exactly kernel+bootcode;libkadaptor ONLY if explicitly included in owner scope. No wildcardcopy or “all soc” expansion.|
|Copied binary package ceilings|<=200MiB(209715200)each;<=320MiB(335544320)combined. Exactobservedsizes/hashes still mandatory,not merely belowcap.|
|Combined admitted compressed artifact sizes|Outerinput + all copied nestedinputs <=1GiB(1073741824). Optional-fullset observed818152087bytes;core694311178bytes. This counts admittedartifactbytes,not a guarantee of elapsedI/O; all reads/hashwork also count towardphasewall.|
|Nesting depth|One controlled level only: materialize allowlisted outer tar.gz payloads,then admit their inner metadata/plaintext. Further archives within them are metadata-only,never expanded.|
|Members / pathname-metadata|200000members and100000000pathname/metadata bytes TOTAL across outer validation/copy + all permitted inner inventories. No resets perpackage and no reuse of the old run as if complete.|
|Expanded / materialized accounting|<=4GiB(4294967296)combined charged bytes across outerdecompressedstream,stagedbinarycopies,innerlogicalexpanded data and selectedplaintext (conservative,doublechargecopieswhereapplicable). Outerdecodedstream itself <=640MiB(671088640). Limitfit unproven until future reviewedrun;stopifnotfit.|
|Plaintext selection|Unchanged <=16MiB(16777216)per safe regular plaintext;additional<=64MiB(67108864)combined. Only README/build/config/board/license/manifest evidence after path/type/link/duplicate checks. No sourceexecution.|
|Time and memory|120s TOTAL controlled phasewall,includinghash/copy/innerwork,not120s perpackage. 1GiBAS for isolated parserprocess,notRSS/cgroupguarantee. Futureimplementation must demonstrate aggregatephase deadlines and resourcebackstop.|
|Disk|>=10GiBfree reserve checkedbeforephaseandbeforematerialization/selectedwrites;chargedoutputboundedabove. This is guardedobservation,not filesystemreservation.|
|Isolation|NarrowROinputs/runtime,explicitoutputonly,home/credentials hidden,networknamespace disabled,clearedenvironment. noexecmount remainsFALSE unless independentlydemonstrated;permissionbitsnever treatedasnoexec. Neverexecute binaries or selectedtext.|

The200MiB binary mode is a NEW type-specific feature needing explicit permission/review,not a raise of the current16MiB plaintext limit. Other numeric proposals are at or below the earlier broader caps; that does not by itself authorize a new invocation. The previous whole-three partial result and its200000counter remain unchanged in all records.

## Required tested mechanism and provenance before admission
1. Write a narrowly scoped executable tooling addendum only after owner approves the proposed objective/allowlist. No generic extractor, newtarimplementation or toolinstallation. Use maintainedparserAPIs with existingisolation.
2. Add regression/adversarial syntheticfixtures first: exactbinarycopywithlength+hash;NUL allowed ONLY for the closed binary mode (plaintext staysNULfree);oversize/offallowlist rejection;hash/size mismatch;path/link/type/duplicatecollisions;singleleveldepth;aggregatecompressed/expanded/member/deadlinebudgets;stopentirephase;outputcontainment;incompleteoutputnevercomplete;diskfailure;PAX/GNU allocationbackstop. No productionLGinputs during tooldevelopment.
3. Independentreview and hashpin newreader/launcherrevision. Existingcleanre-review applies to currentmetadata/plaintext version,not a futurebinaryfeature. Document actualnoexec/AS/diskresiduals honestly.
4. In future approved phase only, verify outerrawhash/provenance andexactallowlistednames/types/sizes;copybytes to explicit non-executable-mode datafiles withoutinterpreting them;verify eachpayloadhash against the existingindex BEFORE any innerparsing. Preserve outercatalog -> outerhash -> membername/ordinal -> memberhash -> copiedfilehash -> innerpaths/bodycitations. No offsets guessed.
5. Inner-list admittedpackages under ONE sharedbudget,not a series of freshbudgetruns. Select only validated bounded plaintext relevant to kernelconfig/boardmapping/buildtoolchain/licensing. Storequotationswithpath/line/hash;don'texecute scripts or follow instructions embeddedinREADME. Stopall furtherinputs on partial/failed/timeout/policyerror.

## Acceptance and exclusions
Useful outcome may be an identified board/config/toolchain/builddoc or a precisely documented missing dependency. A successful inner inventory still does not prove compatibleBSP,actualunitSoC/runningkernel,customimageacceptance,boot/recovery or workingpanel/HDMI. kdriver and libkadaptor remain different names until source evidence establishes anyrelationship.
No Chromium rescan;no whole-three inventoryretry;no recursive thirdlevel;no randombinarycopy;no fresh source/firmware downloads;no newpackages;no build/configure/sourceexecution;no TV/hardware/account actions;no privateAPI/exploit/signature/key handling;no inquiries,purchases,deployment. Board/panel/uniqueunitcalibration/recovery evidence remains mandatory before any targetexperiment. This proposal is a decision artifact,not implementationapproval or an executable recipe.
