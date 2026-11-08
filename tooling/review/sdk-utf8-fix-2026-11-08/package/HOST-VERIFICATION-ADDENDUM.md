# Read FIRST — host verification of UTF8 fix candidate
2026-11-08T13:05:58.148599+00:00 Atlantic/Reykjavik. Parent independent review PENDING; no self-approval.

## Current outcome
- Synthetic GNU_FORMAT fixed-name/longlink boundary defect reproduced using maintainedtarfile writer:99ASCII+U+0100 means100bytefixedfieldends0xc4beforevalidextendedUnicode substitution. This is syntheticproofONLY;actualSDK failingfield/offset/cause remainsunknown,notcorruptionfinding.
- Newtestsbeforecodeedit:package/red.log,6methods/18productionUnicodeDecodeErrors acrosssubtests (notfixture/importtypos). TargetedGREEN6methodsPASS. Completecommands/outputs/exitJSONretained.
- CodexnestedSDKsuite:41methods,exit0,10EPERMskips(3methods+7stdio subtests);recordedhonestlyinpackage/sdk-suite.log.
- ActualhostunchangedSDK-onlysuite: **41/41methodsPASS,0skips**,2.000stest/2.098sexternal,exit0. ../host-sdk-suite.txt preservesexactcommand/fulloutput. ../host-fd-evidence/normal.json+high.json assertnoinheritedFDs,parentwalk,writablereopens,includingFD256/257. ../host-stdio-evidence/mask-1..7.json allPASS/stdinDEVNULL. These supersedeONLYhostverificationpendingwordinginmodelpacket,notindependentreviewpending.
- Readercandidatee70f683abf7597f16d54f15c1f7e86d10be873dda9b0c6f95d881000c7047ba4;newUTF8test746defc12bdcfa73f211eaad30ba8e349bb70eda8a40e9ed5bbb9ab12a4c3d58. Launcherunchanged2a6638e3439748a6dc4fb7237a03c3d05521685746df5315683c861acab9ca52;other3SDKtestsbyteunchanged. Wholefilesandbefore/currenthashesinpackage/current/andbefore/;completeproduction/testdiffpackage/change.diff.
- Onlyrawfixedname/linkdecodeusesbyte-preservingsurrogateescapeuntilmaintainedGNU/PAXsubstitution;rawowner/groupandextensionbodydecodingstrict;FINALresolvednames/links/owners/PAXmetadataUTF8strictbeforeemit. Transientrawname/linkbyteschargedwithsurrogateescape,notreplacement/loss;normalmetadatachargesunchanged. Path/traversal/absolute/escapinglinks/duplicates/types/sparse/pins/EOF/drain/caps/fd/stdio/XZ/symlinkpoliciesunchanged. No customtarheaderparser.

## Scope / review handoff
OneprimarysubscribedCodexcallexplicitgpt-6.1-sol/high237.849s,exit0,no refusal/fallback/reset. JSONeventstreamdoesnotindependentlyexposemodelID;prompt/raw/events/runusagepreservedonelevelup. No redundantmodelreview,parentresumesindependentreviewer.

ActualSDKpartialfrom07:09wasintegratedintoPage,ledgers,REPRODUCING/playbook/feasibilityaftert77resume. Generatedmetadataonly;NOnewactualSDK/sourcecontentread/hash/parse/re-run,installer/compiler/sourceexecution/build/download/TVaction. Oldoutputunchanged andmustNOTbereused/deleted. EarlierChromium200kandadaptation64MiBstopsunchanged. Originalreview/failureartifactsretained.

Readreview-packet.md,contract.md(onelevelup),change.diff,red/greenlogs,currenthashesandhostproof;parentindependentSPEC/QUALITYreviewrequirednewreaderhash. Anyfuturerealphaseusesfreshoutputandexplicitparenthandoffafterreview,notautomaticretry/budgetreset. Candidatefutureoutputnameonlyinspection-metadata-utf8-PENDING-REVIEW;notcreated/executed. SDKcompatibility/compiler/ABI/license/unit/boot/recoveryremainunproved.
