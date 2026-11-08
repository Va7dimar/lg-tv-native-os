# Source-to-unit mapping frontier
Analysis of existing admitted plaintext only;no new archive processing. No source label proves installed hardware.

- ARM Kconfig explicitly calls ARCH_RTK2875 “Realtek2875boards”; ARM tv006 development defconfig selects it.
- Same source also explicitly calls ARCH_LG1K “LGE Ltd LG1xxx-based boards”; ARM lg1k_defconfig selects it and names arm-lg115x-linux-gnueabi-. ARM64 lg1k_defconfig selects ARCH_LG1K,aarch64-linux-gnu- and an ARM32 compiler prefix.
- ARM64 RTK287O/tv006 defconfig independently exists,with aarch64-starfish-linux-.
- Customer menu labels tv001/tv006 as customer builds,not product numbers; no source text maps tv006 to65NANO756PR. Bootcode source k6l/A0 is hardcoded build metadata; PRJ.inc selects project context not yet read.
- Zero occurrences of65NANO756PR,UD15D,kalaupapa,k6lp or rtd2873 in the4802admitted plaintext files. This is a limited selected-text negative search,not global source or hardware proof.

Exact file hashes,linequotes and sourcepaths: `evidence/source-unit-mapping-frontier.json`. Complete selected-text candidate search hits: `evidence/core-two-platform-selected-hits.json`.

## Can mapping finish without opening the TV?
Potentially,if full sales suffix + live installed software/build plus authoritative parts/service cross-reference identify the installed board/panel revision/source association; full suffix alone may still include multiple BOMs. Normal menu/model exterior label can establish sales/software identity without opening. They do not necessarily disclose SoC/board/panel,and an externally visible product label is not an internal-board label. Existing service paperwork/previous repair records may disambiguate replacements. Candidate parts listings do not prove actual installed hardware. If no authoritative link exists,record unresolved;do not infer the chip,request chassis work,or substitute source defaults.

Official model-linked manual routes (view information only): All Settings→General→Devices→TV Management→TV Information;All Settings→Support→Software Update. Firmware API401 remains respected;no commands or retries. Source research/reviews cannot observe these physical-unit facts. Parent handles any unit-info request;no routine question or opening approval requested here. Keep serial,MAC,keys private.
