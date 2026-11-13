# Security and safety policy

## Scope of this project
This repository documents userspace work on an owner-rooted LG webOS TV: a native app
installed with the stock developer installer (`dev/install`) and launched by SAM. It does
not modify the kernel, bootloader, rootfs, tvservice or any other system partition.

**Never overwrite system partitions such as kernel, rootfs or tvservice. The TV will be bricked.**

## No exploit reproduction
This repo intentionally contains **no rooting or exploit procedures, payloads or step-by-step
instructions**. Root status is recorded as an outcome only. For rooting information, use the
community's own documentation at [webosbrew.org](https://www.webosbrew.org/). Pull requests that
add exploit or rooting steps will not be accepted.

## Personal identifiers
Do not commit a TV's serial number, nduid, MAC addresses, pairing/client keys, credentials,
account data or private network details. Redact them in logs and photos before contributing.

## Reporting
If you find a committed identifier or secret, or a vulnerability in the code in this repo,
please open a GitHub security advisory (Security tab -> "Report a vulnerability") rather than a
public issue. Vulnerabilities in LG firmware should be reported to LG, not here.
