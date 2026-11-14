# wayland-hello prototype build. OFF-TV ONLY.
#
#   make host      host-native build for mock tests (needs host gcc + libwayland-client0 at runtime)
#   make test      host build + tests/run_tests.py
#   make arm       ARM EABI5 soft-float build against glibc 2.28 (Debian buster armel) sysroot
#   make abi       write build/arm/ABI-REPORT.txt and enforce GLIBC<=2.28 / NEEDED / e_flags checks
#   make clean
#
# Sysroot: populated by `python3 -I scripts/fetch_buster_armel_sysroot.py` into build-cache/sysroot.

SRC        := src/wayland_hello.c src/menu.c src/photo_frame.c
CFLAGS_COM := -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -fno-strict-aliasing -Isrc

HOSTCC     ?= gcc
CROSS      ?= arm-linux-gnueabi-
ARMCC      ?= $(CROSS)gcc
SYSROOT    ?= $(CURDIR)/build-cache/sysroot
MULTIARCH  := arm-linux-gnueabi
# armv5te + soft float = Debian armel baseline: most conservative ARM EABI5 soft-call target.
ARM_ARCH   ?= -march=armv5te -marm -mfloat-abi=soft
# Explicit old sysroot, start files and link search; -nostdinc keeps host/cross 2.36 headers out.
ARM_SYSFLAGS = --sysroot=$(SYSROOT) \
  -nostdinc -isystem $(SYSROOT)/usr/include/$(MULTIARCH) -isystem $(SYSROOT)/usr/include \
  -isystem $(shell $(ARMCC) -print-file-name=include) \
  -B$(SYSROOT)/usr/lib/$(MULTIARCH) -L$(SYSROOT)/usr/lib/$(MULTIARCH) -L$(SYSROOT)/lib/$(MULTIARCH) \
  -Wl,-rpath-link,$(SYSROOT)/lib/$(MULTIARCH)
ARM_LDFLAGS = -Wl,--hash-style=both -Wl,--as-needed -Wl,-z,relro -Wl,-z,now \
  -Wl,--dynamic-linker=/lib/ld-linux.so.3

SDK_ROOT ?= $(CURDIR)/build-cache/openlgtv-sdk/arm-webos-linux-gnueabi_sdk-buildroot
SDK_CC   ?= $(SDK_ROOT)/bin/arm-webos-linux-gnueabi-gcc

.PHONY: host test arm abi sdk sdk-abi clean
host: build/host/wayland-hello
build/host/wayland-hello: $(SRC)
	mkdir -p $(@D)
	$(HOSTCC) $(CFLAGS_COM) -static-libgcc -o $@ $^ -ldl

test: host
	python3 -I tests/run_tests.py build/host/wayland-hello
	python3 -I tests/test_ipk.py

arm: build/arm/wayland-hello
build/arm/wayland-hello: $(SRC)
	@test -f $(SYSROOT)/usr/lib/$(MULTIARCH)/crt1.o || { echo "sysroot missing: run python3 -I scripts/fetch_buster_armel_sysroot.py"; exit 1; }
	mkdir -p $(@D)
	$(ARMCC) $(ARM_ARCH) $(ARM_SYSFLAGS) $(CFLAGS_COM) -o $@ $^ -ldl $(ARM_LDFLAGS) -Wl,-Map,build/arm/link.map
	$(CROSS)strip -o build/arm/wayland-hello.stripped $@

abi: arm
	sh scripts/abi-check.sh build/arm/wayland-hello build/arm/ABI-REPORT.txt

# openlgtv buildroot-nc4 2026.08-webos SDK. Not committed. Fetch with
# python3 -I scripts/fetch_openlgtv_sdk.py (digest pinned to the GitHub release).
sdk: build/sdk/wayland-hello
build/sdk/wayland-hello: $(SRC)
	@test -x $(SDK_CC) || { echo "SDK gcc missing: python3 -I scripts/fetch_openlgtv_sdk.py"; exit 1; }
	mkdir -p $(@D)
	$(SDK_CC) -marm -mfloat-abi=soft $(CFLAGS_COM) -static-libgcc -o $@ $^ -ldl -lrt \
	  -Wl,--hash-style=both -Wl,--as-needed -Wl,-z,relro -Wl,-z,now \
	  -Wl,--dynamic-linker=/lib/ld-linux.so.3 -Wl,-Map,build/sdk/link.map
sdk-abi: sdk
	sh scripts/abi-check.sh build/sdk/wayland-hello build/sdk/ABI-REPORT.txt

clean:
	rm -rf build
