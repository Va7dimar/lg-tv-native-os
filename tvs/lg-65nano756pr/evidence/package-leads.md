# Package leads from existing outer metadata only

2026-11-08 05:02 Atlantic/Reykjavik. **No original archive read, rehash, nested expansion or source execution in this stage.** The original invocation remains PARTIAL at200,000aggregate members. First two outer lists are complete; archive3's199,863Chromium79 entries are an incomplete prefix. This is a filename/payload-hash inventory,not a source-content/BSP inventory.

## Capability clusters (heuristic filename grouping only)
|Cluster|Packages|
|---|---|
|graphics/UI/input filename leads|10|
|media/audio/video filename leads|20|
|radio/network filename leads|17|
|other upstream package names (purpose not established here)|62|
|runtime/boot-userspace/system filename leads|14|
|build/development/observability filename leads (NOT a target SDK)|9|
|kernel/boot/hardware-adaptation filename leads|3|

Counts total135regular nestedpackages; plus2directories =137entries in the two completed outer lists. Each row records archive/index/hash chain and confidence in JSON. No physical outer offset was captured; a member ordinal is NOT a compressed seek offset. Do not invent random-access coordinates.

## Evidence interpretation
- `soc/kernel-1.0.0-711..4.tar.gz`170,350,960bytes; `soc/bootcode-1.0.0-1099.7.tar.gz`12,014,324bytes; `soc/libkadaptor-1.0.0-908.3.tar.gz`123,840,909bytes are the best narrowly targeted package leads. All remain unopened nested tar.gz payloads.
- Actual media/radio companions:`soc/gstreamer-1.0.0-2089.tar.gz`136,115,594bytes and `soc/r_8812_wifi_driver.tar.gz`79,725,513bytes. Names do not identify this TV's installed SoC/radio or prove driver support.
- Common packages include PulseAudio/ALSA, Qt/Wayland, systemd, Bluetooth/DVB names. They suggest where to investigate functionality,not a complete implementation chain.
- Build/development names include libtool and QtCreator; glibc is a runtime name,not a compiler. No dedicated target crosscompiler SDK, outerREADME/build/config document or exact candidateboard ID was identified in these completed outer lists. Innercontents and remainingarchive3 may differ; no absence claim there.
- Notice `kdriver`id103 is not an exact outer package name; `libkadaptor` is only a distinct adaptation candidate. Notice kernel label4.4.84-711.kalaupapa.4 versus actual filenamekernel-1.0.0-711..4 is a correlation lead,not version equivalence,board mapping or observedrunningkernel.

## Complete first-two-archive table
Observed hashes are payload fingerprints already computed by the admitted outer inventory. They do not authenticate vendor origin,validate nestedarchive structure or reveal inner source.

|Archive suffix / ordinal|Exact member path|Type / bytes|Observed payload SHA256|Cluster|
|---|---|---|---|---|
|1.tar.gz / 0|`common`|dir / 0|not applicable|directory|
|1.tar.gz / 1|`common/qtbase.tar.gz`|file / 125898573|52df01adf240ba1a46fc3634047e833c0ced50ad88a196d58b15ffff6156ff51|graphics/UI/input filename leads|
|1.tar.gz / 2|`common/sbc-1.3.tar.gz`|file / 722580|acec9b96b7da2801c74378400dea99cfbc7c0527283111667c1fb921c4608c1c|media/audio/video filename leads|
|1.tar.gz / 3|`common/libwebsockets-3.0.0.tar.gz`|file / 7554712|96337f1ba0bd75a34e7e863ae27c36ae166c1f011400d234d82167be4d6c1621|radio/network filename leads|
|1.tar.gz / 4|`common/pulseaudio-9.0-webos-open.tar.gz`|file / 340038142|14dfcf08b9dff1fa88b7ad5bec9fb36051030490bea6f89988e7b2c8db1f9d8f|media/audio/video filename leads|
|1.tar.gz / 5|`common/kbd-2.0.4.tar.gz`|file / 2776920|dbd5091002bb5a08b07314fdecda2695b22e20aea6f3ae9ff824eb0781a39382|other upstream package names (purpose not established here)|
|1.tar.gz / 6|`common/libwebsockets-alibaba.zip`|file / 10418678|eb23012886e29cd2dc15327ebef3045c8bee6661756ba16d5d2dcd9b41d20d1d|radio/network filename leads|
|1.tar.gz / 7|`common/libsigc++-2.10.0.tar.gz`|file / 5517082|66667bf10d03e2d443dd2fa4feb74d6af179e889706156c0e517fa356fc52e66|other upstream package names (purpose not established here)|
|1.tar.gz / 8|`common/libsndfile-1.0.28.tar.gz`|file / 1944236|258cb37879ad79dfca5797339bc3df324fd138edb8896951e1888eecdc9bf11e|media/audio/video filename leads|
|1.tar.gz / 9|`common/taglib-1.10.tar.gz`|file / 1254958|fc55cf4fb017c604e144034cbcfdaaad7e8858b15159920e4b56f4dc0bfcb67f|other upstream package names (purpose not established here)|
|1.tar.gz / 10|`common/shadow-4.6.tar.gz`|file / 4356445|74482b01cfd02d59125ec075686ea320d8ffde34ba5219296a1674b77616efd7|runtime/boot-userspace/system filename leads|
|1.tar.gz / 11|`common/libsoup-2.62.3.tar.gz`|file / 3154048|a325ad97e4b5df5e50b3e8b98b49e5c11d7b38167ac8f5b4016dfef3616c6032|radio/network filename leads|
|1.tar.gz / 12|`common/glibc-2.28.tar.xz`|file / 16484344|b1900051afad76f7a4f73e71413df4826dce085ef8ddb785a945b66d7d513082|runtime/boot-userspace/system filename leads|
|1.tar.gz / 13|`common/busybox-1.29.3.tar.gz`|file / 16449090|ef12f661eb65a86027e002dd5ec90079460c49320c09887e13b125f4ce501621|runtime/boot-userspace/system filename leads|
|1.tar.gz / 14|`common/lttng-tools-2.9.11.tar.bz2`|file / 1165109|2c45144acf8dc6fcd655be7370a022e9c03c8b7419af489c9c2e786a335006db|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 15|`common/LVM2.2.02.180.tar.gz`|file / 26198509|ee5f87d2e04dce838ca60e0674b49b66934c14febd180ee5669ec7761693fc25|other upstream package names (purpose not established here)|
|1.tar.gz / 16|`common/tar-1.17.tar.gz`|file / 3357449|38721d85f0f8405132bda9ab3ec656d9356593c66366877717a53186e34cac93|other upstream package names (purpose not established here)|
|1.tar.gz / 17|`common/alsa-utils-1.1.6.tar.gz`|file / 1837419|5ec8c36d7364d0b9a09641cc654b4d6f8b52db9fa2342b8cda2a900b702aae0e|media/audio/video filename leads|
|1.tar.gz / 18|`common/systemd-1_239.tar.gz`|file / 8215223|7738ddda6a44bd113909ee74672b58bf8703f932f5631b838064a0c329abf388|runtime/boot-userspace/system filename leads|
|1.tar.gz / 19|`common/libtasn1-4.13.tar.gz`|file / 2585416|68ea7a35069d2a18d6eb19358a0f739108e23f7ee1e6db7043acd0b69581962b|other upstream package names (purpose not established here)|
|1.tar.gz / 20|`common/lttng-modules-2.10.9.tar.bz2`|file / 304170|a1855bbd02d0f71ebd180e9872309862036624f012442ab9cc5852eb60340145|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 21|`common/pacrunner-0.9.tar.gz`|file / 864273|28f63250ca8788a343455b5059b529f2d98755360dd663611e9365fb63e7312d|other upstream package names (purpose not established here)|
|1.tar.gz / 22|`common/libdaemon-0.14.tar.gz`|file / 971553|c09beee3b088828630167e3d5ee008bf930f8bc342f54b7f933f271e23b8e36b|other upstream package names (purpose not established here)|
|1.tar.gz / 23|`common/sg3_utils-1.42.tar.gz`|file / 5846363|c519d187e4f49cd198d6f8a4203e3bffaed5381931e6353d459c24a4edfa87d5|other upstream package names (purpose not established here)|
|1.tar.gz / 24|`common/iputils-s20180629.tar.gz`|file / 810618|bafc2be78c58e7d3d9b2d1dcba555027de33128e626def24e6757f0bb0a28557|radio/network filename leads|
|1.tar.gz / 25|`common/mpg123-1.25.10.tar.gz`|file / 1669283|a0bfd9c52e1c15d02407f4cb39dbc1cc07a0b799302d8436312620c0711a6769|media/audio/video filename leads|
|1.tar.gz / 26|`common/gzip-1.3.12.tar.gz`|file / 776331|0f4545473d1ea00c05dbd0de969de89787faee49a0ecf4ae9917e3e4105b5f65|other upstream package names (purpose not established here)|
|1.tar.gz / 27|`common/nettle-2.7.1.tar.gz`|file / 1916084|19e4c48f8dae9afdb16e06ab95d1ab7e50532b359945e80fb86943b358b307cb|other upstream package names (purpose not established here)|
|1.tar.gz / 28|`common/libmikmod-3.3.6.tar.gz`|file / 1829234|cb3f6259b3cb6f61eb3393fb842b4d01eb39efb751822425bb0b49acc9a33b0b|media/audio/video filename leads|
|1.tar.gz / 29|`common/libusb-1.0.22.tar.gz`|file / 1284097|ac3e4155aff446b40cae923b5dfec6e29b0cdd68a2e2be30e2ba97366f156ed1|radio/network filename leads|
|1.tar.gz / 30|`common/xnu-1228.9.59.tar.gz`|file / 7927503|b3f063b98ddd59f092b48c26c2b4b578559b6d1f0688c22f29a108d85e3b16b6|runtime/boot-userspace/system filename leads|
|1.tar.gz / 31|`common/v4l-utils-1.14.2.tar.gz`|file / 2861480|4ea937855db1ee34628c43339720dc53e64884400c05341fd13c4d5877e068f6|media/audio/video filename leads|
|1.tar.gz / 32|`common/avahi-0.7.tar.gz`|file / 1992743|a22ab3680b0825da0aef3809077b1286b63e355402ef56a266fc1c7ef1322af9|radio/network filename leads|
|1.tar.gz / 33|`common/gammaray-2.11.0.tar.gz`|file / 10326200|ab0488d2178c532816d491ab361ac3d362590f0e63912f7198f34c1b582209ca|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 34|`common/videothumbnailer-1.0.0-40.tar.gz`|file / 187631383|b16c01376d95cab3e46a9310f58d79b418e88aa1ff7bb78f191e10994f586ecf|media/audio/video filename leads|
|1.tar.gz / 35|`common/libqrencode-4.0.0.tar.gz`|file / 182791|c2c8a8110354463a3332cb48abf8581c8d94136af4dc1418f891cc9c7719e3c1|other upstream package names (purpose not established here)|
|1.tar.gz / 36|`common/libexif-0.6.22.tar.gz`|file / 3293380|228c1afc90b5c026330a6f001e3bef02ab38ff92df71e2d449de82fa52582297|other upstream package names (purpose not established here)|
|1.tar.gz / 37|`common/db-5.3.28.tar.gz`|file / 35090431|e0a992d740709892e81f9d93f06daf305cf73fb81b545afe72478043172c3628|other upstream package names (purpose not established here)|
|1.tar.gz / 38|`common/exiv2-0.25.tar.gz`|file / 5428412|2572bd1f124cceb81b3625cf6597e3c9ad461705bd57b283208b5ff2ab489948|other upstream package names (purpose not established here)|
|1.tar.gz / 39|`common/sunpinyin-2.99.tar.gz`|file / 140211875|1651db64c04dcb805026abfa6fad4c6ff9b802e5b5624707f31535aecd7924a7|other upstream package names (purpose not established here)|
|1.tar.gz / 40|`common/opensource_bt_driver.tar.gz`|file / 74409468|bacb3df12e43413cf86b013d70affceda102a94a24b2fb6e3c0d1b346b5b0dd8|radio/network filename leads|
|1.tar.gz / 41|`common/libxcrypt-4.1.1.tar.gz`|file / 1162815|ee12a48e640796ed61d316ec64ddc602914be8a4f44158395536d588fb3e7228|other upstream package names (purpose not established here)|
|1.tar.gz / 42|`common/npapi-plugins-1.0.0.tar.gz`|file / 167158|0faaba50775f13061f666bd8504f8d9d26038453f013245ea2b89ffcb6a28386|graphics/UI/input filename leads|
|1.tar.gz / 43|`common/alsa-plugins-1.1.6.tar.gz`|file / 1108760|f24ea09d3e142152d779a7c52b1fdcf4df997ac342fbcc66b2cd8fa92e1faec8|media/audio/video filename leads|
|1.tar.gz / 44|`common/libasn.tar.gz`|file / 1377271|766594d6515357a60fd6d3217f4c19217af51f4c7be6e1036d68c9432a20e635|other upstream package names (purpose not established here)|
|1.tar.gz / 45|`common/5.0_FreeRTOS.zip`|file / 4508178|ee4778d3e6fa0b35f43d0e617adfcbc99e1daddb0abd97ca09bcd5c76fafe705|runtime/boot-userspace/system filename leads|
|1.tar.gz / 46|`common/qtwayland.tar.gz`|file / 298780|007e5b813754e341db8a87e87698c969f794dd15d5625bc633c7a058727ebfb0|graphics/UI/input filename leads|
|1.tar.gz / 47|`common/microwindows-src.tar.gz`|file / 3184640|ec52a3017465aa8f11d344e5ecfd7529a2657344ae4e7989cb96b459fd4cdf71|graphics/UI/input filename leads|
|1.tar.gz / 48|`common/keyutils-1.5.5.tar.gz`|file / 246539|1d31008375fea98cf6ba35748a6d2f829649c01706070832a8e65c52a2edd3fa|other upstream package names (purpose not established here)|
|1.tar.gz / 49|`common/cairo-1.14.12.tar.gz`|file / 46645634|9bb928cdeeaf3db0703ae24305a6e82c3f07fe2ad6e376b9a75915bb9b47a229|graphics/UI/input filename leads|
|1.tar.gz / 50|`common/pyzy-0.1.0.tar.gz`|file / 2657262|6b51474cd5305f0b4b434295951b08ef2ae108f479b372594db76df184c724cf|other upstream package names (purpose not established here)|
|1.tar.gz / 51|`common/libmicrohttpd-0.9.50.tar.gz`|file / 1686160|00b32cbdb23a8e72a937457372687872008e64089300a7bc78fbb0f412ab42d7|radio/network filename leads|
|1.tar.gz / 52|`common/base-files_3.0.14.tar.gz`|file / 39035|5fc53039fa17160c93b30852fcdcb62838e97616feed2796d51bf5a754bd647a|runtime/boot-userspace/system filename leads|
|1.tar.gz / 53|`common/util-linux-2.32.1.tar.gz`|file / 10480494|43af9da45250a45bfa545ede3817287ce37498349df9890ddd400b4e8a88740a|other upstream package names (purpose not established here)|
|1.tar.gz / 54|`common/gmp-4.2.1.tar.gz`|file / 3335549|c501d0a06cfe4fad8136848e4861814f4844eb5d1d49d89e585d23e85cf88d79|other upstream package names (purpose not established here)|
|1.tar.gz / 55|`common/libxml++-2.40.1.tar.gz`|file / 2064594|9f11cb1472ba864a2ad97e6d902ff2f54d3c7659b0e5a18282255d4025787c2d|other upstream package names (purpose not established here)|
|1.tar.gz / 56|`common/libnl-3.4.0.tar.gz`|file / 1389602|f0d1170fcb9c70e846f92c324c9a53eafa0d0229c9701a9db2af10e9e2a7a04c|radio/network filename leads|
|1.tar.gz / 57|`common/gstreamer.zip`|file / 394976437|649bd4dec676b3459a730009c3fd7f2673292e6fe1b0b7d13b6559069ece0257|media/audio/video filename leads|
|1.tar.gz / 58|`common/iotop-0.6.tar.gz`|file / 53632|edcbcf265d1d6f9e90c5f3404671daf4315390abf631dd1fdadc5dcdc1985141|other upstream package names (purpose not established here)|
|1.tar.gz / 59|`common/e2fsprogs-1.44.3.tar.gz`|file / 8213946|7165027bafeb838753d7b2eb8c9bdba46dda131c0e3592500796083c312f5387|other upstream package names (purpose not established here)|
|1.tar.gz / 60|`common/fribidi-1.0.5.tar.gz`|file / 2606296|65150dd95e0194d044114adce3282e13bef0da9636daabe1706087c513343c51|other upstream package names (purpose not established here)|
|1.tar.gz / 61|`common/maliit-framework-webos-1.1.0-86_20191211.tar.gz`|file / 590351599|89aa1986e1ab04effe41dcd7e5fd96478a78ea6bbd489ea6e183205f80785ac2|graphics/UI/input filename leads|
|1.tar.gz / 62|`common/ecryptfs-utils-111.tar.gz`|file / 1186920|9eddf440faf56430083b70b3891c8c775cf5682f7f62386b774b3f4b9abd6fd1|other upstream package names (purpose not established here)|
|1.tar.gz / 63|`common/criu-webos_oss_2.tgz`|file / 1675896|0cb76bf97aeb7e3a82a379d38f1dcc383d33a02e36e833ae1cc291b505ed5e92|other upstream package names (purpose not established here)|
|1.tar.gz / 64|`common/gphoto2-2.5.14.tar.gz`|file / 1703439|bd80f642197a32018eb92ba4e6906b7acbe950661eed364c7581623b3bfa1ce9|other upstream package names (purpose not established here)|
|1.tar.gz / 65|`common/ptmalloc3.tar.gz`|file / 284420|ed96fd0717f1aa1c794f9c583842f2a1519c40d7c7a7eae7b1f096a3dd60dca9|other upstream package names (purpose not established here)|
|1.tar.gz / 66|`common/libwfdsie.tar.gz`|file / 4195|a44cec69c814b46f11a49a72ff9ab7a42604fc3167646d8a0262c8bd23a76297|media/audio/video filename leads|
|1.tar.gz / 67|`common/opkg-0.3.6.tar.gz`|file / 1245772|4f1b4bc4ca0d7c33af076c2ae97ae167de49e0f69246376549e6661cf84f6c31|runtime/boot-userspace/system filename leads|
|1.tar.gz / 68|`common/libgphoto2-2.5.16.tar.gz`|file / 9814353|75b448c63750052ed9896647ed40175f9bb7851b82b078e5f364710309caebdd|other upstream package names (purpose not established here)|
|1.tar.gz / 69|`common/userspace-rcu-0.10.1.tar.bz2`|file / 503347|9c09220be4435dc27fcd22d291707b94b97f159e0c442fbcd60c168f8f79eb06|other upstream package names (purpose not established here)|
|1.tar.gz / 70|`common/libsdl-image-webos.tar.gz`|file / 2057024|df1f80e9115d1bc87d5346e7c0e3e5b58ab8b353456d4a426a27f699a3768856|graphics/UI/input filename leads|
|1.tar.gz / 71|`common/psmisc-23.1.tar.gz`|file / 811433|a0f3d91aa89654bb9dd66838fbeac3f7b99a8b99a227264b5fb4cb4cda5c47d1|runtime/boot-userspace/system filename leads|
|1.tar.gz / 72|`common/lsb-release-1.4.tar.gz`|file / 17635|718875f8f089748a30f240fa1a88fa2881d7fbd0201256fcd31ce58da692dd0d|runtime/boot-userspace/system filename leads|
|1.tar.gz / 73|`common/libsmpeg-webos.tar.gz`|file / 931485|8909a23ac60fdd3a38cc203d5c3361a1d9457841d226d2cc24335f9ff048c3c3|media/audio/video filename leads|
|1.tar.gz / 74|`common/opensource_bt_drv.tgz`|file / 362065920|ab3a2e90428ed18d212a9411c36bc0a03700e0f300a78a173367d3cae1002ec7|radio/network filename leads|
|1.tar.gz / 75|`common/lttng-ust-2.10.3.tar.bz2`|file / 799603|9e8420f90d5f963f7aa32bc6d44adc1e491136f687c69ffb7a3075d33b40852b|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 76|`common/dbus-1.12.10.tar.gz`|file / 2858025|3d04711c264de4752daffa44c4ca7f9777c5360ec6576d975a20554f31ae88c5|radio/network filename leads|
|1.tar.gz / 77|`common/iptables-1.6.2.tar.gz`|file / 1315817|f26e12df64461931e45804673f10d8c0a0280150ec8482ab3f37a26e31fa5d85|radio/network filename leads|
|1.tar.gz / 78|`common/hunspell-1.3.2.tar.gz`|file / 4176125|3ca4b3a5bc5858c84e48e7e7f79ca6176227bc047d6381fe3b2dc25cae6fab9c|other upstream package names (purpose not established here)|
|1.tar.gz / 79|`common/netbase-5.4.tar.gz`|file / 39103|8b5949d06730a8d5d5ffd4d3d398be4239d93ef396c3548a9f606e511048a855|runtime/boot-userspace/system filename leads|
|1.tar.gz / 80|`common/qt-creator-opensource-src-3.6.0.tar.gz`|file / 23127195|b130104963053e21f227b08009545894af33df495445a8651843bad4b52a1dec|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 81|`common/base-passwd_3.5.29.tar.gz`|file / 81174|f0b66388b2c8e49c15692439d2bee63bcdd4bbbf7a782c7f64accc55986b6a36|runtime/boot-userspace/system filename leads|
|1.tar.gz / 82|`common/uchardet-0.0.1.tar.gz`|file / 193752|aa168af4a66045b0642c47cbef51319edcca1f0215da9ce325926c9de09638d9|other upstream package names (purpose not established here)|
|1.tar.gz / 83|`common/nss-3.39.tar.gz`|file / 129015756|a705433074a775edf84f14a093a803d904957f5dc7f22f096cc2f81c79c35ba4|other upstream package names (purpose not established here)|
|1.tar.gz / 84|`common/glibmm-2.56.0.tar.gz`|file / 12085762|f362512aace7b838e8888a7427d2bd9b518ec05b0b04a9e8fdd906a2daf72817|other upstream package names (purpose not established here)|
|1.tar.gz / 85|`common/mSBC_lib_v1.1.54.8.zip`|file / 4320906|b453be080ebb2398f308ce88d5cac6f934b6e855c7cb8cd8f4184ecaf4a5c1d0|media/audio/video filename leads|
|1.tar.gz / 86|`common/cryptsetup-2.0.4.tar.gz`|file / 11814368|a8d5a8af52c86f91d965a40c49823fae0ed3b5f04f0257bd8978a6d55b1f7b78|other upstream package names (purpose not established here)|
|1.tar.gz / 87|`common/libgpg-error-1.32.tar.gz`|file / 1871141|34f29eef6c0c75740573ba42736b6bfff9fe705789ac719713ce04afc9dbdc0b|other upstream package names (purpose not established here)|
|1.tar.gz / 88|`common/libconfig-1.7.2.tar.gz`|file / 2787658|7f9a5c7f7dec6c498c0647257fb9ffacdd1e55323f6b75284e6e348cc4bf2d19|other upstream package names (purpose not established here)|
|1.tar.gz / 89|`common/readline-5.2.tar.gz`|file / 2462326|cdae9cca4ec16e534376355e0aba3accc53a7d4fafe99405f53a61fd1022803c|other upstream package names (purpose not established here)|
|1.tar.gz / 90|`common/SDL_mixer-1.2.11.tar.gz`|file / 2690654|86145ac39cac6d2c6169c226f937648dca5e89dcd828751763dd174fa9af9cf9|graphics/UI/input filename leads|
|1.tar.gz / 91|`common/ginga.ar.tgz`|file / 430425809|7abff3f73cd1c3da6ee440bf8653a5e8387dfbde1392a30ff0ddaac72283dea2|other upstream package names (purpose not established here)|
|1.tar.gz / 92|`common/libhangul-0.1.0.tar.gz`|file / 10006394|c4da784c6be4024f49c4ea5a8030550da9191c8652dff6dd82bd8d229f87d08f|other upstream package names (purpose not established here)|
|1.tar.gz / 93|`common/ffmpeg-4.0.2.tar.gz`|file / 14109744|1d31d5392b81dc042b112d8d943f6630ea9fe68d680c8d66fefc693f1acb8b5e|media/audio/video filename leads|
|1.tar.gz / 94|`common/libmnl-1.0.4.tar.gz`|file / 811377|182e5cb75211af9e3f32dda0ec3b20a388e113898fb0769aa2dd525aeabc34c7|radio/network filename leads|
|1.tar.gz / 95|`common/nss-mdns-0.10.tar.gz`|file / 353130|1e683c2e7c3921814706d62fbbd3e9cbf493a75fa00255e0e715508d8134fa6d|radio/network filename leads|
|1.tar.gz / 96|`common/iproute2-4.19.0.tar.gz`|file / 7232552|00a513d98c2d29f110a8e2ee01eb35ae388b3bd7ade7846dd3b3189108171eb3|radio/network filename leads|
|1.tar.gz / 97|`common/gettext-0.16.1.tar.gz`|file / 11499398|6c149066d873f2e18baf9ffb260646a93211cfd4b49a21b897cc63b61ed97cf5|other upstream package names (purpose not established here)|
|1.tar.gz / 98|`common/gptfdisk-0.8.10.tar.gz`|file / 3710880|41eb149835957ce96b13aad28f2bd9d79c1f3258daf33ab00b0bc93855ad3ef7|other upstream package names (purpose not established here)|
|1.tar.gz / 99|`common/nspr-4.19.tar.gz`|file / 1466849|714dab17c5865db6e9a306fbea7b5b2f65edaed3c5691926b89e9ca3e6c7f1b9|other upstream package names (purpose not established here)|
|1.tar.gz / 100|`common/fuse-2.9.8.tar.gz`|file / 5272960|ce3bb2f2b2bc0664f0ff395ed16f3a483d38126c586727a96c6b33ed918ad254|other upstream package names (purpose not established here)|
|1.tar.gz / 101|`common/ca-certificates-master.tar.gz`|file / 309632|da8fa438b7c450445fe955779e4408c198df1aa11d3d45c4e02fa87479bc65fe|other upstream package names (purpose not established here)|
|1.tar.gz / 102|`common/mozilla-plugin-samples-npruntime.zip`|file / 3142|d225b4cf151e81b9fadeedf9f362c7704a8e63b57e2bbb92f6db3b65ec2b514f|graphics/UI/input filename leads|
|1.tar.gz / 103|`common/acl-2.2.52.src.tar.gz`|file / 386604|179074bb0580c06c4b4137be4c5a92a701583277967acdb5546043c7874e0d23|other upstream package names (purpose not established here)|
|1.tar.gz / 104|`common/alsa-lib-1.1.6.tar.gz`|file / 6750168|2a2dbedb911459372cd6aadb606ed42f79fcb5c5ccd151cecac4caeaff55da8c|media/audio/video filename leads|
|1.tar.gz / 105|`common/qtquickcontrols-opensource-src-5.4.1.tar.gz`|file / 1193764|4ea71d979666ede5785cc5f000bc52ed1c966aab11154c7a645111546ae46590|graphics/UI/input filename leads|
|1.tar.gz / 106|`common/efs_os.tar.gz`|file / 10230|06e388ef2178da2858840a10bdd23c71eb35de2dabbe63b653b1159a1ce865fc|other upstream package names (purpose not established here)|
|1.tar.gz / 107|`common/glib-2.58.0.tar.xz`|file / 4900456|c0f4ce0730b4f95c47b711613b5406a887c2ee13ea6d25930d72a4fa7fdb77f6|other upstream package names (purpose not established here)|
|1.tar.gz / 108|`common/smartmontools-6.6.tar.gz`|file / 1165880|0a7b2358ee3a2ebb4174b0054278098b820f2cf17950dcf7e3d6598f482841f9|other upstream package names (purpose not established here)|
|1.tar.gz / 109|`common/libgcrypt-1.8.4.tar.gz`|file / 4312336|47f18b537330ec203518012e7341a856a86b45680a1bea0033b3e9e5d63eab53|other upstream package names (purpose not established here)|
|1.tar.gz / 110|`common/gnutls-3.3.30.tar.gz`|file / 11316779|97c1c6fb36362d68192038910722b097762f5d23dfc23089807276b576628d84|other upstream package names (purpose not established here)|
|1.tar.gz / 111|`common/elfutils-0.148.tar.gz`|file / 3358999|d0c94b3129395051d6ef994b6a19cf71dca1873e531cdd679ed0d229d33d2246|other upstream package names (purpose not established here)|
|1.tar.gz / 112|`common/libaio-0.3.111.tar.gz`|file / 108708|8ad5ec4498c63d9ed9d909b8c8b167fc64d506eb82d5ddecd7bec6f526116c3b|other upstream package names (purpose not established here)|
|1.tar.gz / 113|`common/xz-5.2.4.tar.gz`|file / 2194981|8875b759d90567170280ccc1d4f2ae46c84fd563da737da6ab417697e39c3033|other upstream package names (purpose not established here)|
|1.tar.gz / 114|`common/glib-networking-2.54.1.tar.gz`|file / 1281550|4e91c9a1466ecb1aa1c76644c72656249d4911732383d40b2788bd6ec247c883|other upstream package names (purpose not established here)|
|1.tar.gz / 115|`common/dvbfrontend_web60.tar.gz`|file / 11786100|c0a7885f73b45f77bb8b5184a6c85622ca96b138cfb756552434dedd7b4bc344|media/audio/video filename leads|
|1.tar.gz / 116|`common/connman.tgz`|file / 303619742|9d2c1803a5fad2545c90667e802b31654f54119a72056923b33a1680e774640d|radio/network filename leads|
|1.tar.gz / 117|`common/fdk-aac-2.0.1.tar.gz`|file / 3395664|355e23311b99b75b28a584b0a4de6b5d282c7e8bbe0b39b41cef6859d59fa86c|media/audio/video filename leads|
|1.tar.gz / 118|`common/kmod-25.tar.gz`|file / 1456607|ecde61c7db17051b862a9c903c66bb9d4a422871ea42f596b27e3e6a3a780f60|runtime/boot-userspace/system filename leads|
|1.tar.gz / 119|`common/flac-1.3.2.tar.gz`|file / 2162190|ad32c609eab601c24a2b8759b05a862fcd0d10b08ef4e50d435d8361285e3401|media/audio/video filename leads|
|1.tar.gz / 120|`common/GConf-3.2.6.tar.xz`|file / 1559904|1912b91803ab09a5eed34d364bf09fe3a2a9c96751fde03a4e0cfa51a04d784c|other upstream package names (purpose not established here)|
|1.tar.gz / 121|`common/procps-ng-3.3.15.tar.gz`|file / 2297554|adb124803a3696660cc61c87a919d6e3151fcc30b6c27d1251550c23b25f3932|runtime/boot-userspace/system filename leads|
|1.tar.gz / 122|`common/iftop-1.0pre4.tar.gz`|file / 704032|57284f5170e585f0e79748b2b18601d0fb2d6a3b15366feb8be218dfa8825acd|other upstream package names (purpose not established here)|
|1.tar.gz / 123|`common/makedevs-native-1.0.1-r0-patched.tar.gz`|file / 7450|fdfb880fb49f513bb6124e58e295317ccb0aec512cdea1d4b5357a198aa0c0f7|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 124|`common/libwfdsie_webos6_0.tar.gz`|file / 4196|7cf920d3736699e4a805f599f4ea452a5a4aec1d77854a7168e844f152bdda4d|media/audio/video filename leads|
|1.tar.gz / 125|`common/shared-mime-info-1.10.tar.gz`|file / 1715891|9813f3105fbeaa456bb7480cb5c88a7200ce391d8bf3bfd4a4dbb45833827f9d|other upstream package names (purpose not established here)|
|1.tar.gz / 126|`common/guider-master.zip`|file / 526468|1e3943cca4c9c9d78e606db1d6479780aed92b7b092ce78e929335134cbac704|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 127|`common/libtool-2.4.6.tar.gz`|file / 1806697|e3bd4d5d3d025a36c21dd6af7ea818a2afcd4dfc1ea5a17b39d7854bcd0c06e3|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 128|`common/gphotofs-0.5.tar.gz`|file / 991132|570c67d917f31169f1976a3e54f7483cb7d1c99eb4bf07968ffb5a0dc2371342|other upstream package names (purpose not established here)|
|1.tar.gz / 129|`common/babeltrace-1.5.6.tar.bz2`|file / 1004367|5308bc217828dd571b3259f482a85533554064d4563906ff3c5774ecf915bbb7|build/development/observability filename leads (NOT a target SDK)|
|1.tar.gz / 130|`common/attr-2.4.47.tar.gz`|file / 1539365|03fe0a3e9208313a94d0f5fa12844e7d6fe7aa23a16bc59673a64da3bb39fc2c|other upstream package names (purpose not established here)|
|2.tar.gz / 0|`soc`|dir / 0|not applicable|directory|
|2.tar.gz / 1|`soc/libkadaptor-1.0.0-908.3.tar.gz`|file / 123840909|46e7e652bc8f6fc9a57ade3baca9b1300a9e8c1bdc4bcde3cb7675116184bf25|kernel/boot/hardware-adaptation filename leads|
|2.tar.gz / 2|`soc/r_8812_wifi_driver.tar.gz`|file / 79725513|4fa16013269ed5104024d62c2acc636f0ed868d0540bd87527359bd15de13e94|radio/network filename leads|
|2.tar.gz / 3|`soc/gstreamer-1.0.0-2089.tar.gz`|file / 136115594|5b32c597ce45dd5601427ed704e11fcc06f809f8de6e4e6928e4bd5b1eae1675|media/audio/video filename leads|
|2.tar.gz / 4|`soc/kernel-1.0.0-711..4.tar.gz`|file / 170350960|110f08578519954be3113108ca461d4190d387c3cbb6e50d648274c9dcaf9962|kernel/boot/hardware-adaptation filename leads|
|2.tar.gz / 5|`soc/bootcode-1.0.0-1099.7.tar.gz`|file / 12014324|b88f252cf9ae4f4535e015959916cd87067f0e6cf551ef0f189cdc2f4365e23e|kernel/boot/hardware-adaptation filename leads|
