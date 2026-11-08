# Community SDK acquisition and bounded static assessment
2026-11-08T06:15:43.302057+00:00 · Atlantic/Reykjavik

## Acquired files
All3publicGitHubassetsHTTP200,regularfilesmode0644.Publicreleaseassetsdigestnull;localfingerprintsarenotLGauthentication.NoSDKinstallerorarchivepayloadexecuted/parsed.
|Asset|Bytes|SHA256|
|---|---:|---|
|native_sysroot_dependencies.tar.gz|8017931|f97498cc24de8a617be8e842962e30299be034730981ac8da0e216548a92f48a|
|starfish-sdk-x86_64-ca9v1-toolchain-5.0.0-20191125.sh|166821312|3029c64809fe93e6fe6bfb72ac9de6ec556452a0790feb0f9b23abed409e669b|
|target_sysroot_dependencies.tar.gz|323786694|b5bbe22da19a9fabea1f24cc1965e5a853e9d2935e9e5bdfcd81d7c83174f39b|
Total498625937Bof20GiBbudget;remaining20976210543B. PublicURLs,exactcurlcommands/status/versions/timing,communitycatalogclaimandlocalpaths:`acquisition-manifest.json` / `acquisition/`.NotrequiredMarch20190307version;candidateNovember20191125isstillusefulfordata-onlycomparison,notprovenreplacement.

## Prefix/header facts
- PubliccommunityassetsacquiredHTTP200,regular0644,exactexpectedbytecounts,streamSHA256;noofficialreferencehashes.
- SDKheaderdeclaresx86_64hostand5.0.0-20191125defaultpath/title;expectedenvironmentfilenameca9v1-starfishmllib32-linux-gnueabi.
- SDK_GCC_VERempty;INST_GCC_VERuseshostgcc;bundledcompiler/binutil/glibc/sysrootversionsnotidentified.
- No license/copyright/SPDXtextin358-lineheader;payloadlicensingunknown.
- ObservedliteralMARKERline10812–10819,nextbyte10820beginsfd377a585a00;headeruses tar tvJ/tar xJ aftermarker. ExpectedXZ-compressedtar,notvalidatedarchive.
- Native/targetassetprefixesbegin1f8b08:gzipmagiconly,nogzip/tarintegritychecked.
- 166810492rawbytesremainafterSDKmarker;notclaimsinglevalidXZstream,nortrailingbytepolicyresolved.
- Headerwouldexecuteenvironment/hostcommandsbeforeoptionhandlingandpayloadrelocationscripts;noargumentsafeexecutionassumed. Installerneverrun.

Maximum262144Bperfileobserved;binaryprefixesandtheirSHAinprefix-assessment/. `file`utilityabsent(exit127),notinstalled;explicitlyallowedPythonboundeddatareadsused. No decompression/gziptest/XZtest/tarlisting. Header358lines/10820B includingliteralmarker;firstSDKpayloadbytesXZmagic. HeaderfileSHA25616f25f603c54a796a5c69d65ed085cc63c73f5962fa8ed5fc65e6b54f65cf07e.

## Exact header citations
- Lines1–9: '#!/bin/sh\n\n[ -z "$ENVCLEANED" ] && exec /usr/bin/env -i ENVCLEANED=1 HOME="$HOME" \\\n\tLC_ALL=en_US.UTF-8 \\\n\tTERM=$TERM \\\n\tICECC_PATH="$ICECC_PATH" \\\n\thttp_proxy="$http_proxy" https_proxy="$https_proxy" ftp_proxy="$ftp_proxy" \\\n\tno_proxy="$no_proxy" all_proxy="$all_proxy" GIT_PROXY_COMMAND="$GIT_PROXY_COMMAND" "$0" "$@"\n[ -f /etc/environment ] && . /etc/environment'
- Lines26–30: 'INST_ARCH=$(uname -m | sed -e "s/i[3-6]86/ix86/" -e "s/x86[-_]64/x86_64/")\nSDK_ARCH=$(echo x86_64 | sed -e "s/i[3-6]86/ix86/" -e "s/x86[-_]64/x86_64/")\n\nINST_GCC_VER=$(gcc --version | sed -ne \'s/.* \\([0-9]\\+\\.[0-9]\\+\\)\\.[0-9]\\+.*/\\1/p\')\nSDK_GCC_VER=\'\''
- Lines32–57: 'verlte () {\n\t[  "$1" = "`printf "$1\\n$2" | sort -V | head -n1`" ]\n}\n\nverlt() {\n\t[ "$1" = "$2" ] && return 1 || verlte $1 $2\n}\n\nverlt `uname -r` 3.2.0\nif [ $? = 0 ]; then\n\techo "Error: The SDK needs a kernel > 3.2.0"\n\texit 1\nfi\n\nif [ "$INST_ARCH" != "$SDK_ARCH" ]; then\n\t# Allow for installation of ix86 SDK on x86_64 host\n\tif [ "$INST_ARCH" != x86_64 -o "$SDK_ARCH" != ix86 ]; then\n\t\techo "Error: Incompatible SDK installer! Your host is $INST_ARCH and this SDK was built for $SDK_ARCH hosts."\n\t\texit 1\n\tfi\nfi\n\nif ! xz -V > /dev/null 2>&1; then\n\techo "Error: xz is required for installation of this SDK, please install it first"\n\texit 1\nfi'
- Lines59–62: 'DEFAULT_INSTALL_DIR="/opt/starfish-sdk-x86_64/5.0.0-20191125"\nSUDO_EXEC=""\nEXTRA_TAR_OPTIONS=""\ntarget_sdk_dir=""'
- Lines98–120: '\t\techo "Usage: $(basename $0) [-y] [-d <dir>]"\n\t\techo "  -y         Automatic yes to all prompts"\n\t\techo "  -d <dir>   Install the SDK to <dir>"\n\t\techo "======== Extensible SDK only options ============"\n\t\techo "  -n         Do not prepare the build system"\n\t\techo "  -p         Publish mode (implies -n)"\n\t\techo "======== Advanced DEBUGGING ONLY OPTIONS ========"\n\t\techo "  -S         Save relocation scripts"\n\t\techo "  -R         Do not relocate executables"\n\t\techo "  -D         use set -x to see what is going on"\n\t\techo "  -l         list files that will be extracted"\n\t\texit 1\n\t\t;;\n\tesac\ndone\n\npayload_offset=$(($(grep -na -m1 "^MARKER:$" $0|cut -d\':\' -f1) + 1))\nif [ "$listcontents" = "1" ] ; then\n    tail -n +$payload_offset $0| tar tvJ || exit 1\n    exit\nfi\n\ntitlestr="webOS TV SDK installer version 5.0.0-20191125"'
- Lines130–138: '# SDK_EXTENSIBLE is exposed from the SDK_PRE_INSTALL_COMMAND above\nif [ "$SDK_EXTENSIBLE" = "1" ]; then\n\tDEFAULT_INSTALL_DIR="~/starfish_sdk"\n\tif [ "$INST_GCC_VER" = \'4.8\' -a "$SDK_GCC_VER" = \'4.9\' ] || [ "$INST_GCC_VER" = \'4.8\' -a "$SDK_GCC_VER" = \'\' ] || \\\n\t\t[ "$INST_GCC_VER" = \'4.9\' -a "$SDK_GCC_VER" = \'\' ]; then\n\t\techo "Error: Incompatible SDK installer! Your host gcc version is $INST_GCC_VER and this SDK was built by gcc higher version."\n\t\texit 1\n\tfi\nfi'
- Lines186–186: 'if [ -e "$target_sdk_dir/environment-setup-ca9v1-starfishmllib32-linux-gnueabi" ]; then'
- Lines234–235: 'printf "Extracting SDK..."\ntail -n +$payload_offset $0| $SUDO_EXEC tar xJ -C $target_sdk_dir --checkpoint=.2500 $EXTRA_TAR_OPTIONS || exit 1'
- Lines241–262: 'for env_setup_script in `ls $target_sdk_dir/environment-setup-*`; do\n\tif grep -q \'OECORE_NATIVE_SYSROOT=\' $env_setup_script; then\n\t\t# Handle custom env setup scripts that are only named\n\t\t# environment-setup-* so that they have relocation\n\t\t# applied - what we want beyond here is the main one\n\t\t# rather than the one that simply sorts last\n\t\treal_env_setup_script="$env_setup_script"\n\tfi\n\t$SUDO_EXEC sed -e "s:/opt/starfish-sdk-x86_64/5.0.0-20191125:$target_sdk_dir:g" -i $env_setup_script\ndone\nif [ -n "$real_env_setup_script" ] ; then\n\tenv_setup_script="$real_env_setup_script"\nfi\n\nif ! xargs --version > /dev/null 2>&1; then\n\techo "xargs is required by the relocation script, please install it first. Abort!"\n\texit 1\nfi\n\n# fix dynamic loader paths in all ELF SDK binaries\nnative_sysroot=$($SUDO_EXEC cat $env_setup_script |grep \'OECORE_NATIVE_SYSROOT=\'|cut -d\'=\' -f2|tr -d \'"\')\ndl_path=$($SUDO_EXEC find $native_sysroot/lib -name "ld-linux*")'
- Lines281–305: 'for py in python python2 python3\ndo\n\tPYTHON=\\`which \\${py} 2>/dev/null\\`\n\tif [ \\$? -eq 0 ]; then\n\t\tbreak;\n\tfi\ndone\n\nif [ x\\${PYTHON} = "x"  ]; then\n\techo "SDK could not be relocated.  No python found."\n\texit 1\nfi\n\\${PYTHON} ${env_setup_script%/*}/relocate_sdk.py $target_sdk_dir $dl_path $executable_files\nEOF\n\n$SUDO_EXEC mv $tdir/relocate_sdk.sh ${env_setup_script%/*}/relocate_sdk.sh\n$SUDO_EXEC chmod 755 ${env_setup_script%/*}/relocate_sdk.sh\nrm -rf $tdir\nif [ $relocate = 1 ] ; then\n\t$SUDO_EXEC ${env_setup_script%/*}/relocate_sdk.sh\n\tif [ $? -ne 0 ]; then\n\t\techo "SDK could not be set up. Relocate script failed. Abort!"\n\t\texit 1\n\tfi\nfi'
- Lines343–358: 'post_relocate="$target_sdk_dir/post-relocate-setup.sh"\nif [ -e "$post_relocate" ]; then\n\t$SUDO_EXEC sed -e "s:/opt/starfish-sdk-x86_64/5.0.0-20191125:$target_sdk_dir:g" -i $post_relocate\n\t$SUDO_EXEC /bin/sh $post_relocate "$target_sdk_dir" "/opt/starfish-sdk-x86_64/5.0.0-20191125"\n\t$SUDO_EXEC rm -f $post_relocate\nfi\n\necho "SDK has been successfully set up and is ready to be used."\necho "Each time you wish to use the SDK in a new shell session, you need to source the environment setup script e.g."\nfor env_setup_script in `ls $target_sdk_dir/environment-setup-*`; do\n\techo " \\$ . $env_setup_script"\ndone\n\nexit 0\n\nMARKER:'

## Review reconciliation
- Hostkernelpredicatepermits3.2.0,despiteerrorstring>3.2.0;primary/Geministrictgreaterclaimrejected.
- HeaderindicatesSDKhostandtargetlabels—notactualTVhardwareorpayloadcompilercontents.
- DoNOTfollowGeminiinventorygznow suggestion:currenttaskstaticassessmentONLY;allpayloadinventorydeferredtotestedreaderphase.
- No upfrontrequirementthatlaterSDKmustbeABI-identical;validatedcompatibility/API/ABIchecksneeded,nocompatiblealternativecurrentlyproved.

MainOpusrequested5.5high53.499s reportedONLYclaude-opus-5-5,safety_stops0,is_errorfalse. Codexactualgpt-6.1-sol/high37.410s;Gemini requestedgemini-4-argon-high84.049s,noindependentactualmodelidentifier.All3returnedsubstantiveexit0,norefusal/timeout/operatorfallback.Sourcequotescheckedagainstheader. Rawpackets/outcomes:`plan-reviews/2026-11-08-sdk-acquisition/`.

## Readiness and boundary
- Localhashesfingerprintcommunitydownloads,notLGauthentication.
- March20190307versusNovember20191125compatibilityunproved.
- No SDKinstallation,sourceexecution,build,payloadparse,TVaction or productiontoolchange.
- Bootpackaging/aux/hardware-settinggaps,unitidentity,legitimateboot/recoveryremainunresolved.
CurrentmaintainedinventoryreaderforcesgzipandcannotadmitthispinnedselfextractingSDKslice/XZpayloadunchanged. Noinstaller--help/-l/unpackinvocationispermitted. Exactminimumnewformatadapterandtestsarein`handoff/sdk-static-inventory-reader-requirements.md`;parentcoordination—notanownerpermissionpause. No productioncodeeditedhere.
