**Historical analysis: superseded by [the consolidated ODS-verified report](../RK-ZYNQ7020-F_Consolidated_Report.md).** Statements below about missing physical pins or unreviewed spreadsheets describe the earlier investigation.

**EMIO routing recovery: investigation status**

No new EMIO-to-package-pin assignment has been recovered or verified. The existing logical EMIO map in REPORT.md remains valid; package-ball assignments remain unknown.

`../extract_pl.py` extracts the PL partition from the requested BOOT.bin, checks partition-header checksums, converts byte order and walks the entire packet stream without truncation. It does not validate configuration CRCs, decompress configuration frames, decode routing switches or trace nets.

- `pl_boot_word_order.bin`: exact 2,489,280-byte payload from BOOT offset 0x19740.
- `pl_configuration_be.bin`: same words serialized big-endian for configuration-data analysis; no standalone Xilinx `.bit` metadata wrapper.
- `manifest.json`: hashes, IDCODE, register/command counts and verification scope.
- `packets.json`: packet offsets, register addresses, sizes and initial data words.

The configuration stream writes IDCODE 0x03727093. There are 4,484 writes to MFWR (configuration register 0x0A), showing multi-frame-write compression. Therefore simply extracting FDRI packets does not reconstruct the complete frame contents. Compression must be handled before trusting any routing result.

[Project X-Ray's database](https://github.com/f4pga/prjxray-db/blob/master/Info.md) includes Zynq7, xc7z020clg484 and PS7 port information. This makes reverse tracing plausible, but does not establish that every required configuration feature is covered. [Upstream compression support work](https://github.com/f4pga/prjxray/pull/2060) is experimental; decoder compatibility and correctness must be checked for this stream.

The current environment has no bitread/bit2fasm on PATH and no installed WSL. No reverse-engineering toolchain or device database was downloaded or installed for this investigation. Missing tools are an environment limitation, not proof that extraction is impossible.

Remaining work: obtain a decoder that supports this compression, validate its reconstructed frames, decode programmable routing against the matching device database, trace PS7 EMIO ports through routing and any intervening logic to IOB sites, and map those sites to CLG484 balls. A package-pin result should be cross-checked against known board connections before turning it into XDC constraints. Original net names and original HDL are not required for tracing physical routes, but are not directly retained as a named mapping in these packets.
