# LG webOS6 KLP1.0 notice inventory (NOT source archive inventory)

## Provenance and limits
Public browser worker reports exact-model65NANO756PR catalog entry, TV/AV>TV, software label webOS6.0 KLP1.0, release sequence510320 and three displayed source archives webOS6.0 KLP_1.0_1.tar.gz / _2.tar.gz / _3.tar.gz. Exact spacing in filenames not independently verified here; no archive downloaded. Catalog association is not proof of installed firmware. Filename210204 is NOT established publication date.
Locally audited original: `OSSNotice-3253_webOS 6.0 KLP_1.0_210204.html`. Parsed with BeautifulSoup only; no scripts/code executed. This license notice is not a BSP, dependency lockfile, reproducible-build manifest or archive file list.

Bytes: 5562232; SHA256: `3e7a13e14f6cd328c9b5483c25c416e735da67dc5cd08131b61804a9b06fbf8f`. 317 grouped notice sections; 923 unique names in file-list fields; 41 distinct license strings (not normalized license identities).

## Concrete target-relevant entries
| Section | Listed names | Notice license label | What this establishes |
|---|---|---|---|
|id103|kdriver|GPL-2.0|Driver-related component named; implementation/coverage unknown.|
|id104|kernel-base, kernel-image, kernel-image-uimage, kernel-module-demod-khal-4.4.84-711.kalaupapa.4, kernel-module-gsr-module-4.4.84-711.kalaupapa.4, kernel-module-gsr-module-fake-4.4.84-711.kalaupapa.4|GPL-2.0|Kernel package and module labels include4.4.84-711.kalaupapa.4; not measured running kernel, archive content or board-support proof.|
|id222|omx-il-rtk|LGPL-2.1|RTK-named OMX component; NOT proof installed SoC is Realtek.|
|id227|packagegroup-starfish-bsp|Apache-2.0|BSP packagegroup label, NOT proof complete BSP included.|
|id294|videooutput-adaptation-layer-starfish|Apache-2.0|Video adaptation component named; panel/HDMI receiver drivers not proven.|
|id295|videooutputd, videooutputd-localization|Apache-2.0|Video output service labels, not a complete display pipeline.|
|id14|audiooutputd|Apache-2.0|Audio service label, not proof hardware audio driver.|
|id114/id128|libatomic,libgomp,libstdc++,libgcc|GPL-3.0-with-GCC-exception|Runtime library labels do not establish compiler/toolchain version/build recipe.|

Additional listed families: ALSA, PulseAudio, GStreamer incl gstreamer1.0-plugins-rtk, Wayland, qtwayland-webos, luna-surfacemanager, nyx-modules-starfish and tuner modules. These improve package-audit search targets; generic/common components and cross-platform tuner labels do NOT identify this unit's hardware. No exact component versions except version-bearing package labels above can be inferred.

## Negative searches (limited to this notice)
No literal u-boot, uboot, bootloader, toolchain, HDMI, Realtek, MediaTek, MStar, UD15D, EAX69581701,65NANO756PR or KLP found in decoded document text. Absence here does NOT prove absence from source archives/firmware/hardware.
Zero HTML hyperlinks. Eleven unique plain-text URL tokens appear, all license/attribution/project references (Apache, GNU GCC exception, Mozilla, OpenSSL, Python logo, FreeType, HDL identifier). No ordinary source-archive download URL or target-build documentation link found. URL token extraction is literal and some have trailing punctuation; not a validated link registry.

## Next staged action
Using normal public catalog UI, obtain archive sizes/names and download source archives to box only if proceeding; retain provenance/checksums. List archive contents without executing build/install scripts; search READMEs, licenses, kernel/platform/config/device trees, kdriver, OMX/video/audio adaptation, packagegroup and toolchain manifests. Evaluate exact-target mapping, missing binary dependencies and legitimate boot/recovery separately. Do not invoke hidden download APIs. No source build/flash/TV action is implied or approved.

## Complete grouped notice inventory
| Section | File-list labels | License-list labels |
|---|---|---|
|id0|acr2|Apache-2.0, MIT, OpenSSL, Zlib|
|id1|activitymanager|Apache-2.0|
|id2|aiservice, aiservice-localization|Apache-2.0|
|id3|alibaba-adapter|LGPL-2.1, MIT, OpenSSL, Zlib|
|id4|alsa-conf, alsa-lib|GPLv2, LGPLv2.1|
|id5|alsa-plugins-pulseaudio-conf, libasound-module-conf-pulse, libasound-module-ctl-pulse, libasound-module-pcm-pulse|GPLv2, LGPLv2.1|
|id6|alsa-states|MIT|
|id7|alsa-utils, alsa-utils-aconnect, alsa-utils-alsactl, alsa-utils-alsaloop, alsa-utils-alsamixer, alsa-utils-alsaucm, alsa-utils-amixer, alsa-utils-aplay, alsa-utils-aseqdump, alsa-utils-aseqnet, alsa-utils-iecset, alsa-utils-midi, alsa-utils-speakertest|GPLv2|
|id8|amazon-alexa-adapter, amazon-alexa-adapter-localization|Apache-2.0, ISC, MIT|
|id9|aom|BSD|
|id10|app-shell, com.webos.app.browser, webruntime|Apache-2.0, BSD-3-Clause, LGPL-2.1, MIT, MPL-1.1|
|id11|applicationinstallerutility|Apache-2.0|
|id12|arm-compute-library|MIT|
|id13|armnn|MIT|
|id14|audiooutputd|Apache-2.0|
|id15|avahi-daemon, libavahi-client, libavahi-common, libavahi-core, libavahi-glib, libavahi-gobject|GPLv2, LGPLv2.1|
|id16|base-files|GPLv2|
|id17|base-passwd|GPLv2|
|id18|boost, boost-atomic, boost-chrono, boost-container, boost-context, boost-contract, boost-coroutine, boost-date-time, boost-filesystem, boost-graph, boost-iostreams, boost-locale, boost-log, boost-math, boost-program-options, boost-python, boost-random, boost-regex, boost-serialization, boost-signals, boost-system, boost-test, boost-thread, boost-timer, boost-wave|BSL-1.0, MIT, Python-2.0|
|id19|busybox, busybox-syslog, busybox-udhcpc|GPLv2, bzip2|
|id20|bzip2, libbz2|bzip2|
|id21|c-ares|MIT|
|id22|ca-certificates|GPL-2.0, MPL-2.0|
|id23|cairo|LGPLv2.1, MPL-1|
|id24|capstone|BSD|
|id25|com.palm.service.devmode|Apache-2.0|
|id26|com.webos.app.enactbrowser|LicenseRef-EnactBrowser-Evaluation|
|id27|com.webos.app.liveginga|GPL-2.0|
|id28|com.webos.app.self-diagnosis, com.webos.app.self-diagnosis-localization|Apache-2.0, BSD-3-Clause, ISC, MIT|
|id29|com.webos.service.pkgverifier|Apache-2.0|
|id30|configd|Apache-2.0|
|id31|configurator|Apache-2.0|
|id32|connman, connman-client|GPLv2|
|id33|connman-conf|GPLv2|
|id34|cpushareholder-stub|Apache-2.0|
|id35|crashd, libsegfault-webos|Apache-2.0, LGPL-2.1|
|id36|criu-webos|GPLv2, LGPLv2.1|
|id37|cryptsetup|GPL-2.0-with-OpenSSL-exception|
|id38|curl, libcurl|MIT|
|id39|db8|Apache-2.0|
|id40|dbus, dbus-lib|AFL-2, GPL-2.0, GPLv2|
|id41|dbus-gpl|GPL-2.0|
|id42|dvbfrontend, dvbfrontend-atsc, dvbfrontend-dvb, kernel-module-a8303, kernel-module-a8303jp, kernel-module-atbm8891, kernel-module-atsc-dtv-soc, kernel-module-atsc-dtv-soc-chip, kernel-module-atsc-lgdt3307-chip, kernel-module-cxd2857, kernel-module-dtmb-dtv-soc, kernel-module-dtmb-dtv-soc-chip, kernel-module-dvb-a8303-adapter, kernel-module-dvb-a8303-chip, kernel-module-dvb-a8303jp-chip, kernel-module-dvb-atbm8891-adapter, kernel-module-dvb-atbm8891-chip, kernel-module-dvb-common-adapter, kernel-module-dvb-cxd2857-adapter, kernel-module-dvb-dtv-soc, kernel-module-dvb-dtv-soc-chip, kernel-module-dvb-lgdt3307-adapter, kernel-module-dvb-lnbr-adapter, kernel-module-dvb-lnbr-chip, kernel-module-dvb-mxl683-adapter, kernel-module-dvb-rda-adapter, kernel-module-dvb-rda5815m-chip, kernel-module-dvb-rda5816-chip, kernel-module-dvb-rt740-adapter, kernel-module-dvb-rt740-chip, kernel-module-dvb-si2151-chip, kernel-module-dvb-si2169d-chip, kernel-module-dvb-si2178b-chip, kernel-module-dvb-si2178bjp-chip, kernel-module-dvb-silab-adapter, kernel-module-integ-dtv-soc, kernel-module-integ-dtv-soc-chip, kernel-module-isdb-cxd2857-chip, kernel-module-isdb-dtv-soc, kernel-module-isdb-dtv-soc-chip, kernel-module-isdb-mxl683-chip, kernel-module-lgdt3307, kernel-module-lnbr, kernel-module-mxl683, kernel-module-rda5815m, kernel-module-rda5816, kernel-module-rt740, kernel-module-si2151, kernel-module-si2169d, kernel-module-si2178b, kernel-module-si2178b-atv, kernel-module-si2178bjp, kernel-module-webos-tv|GPL-2.0|
|id43|e2fsprogs, e2fsprogs-resize2fs, libcomerr, libe2p, libext2fs, libss|BSD, GPLv2, LGPLv2, MIT|
|id44|e2fsprogs-badblocks, e2fsprogs-e2fsck, e2fsprogs-mke2fs, e2fsprogs-tune2fs|GPLv2|
|id45|ecryptfs-utils|GPL-2.0|
|id46|enhanced-flash-swap, kernel-module-dm-eswap-4.4.84-711.kalaupapa.4, kernel-module-dm-eswap-adaptor-4.4.84-711.kalaupapa.4|GPLv2|
|id47|event-monitor|Apache-2.0|
|id48|exiv2|GPLv2|
|id49|expat|MIT|
|id50|fdk-aac|Fraunhofer_FDK_AAC_Codec_Library_for_Android|
|id51|filecache|Apache-2.0|
|id52|flac, libflac|BSD, GFDL-1.2, GPLv2, LGPLv2.1|
|id53|fontconfig, fontconfig-utils|MIT, MIT-style, PD|
|id54|freetype|FreeType, GPLv2|
|id55|fribidi|LGPLv2.1|
|id56|fuse, fuse-utils, libulockmgr|GPLv2, LGPLv2|
|id57|fuser, killall, psmisc, pstree|GPLv2|
|id58|gettext-runtime|GPLv2|
|id59|glib-2.0|BSD, LGPLv2.1, PD|
|id60|glib-networking|LGPLv2|
|id61|glibc, glibc-utils, tzcode|BSD, GPLv2, LGPLv2.1|
|id62|glibc-gconv, glibc-gconv-big5, glibc-gconv-cp1250, glibc-gconv-cp1251, glibc-gconv-cp1252, glibc-gconv-cp1253, glibc-gconv-cp1254, glibc-gconv-cp1255, glibc-gconv-cp1256, glibc-gconv-cp1258, glibc-gconv-euc-cn, glibc-gconv-euc-kr, glibc-gconv-gb18030, glibc-gconv-ibm874, glibc-gconv-iso-6937, glibc-gconv-iso8859-1, glibc-gconv-iso8859-11, glibc-gconv-iso8859-15, glibc-gconv-iso8859-2, glibc-gconv-iso8859-3, glibc-gconv-iso8859-4, glibc-gconv-iso8859-5, glibc-gconv-iso8859-6, glibc-gconv-iso8859-7, glibc-gconv-iso8859-8, glibc-gconv-iso8859-9, glibc-gconv-libgb, glibc-gconv-libksc, glibc-gconv-sjis, glibc-gconv-uhc, glibc-gconv-unicode, glibc-gconv-utf-16, glibc-gconv-utf-32|GPLv2, LGPLv2.1|
|id63|glibmm|GPLv2, LGPLv2.1|
|id64|gmp|LGPLv2.1|
|id65|gnutls|LGPLv2.1|
|id66|google-assistant-adapter|Apache-2.0, BSD-3-Clause, MIT, OpenSSL|
|id67|gphoto2|GPLv2|
|id68|gphotofs|GPL-2.0|
|id69|gptfdisk-sgdisk|GPL-2.0|
|id70|gstreamer1.0|LGPLv2|
|id71|gstreamer1.0-libav|LGPLv2, LGPLv2.1|
|id72|gstreamer1.0-omx|LGPLv2|
|id73|gstreamer1.0-plugins-bad, gstreamer1.0-plugins-bad-adpcmdec, gstreamer1.0-plugins-bad-adpcmenc, gstreamer1.0-plugins-bad-aiff, gstreamer1.0-plugins-bad-asfmux, gstreamer1.0-plugins-bad-autoconvert, gstreamer1.0-plugins-bad-bz2, gstreamer1.0-plugins-bad-camerabin, gstreamer1.0-plugins-bad-ckdrm, gstreamer1.0-plugins-bad-coloreffects, gstreamer1.0-plugins-bad-dashdemux, gstreamer1.0-plugins-bad-debugutilsbad, gstreamer1.0-plugins-bad-dvbsuboverlay, gstreamer1.0-plugins-bad-dvdspu, gstreamer1.0-plugins-bad-frei0r, gstreamer1.0-plugins-bad-h265combiner, gstreamer1.0-plugins-bad-hls, gstreamer1.0-plugins-bad-id3tag, gstreamer1.0-plugins-bad-interlace, gstreamer1.0-plugins-bad-ivfparse, gstreamer1.0-plugins-bad-legacyrawparse, gstreamer1.0-plugins-bad-meta, gstreamer1.0-plugins-bad-midi, gstreamer1.0-plugins-bad-mpegpsdemux, gstreamer1.0-plugins-bad-mpegpsmux, gstreamer1.0-plugins-bad-mpegtsdemux, gstreamer1.0-plugins-bad-mpegtsmux, gstreamer1.0-plugins-bad-multiappsrc, gstreamer1.0-plugins-bad-mxf, gstreamer1.0-plugins-bad-pcapparse, gstreamer1.0-plugins-bad-proxy, gstreamer1.0-plugins-bad-removesilence, gstreamer1.0-plugins-bad-rfbsrc, gstreamer1.0-plugins-bad-rtponvif, gstreamer1.0-plugins-bad-sdpelem, gstreamer1.0-plugins-bad-smooth, gstreamer1.0-plugins-bad-smoothstreaming, gstreamer1.0-plugins-bad-speed, gstreamer1.0-plugins-bad-subenc, gstreamer1.0-plugins-bad-videofiltersbad, gstreamer1.0-plugins-bad-videoframe-audiolevel, gstreamer1.0-plugins-bad-videoparsersbad, gstreamer1.0-plugins-bad-waylandsink, libgstadaptivedemux-1.0, libgstbadaudio-1.0, libgstbasecamerabinsrc-1.0, libgstbasedrm-1.0, libgstcodecparsers-1.0, libgstinsertbin-1.0, libgstisoff-1.0, libgstmpegts-1.0, libgstmultiapp-1.0, libgstphotography-1.0, libgstplayer-1.0, libgsturidownloader-1.0, libgstwayland-1.0, libgstwebrtc-1.0|LGPLv2, LGPLv2.1|
|id74|gstreamer1.0-plugins-base, gstreamer1.0-plugins-base-adder, gstreamer1.0-plugins-base-alsa, gstreamer1.0-plugins-base-app, gstreamer1.0-plugins-base-apps, gstreamer1.0-plugins-base-audioconvert, gstreamer1.0-plugins-base-audiomixer, gstreamer1.0-plugins-base-audiorate, gstreamer1.0-plugins-base-audioresample, gstreamer1.0-plugins-base-encoding, gstreamer1.0-plugins-base-ivorbisdec, gstreamer1.0-plugins-base-meta, gstreamer1.0-plugins-base-ogg, gstreamer1.0-plugins-base-opengl, gstreamer1.0-plugins-base-pbtypes, gstreamer1.0-plugins-base-playback, gstreamer1.0-plugins-base-rawparse, gstreamer1.0-plugins-base-subparse, gstreamer1.0-plugins-base-tcp, gstreamer1.0-plugins-base-typefindfunctions, gstreamer1.0-plugins-base-videoconvert, gstreamer1.0-plugins-base-videorate, gstreamer1.0-plugins-base-videoscale, gstreamer1.0-plugins-base-videotestsrc, gstreamer1.0-plugins-base-volume, gstreamer1.0-plugins-base-vorbis, libgstallocators-1.0, libgstapp-1.0, libgstaudio-1.0, libgstfft-1.0, libgstgl-1.0, libgstpbutils-1.0, libgstriff-1.0, libgstrtp-1.0, libgstrtsp-1.0, libgstsdp-1.0, libgstsubtitle-1.0, libgsttag-1.0, libgstvideo-1.0|LGPLv2|
|id75|gstreamer1.0-plugins-cool, gstreamer1.0-plugins-cool-avibin, gstreamer1.0-plugins-cool-cooltracer, gstreamer1.0-plugins-cool-decproxy, gstreamer1.0-plugins-cool-dolbystreamcombiner, gstreamer1.0-plugins-cool-dvcombbin, gstreamer1.0-plugins-cool-dynappsrc, gstreamer1.0-plugins-cool-fakedec, gstreamer1.0-plugins-cool-httpextbin, gstreamer1.0-plugins-cool-meta, gstreamer1.0-plugins-cool-mpomux, gstreamer1.0-plugins-cool-splitappsink, gstreamer1.0-plugins-cool-textbin, gstreamer1.0-plugins-cool-tsinkbin, libgstcool-1.0|LGPLv2|
|id76|gstreamer1.0-plugins-dvr, gstreamer1.0-plugins-dvr-dashsink, gstreamer1.0-plugins-dvr-dvrdashdemux, gstreamer1.0-plugins-dvr-dvrdrm, gstreamer1.0-plugins-dvr-dvrisomp4, gstreamer1.0-plugins-dvr-dvrmpegtsdemux, gstreamer1.0-plugins-dvr-meta, libgstdvrmpegts-1.0|LGPLv2.1|
|id77|gstreamer1.0-plugins-good, gstreamer1.0-plugins-good-alaw, gstreamer1.0-plugins-good-apetag, gstreamer1.0-plugins-good-audioparsers, gstreamer1.0-plugins-good-auparse, gstreamer1.0-plugins-good-avi, gstreamer1.0-plugins-good-deinterlace, gstreamer1.0-plugins-good-equalizer, gstreamer1.0-plugins-good-flac, gstreamer1.0-plugins-good-flv, gstreamer1.0-plugins-good-flxdec, gstreamer1.0-plugins-good-icydemux, gstreamer1.0-plugins-good-id3demux, gstreamer1.0-plugins-good-interleave, gstreamer1.0-plugins-good-isomp4, gstreamer1.0-plugins-good-isomp4-1-8, gstreamer1.0-plugins-good-level, gstreamer1.0-plugins-good-matroska, gstreamer1.0-plugins-good-meta, gstreamer1.0-plugins-good-mulaw, gstreamer1.0-plugins-good-multifile, gstreamer1.0-plugins-good-multipart, gstreamer1.0-plugins-good-pulseaudio, gstreamer1.0-plugins-good-replaygain, gstreamer1.0-plugins-good-rtp, gstreamer1.0-plugins-good-rtpmanager, gstreamer1.0-plugins-good-rtsp, gstreamer1.0-plugins-good-soup, gstreamer1.0-plugins-good-spectrum, gstreamer1.0-plugins-good-speex, gstreamer1.0-plugins-good-taglib, gstreamer1.0-plugins-good-udp, gstreamer1.0-plugins-good-video4linux2, gstreamer1.0-plugins-good-videofilter, gstreamer1.0-plugins-good-videomixer, gstreamer1.0-plugins-good-wavenc, gstreamer1.0-plugins-good-wavpack, gstreamer1.0-plugins-good-wavparse|LGPLv2|
|id78|gstreamer1.0-plugins-nano, gstreamer1.0-plugins-nano-activeregiondetector, gstreamer1.0-plugins-nano-meta, libgstnano-1.0|LGPLv2|
|id79|gstreamer1.0-plugins-rtk|LGPL-2.1|
|id80|gstreamer1.0-plugins-ugly, gstreamer1.0-plugins-ugly-asf, gstreamer1.0-plugins-ugly-dvdlpcmdec, gstreamer1.0-plugins-ugly-dvdsub, gstreamer1.0-plugins-ugly-meta|LGPLv2, LGPLv2.1|
|id81|gzip|GPLv2|
|id82|harfbuzz|MIT|
|id83|hbbtv2-plugin|Apache-2.0, BSD-2-Clause, MPL-1.1, NPL-1.1, Zlib|
|id84|hdparm|BSD|
|id85|hunspell|LGPL-2.1, MPL-1.1|
|id86|iconnectivity|Apache-2.0, BSD-2-Clause, BSD-3-Clause|
|id87|icu, libicudata, libicui18n, libicuio, libicutu, libicuuc|ICU|
|id88|iftop|GPLv2|
|id89|ilib-qml-plugin|Apache-2.0|
|id90|ilib-webapp|Apache-2.0|
|id91|imemanager, imemanager-localization|Apache-2.0, MIT|
|id92|iot-client-webos, iot-client-webos-localization|EDL-1.0, MIT, curl|
|id93|iotop|GPLv2|
|id94|iproute2|GPLv2|
|id95|iptables, iptables-module-ebt-802-3, iptables-module-ebt-ip, iptables-module-ebt-log, iptables-module-ebt-mark-m, iptables-module-ip6t-ah, iptables-module-ip6t-dnat, iptables-module-ip6t-dnpt, iptables-module-ip6t-dst, iptables-module-ip6t-eui64, iptables-module-ip6t-frag, iptables-module-ip6t-hbh, iptables-module-ip6t-hl, iptables-module-ip6t-icmp6, iptables-module-ip6t-ipv6header, iptables-module-ip6t-log, iptables-module-ip6t-masquerade, iptables-module-ip6t-mh, iptables-module-ip6t-netmap, iptables-module-ip6t-redirect, iptables-module-ip6t-reject, iptables-module-ip6t-rt, iptables-module-ip6t-snat, iptables-module-ip6t-snpt, iptables-module-ip6t-srh, iptables-module-ipt-ah, iptables-module-ipt-clusterip, iptables-module-ipt-dnat, iptables-module-ipt-ecn, iptables-module-ipt-icmp, iptables-module-ipt-log, iptables-module-ipt-masquerade, iptables-module-ipt-netmap, iptables-module-ipt-realm, iptables-module-ipt-redirect, iptables-module-ipt-reject, iptables-module-ipt-snat, iptables-module-ipt-ttl, iptables-module-ipt-ulog, iptables-module-xt-addrtype, iptables-module-xt-audit, iptables-module-xt-bpf, iptables-module-xt-cgroup, iptables-module-xt-checksum, iptables-module-xt-classify, iptables-module-xt-cluster, iptables-module-xt-comment, iptables-module-xt-connbytes, iptables-module-xt-connlimit, iptables-module-xt-connmark, iptables-module-xt-connsecmark, iptables-module-xt-conntrack, iptables-module-xt-cpu, iptables-module-xt-ct, iptables-module-xt-dccp, iptables-module-xt-devgroup, iptables-module-xt-dscp, iptables-module-xt-ecn, iptables-module-xt-esp, iptables-module-xt-hashlimit, iptables-module-xt-helper, iptables-module-xt-hmark, iptables-module-xt-idletimer, iptables-module-xt-ipcomp, iptables-module-xt-iprange, iptables-module-xt-ipvs, iptables-module-xt-led, iptables-module-xt-length, iptables-module-xt-limit, iptables-module-xt-mac, iptables-module-xt-mangle, iptables-module-xt-mark, iptables-module-xt-multiport, iptables-module-xt-nfacct, iptables-module-xt-nflog, iptables-module-xt-nfqueue, iptables-module-xt-notrack, iptables-module-xt-osf, iptables-module-xt-owner, iptables-module-xt-physdev, iptables-module-xt-pkttype, iptables-module-xt-policy, iptables-module-xt-quota, iptables-module-xt-rateest, iptables-module-xt-recent, iptables-module-xt-rpfilter, iptables-module-xt-sctp, iptables-module-xt-secmark, iptables-module-xt-set, iptables-module-xt-socket, iptables-module-xt-standard, iptables-module-xt-state, iptables-module-xt-statistic, iptables-module-xt-string, iptables-module-xt-synproxy, iptables-module-xt-tcp, iptables-module-xt-tcpmss, iptables-module-xt-tcpoptstrip, iptables-module-xt-tee, iptables-module-xt-time, iptables-module-xt-tos, iptables-module-xt-tproxy, iptables-module-xt-trace, iptables-module-xt-u32, iptables-module-xt-udp, iptables-modules|GPLv2|
|id96|iputils, iputils-arping, iputils-clockdiff, iputils-ping, iputils-rarpd, iputils-rdisc, iputils-tftpd, iputils-tracepath, iputils-traceroute6|BSD, GPLv2|
|id97|iw|BSD|
|id98|jansson|MIT|
|id99|jemalloc|BSD|
|id100|json-c|MIT|
|id101|jsoncpp|MIT|
|id102|kbd, kbd-consolefonts, kbd-keymaps|GPLv2|
|id103|kdriver|GPL-2.0|
|id104|kernel-base, kernel-image, kernel-image-uimage, kernel-module-demod-khal-4.4.84-711.kalaupapa.4, kernel-module-gsr-module-4.4.84-711.kalaupapa.4, kernel-module-gsr-module-fake-4.4.84-711.kalaupapa.4|GPL-2.0|
|id105|keyutils|GPL-2.0, LGPL-2.1|
|id106|kmod|GPL-2.0, LGPL-2.1|
|id107|legacy-broadcast-atsc, legacy-broadcast-atsc-localization|MPL-1.1, Zlib|
|id108|legacy-broadcast-dvb, legacy-broadcast-dvb-localization|MPL-1.1, Zlib|
|id109|leptonica|BSD-2-Clause|
|id110|leveldb|BSD-3-Clause|
|id111|libacl|LGPLv2.1|
|id112|libaio|LGPLv2.1|
|id113|libarchive|BSD|
|id114|libatomic, libgomp, libstdc++|GPL-3.0-with-GCC-exception|
|id115|libattr|LGPLv2.1|
|id116|libavcodec, libavfilter, libavformat, libavutil, libswresample, libswscale|LGPLv2.1|
|id117|libbson|Apache-2.0|
|id118|libcap|BSD, GPLv2|
|id119|libconfig|LGPLv2.1|
|id120|libcrypto, libssl, openssl, openssl-bin, openssl-conf|openssl|
|id121|libcrypto10, libssl10, openssl10, openssl10-bin, openssl10-conf|openssl|
|id122|libdaemon|LGPLv2.1|
|id123|libdevmapper|GPLv2, LGPLv2.1|
|id124|libdvbfrontend|GPL-2.0|
|id125|libdvbv5|GPLv2, LGPLv2.1|
|id126|libexif|LGPLv2.1|
|id127|libffi|MIT|
|id128|libgcc|GPL-3.0-with-GCC-exception|
|id129|libgcrypt|LGPLv2.1|
|id130|libgpg-error|GPLv2, LGPLv2.1|
|id131|libgphoto2, libgphoto2-camlibs, libgphotoport|LGPLv2.1|
|id132|libhangul|LGPLv2.1|
|id133|libjpeg-turbo|BSD-3-Clause|
|id134|libkmod|LGPL-2.1|
|id135|libltdl|GPLv2, LGPLv2.1|
|id136|liblzma|PD|
|id137|libmicrohttpd|LGPL-2.1|
|id138|libmikmod|LGPLv2.1|
|id139|libmnl|LGPLv2.1|
|id140|libnl, libnl-genl|GPL-2.0, LGPLv2.1|
|id141|libnlp|BSD-3-Clause, MIT|
|id142|libnsbmp|MIT|
|id143|libnss-mdns|LGPLv2.1|
|id144|libogg|BSD|
|id145|libopkg, opkg|GPLv2|
|id146|libopus|BSD-3-Clause|
|id147|libpbnjson|Apache-2.0|
|id148|libpcap|BSD|
|id149|libpcre|BSD|
|id150|libpng|Libpng|
|id151|libpng12|Libpng|
|id152|libpulse, libpulse-simple, libpulsecommon, libpulsecore, pulseaudio, pulseaudio-lib-alsa-util, pulseaudio-lib-cli, pulseaudio-lib-protocol-cli, pulseaudio-lib-protocol-native, pulseaudio-lib-rtp, pulseaudio-misc, pulseaudio-module-alsa-card, pulseaudio-module-alsa-sink, pulseaudio-module-alsa-source, pulseaudio-module-always-sink, pulseaudio-module-augment-properties, pulseaudio-module-card-restore, pulseaudio-module-cli-protocol-tcp, pulseaudio-module-cli-protocol-unix, pulseaudio-module-default-device-restore, pulseaudio-module-detect, pulseaudio-module-device-restore, pulseaudio-module-filter-apply, pulseaudio-module-filter-heuristics, pulseaudio-module-intended-roles, pulseaudio-module-native-protocol-tcp, pulseaudio-module-native-protocol-unix, pulseaudio-module-null-sink, pulseaudio-module-null-source, pulseaudio-module-palm-policy, pulseaudio-module-position-event-sounds, pulseaudio-module-rescue-streams, pulseaudio-module-role-cork, pulseaudio-module-rtp-recv, pulseaudio-module-rtp-send, pulseaudio-module-stream-restore, pulseaudio-module-suspend-on-idle, pulseaudio-module-switch-on-port-available, pulseaudio-module-udev-detect, pulseaudio-server|GPLv2, LGPLv2.1|
|id153|libpython2, python-codecs, python-compression, python-contextlib, python-core, python-crypt, python-ctypes, python-curses, python-datetime, python-email, python-fcntl, python-io, python-json, python-lang, python-math, python-mime, python-netclient, python-pickle, python-pprint, python-shell, python-subprocess, python-syslog, python-textutils, python-threading, python-unixadmin, python-xml, python-zlib|PSFv2|
|id154|librolegen|Apache-2.0|
|id155|libsamplerate0|BSD-2-Clause|
|id156|libsdl-image-webos|LGPLv2|
|id157|libsdl-mixer-webos|LGPLv2|
|id158|libsdl-net-webos|Zlib|
|id159|libsdl-ttf-webos|Zlib|
|id160|libsdl2-webos|Zlib|
|id161|libsigc++-2.0|LGPLv2.1|
|id162|libsmpeg-webos|LGPL-2.0|
|id163|libsndfile1|LGPLv2.1|
|id164|libsolv|BSD-3-Clause|
|id165|libsoup-2.4|LGPLv2|
|id166|libsqlite3, sqlite3|PD|
|id167|libsystemd, libudev, systemd, systemd-analyze, systemd-extra-utils, systemd-vconsole-setup, udev, udev-hwdb|GPLv2, LGPLv2.1|
|id168|libtasn1|LGPLv2.1|
|id169|libtirpc|BSD|
|id170|libunwind|MIT|
|id171|libusb1|LGPLv2.1|
|id172|libuv|MIT|
|id173|libvorbis|BSD|
|id174|libwebosi18n|Apache-2.0|
|id175|libwebp|BSD|
|id176|libwebsockets|LGPL-2.1|
|id177|libwrap, tcp-wrappers|BSD|
|id178|libxcrypt|LGPLv2.1|
|id179|libxkbcommon|MIT, MIT-style|
|id180|libxml++|LGPL-2.1|
|id181|libxml2|MIT|
|id182|lighttpd, lighttpd-module-access, lighttpd-module-accesslog, lighttpd-module-dirlisting, lighttpd-module-indexfile, lighttpd-module-staticfile|BSD|
|id183|ls2-helpers|Apache-2.0|
|id184|lsb|GPLv2|
|id185|luna-init|Apache-2.0|
|id186|luna-prefs|Apache-2.0|
|id187|luna-prefs-data|Apache-2.0|
|id188|luna-service2|Apache-2.0|
|id189|luna-service2-security-conf|Apache-2.0|
|id190|luna-service2-security-conf-pub|Apache-2.0|
|id191|luna-surfacemanager, luna-surfacemanager-base, luna-surfacemanager-localization|Apache-2.0|
|id192|luna-sysservice|Apache-2.0|
|id193|lvm2, lvm2-scripts|GPLv2, LGPLv2.1|
|id194|makedevs|GPLv2|
|id195|maliit-framework-webos|LGPLv2|
|id196|mdns|Apache-2.0|
|id197|mheg|BSD-3-Clause, IJG, LGPL-2.1, Libpng, MIT, OpenSSL, Zlib, curl|
|id198|mojoloader|Apache-2.0|
|id199|mojoservicelauncher|Apache-2.0|
|id200|mpg123|LGPLv2.1|
|id201|msgpack|Apache-2.0|
|id202|ncurses, ncurses-libformw, ncurses-libmenuw, ncurses-libncurses, ncurses-libncursesw, ncurses-libpanelw, ncurses-libtinfo, ncurses-terminfo-base|MIT|
|id203|ne10|BSD-3-Clause|
|id204|netbase|GPLv2|
|id205|nettle|LGPLv2.1|
|id206|nghttp2|MIT|
|id207|nodejs|Artistic-2.0, BSD, MIT|
|id208|nodejs-module-usocket|ISC|
|id209|nodejs-module-webos-dynaload|Apache-2.0|
|id210|nodejs-module-webos-pmlog|Apache-2.0|
|id211|nodejs-module-webos-service|Apache-2.0|
|id212|nodejs-module-webos-sysbus|Apache-2.0|
|id213|notificationmgr|Apache-2.0|
|id214|npapi-plugins|Apache-2.0, BSD-2-Clause, MPL-1.1, NPL-1.1, Zlib|
|id215|nspr|GPL-2.0, LGPL-2.1, MPL-2.0|
|id216|nss|GPL-2.0, LGPL-2.1, MPL-2.0|
|id217|nuance-stt-adapter|BSD-3-Clause, MIT|
|id218|nyx-lib|Apache-2.0|
|id219|nyx-modules|Apache-2.0|
|id220|nyx-modules-starfish|Apache-2.0|
|id221|nyx-utils|Apache-2.0|
|id222|omx-il-rtk|LGPL-2.1|
|id223|openwnn-webos|Apache-2.0|
|id224|opkg-arch-config|MIT|
|id225|os-release|MIT|
|id226|packagegroup-core-boot|MIT|
|id227|packagegroup-starfish-bsp|Apache-2.0|
|id228|packagegroup-starfish-core|Apache-2.0|
|id229|packagegroup-starfish-extended|Apache-2.0|
|id230|packagegroup-starfish-foss|Apache-2.0|
|id231|packagegroup-starfish-ndk|Apache-2.0|
|id232|packagegroup-starfish-qt5|Apache-2.0|
|id233|packagegroup-starfish-tvsystem, packagegroup-starfish-tvsystem-atsc, packagegroup-starfish-tvsystem-dmost, packagegroup-starfish-tvsystem-dvb|Apache-2.0|
|id234|packagegroup-webos-extended|Apache-2.0|
|id235|packagegroup-webos-pro-extended|Apache-2.0|
|id236|packagegroup-webos-pro-qt5|Apache-2.0|
|id237|pacrunner|GPLv2|
|id238|pixman|MIT, MIT-style, PD|
|id239|pmklogd|Apache-2.0|
|id240|pmlogctl|Apache-2.0|
|id241|pmlogdaemon|Apache-2.0|
|id242|pmloglib|Apache-2.0|
|id243|poco-crypto, poco-foundation, poco-json, poco-net, poco-netssl, poco-util, poco-xml|BSL-1.0|
|id244|popt|MIT|
|id245|procps|GPLv2, LGPLv2|
|id246|protobuf|BSD-3-Clause|
|id247|protobuf-c|BSD-2-Clause|
|id248|ptmalloc3|LGPLv2|
|id249|pugixml|MIT|
|id250|pyzy|LGPLv2.1|
|id251|qml-webos-bridge|Apache-2.0|
|id252|qml-webos-components|Apache-2.0|
|id253|qml-webos-framework|Apache-2.0|
|id254|qrencode|LGPLv2.1|
|id255|qtwayland-webos|Apache-2.0|
|id256|readline|GPLv2|
|id257|run-postinsts|MIT|
|id258|sbc|LGPLv2.1|
|id259|scd-service|Apache-2.0, BSD-2-Clause, BSD-3-Clause|
|id260|sdparm|BSD|
|id261|second-screen-service, second-screen-service-localization|Apache-2.0, MIT|
|id262|securitymanager|MIT, OpenSSL|
|id263|settingsservice-conf|Apache-2.0|
|id264|sg3-utils|BSD, GPLv2|
|id265|shadow, shadow-base|Artistic-1.0, BSD, GPL-2.0|
|id266|shadow-gpl|GPL-2.0|
|id267|shadow-securetty|MIT|
|id268|shared-mime-info|GPLv2|
|id269|sleepd|Apache-2.0|
|id270|smartmontools|GPLv2|
|id271|snappy|BSD-3-Clause|
|id272|speex|BSD|
|id273|speexdsp|BSD|
|id274|starfish-initscripts|Apache-2.0, GPL-2.0|
|id275|sunpinyin|LGPLv2.1|
|id276|systemd-compat-units|MIT|
|id277|systemd-conf|GPLv2, LGPLv2.1|
|id278|systemd-serialgetty|GPLv2|
|id279|taglib|LGPLv2.1, MPL-1|
|id280|tar|GPLv2|
|id281|tesseract|Apache-2.0|
|id282|tesseract-lang-eng|Apache-2.0|
|id283|thrift|Apache-2.0|
|id284|tiff|BSD-2-Clause|
|id285|tpl-libs|Apache-2.0, BSD-2-Clause|
|id286|tremor|BSD|
|id287|tts|BSD-3-Clause, MIT|
|id288|tzdata, tzdata-africa, tzdata-americas, tzdata-antarctica, tzdata-arctic, tzdata-asia, tzdata-atlantic, tzdata-australia, tzdata-europe, tzdata-misc, tzdata-pacific, tzdata-posix, tzdata-right|BSD, BSD-3-Clause, PD|
|id289|uchardet|MPLv1.1|
|id290|umi|Apache-2.0|
|id291|update-alternatives-opkg|GPLv2|
|id292|uriparser|BSD-3-Clause|
|id293|util-linux, util-linux-agetty, util-linux-cfdisk, util-linux-fdisk, util-linux-fsck, util-linux-getopt, util-linux-ionice, util-linux-libblkid, util-linux-libfdisk, util-linux-libmount, util-linux-libsmartcols, util-linux-libuuid, util-linux-losetup, util-linux-lsblk, util-linux-mkfs, util-linux-mount, util-linux-mountpoint, util-linux-prlimit, util-linux-readprofile, util-linux-sfdisk, util-linux-sulogin, util-linux-swaponoff, util-linux-switch-root, util-linux-umount|BSD, GPLv2, LGPLv2.1|
|id294|videooutput-adaptation-layer-starfish|Apache-2.0|
|id295|videooutputd, videooutputd-localization|Apache-2.0|
|id296|videothumbnailer|GPL-2.0|
|id297|voiceinput|Apache-2.0, BSD-2-Clause, BSD-3-Clause, MIT, OpenSSL|
|id298|volatile-binds|MIT|
|id299|wam, wam-localization|Apache-2.0|
|id300|wavpack|BSD|
|id301|wayland|MIT|
|id302|webos-bluetooth-service|Apache-2.0|
|id303|webos-connman-adapter|Apache-2.0, LGPL-2.1|
|id304|webos-fontconfig-files|Apache-2.0|
|id305|webos-fonts|Apache-2.0, OFL-1.1|
|id306|webos-initscripts|Apache-2.0, MIT|
|id307|webos-nettools|Apache-2.0|
|id308|webos-pro-initscripts|Apache-2.0, MIT|
|id309|webos-wayland-extensions|Apache-2.0|
|id310|widevine-classic|MIT, OpenSSL|
|id311|wpa-supplicant, wpa-supplicant-cli, wpa-supplicant-passphrase|BSD|
|id312|wpa-supplicant-conf|GPLv2|
|id313|xinetd|BSD|
|id314|xkeyboard-config|MIT, MIT-style|
|id315|yajl|ISC|
|id316|zlib|Zlib|

## Plain-text URL tokens
- http://hdl.handle.net/1895.22/1013
- http://mozilla.org/MPL/2.0/.
- http://www.apache.org/licenses/
- http://www.apache.org/licenses/LICENSE-2.0
- http://www.gnu.org/copyleft/.
- http://www.gnu.org/licenses/gcc-exception.html
- http://www.mozilla.org/MPL/
- http://www.mozilla.org/NPL/
- http://www.openssl.org/)
- http://www.pythonlabs.com/logos.html
- https://www.freetype.org
