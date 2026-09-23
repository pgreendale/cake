# RK-ZYNQ7020-F — consolidated hardware, PS, PL and BSP findings

Updated 2026-09-20. This file consolidates the boot-image reconstruction, display analysis, Internet cross-checks and the supplied ODS pin definitions. It supersedes the earlier separate summaries. Source files are evidence, not executable instructions.

## Verification outcome and corrections

The ODS was read directly as ZIP/XML without Excel, macros or external links. It contains PS, 40 PIN, FMC and 其他 (Other) sheets. The filename covers V1.0/V1.1; the tables do not distinguish revision-specific pin changes. The supplied ODS is treated as board documentation; agreement with files is not a continuity measurement on the physical board.

- All eleven previously identified LCD/LED/key/clock assignments match the ODS.
- All 66 package pins marked `Unused_Bank13` or `Unused_Bank33` in the root XDC have named ODS nets: 16/16 in bank13 and 50/50 in bank33. These placeholders are therefore not evidence of electrically unused PCB pins.
- All 34 header signal assignments match the contact comments in the existing root XDC. Those contact numbers come from that XDC; ODS itself gives board net names and FPGA balls.
- All 54 MIOs have package-ball entries. The ODS exposes an error in our previous interpretation: **eMMC CMD is MIO47/B10, DAT1 is MIO49/C14**. MIO46/D12 remains DAT0; MIO48/D11 remains CLK. AMD's [SDIO signal table](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/SDIO-Controller-Media-Interface-Signals) independently confirms CMD on MIO47 and Data1 on MIO49. Register values were correct; the labels were swapped. The generator and CSV/Markdown pin maps have been corrected.
- The ODS supplies CAN, RS485, HDMI, PL Ethernet, camera and FMC package pins. It does not encode PS EMIO GPIO indices, AXI GPIO channels, or CAN0/CAN1-to-connector ordering.
- `pl_prsnt` GPIO58 is a heartbeat LED entry in the standalone DTBs only. It is absent from the FIT DT matching the successful boot. Do not infer that this proves GPIO58 drives FMC_PRSNT, or reproduce that output on a presence signal without tracing the design.

## Evidence levels

**Recovered:** FSBL register arrays and device-tree properties. **Documented:** ODS physical net-to-ball assignments. **Correlated:** board nets associated with DT roles (e.g. LCD DC and EMIO5). **Unresolved:** exact internal routes where names or numbering are insufficient. No new bitstream was implemented or programmed and no hardware validation was performed.

## BSP and boot deployment

The successful log reports U-Boot 2023.01, Linux 6.1.5-xilinx-v2023.1, GCC 12.2.0 and an ARM hard-float userspace executable. These identify the observed software versions, not a complete reproducible vendor BSP source archive. `board` and `bsp` both identify `zynq-generic-7z020`; `board-variant` is `qemuboot-xilinx:armv7a:zynq:zynq-7z:zynq-generic:zynq-generic-7z020`.

The successful kernel command line is `console=ttyPS0,115200 earlycon root=/dev/mmcblk1p1 rw rootwait`. eMMC partition 1 holds the ext4 root filesystem. The installation script copies the SD rootfs from `/media/sd-mmcblk0p2` to eMMC. It writes BOOT.BIN, boot.scr and image.ub to QSPI and clears the environment. It was inspected only, not executed.

| MTD | Start | End, exclusive | Successful-boot label / content |
|---|---|---|---|
| 0 | 0x00000000 | 0x009B0000 | qspi-boot / BOOT.BIN |
| 1 | 0x009B0000 | 0x009C0000 | qspi-bootenv |
| 2 | 0x009C0000 | 0x009D0000 | qspi-bootscr / boot.scr |
| 3 | 0x009D0000 | 0x01ED0000 | qspi-kernel / image.ub |
| 4 | 0x01ED0000 | 0x02000000 | space |

Use the FIT device tree matching the successful log when reproducing that QSPI/eMMC deployment; the standalone DTBs describe a different partition layout. Rootfs contents and binaries alone do not recover all kernel configuration options, recipes or vendor source patches.

## Detailed PS, clocks, DDR and boot-image reconstruction

The supplied BOOT.bin contains recoverable, unencrypted PS7 initialization tables. These give substantially stronger evidence for MIO, clocks and DDR than a device tree alone. The configuration is for a custom RK-ZYNQ7020-F system; these files do not establish that the PCB is a ZedBoard or ZC702 derivative. Do not substitute either board's preset for the recovered configuration.

This is an offline reconstruction, not a hardware-tested Vivado project. Register values are recoverable exactly; some original Vivado inputs are not uniquely recoverable from the generated register values. Physical board nets are now documented by the supplied ODS. Their internal EMIO/AXI routing must be distinguished from package-pin wiring.

**Evidence and reproducibility**

- Requested `Boot_Modified_RK7020/BOOT.bin`: SHA-256 `1ec41e19e99cf829cce88d4cbcb826a0e15bd8256619c7e9e2bd138fe493a6a5`. Identical to `Filesystem/boot/BOOT.bin`.
- FSBL starts at BOOT offset `0x1700`, length `0x18008`; boot-header checksum validated. Its SHA-256 is `082544a4b83932ae87fa28457e289e7121cfd25062e426fed072bea8d0c357e2`.
- `Filesystem/opt/image/BOOT.BIN` differs as a whole but contains the identical FSBL.
- `_BOOT.BIN` is a different build: its DDR, MIO and PLL tables do NOT match. It was not used as the configuration authority.
- Both requested DTBs are byte-identical, SHA-256 `7b2c238bbdacb6bcd5789789c9f1c439f9bb1c0b81c86945f32d8b4cfe05971f`.
- The FIT `Filesystem/opt/image/image.ub` contains a third DTB at offset `0x48b34c`, size 29234. Its SHA-256 `54f70ddb853f0909838028b88711521cb1e4d88beca83c64a2729818e3b55b8c` exactly matches the successful boot in `debug_output.txt`. Its PS peripheral configuration agrees with the requested DTBs; flash partition layout, some QSPI properties and root filesystem selection differ.
- The existing `buildroot_custom/buildroot_external/board/zynq/RK-ZYNQ7020-F/ps7_init/ps7_init_gpl.c` has byte-identical DDR, MIO, PLL and peripheral initialization arrays. Its clock tables differ; see below.
- `recovered_ps7_init_gpl.c` preserves that source and replaces its three clock tables with the actual binary tables. All 21 initialization arrays were encoded and located verbatim in the FSBL; see `verification.txt`. This validates the arrays, not the entire C executable or every other FSBL action. Use the existing companion header when examining/building this source; it is an analysis artifact, not an automatically installed replacement.
- `analyze.py` reproduces DTB decoding, checksums and table extraction. `make_artifacts.py` produces the pin inventory and reconstructed C source. Neither executes board scripts or writes to hardware.

Xilinx's [PS7 bytecode definition](https://github.com/Xilinx/embeddedsw/blob/master/lib/sw_apps/zynq_fsbl/misc/zed/ps7_init.h) documents the instruction encoding used in the extraction. Register interpretation follows [AMD UG585](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM), with individual register references below.

**Vivado peripheral selections**

| PS block | Selection to reproduce | Evidence / details |
|---|---|---|
| Quad SPI | Enabled, single flash, x4, MIO 1–6 | One CS; Winbond W25Q256, 32 MiB. MIO 8 is GPIO, not the QSPI feedback-clock pin. DT flash maximum SCLK 50 MHz. |
| UART0 | Enabled, MIO 10–11, TX/RX | RX=10, TX=11; console 115200n8; no hardware flow control exposed. |
| UART1 | Disabled in DT | Extra Linux serial ports are PL AXI UART16550 cores. |
| I2C0 | Enabled, MIO 14–15 | SCL=14, SDA=15; DT bus speed 100 kHz; EEPROM 0x50, PCF8563 RTC 0x51. |
| I2C1 | Enabled, EMIO | No I2C1 MIO mux selected; DT assigns this controller to HDMI EDID, 100 kHz. ODS: SCL=AA16, SDA=AB16; DT-to-board association inferred. |
| GEM0 / ENET0 | Enabled, RGMII MIO 16–27, MDIO MIO 52–53 | MDC=52, MDIO=53; `rgmii-id`; boot log identifies RTL8211F PHY address 0. |
| GEM1 / ENET1 | Disabled in DT | Linux eth1 is PL AXI Ethernet, not PS GEM1 via EMIO. |
| USB0 | Enabled, ULPI MIO 28–39 | Linux host mode; reset GPIO MIO 13. |
| USB1 | Disabled in DT; no MIO route | An APER clock-enable bit is set in FSBL; that alone does not prove an enabled external USB1 interface. |
| SD0 | Enabled, 4-bit, MIO 40–45 | SD card; card detect MIO 9; no write-protect or power-control feature in DT. |
| SD1 | Enabled, 4-bit, MIO 46–51 | Samsung KLM8G1GETF-B041, nominal 8 GB eMMC 5.1, identified from subsequent package photograph. No card-detect/write-protect/power-control feature in DT. Boot log identifies 8GTF4R, 7.28 GiB usable. |
| SPI0 | Enabled, EMIO | No SPI0 MIO route; DT `num-cs=3`, undecoded chip selects. ST7789V display on CS0, mode 3, max 32 MHz. Whether all three CS outputs reach pins is unknown. |
| SPI1 | Disabled in DT | Linux `spi1` here is an alias for PS SPI0; do not enable PS SPI1 based on that Linux name. |
| CAN0, CAN1 | Both enabled, EMIO | Both DT nodes enabled; FSBL enables clocks for both, with no CAN MIO mux. Application script requests 1 Mbit/s on both. ODS: board CAN1 RX/TX=Y14/AA14, CAN2 RX/TX=W15/Y15; PS controller-to-board channel order remains unproven. |
| GPIO MIO | Enabled | Keys on MIO 0/12; LEDs on MIO 8/7; USB reset on MIO 13. |
| GPIO EMIO | Enabled, width 11 | Device tree `emio-gpio-width=<11>`, logical EMIO[10:0]. Mapping below. |
| NAND / NOR / SMC memory | Disabled in DT; no corresponding MIO mux | An SMC APER enable bit does not establish a usable external memory interface. |
| TTC0/1, watchdog, DMA, XADC | On-chip controllers represented in DT | No TTC waveform, external watchdog, PJTAG or trace MIO routes selected. External EMIO ports for these cannot be inferred just from generic DT nodes. |

EMIO peripheral ports are independent interfaces: CAN0_TX and I2C1_SCL are not members of the 11-bit GPIO EMIO bus.

The subsequent eMMC photograph reads `SEC`, `KLM8G1GETF`, and `B041`, identifying Samsung **KLM8G1GETF-B041**. Samsung's [eMMC family datasheet (rendered copy)](https://manuals.plus/m/4bd2d2c8c04691de1ba9c1ad3140ff8505c9695def9278c3ceb969294de52698) identifies an 8 GB eMMC 5.1 device, 153-ball FBGA. This agrees with the log's 8GTF4R / 7.28 GiB device on SD1, exposed as `/dev/mmcblk1`, with two 4 MiB boot areas and a 512 KiB RPMB. For this recovered design use SD1 in 4-bit mode: CLK=MIO48, CMD=MIO47, DAT0=MIO46, DAT1=MIO49, DAT2=MIO50, DAT3=MIO51. Its MIO buffers are configured for 1.8 V. The eMMC package marking does not establish the actual supply voltage or reset-pin wiring. The 100 MHz SD reference clock is a controller input clock, not evidence of a 100 MHz eMMC bus clock or an HS200/HS400 operating mode.

**MIO electrical configuration and complete pin map**

PS I/O bank 500 / Vivado MIO bank 0, MIO 0–15: **LVCMOS33**. PS I/O bank 501 / Vivado MIO bank 1, MIO 16–53: **LVCMOS18**. These are programmed I/O standards, not voltage measurements. GPIO controller banks have different boundaries (0–31 and 32–53); do not confuse GPIO bank numbering with PS voltage banks.

All MIO Speed bits are zero (slow slew). Pull-ups are enabled except on MIO 2–8. Per-pin register values, masks, pull-up and tri-state fields are in [mio_pinout.csv](mio_pinout.csv) and the readable [complete 54-pin table](mio_pinout.md). TRI_ENABLE is an initialization field, not a substitute for the peripheral/GPIO runtime direction. MIO 9 is initialized with mask `0x3F01`, which intentionally leaves mux fields untouched; SD card detect uses its input tap.

| MIO | Function |
|---|---|
| 0 | PS key 1, active low |
| 1 | QSPI CS0# |
| 2, 3, 4, 5 | QSPI DQ0, DQ1, DQ2, DQ3 |
| 6 | QSPI SCLK |
| 7, 8 | PS LED 2, PS LED 1, active high |
| 9 | SD0 card detect |
| 10, 11 | UART0 RX, TX |
| 12 | PS key 2, active low |
| 13 | USB0 PHY reset GPIO |
| 14, 15 | I2C0 SCL, SDA |
| 16 | GEM0 TX clock |
| 17–20 | GEM0 TXD[0–3] |
| 21 | GEM0 TX control |
| 22 | GEM0 RX clock |
| 23–26 | GEM0 RXD[0–3] |
| 27 | GEM0 RX control |
| 28, 29, 30, 31 | USB0 ULPI D4, DIR, STP, NXT |
| 32, 33, 34, 35 | USB0 ULPI D0, D1, D2, D3 |
| 36, 37, 38, 39 | USB0 ULPI CLK, D5, D6, D7 |
| 40, 41 | SD0 CLK, CMD |
| 42–45 | SD0 D[0–3] |
| 46, 47 | SD1 D0, CMD |
| 48, 49 | SD1 CLK, D1 |
| 50, 51 | SD1 D2, D3 |
| 52, 53 | GEM0 MDC, MDIO |

Electrical field definitions: [MIO register](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-MIO_PIN_00-Details). The SD1 pin ordering differs from SD0: [MIO46](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-MIO_PIN_46-Details), [MIO48](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-MIO_PIN_48-Details?contentId=fMt~I_CwClJdI268zdXLyA). [MDIO routing](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/MDIO-Interface-Signals-via-MIO-and-EMIO?contentId=8IHfZw4K~tF7rOzU1k8sRQ) confirms pins 52/53.

`SD0_WP_CD_SEL=0x00090037` selects CD=MIO9, WP=EMIO. `SD1_WP_CD_SEL=0x003A0039` selects both through EMIO. Those selector encodings do not mean GPIO EMIO[1], [3], etc.; these are dedicated SD interface inputs. DT disables SD0 WP and SD1 WP/CD. [Selector definition](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-SD0_WP_CD_SEL-Details).

**GPIO EMIO map**

The PS GPIO controller's device-tree line number is 54 + EMIO index. It is not necessarily the legacy global Linux sysfs GPIO number.

| EMIO GPIO | PS GPIO line | Known use |
|---|---|---|
| 0 | 54 | pl_led1, active high |
| 1 | 55 | pl_led2, active high |
| 2 | 56 | pl_key1, active low |
| 3 | 57 | pl_key2, active low |
| 4 | 58 | Standalone DT only: pl_prsnt heartbeat output; absent from successful-boot FIT DT. FMC_PRSNT=AB14 is only a name-based candidate, not verified routing. |
| 5 | 59 | ST7789V display D/C, active high |
| 6 | 60 | Not named in DT |
| 7 | 61 | ST7789V display reset, active low |
| 8 | 62 | Not named in DT |
| 9 | 63 | Not named in DT |
| 10 | 64 | Not named in DT |

`qt_7020` is a 32-bit ARM ELF application with debug strings. It references RK-ZYNQ7020-F, CAN0/1, GPIO, displays and RS485, including `/sys/class/gpio/gpio916` and `gpio917` for RS485 control. Without establishing that kernel's GPIO base and tracing the relevant code, assigning those global numbers to EMIO indices would be speculative. The strings are not a Vivado pin constraint source.

**Clocks recovered from the FSBL**

DT specifies PS_CLK=33,333,333 Hz. Values below are nominal; actual oscillator tolerance and subsequent Linux clock changes are outside the extraction.

| Clock | Frequency | Derivation / setting |
|---|---|---|
| ARM PLL | 1533.333 MHz | PS_CLK × 46 |
| CPU | 766.667 MHz | ARM PLL / 2; 6:2:1 mode |
| CPU_3x / CPU_2x / CPU_1x | 383.333 / 255.556 / 127.778 MHz | CPU clock ratios |
| DDR PLL | 1066.667 MHz | PS_CLK × 32 |
| DDR_3x / DDR memory CK | 533.333 MHz | DDR PLL / 2 |
| DDR_2x | 355.556 MHz | DDR PLL / 3 |
| IO PLL | 1000 MHz | PS_CLK × 30 |
| DCI | 10.1587 MHz | DDR PLL / 15 / 7 |
| GEM0 TX reference | 125 MHz | IO PLL / 8 / 1 |
| QSPI reference | 200 MHz | IO PLL / 5; not flash SCLK |
| SD0 and SD1 reference | 100 MHz | IO PLL / 10 |
| UART0 reference | 100 MHz | IO PLL / 10; not serial baud rate |
| SPI0 reference | 166.667 MHz | IO PLL / 6; not SPI SCLK |
| CAN0 and CAN1 reference | 100 MHz | IO PLL / 5 / 2; both enabled |
| PCAP | 200 MHz | IO PLL / 5 |
| FCLK0 | 100 MHz | IO PLL / 5 / 2 |
| FCLK1 | 153.333 MHz | ARM PLL / 10 / 1 |
| FCLK2/3 | Not enabled by supplied DT | DT fclk-enable=3; no FSBL divider writes for these outputs |

The existing local source differs at `0xF8000180`: it requests FCLK1=200 MHz from IO PLL (`0x00100500`), whereas the supplied boot binary writes **`0x00100A20`**, selecting ARM PLL /10 /1. This is an actual recovered boot value, not an assumption based on the PL's 200 MHz fixed-clock DT node. The PL can contain separate clock generators. [FCLK source/divider definition](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-FPGA1_CLK_CTRL-Details).

The binary also adds `CAN_CLK_CTRL` (`0xF800015C`, mask `0x03F03F33`, value `0x00200503`) and `CAN_MIOCLK_CTRL` (`0xF8000160`, mask `0x007F007F`, value 0), and changes APER enables from `0x01DC4C4D` to `0x01DF4C4D`. Thus the old local clock tables must not be copied unchanged.

**DDR configuration to reproduce**

These values come from the silicon-3.x initialization array, which exactly matches the local generated source. The successful log reports silicon v3.1 and 1 GiB with ECC disabled.

| Setting | Recovered value |
|---|---|
| Memory type | DDR3 protocol, not DDR2/LPDDR2 |
| Bus width | 32 bits, all four byte lanes enabled |
| Total size | 1 GiB; address range 0x00000000–0x3FFFFFFF |
| Rank count | One |
| Geometry | 15 row bits, 10 column bits, 3 bank bits (8 banks) |
| Clock | 533.333 MHz, tCK approximately 1.875 ns |
| Data rate | Approximately 1066.667 MT/s |
| Burst length | BL8 |
| CAS latency | CL7 |
| CAS write latency | CWL6; controller write-latency field is 5 because it encodes WL−1 |
| Additive latency | 0 |
| 2T timing | Disabled (1T) |
| ECC | Disabled; scrub disabled |
| Automatic refresh | Enabled |
| Power-down enable | 0 in initial control register |
| Write leveling | Enabled |
| Read DQS gate training | Enabled |
| Read data-eye training | Enabled |
| DDR VREF | External VREF enabled, internal VREF disabled (control at 0xF8000B6C = 0x260 under mask 0x7FFF) |
| Mode registers | MR0=0x0B30, MR1=0x0004, MR2=0x0008, MR3=0x0000 at initialization |

The geometry follows address-map registers `0xF800603C=0x00000777`, `0xF8006040=0xFFF00000`, `0xF8006044=0x0F666666`: byte address bits [11:2] carry columns, [14:12] banks, [29:15] rows. The column field names are shifted relative to physical column numbering in full-width mode; `col_b9=15` does not mean only nine column bits. See [column mapping](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-DRAM_addr_map_col-Details?contentId=zEAC0GeE~MvHpd4vGu0q6g) and [bank mapping](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-DRAM_addr_map_bank-Details).

The subsequently supplied DDR photograph shows two Micron chips whose markings appear to read D9SHD. Rockchip's manufacturer-authored [DDR support list](https://lo01.g77k.com/aeb/docs/en/Common/AVL/Rockchip_Support_List_DDR_Ver2.61.pdf) maps D9SHD to MT41K256M16TW-107:P, a 4-Gbit x16 DDR3L device in a 96-ball package. The identification is conditional on reading the slightly blurred marking correctly. [Micron's catalog](https://tw.micron.com/products/memory/dram-components/ddr3-sdram/part-catalog) independently lists this part as 256M x16, 4 Gb, 1866 MT/s, nominal 1.35 V. Two such devices give the recovered 32-bit bus and 1 GiB capacity. The photograph identifies the likely installed part, not necessarily the original Vivado memory-part dropdown choice. Actual board DDR supply voltage still requires schematic or measurement evidence.

| Timing | Programmed cycles / encoding | Approximate duration at 533.333 MHz |
|---|---|---|
| tRCD | 7 | 13.125 ns |
| tRP | 7 | 13.125 ns |
| tRAS minimum | 19 | 35.625 ns |
| tRC | 27 | 50.625 ns |
| tRFC minimum | 161 | 301.875 ns |
| tFAW | 22 | 41.25 ns |
| tRRD | 6 | 11.25 ns |
| tCCD | 4 | 7.5 ns |
| tWR | 12, decoded from MR0 | 22.5 ns |
| tRTP | 5, from rd2pre with AL=0 | 9.375 ns |
| tWTR | 5, from wr2rd=15 minus CWL6 and BL/2=4 | 9.375 ns |
| tREFI | 0x82 × 32 = 4160 | 7.8 microseconds |
| tCKE | 4 | 7.5 ns |
| tXP | 5 | 9.375 ns |

These are resulting programmed timing intervals, not necessarily the exact nanosecond values typed into Vivado: rounding to clock cycles prevents unique recovery of the original inputs. The write-latency field must not be misread as CWL5; AMD specifies [WL−1 encoding and turnaround formulas](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-DRAM_param_reg2-Details).

All four byte lanes have the following initial PHY ratios: write-level initial ratio 0; gate-level initial ratio 0xA4; read DQS 0x35; write DQS 0x80; FIFO write-enable 0xF9; write data 0xC0. Control slave ratio is 0x100, clock-output inversion enabled. These are initial values; training can change the operational delays. They do not uniquely identify PCB DQS-to-clock delays or trace lengths entered in Vivado.

The complete DDR controller writes, QoS/arbitration settings, masks and PHY fields are retained in [ddr_annotated.txt](ddr_annotated.txt), the binary `.registers.txt` dump and [recovered_ps7_init_gpl.c](recovered_ps7_init_gpl.c). DDR I/O drive, termination, VREF and DCI writes are in [mio_annotated.txt](mio_annotated.txt); despite its name this generated table initializes DDR I/O as well as MIO.

**PL interfaces and address space**

The supplied ODS has been parsed and compared; the complete pin tables and verification results are included below. The bitstream packet analysis itself recovered no routes.

The requested `Boot_Modified_RK7020/BOOT.bin` does contain a PL configuration bitstream. Its four partition headers at 0xC80–0xD7F have valid checksums. The image-name table identifies the following contents:

| Image | Payload offset in BOOT.bin | Payload bytes |
|---|---|---|
| fsbl.elf | 0x1700 | 98,312 |
| download-zynq-generic-7z020.bit | 0x19740 | 2,489,280 |
| u-boot.elf | 0x279300 | 1,035,788 |
| system-top.dtb | 0x376140 | 29,292 |

The bitstream partition has attribute 0x20 (PL destination, FSBL-owned), and its payload contains configuration sync word 0xAA995566 at BOOT offset 0x19770, stored in little-endian word order. The normal FSBL flow loads this partition into the PL before handing control to U-Boot. These are boot-packaged payloads; the embedded `.bit` image name does not imply the original standalone `.bit` file header is retained. Header layout and PL attribute definitions are in [Xilinx image_mover.h](https://raw.githubusercontent.com/Xilinx/embeddedsw/master/lib/sw_apps/zynq_fsbl/src/image_mover.h). The compiled bitstream does not directly supply the original Vivado block design, HDL, or named XDC constraints.

| Address | PL device described by DT |
|---|---|
| 0x40400000 | AXI Ethernet DMA |
| 0x41000000 | AXI Ethernet, second RTL8211F PHY address 1, rgmii-rxid |
| 0x41200000, 0x41210000, 0x41220000, 0x41230000 | Four AXI GPIO controllers |
| 0x41600000 | AXI IIC, EEPROM at 0x50 |
| 0x43000000 | AXI VDMA, display read channel |
| 0x43C00000 | Digilent dynamic clock IP |
| 0x43C10000, 0x43C20000 | AXI UART16550, associated with RS485 application functions |
| 0x43C30000 | Video timing controller |

The 0x4xxxxxxx peripheral address region implies PS M_AXI_GP0 access. PL DMA and VDMA require a path into PS memory, but these files do not uniquely identify which S_AXI_HP port(s), widths, interconnect topology or ACP choices were used. Do not infer all HP ports are enabled because generic DDR arbitration registers are initialized.

PL interrupts in DT use GIC SPI offsets 29–36 and 52 (GIC IDs 61–68 and 84). These establish required interrupt connectivity, but do not reconstruct the original concat instance and block-diagram wiring. FCLK0 is referenced throughout the AXI peripherals; FCLK1 is referenced by the VDMA memory/video clocks. Keeping the same device tree requires recreating compatible PL hardware, not only the PS block.

**Interpretation of the other supplied files and remaining limits**

`board` and `bsp` contain `zynq-generic-7z020`; `board-variant` contains generic PetaLinux machine/override identifiers. They identify the software build target, not a ZedBoard/ZC702 PCB or Vivado preset. `burn_qspi.sh` identifies RK-ZYNQ7020-F and a QSPI/eMMC installation workflow; it contains no DDR training or MIO configuration. It was read as evidence and was not executed. The successful log and embedded FIT explain the script's partition order; the standalone DTBs describe a different partition layout.

The workspace `info.md` identifies a Riguke board and a 484-pin Zynq package. This is contextual information, not proof of the complete silicon ordering code or speed grade. The XDC found at workspace root concerns a separate PL pin investigation; its port names do not establish connections to the original design's EMIO nets. No original XSA/HDF, HWH, block design or board-specific PS preset was found in the workspace search.

The user confirms XC7Z020CLG484-2: device XC7Z020, package CLG484, speed grade -2. Use Vivado part identifier `xc7z020clg484-2`. The commercial/industrial temperature suffix was not supplied. To complete an exact Vivado reconstruction, the missing evidence is: FPGA temperature grade; actual DDR supply voltage; original DDR PCB delay inputs; and original internal PL routing/channel assignments. Physical peripheral nets are listed in the ODS tables below. An original XSA/HDF or Vivado project would supply most of this. Without it, recreate the proven PS settings above, regenerate ps7_init, compare its register arrays against these recovered values, and validate on the actual hardware. Matching DDR registers is a stronger comparison than merely choosing a familiar development-board preset.

For Vivado, use the identified MT41K256M16TW-107 part if available, with total bus width 32 bits and the recovered 533.333 MHz operating clock. The part's 1866 MT/s rating is its speed-bin capability, not the clock used by this boot image. Retain the recovered operating-point target (CL7/CWL6) when comparing generated initialization, subject to checking the selected part's timing requirements. Neither photograph resolves DDR PCB trace delays or trained runtime PHY values.


## Display and application findings

**Display identification from showbmptest and the running-system evidence**

`Filesystem/opt/showbmptest` is a 16,484-byte ARM ELF executable, dynamically linked through `/lib/ld-linux-armhf.so.3`. Its strings and symbols identify a generic BMP-to-framebuffer program: `showbmptest.c`, `show_bmp`, `show_picture`, `cursor_bitmap_format_convert`, `fb_info`, and `img_info`. It names `/dev/fb0`, imports `ioctl`, `mmap`, and BMP file-reading functions, and contains framebuffer geometry/color-layout diagnostics. There are no I2C device paths or display-controller names among its extracted printable strings. This establishes a framebuffer application; the executable alone does not identify the panel or a direct I2C interface.

The supplied successful `debug_output.txt`, line 269, explicitly binds the application's target framebuffer:

```text
graphics fb0: fb_st7789v frame buffer, 320x172, 107 KiB video memory, 4 KiB buffer memory, fps=33, spi1.0 at 32 MHz
```

The standalone DTBs and the FIT DTB matching that boot log declare `sitronix,st7789v` under PS SPI0 (`0xE0006000`). Thus the supported identification is a **Sitronix ST7789V-compatible TFT**, configured for **172 x 320 pixels**, rotated 270 degrees to a **320 x 172 framebuffer**, connected by **SPI**. The exact LCD module manufacturer, product number, diagonal size and controller silicon revision cannot be determined from this executable or the compatible string alone.

| Setting | Evidence-backed value |
|---|---|
| Linux driver in supplied system | `fb_st7789v`, FBTFT framework |
| Linux device | `/dev/fb0`, associated with `spi1.0` in this boot |
| Actual PS controller | SPI0, address 0xE0006000; DT alias makes it Linux SPI bus 1 |
| PS routing | EMIO; no SPI0 MIO mux selected in FSBL |
| Chip select | CS0 |
| SPI mode | 3 (`spi-cpol` and `spi-cpha`) |
| SPI maximum clock | 32 MHz |
| Display geometry | width 172, height 320, rotation 270 |
| Requested update rate | DT fps=30 |
| D/C GPIO | PS GPIO line 59 = EMIO GPIO5, active high |
| Reset GPIO | PS GPIO line 61 = EMIO GPIO7, active low |
| FBTFT buswidth property | 8; this is not an eight-wire SPI data bus |
| RGB property | Present |
| Physical package pins (ODS) | SCLK V18, MOSI U19, CS AA13, D/C W13, reset AA18, backlight Y13; original backlight control source unresolved |

To reproduce the existing Linux interface, use the kernel's [FBTFT ST7789V driver](https://github.com/torvalds/linux/blob/v6.1/drivers/staging/fbtft/fb_st7789v.c) and enable `CONFIG_FB_TFT` and `CONFIG_FB_TFT_ST7789V`, together with their framebuffer, SPI, GPIO and backlight dependencies. Module name: `fb_st7789v`. See [Kconfig](https://github.com/torvalds/linux/blob/v6.1/drivers/staging/fbtft/Kconfig). Preserve the board's existing DT node from `fit_system-top.dts` or the decompiled standalone DTB, including GPIO polarities and geometry.

This identifies the driver already working in the supplied log. The original kernel source was not supplied, so possible vendor modifications to panel initialization, gamma, inversion or display-window offsets remain unverified. A generic ST7789V driver may require panel-specific adjustments for this 172-pixel-wide module. Do not substitute a different ST7789V driver solely on the controller name without checking its pixel transport and framebuffer interface.

For Vivado, the display requires PS SPI0 through EMIO and GPIO EMIO5/7, with the ODS package assignments above. I2C1 is assigned to HDMI EDID in the device tree; it is a separate function from this SPI framebuffer display.

On the running board, `cat /sys/class/graphics/fb0/name` can confirm which driver currently owns fb0, since framebuffer numbering can change between builds. No executable from the supplied filesystem was run during this analysis.

## PS EMIO to physical board signals

The following associations combine the DT and the ODS. They are strong functional correlations for LCD/LED/key/HDMI, not a decoded netlist. Package assignments themselves are documented in the ODS.

| PS function | Physical signal and ball | Confidence / limit |
|---|---|---|
| SPI0 SCLK / MOSI / SS0 | LCD_SCL V18 / LCD_SDA U19 / LCD_CS AA13 | ODS + DT; no panel MISO connection identified |
| I2C1 SCL / SDA | HDMI1_SCL AA16 / HDMI1_SDA AB16 | ODS + DT EDID association |
| EMIO GPIO0 / GPIO1 | PL_LED1 V15 / PL_LED2 V13 | ODS + DT GPIO54/55; active high |
| EMIO GPIO2 / GPIO3 | PL_KEY1 W18 / PL_KEY2 V14 | ODS + DT GPIO56/57; active low |
| EMIO GPIO5 | LCD_DC W13 | ODS + DT GPIO59 |
| EMIO GPIO7 | LCD_RST AA18 | ODS + DT GPIO61; active low |
| CAN0 and CAN1 | Board CAN1 RX Y14, TX AA14; CAN2 RX W15, TX Y15 | Both PS controllers enabled via EMIO; channel order unproven |
| EMIO GPIO4 | Possibly FMC_PRSNT AB14 | Name-only candidate; DT direction conflict and FIT omission; unresolved |
| EMIO GPIO6/8/9/10 | Unresolved | Do not fill by elimination |

LCD_LED is Y13, PHY2_RST is Y21, RS485_DE1 is Y20 and RS485_DE2 is U22. Knowing these physical nets does not establish which EMIO/AXI GPIO bit drives them. Qt's legacy GPIO916/917 strings are insufficient to establish the GPIO-controller base or wiring.

RS485 TX/RX are PL UART signals, not evidence that PS UART1 should be enabled. FMC_SCL/SDA are R7/U7; association with AXI IIC at 0x41600000 is plausible but not proved by the spreadsheet. The camera nets do not prove that the supplied factory PL image contains a working CSI receiver.

## Complete board pin inventory from ODS

`PIN` means FPGA package ball, not a connector contact. Names and net spellings below preserve the workbook (including `MIPI_LAN`). PS has programmed LVCMOS33 on bank500 and LVCMOS18 on bank501. Published project XDC confirms LVCMOS33 for the eleven bank33 pins checked. The ODS does not specify IOSTANDARD, VCCO or external pull resistors: do not derive electrical standards solely from bank numbers. HDMI differential pairs and MIPI circuitry need interface-specific implementation. FMC VREF entries are reference-voltage connections, not generic outputs.

### PS

| Group | Package ball | Device pin name | Board net | ODS row |
|---|---|---|---|---|
| QSPI | A1 | PS_MIO1_500 | PS_MIO1_QSPI_CS | 3 |
| SD CARD | E14 | PS_MIO40_501 | SD_CLK | 3 |
| EMMC | D12 | PS_MIO46_501 | MMC_DAT0 | 3 |
| QSPI | A2 | PS_MIO2_500 | PS_MIO2_QSPI_DQ0 | 4 |
| SD CARD | C8 | PS_MIO41_501 | SD_CMD | 4 |
| EMMC | B10 | PS_MIO47_501 | MMC_CMD | 4 |
| QSPI | F6 | PS_MIO3_500 | PS_MIO3_QSPI_DQ1 | 5 |
| SD CARD | D8 | PS_MIO42_501 | SD_D0 | 5 |
| EMMC | D11 | PS_MIO48_501 | MMC_CLK | 5 |
| QSPI | E4 | PS_MIO4_500 | PS_MIO4_QSPI_DQ2 | 6 |
| SD CARD | B11 | PS_MIO43_501 | SD_D1 | 6 |
| EMMC | C14 | PS_MIO49_501 | MMC_DAT1 | 6 |
| QSPI | A3 | PS_MIO5_500 | PS_MIO5_QSPI_DQ3 | 7 |
| SD CARD | E13 | PS_MIO44_501 | SD_D2 | 7 |
| EMMC | D13 | PS_MIO50_501 | MMC_DAT2 | 7 |
| QSPI | A4 | PS_MIO6_500 | PS_MIO6_QSPI_CLK | 8 |
| SD CARD | B9 | PS_MIO45_501 | SD_D3 | 8 |
| EMMC | C10 | PS_MIO51_501 | MMC_DAT3 | 8 |
| SD CARD | C4 | PS_MIO9_500 | PS_MIO9_SD_CD | 9 |
| PS ETH | D6 | PS_MIO16_501 | PHY1_TXCK | 14 |
| USB | A12 | PS_MIO28_501 | USB_DATA4 | 14 |
| I2C | B6 | PS_MIO14_500 | PS_MIO14_IIC0_SCL | 14 |
| PS ETH | E9 | PS_MIO17_501 | PHY1_TXD0 | 15 |
| USB | E8 | PS_MIO29_501 | USB_DIR | 15 |
| I2C | E6 | PS_MIO15_500 | PS_MIO15_IIC0_SDA | 15 |
| PS ETH | A7 | PS_MIO18_501 | PHY1_TXD1 | 16 |
| USB | A11 | PS_MIO30_501 | USB_STP | 16 |
| PS ETH | E10 | PS_MIO19_501 | PHY1_TXD2 | 17 |
| USB | F9 | PS_MIO31_501 | USB_NXT | 17 |
| PS ETH | A8 | PS_MIO20_501 | PHY1_TXD3 | 18 |
| USB | C7 | PS_MIO32_501 | USB_DATA0 | 18 |
| PS ETH | F11 | PS_MIO21_501 | PHY1_TXCTL | 19 |
| USB | G13 | PS_MIO33_501 | USB_DATA1 | 19 |
| PS ETH | A14 | PS_MIO22_501 | PHY1_RXCK | 20 |
| USB | B12 | PS_MIO34_501 | USB_DATA2 | 20 |
| PS ETH | E11 | PS_MIO23_501 | PHY1_RXD0 | 21 |
| USB | F14 | PS_MIO35_501 | USB_DATA3 | 21 |
| PS ETH | B7 | PS_MIO24_501 | PHY1_RXD1 | 22 |
| USB | A9 | PS_MIO36_501 | USB_CLK | 22 |
| PS ETH | F12 | PS_MIO25_501 | PHY1_RXD2 | 23 |
| USB | B14 | PS_MIO37_501 | USB_DATA5 | 23 |
| PS ETH | A13 | PS_MIO26_501 | PHY1_RXD3 | 24 |
| USB | F13 | PS_MIO38_501 | USB_DATA6 | 24 |
| PS ETH | D7 | PS_MIO27_501 | PHY1_RXCTL | 25 |
| USB | C13 | PS_MIO39_501 | USB_DATA7 | 25 |
| PS ETH | D10 | PS_MIO52_501 | PHY1_MDC | 26 |
| USB | A6 | PS_MIO13_500 | PS_MIO13_USB_RST | 26 |
| PS ETH | C12 | PS_MIO53_501 | PHY1_MDIO | 27 |
| PS LED | D5 | PS_MIO7_500 | PS_MIO7_LED2 | 32 |
| PS KEY | G6 | PS_MIO0_500 | PS_MIO0_KEY1 | 32 |
| UART | G7 | PS_MIO10_500 | PS_MIO10_UART_RX | 32 |
| PS LED | E5 | PS_MIO8_500 | PS_MIO8_LED1 | 33 |
| PS KEY | C5 | PS_MIO12_500 | PS_MIO12_KEY2 | 33 |
| UART | B4 | PS_MIO11_500 | PS_MIO11_UART_TX | 33 |

### 40 PIN

| Group | Package ball | Device pin name | Board net | ODS row |
|---|---|---|---|---|
| 40 PIN | W12 | IO_L4N_T0_13 | IO1_N | 3 |
| 40 PIN | V12 | IO_L4P_T0_13 | IO1_P | 4 |
| 40 PIN | V9 | IO_L1N_T0_13 | IO2_N | 5 |
| 40 PIN | V10 | IO_L1P_T0_13 | IO2_P | 6 |
| 40 PIN | U9 | IO_L6N_T0_VREF_13 | IO3_N | 7 |
| 40 PIN | U10 | IO_L6P_T0_13 | IO3_P | 8 |
| 40 PIN | AB12 | IO_L7N_T1_13 | IO4_N | 9 |
| 40 PIN | AA12 | IO_L7P_T1_13 | IO4_P | 10 |
| 40 PIN | Y10 | IO_L10N_T1_13 | IO5_N | 11 |
| 40 PIN | Y11 | IO_L10P_T1_13 | IO5_P | 12 |
| 40 PIN | U11 | IO_L5N_T0_13 | IO6_N | 13 |
| 40 PIN | U12 | IO_L5P_T0_13 | IO6_P | 14 |
| 40 PIN | AB9 | IO_L9N_T1_DQS_13 | IO7_N | 15 |
| 40 PIN | AB10 | IO_L9P_T1_DQS_13 | IO7_P | 16 |
| 40 PIN | AB11 | IO_L8N_T1_13 | IO8_N | 17 |
| 40 PIN | AA11 | IO_L8P_T1_13 | IO8_P | 18 |
| 40 PIN | W8 | IO_L2N_T0_13 | IO9_N | 19 |
| 40 PIN | V8 | IO_L2P_T0_13 | IO9_P | 20 |
| 40 PIN | W10 | IO_L3N_T0_DQS_13 | IO10_N | 21 |
| 40 PIN | W11 | IO_L3P_T0_DQS_13 | IO10_P | 22 |
| 40 PIN | AB6 | IO_L17N_T2_13 | IO11_N | 23 |
| 40 PIN | AB7 | IO_L17P_T2_13 | IO11_P | 24 |
| 40 PIN | AA8 | IO_L11N_T1_SRCC_13 | IO12_N | 25 |
| 40 PIN | AA9 | IO_L11P_T1_SRCC_13 | IO12_P | 26 |
| 40 PIN | AB4 | IO_L16N_T2_13 | IO13_N | 27 |
| 40 PIN | AB5 | IO_L16P_T2_13 | IO13_P | 28 |
| 40 PIN | AA6 | IO_L14N_T2_SRCC_13 | IO14_N | 29 |
| 40 PIN | AA7 | IO_L14P_T2_SRCC_13 | IO14_P | 30 |
| 40 PIN | Y5 | IO_L13N_T2_MRCC_13 | IO15_N | 31 |
| 40 PIN | Y6 | IO_L13P_T2_MRCC_13 | IO15_P | 32 |
| 40 PIN | AA4 | IO_L18N_T2_13 | IO16_N | 33 |
| 40 PIN | Y4 | IO_L18P_T2_13 | IO16_P | 34 |
| 40 PIN | AB1 | IO_L15N_T2_DQS_13 | IO17_N | 35 |
| 40 PIN | AB2 | IO_L15P_T2_DQS_13 | IO17_P | 36 |

### FMC

| Group | Package ball | Device pin name | Board net | ODS row |
|---|---|---|---|---|
| FMC | L19 | IO_L12N_T1_MRCC_34 | FMC_CLK0_N | 3 |
| FMC COM | AB14 | IO_L24P_T3_33 | FMC_PRSNT | 3 |
| FMC | L18 | IO_L12P_T1_MRCC_34 | FMC_CLK0_P | 4 |
| FMC COM | R7 | IO_0_13 | FMC_SCL | 4 |
| FMC | C19 | IO_L12N_T1_MRCC_35 | FMC_CLK1_N | 5 |
| FMC COM | U7 | IO_25_13 | FMC_SDA | 5 |
| FMC | D18 | IO_L12P_T1_MRCC_35 | FMC_CLK1_P | 6 |
| FMC COM | F17 | IO_L6N_T0_VREF_35 | FMC_VREF | 6 |
| FMC | M20 | IO_L13N_T2_MRCC_34 | FMC_LA00_CC_N | 7 |
| FMC COM | H20 | IO_L19N_T3_VREF_35 | FMC_VREF | 7 |
| FMC | M19 | IO_L13P_T2_MRCC_34 | FMC_LA00_CC_P | 8 |
| FMC COM | M16 | IO_L6N_T0_VREF_34 | FMC_VREF | 8 |
| FMC | N20 | IO_L14N_T2_SRCC_34 | FMC_LA01_CC_N | 9 |
| FMC COM | P15 | IO_L19N_T3_VREF_34 | FMC_VREF | 9 |
| FMC | N19 | IO_L14P_T2_SRCC_34 | FMC_LA01_CC_P | 10 |
| FMC | P18 | IO_L20N_T3_34 | FMC_LA02_N | 11 |
| FMC | P17 | IO_L20P_T3_34 | FMC_LA02_P | 12 |
| FMC | P22 | IO_L16N_T2_34 | FMC_LA03_N | 13 |
| FMC | N22 | IO_L16P_T2_34 | FMC_LA03_P | 14 |
| FMC | M22 | IO_L15N_T2_DQS_34 | FMC_LA04_N | 15 |
| FMC | M21 | IO_L15P_T2_DQS_34 | FMC_LA04_P | 16 |
| FMC | K18 | IO_L7N_T1_34 | FMC_LA05_N | 17 |
| FMC | J18 | IO_L7P_T1_34 | FMC_LA05_P | 18 |
| FMC | L22 | IO_L10N_T1_34 | FMC_LA06_N | 19 |
| FMC | L21 | IO_L10P_T1_34 | FMC_LA06_P | 20 |
| FMC | T17 | IO_L21N_T3_DQS_34 | FMC_LA07_N | 21 |
| FMC | T16 | IO_L21P_T3_DQS_34 | FMC_LA07_P | 22 |
| FMC | J22 | IO_L8N_T1_34 | FMC_LA08_N | 23 |
| FMC | J21 | IO_L8P_T1_34 | FMC_LA08_P | 24 |
| FMC | R21 | IO_L17N_T2_34 | FMC_LA09_N | 25 |
| FMC | R20 | IO_L17P_T2_34 | FMC_LA09_P | 26 |
| FMC | T19 | IO_L22N_T3_34 | FMC_LA10_N | 27 |
| FMC | R19 | IO_L22P_T3_34 | FMC_LA10_P | 28 |
| FMC | N18 | IO_L5N_T0_34 | FMC_LA11_N | 29 |
| FMC | N17 | IO_L5P_T0_34 | FMC_LA11_P | 30 |
| FMC | P21 | IO_L18N_T2_34 | FMC_LA12_N | 31 |
| FMC | P20 | IO_L18P_T2_34 | FMC_LA12_P | 32 |
| FMC | M17 | IO_L4N_T0_34 | FMC_LA13_N | 33 |
| FMC | L17 | IO_L4P_T0_34 | FMC_LA13_P | 34 |
| FMC | K20 | IO_L11N_T1_SRCC_34 | FMC_LA14_N | 35 |
| FMC | K19 | IO_L11P_T1_SRCC_34 | FMC_LA14_P | 36 |
| FMC | J17 | IO_L2N_T0_34 | FMC_LA15_N | 37 |
| FMC | J16 | IO_L2P_T0_34 | FMC_LA15_P | 38 |
| FMC | K21 | IO_L9N_T1_DQS_34 | FMC_LA16_N | 39 |
| FMC | J20 | IO_L9P_T1_DQS_34 | FMC_LA16_P | 40 |
| FMC | B20 | IO_L13N_T2_MRCC_35 | FMC_LA17_CC_N | 41 |
| FMC | B19 | IO_L13P_T2_MRCC_35 | FMC_LA17_CC_P | 42 |
| FMC | C20 | IO_L14N_T2_AD4N_SRCC_35 | FMC_LA18_CC_N | 43 |
| FMC | D20 | IO_L14P_T2_AD4P_SRCC_35 | FMC_LA18_CC_P | 44 |
| FMC | G16 | IO_L4N_T0_35 | FMC_LA19_N | 45 |
| FMC | G15 | IO_L4P_T0_35 | FMC_LA19_P | 46 |
| FMC | G21 | IO_L22N_T3_AD7N_35 | FMC_LA20_N | 47 |
| FMC | G20 | IO_L22P_T3_AD7P_35 | FMC_LA20_P | 48 |
| FMC | E20 | IO_L21N_T3_DQS_AD14N_35 | FMC_LA21_N | 49 |
| FMC | E19 | IO_L21P_T3_DQS_AD14P_35 | FMC_LA21_P | 50 |
| FMC | F19 | IO_L20N_T3_AD6N_35 | FMC_LA22_N | 51 |
| FMC | G19 | IO_L20P_T3_AD6P_35 | FMC_LA22_P | 52 |
| FMC | D15 | IO_L3N_T0_DQS_AD1N_35 | FMC_LA23_N | 53 |
| FMC | E15 | IO_L3P_T0_DQS_AD1P_35 | FMC_LA23_P | 54 |
| FMC | A19 | IO_L10N_T1_AD11N_35 | FMC_LA24_N | 55 |
| FMC | A18 | IO_L10P_T1_AD11P_35 | FMC_LA24_P | 56 |
| FMC | C22 | IO_L16N_T2_35 | FMC_LA25_N | 57 |
| FMC | D22 | IO_L16P_T2_35 | FMC_LA25_P | 58 |
| FMC | E18 | IO_L5N_T0_AD9N_35 | FMC_LA26_N | 59 |
| FMC | F18 | IO_L5P_T0_AD9P_35 | FMC_LA26_P | 60 |
| FMC | D21 | IO_L17N_T2_AD5N_35 | FMC_LA27_N | 61 |
| FMC | E21 | IO_L17P_T2_AD5P_35 | FMC_LA27_P | 62 |
| FMC | A17 | IO_L9N_T1_DQS_AD3N_35 | FMC_LA28_N | 63 |
| FMC | A16 | IO_L9P_T1_DQS_AD3P_35 | FMC_LA28_P | 64 |
| FMC | C18 | IO_L11N_T1_SRCC_35 | FMC_LA29_N | 65 |
| FMC | C17 | IO_L11P_T1_SRCC_35 | FMC_LA29_P | 66 |
| FMC | B15 | IO_L7N_T1_AD2N_35 | FMC_LA30_N | 67 |
| FMC | C15 | IO_L7P_T1_AD2P_35 | FMC_LA30_P | 68 |
| FMC | B17 | IO_L8N_T1_AD10N_35 | FMC_LA31_N | 69 |
| FMC | B16 | IO_L8P_T1_AD10P_35 | FMC_LA31_P | 70 |
| FMC | A22 | IO_L15N_T2_DQS_AD12N_35 | FMC_LA32_N | 71 |
| FMC | A21 | IO_L15P_T2_DQS_AD12P_35 | FMC_LA32_P | 72 |
| FMC | B22 | IO_L18N_T2_AD13N_35 | FMC_LA33_N | 73 |
| FMC | B21 | IO_L18P_T2_AD13P_35 | FMC_LA33_P | 74 |

### 其他

| Group | Package ball | Device pin name | Board net | ODS row |
|---|---|---|---|---|
| PL ETH | Y19 | IO_L11P_T1_SRCC_33 | PHY2_RXCK | 3 |
| HDMI | Y16 | IO_L14N_T2_SRCC_33 | HDMI1_CLK_N | 3 |
| MIPI | Y8 | IO_L12N_T1_MRCC_13 | MIPI_CLK_N | 3 |
| PL ETH | V19 | IO_L6N_T0_VREF_33 | PHY2_RXCTL | 4 |
| HDMI | W16 | IO_L14P_T2_SRCC_33 | HDMI1_CLK_P | 4 |
| MIPI | Y9 | IO_L12P_T1_MRCC_13 | MIPI_CLK_P | 4 |
| PL ETH | W20 | IO_L4P_T0_33 | PHY2_RXD0 | 5 |
| HDMI | AB17 | IO_L17N_T2_33 | HDMI1_DATA0_N | 5 |
| MIPI | W5 | IO_L24N_T3_13 | MIPI_LAN0_N | 5 |
| PL ETH | W21 | IO_L4N_T0_33 | PHY2_RXD1 | 6 |
| HDMI | AA17 | IO_L17P_T2_33 | HDMI1_DATA0_P | 6 |
| MIPI | W6 | IO_L24P_T3_13 | MIPI_LAN0_P | 6 |
| PL ETH | U20 | IO_L5P_T0_33 | PHY2_RXD2 | 7 |
| HDMI | V17 | IO_L16N_T2_33 | HDMI1_DATA1_N | 7 |
| MIPI | U4 | IO_L20N_T3_13 | MIPI_LAN1_N | 7 |
| PL ETH | V20 | IO_L5N_T0_33 | PHY2_RXD3 | 8 |
| HDMI | U17 | IO_L16P_T2_33 | HDMI1_DATA1_P | 8 |
| MIPI | T4 | IO_L20P_T3_13 | MIPI_LAN1_P | 8 |
| PL ETH | AB22 | IO_L7N_T1_33 | PHY2_TXCK | 9 |
| HDMI | U16 | IO_L15N_T2_DQS_33 | HDMI1_DATA2_N | 9 |
| MIPI | T6 | IO_L19N_T3_VREF_13 | MIPI_LP0_N | 9 |
| PL ETH | AB21 | IO_L8N_T1_33 | PHY2_TXCTL | 10 |
| HDMI | U15 | IO_L15P_T2_DQS_33 | HDMI1_DATA2_P | 10 |
| MIPI | R6 | IO_L19P_T3_13 | MIPI_LP0_P | 10 |
| PL ETH | T21 | IO_L1P_T0_33 | PHY2_TXD0 | 11 |
| HDMI | Y18 | IO_L12P_T1_MRCC_33 | HDMI1_HPD | 11 |
| MIPI | W7 | IO_L23N_T3_13 | MIPI_LP1_N | 11 |
| PL ETH | U21 | IO_L1N_T0_33 | PHY2_TXD1 | 12 |
| HDMI | AA16 | IO_L18P_T2_33 | HDMI1_SCL | 12 |
| MIPI | V7 | IO_L23P_T3_13 | MIPI_LP1_P | 12 |
| PL ETH | AA22 | IO_L7P_T1_33 | PHY2_TXD2 | 13 |
| HDMI | AB16 | IO_L18N_T2_33 | HDMI1_SDA | 13 |
| MIPI | U5 | IO_L22N_T3_13 | MIPI_LPCLK_N | 13 |
| PL ETH | AA21 | IO_L8P_T1_33 | PHY2_TXD3 | 14 |
| MIPI | U6 | IO_L22P_T3_13 | MIPI_LPCLK_P | 14 |
| PL ETH | Y21 | IO_L9N_T1_DQS_33 | PHY2_RST | 15 |
| MIPI | U14 | IO_25_33 | CAM_CLK | 15 |
| PL ETH | AB20 | IO_L10N_T1_33 | PHY2_MDC | 16 |
| MIPI | AB15 | IO_L24N_T3_33 | CAM_GPIO | 16 |
| PL ETH | AB19 | IO_L10P_T1_33 | PHY2_MDIO | 17 |
| MIPI | V5 | IO_L21P_T3_DQS_13 | CAM_SCL | 17 |
| MIPI | V4 | IO_L21N_T3_DQS_13 | CAM_SDA | 18 |
| CAN | Y14 | IO_L22P_T3_33 | CAN1_RX | 23 |
| RS485 | AA19 | IO_L11N_T1_SRCC_33 | RS485_RXD1 | 23 |
| LCD | AA13 | IO_L23N_T3_33 | LCD_CS | 23 |
| CAN | AA14 | IO_L22N_T3_33 | CAN1_TX | 24 |
| RS485 | W22 | IO_L3N_T0_DQS_33 | RS485_TXD1 | 24 |
| LCD | W13 | IO_L20N_T3_33 | LCD_DC | 24 |
| CAN | W15 | IO_L21P_T3_DQS_33 | CAN2_RX | 25 |
| RS485 | Y20 | IO_L9P_T1_DQS_33 | RS485_DE1 | 25 |
| LCD | Y13 | IO_L23P_T3_33 | LCD_LED | 25 |
| CAN | Y15 | IO_L21N_T3_DQS_33 | CAN2_TX | 26 |
| RS485 | V22 | IO_L3P_T0_DQS_33 | RS485_RXD2 | 26 |
| LCD | AA18 | IO_L12N_T1_MRCC_33 | LCD_RST | 26 |
| RS485 | T22 | IO_L2P_T0_33 | RS485_TXD2 | 27 |
| LCD | V18 | IO_L6P_T0_33 | LCD_SCL | 27 |
| RS485 | U22 | IO_L2N_T0_33 | RS485_DE2 | 28 |
| LCD | U19 | IO_0_33 | LCD_SDA | 28 |
| PL LED | V15 | IO_L19N_T3_VREF_33 | PL_LED1 | 33 |
| PL KEY | W18 | IO_L13N_T2_MRCC_33 | PL_KEY1 | 33 |
| PL CLK | W17 | IO_L13P_T2_MRCC_33 | PL_CLK | 33 |
| PL LED | V13 | IO_L20P_T3_33 | PL_LED2 | 34 |
| PL KEY | V14 | IO_L19P_T3_33 | PL_KEY2 | 34 |

## Complete MIO electrical settings with package balls

| MIO | Ball | Function | Standard | Pullup | TRI_ENABLE | Register | Mask | Value |
|---|---|---|---|---|---|---|---|---|
| 0 | G6 | GPIO: ps_key1 | LVCMOS33 | 1 | 0 | 0xF8000700 | 0x00003FFF | 0x00001600 |
| 1 | A1 | QSPI0 CS0# | LVCMOS33 | 1 | 0 | 0xF8000704 | 0x00003FFF | 0x00001602 |
| 2 | A2 | QSPI0 DQ0 | LVCMOS33 | 0 | 0 | 0xF8000708 | 0x00003FFF | 0x00000602 |
| 3 | F6 | QSPI0 DQ1 | LVCMOS33 | 0 | 0 | 0xF800070C | 0x00003FFF | 0x00000602 |
| 4 | E4 | QSPI0 DQ2 | LVCMOS33 | 0 | 0 | 0xF8000710 | 0x00003FFF | 0x00000602 |
| 5 | A3 | QSPI0 DQ3 | LVCMOS33 | 0 | 0 | 0xF8000714 | 0x00003FFF | 0x00000602 |
| 6 | A4 | QSPI0 SCLK | LVCMOS33 | 0 | 0 | 0xF8000718 | 0x00003FFF | 0x00000602 |
| 7 | D5 | GPIO: ps_led2 | LVCMOS33 | 0 | 0 | 0xF800071C | 0x00003FFF | 0x00000600 |
| 8 | E5 | GPIO: ps_led1 (QSPI feedback clock not selected) | LVCMOS33 | 0 | 0 | 0xF8000720 | 0x00003FFF | 0x00000600 |
| 9 | C4 | SD0 card detect (input tap) | LVCMOS33 | 1 | 1 | 0xF8000724 | 0x00003F01 | 0x00001601 |
| 10 | G7 | UART0 RX | LVCMOS33 | 1 | 1 | 0xF8000728 | 0x00003FFF | 0x000016E1 |
| 11 | B4 | UART0 TX | LVCMOS33 | 1 | 0 | 0xF800072C | 0x00003FFF | 0x000016E0 |
| 12 | C5 | GPIO: ps_key2 | LVCMOS33 | 1 | 0 | 0xF8000730 | 0x00003FFF | 0x00001600 |
| 13 | A6 | GPIO: USB0 PHY reset | LVCMOS33 | 1 | 0 | 0xF8000734 | 0x00003FFF | 0x00001600 |
| 14 | B6 | I2C0 SCL | LVCMOS33 | 1 | 0 | 0xF8000738 | 0x00003FFF | 0x00001640 |
| 15 | E6 | I2C0 SDA | LVCMOS33 | 1 | 0 | 0xF800073C | 0x00003FFF | 0x00001640 |
| 16 | D6 | GEM0 TX_CLK | LVCMOS18 | 1 | 0 | 0xF8000740 | 0x00003FFF | 0x00001202 |
| 17 | E9 | GEM0 TXD0 | LVCMOS18 | 1 | 0 | 0xF8000744 | 0x00003FFF | 0x00001202 |
| 18 | A7 | GEM0 TXD1 | LVCMOS18 | 1 | 0 | 0xF8000748 | 0x00003FFF | 0x00001202 |
| 19 | E10 | GEM0 TXD2 | LVCMOS18 | 1 | 0 | 0xF800074C | 0x00003FFF | 0x00001202 |
| 20 | A8 | GEM0 TXD3 | LVCMOS18 | 1 | 0 | 0xF8000750 | 0x00003FFF | 0x00001202 |
| 21 | F11 | GEM0 TX_CTL | LVCMOS18 | 1 | 0 | 0xF8000754 | 0x00003FFF | 0x00001202 |
| 22 | A14 | GEM0 RX_CLK | LVCMOS18 | 1 | 1 | 0xF8000758 | 0x00003FFF | 0x00001203 |
| 23 | E11 | GEM0 RXD0 | LVCMOS18 | 1 | 1 | 0xF800075C | 0x00003FFF | 0x00001203 |
| 24 | B7 | GEM0 RXD1 | LVCMOS18 | 1 | 1 | 0xF8000760 | 0x00003FFF | 0x00001203 |
| 25 | F12 | GEM0 RXD2 | LVCMOS18 | 1 | 1 | 0xF8000764 | 0x00003FFF | 0x00001203 |
| 26 | A13 | GEM0 RXD3 | LVCMOS18 | 1 | 1 | 0xF8000768 | 0x00003FFF | 0x00001203 |
| 27 | D7 | GEM0 RX_CTL | LVCMOS18 | 1 | 1 | 0xF800076C | 0x00003FFF | 0x00001203 |
| 28 | A12 | USB0 ULPI D4 | LVCMOS18 | 1 | 0 | 0xF8000770 | 0x00003FFF | 0x00001204 |
| 29 | E8 | USB0 ULPI DIR | LVCMOS18 | 1 | 1 | 0xF8000774 | 0x00003FFF | 0x00001205 |
| 30 | A11 | USB0 ULPI STP | LVCMOS18 | 1 | 0 | 0xF8000778 | 0x00003FFF | 0x00001204 |
| 31 | F9 | USB0 ULPI NXT | LVCMOS18 | 1 | 1 | 0xF800077C | 0x00003FFF | 0x00001205 |
| 32 | C7 | USB0 ULPI D0 | LVCMOS18 | 1 | 0 | 0xF8000780 | 0x00003FFF | 0x00001204 |
| 33 | G13 | USB0 ULPI D1 | LVCMOS18 | 1 | 0 | 0xF8000784 | 0x00003FFF | 0x00001204 |
| 34 | B12 | USB0 ULPI D2 | LVCMOS18 | 1 | 0 | 0xF8000788 | 0x00003FFF | 0x00001204 |
| 35 | F14 | USB0 ULPI D3 | LVCMOS18 | 1 | 0 | 0xF800078C | 0x00003FFF | 0x00001204 |
| 36 | A9 | USB0 ULPI CLK | LVCMOS18 | 1 | 1 | 0xF8000790 | 0x00003FFF | 0x00001205 |
| 37 | B14 | USB0 ULPI D5 | LVCMOS18 | 1 | 0 | 0xF8000794 | 0x00003FFF | 0x00001204 |
| 38 | F13 | USB0 ULPI D6 | LVCMOS18 | 1 | 0 | 0xF8000798 | 0x00003FFF | 0x00001204 |
| 39 | C13 | USB0 ULPI D7 | LVCMOS18 | 1 | 0 | 0xF800079C | 0x00003FFF | 0x00001204 |
| 40 | E14 | SD0 CLK | LVCMOS18 | 1 | 0 | 0xF80007A0 | 0x00003FFF | 0x00001280 |
| 41 | C8 | SD0 CMD | LVCMOS18 | 1 | 0 | 0xF80007A4 | 0x00003FFF | 0x00001280 |
| 42 | D8 | SD0 D0 | LVCMOS18 | 1 | 0 | 0xF80007A8 | 0x00003FFF | 0x00001280 |
| 43 | B11 | SD0 D1 | LVCMOS18 | 1 | 0 | 0xF80007AC | 0x00003FFF | 0x00001280 |
| 44 | E13 | SD0 D2 | LVCMOS18 | 1 | 0 | 0xF80007B0 | 0x00003FFF | 0x00001280 |
| 45 | B9 | SD0 D3 | LVCMOS18 | 1 | 0 | 0xF80007B4 | 0x00003FFF | 0x00001280 |
| 46 | D12 | SD1 D0 | LVCMOS18 | 1 | 0 | 0xF80007B8 | 0x00003FFF | 0x00001280 |
| 47 | B10 | SD1 CMD | LVCMOS18 | 1 | 0 | 0xF80007BC | 0x00003FFF | 0x00001280 |
| 48 | D11 | SD1 CLK | LVCMOS18 | 1 | 0 | 0xF80007C0 | 0x00003FFF | 0x00001280 |
| 49 | C14 | SD1 D1 | LVCMOS18 | 1 | 0 | 0xF80007C4 | 0x00003FFF | 0x00001280 |
| 50 | D13 | SD1 D2 | LVCMOS18 | 1 | 0 | 0xF80007C8 | 0x00003FFF | 0x00001280 |
| 51 | C10 | SD1 D3 | LVCMOS18 | 1 | 0 | 0xF80007CC | 0x00003FFF | 0x00001280 |
| 52 | D10 | GEM0 MDC | LVCMOS18 | 1 | 0 | 0xF80007D0 | 0x00003FFF | 0x00001280 |
| 53 | C12 | GEM0 MDIO | LVCMOS18 | 1 | 0 | 0xF80007D4 | 0x00003FFF | 0x00001280 |

## Vivado reconstruction and remaining limits

Select `xc7z020clg484-2`, reproduce the PS settings and 11-bit GPIO EMIO bus above, and route the documented board nets to appropriate ports. The 50 MHz PL oscillator is W17, separate from PS_CLK and FCLK outputs. Implement compatible AXI addresses, interrupts, DMA memory paths and video clocks for the chosen DT. Replace matching `Unused_*` placeholder constraints before assigning peripheral ports to those same balls; active project constraints were not changed here.

The original M_AXI_GP0-based peripheral map is recoverable, but exact HP/ACP port choices, AXI topology, interrupt concatenation and all internal control-bit assignments remain unknown. The compressed PL bitstream was extracted and packet-parsed: IDCODE 0x03727093, 4484 MFWR writes, 2489280 bytes. Configuration CRCs, decompressed frames and routing have not been validated. Packet parsing does not recover original HDL or named nets.

The ODS does not provide DDR dedicated-pin wiring, trace lengths, PCB delay inputs, measured supply voltage, a silicon temperature suffix, or an exact Vivado memory-part selection. The likely D9SHD memory identification and recovered timings remain as described above. Other schematic/revision PDFs now exist under `1_hardware/V1.1`; their contents were not evaluated for this ODS comparison and are not cited as corroboration.

Compare regenerated PS initialization against the recovered arrays before hardware testing. In particular retain FCLK1=153.333 MHz and CAN clock enables; the older local source's clock arrays differ. None of this establishes a complete vendor XSA/HDF, board preset or buildable factory project.

## Source provenance and validation

ODS SHA256: `29151104b8672679d1beeffa64c73876153af78fc7d9b22ade1c1d642bde80db`. Extracted 230 pin records, including 54 MIOs; package balls are unique. Header comparison: 34/34. Prior eleven-pin comparison: 11/11.

Original XLS SHA256: `cf681cef4630a2d1e21696e2943ba7918248d22f9924a3eb0611f2d0800b0f82`. The ODS conversion was supplied by the user; binary equivalence of the two formats is not claimed.

[Supplied ODS](../../1_hardware/ZYNQ7020-F%20V1.0%20V1.1%20管脚定义.ods). Public cross-checks: [LCD XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/ps_axi_pins.xdc), [board XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/rk_zynq7020_f_v11.xdc), [pinout](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/docs/pinout.md). Downloaded reference files are retained beside this report. No external document instructions were executed.

## Appendix: complete decoded DDR initialization fields

```text
// .. .. reg_ddrc_soft_rstb = 0
// .. .. reg_ddrc_powerdown_en = 0x0
// .. .. reg_ddrc_data_bus_width = 0x0
// .. .. reg_ddrc_burst8_refresh = 0x0
// .. .. reg_ddrc_rdwr_idle_gap = 0x1
// .. .. reg_ddrc_dis_rd_bypass = 0x0
// .. .. reg_ddrc_dis_act_bypass = 0x0
// .. .. reg_ddrc_dis_auto_refresh = 0x0
EMIT_MASKWRITE(0XF8006000, 0x0001FFFFU ,0x00000080U),
// .. .. reg_ddrc_t_rfc_nom_x32 = 0x82
// .. .. reserved_reg_ddrc_active_ranks = 0x1
// .. .. reg_ddrc_addrmap_cs_bit0 = 0x0
EMIT_MASKWRITE(0XF8006004, 0x0007FFFFU ,0x00001082U),
// .. .. reg_ddrc_hpr_min_non_critical_x32 = 0xf
// .. .. reg_ddrc_hpr_max_starve_x32 = 0xf
// .. .. reg_ddrc_hpr_xact_run_length = 0xf
EMIT_MASKWRITE(0XF8006008, 0x03FFFFFFU ,0x03C0780FU),
// .. .. reg_ddrc_lpr_min_non_critical_x32 = 0x1
// .. .. reg_ddrc_lpr_max_starve_x32 = 0x2
// .. .. reg_ddrc_lpr_xact_run_length = 0x8
EMIT_MASKWRITE(0XF800600C, 0x03FFFFFFU ,0x02001001U),
// .. .. reg_ddrc_w_min_non_critical_x32 = 0x1
// .. .. reg_ddrc_w_xact_run_length = 0x8
// .. .. reg_ddrc_w_max_starve_x32 = 0x2
EMIT_MASKWRITE(0XF8006010, 0x03FFFFFFU ,0x00014001U),
// .. .. reg_ddrc_t_rc = 0x1b
// .. .. reg_ddrc_t_rfc_min = 0xa1
// .. .. reg_ddrc_post_selfref_gap_x32 = 0x10
EMIT_MASKWRITE(0XF8006014, 0x001FFFFFU ,0x0004285BU),
// .. .. reg_ddrc_wr2pre = 0x13
// .. .. reg_ddrc_powerdown_to_x32 = 0x6
// .. .. reg_ddrc_t_faw = 0x16
// .. .. reg_ddrc_t_ras_max = 0x24
// .. .. reg_ddrc_t_ras_min = 0x13
// .. .. reg_ddrc_t_cke = 0x4
EMIT_MASKWRITE(0XF8006018, 0xF7FFFFFFU ,0x44E458D3U),
// .. .. reg_ddrc_write_latency = 0x5
// .. .. reg_ddrc_rd2wr = 0x7
// .. .. reg_ddrc_wr2rd = 0xf
// .. .. reg_ddrc_t_xp = 0x5
// .. .. reg_ddrc_pad_pd = 0x0
// .. .. reg_ddrc_rd2pre = 0x5
// .. .. reg_ddrc_t_rcd = 0x7
EMIT_MASKWRITE(0XF800601C, 0xFFFFFFFFU ,0x7282BCE5U),
// .. .. reg_ddrc_t_ccd = 0x4
// .. .. reg_ddrc_t_rrd = 0x6
// .. .. reg_ddrc_refresh_margin = 0x2
// .. .. reg_ddrc_t_rp = 0x7
// .. .. reg_ddrc_refresh_to_x32 = 0x8
// .. .. reg_ddrc_mobile = 0x0
// .. .. reg_ddrc_en_dfi_dram_clk_disable = 0x0
// .. .. reg_ddrc_read_latency = 0x7
// .. .. reg_phy_mode_ddr1_ddr2 = 0x1
// .. .. reg_ddrc_dis_pad_pd = 0x0
EMIT_MASKWRITE(0XF8006020, 0x7FDFFFFCU ,0x270872D0U),
// .. .. reg_ddrc_en_2t_timing_mode = 0x0
// .. .. reg_ddrc_prefer_write = 0x0
// .. .. reg_ddrc_mr_wr = 0x0
// .. .. reg_ddrc_mr_addr = 0x0
// .. .. reg_ddrc_mr_data = 0x0
// .. .. ddrc_reg_mr_wr_busy = 0x0
// .. .. reg_ddrc_mr_type = 0x0
// .. .. reg_ddrc_mr_rdata_valid = 0x0
EMIT_MASKWRITE(0XF8006024, 0x0FFFFFC3U ,0x00000000U),
// .. .. reg_ddrc_final_wait_x32 = 0x7
// .. .. reg_ddrc_pre_ocd_x32 = 0x0
// .. .. reg_ddrc_t_mrd = 0x4
EMIT_MASKWRITE(0XF8006028, 0x00003FFFU ,0x00002007U),
// .. .. reg_ddrc_emr2 = 0x8
// .. .. reg_ddrc_emr3 = 0x0
EMIT_MASKWRITE(0XF800602C, 0xFFFFFFFFU ,0x00000008U),
// .. .. reg_ddrc_mr = 0xb30
// .. .. reg_ddrc_emr = 0x4
EMIT_MASKWRITE(0XF8006030, 0xFFFFFFFFU ,0x00040B30U),
// .. .. reg_ddrc_burst_rdwr = 0x4
// .. .. reg_ddrc_pre_cke_x1024 = 0x16d
// .. .. reg_ddrc_post_cke_x1024 = 0x1
// .. .. reg_ddrc_burstchop = 0x0
EMIT_MASKWRITE(0XF8006034, 0x13FF3FFFU ,0x000116D4U),
// .. .. reg_ddrc_force_low_pri_n = 0x0
// .. .. reg_ddrc_dis_dq = 0x0
EMIT_MASKWRITE(0XF8006038, 0x00000003U ,0x00000000U),
// .. .. reg_ddrc_addrmap_bank_b0 = 0x7
// .. .. reg_ddrc_addrmap_bank_b1 = 0x7
// .. .. reg_ddrc_addrmap_bank_b2 = 0x7
// .. .. reg_ddrc_addrmap_col_b5 = 0x0
// .. .. reg_ddrc_addrmap_col_b6 = 0x0
EMIT_MASKWRITE(0XF800603C, 0x000FFFFFU ,0x00000777U),
// .. .. reg_ddrc_addrmap_col_b2 = 0x0
// .. .. reg_ddrc_addrmap_col_b3 = 0x0
// .. .. reg_ddrc_addrmap_col_b4 = 0x0
// .. .. reg_ddrc_addrmap_col_b7 = 0x0
// .. .. reg_ddrc_addrmap_col_b8 = 0x0
// .. .. reg_ddrc_addrmap_col_b9 = 0xf
// .. .. reg_ddrc_addrmap_col_b10 = 0xf
// .. .. reg_ddrc_addrmap_col_b11 = 0xf
EMIT_MASKWRITE(0XF8006040, 0xFFFFFFFFU ,0xFFF00000U),
// .. .. reg_ddrc_addrmap_row_b0 = 0x6
// .. .. reg_ddrc_addrmap_row_b1 = 0x6
// .. .. reg_ddrc_addrmap_row_b2_11 = 0x6
// .. .. reg_ddrc_addrmap_row_b12 = 0x6
// .. .. reg_ddrc_addrmap_row_b13 = 0x6
// .. .. reg_ddrc_addrmap_row_b14 = 0x6
// .. .. reg_ddrc_addrmap_row_b15 = 0xf
EMIT_MASKWRITE(0XF8006044, 0x0FFFFFFFU ,0x0F666666U),
// .. .. reg_phy_rd_local_odt = 0x0
// .. .. reg_phy_wr_local_odt = 0x3
// .. .. reg_phy_idle_local_odt = 0x3
// .. .. reserved_reg_ddrc_rank0_wr_odt = 0x1
// .. .. reserved_reg_ddrc_rank0_rd_odt = 0x0
EMIT_MASKWRITE(0XF8006048, 0x0003F03FU ,0x0003C008U),
// .. .. reg_phy_rd_cmd_to_data = 0x0
// .. .. reg_phy_wr_cmd_to_data = 0x0
// .. .. reg_phy_rdc_we_to_re_delay = 0x8
// .. .. reg_phy_rdc_fifo_rst_disable = 0x0
// .. .. reg_phy_use_fixed_re = 0x1
// .. .. reg_phy_rdc_fifo_rst_err_cnt_clr = 0x0
// .. .. reg_phy_dis_phy_ctrl_rstn = 0x0
// .. .. reg_phy_clk_stall_level = 0x0
// .. .. reg_phy_gatelvl_num_of_dq0 = 0x7
// .. .. reg_phy_wrlvl_num_of_dq0 = 0x7
EMIT_MASKWRITE(0XF8006050, 0xFF0F8FFFU ,0x77010800U),
// .. .. reg_ddrc_dis_dll_calib = 0x0
EMIT_MASKWRITE(0XF8006058, 0x00010000U ,0x00000000U),
// .. .. reg_ddrc_rd_odt_delay = 0x3
// .. .. reg_ddrc_wr_odt_delay = 0x0
// .. .. reg_ddrc_rd_odt_hold = 0x0
// .. .. reg_ddrc_wr_odt_hold = 0x5
EMIT_MASKWRITE(0XF800605C, 0x0000FFFFU ,0x00005003U),
// .. .. reg_ddrc_pageclose = 0x0
// .. .. reg_ddrc_lpr_num_entries = 0x1f
// .. .. reg_ddrc_auto_pre_en = 0x0
// .. .. reg_ddrc_refresh_update_level = 0x0
// .. .. reg_ddrc_dis_wc = 0x0
// .. .. reg_ddrc_dis_collision_page_opt = 0x0
// .. .. reg_ddrc_selfref_en = 0x0
EMIT_MASKWRITE(0XF8006060, 0x000017FFU ,0x0000003EU),
// .. .. reg_ddrc_go2critical_hysteresis = 0x0
// .. .. reg_arb_go2critical_en = 0x1
EMIT_MASKWRITE(0XF8006064, 0x00021FE0U ,0x00020000U),
// .. .. reg_ddrc_wrlvl_ww = 0x41
// .. .. reg_ddrc_rdlvl_rr = 0x41
// .. .. reg_ddrc_dfi_t_wlmrd = 0x28
EMIT_MASKWRITE(0XF8006068, 0x03FFFFFFU ,0x00284141U),
// .. .. dfi_t_ctrlupd_interval_min_x1024 = 0x10
// .. .. dfi_t_ctrlupd_interval_max_x1024 = 0x16
EMIT_MASKWRITE(0XF800606C, 0x0000FFFFU ,0x00001610U),
// .. .. reg_ddrc_dfi_t_ctrl_delay = 0x1
// .. .. reg_ddrc_dfi_t_dram_clk_disable = 0x1
// .. .. reg_ddrc_dfi_t_dram_clk_enable = 0x1
// .. .. reg_ddrc_t_cksre = 0x6
// .. .. reg_ddrc_t_cksrx = 0x6
// .. .. reg_ddrc_t_ckesr = 0x4
EMIT_MASKWRITE(0XF8006078, 0x03FFFFFFU ,0x00466111U),
// .. .. reg_ddrc_t_ckpde = 0x2
// .. .. reg_ddrc_t_ckpdx = 0x2
// .. .. reg_ddrc_t_ckdpde = 0x2
// .. .. reg_ddrc_t_ckdpdx = 0x2
// .. .. reg_ddrc_t_ckcsx = 0x3
EMIT_MASKWRITE(0XF800607C, 0x000FFFFFU ,0x00032222U),
// .. .. reg_ddrc_dis_auto_zq = 0x0
// .. .. reg_ddrc_ddr3 = 0x1
// .. .. reg_ddrc_t_mod = 0x200
// .. .. reg_ddrc_t_zq_long_nop = 0x200
// .. .. reg_ddrc_t_zq_short_nop = 0x40
EMIT_MASKWRITE(0XF80060A4, 0xFFFFFFFFU ,0x10200802U),
// .. .. t_zq_short_interval_x1024 = 0xcb73
// .. .. dram_rstn_x1024 = 0x69
EMIT_MASKWRITE(0XF80060A8, 0x0FFFFFFFU ,0x0690CB73U),
// .. .. deeppowerdown_en = 0x0
// .. .. deeppowerdown_to_x1024 = 0xff
EMIT_MASKWRITE(0XF80060AC, 0x000001FFU ,0x000001FEU),
// .. .. dfi_wrlvl_max_x1024 = 0xfff
// .. .. dfi_rdlvl_max_x1024 = 0xfff
// .. .. ddrc_reg_twrlvl_max_error = 0x0
// .. .. ddrc_reg_trdlvl_max_error = 0x0
// .. .. reg_ddrc_dfi_wr_level_en = 0x1
// .. .. reg_ddrc_dfi_rd_dqs_gate_level = 0x1
// .. .. reg_ddrc_dfi_rd_data_eye_train = 0x1
EMIT_MASKWRITE(0XF80060B0, 0x1FFFFFFFU ,0x1CFFFFFFU),
// .. .. reg_ddrc_skip_ocd = 0x1
EMIT_MASKWRITE(0XF80060B4, 0x00000200U ,0x00000200U),
// .. .. reg_ddrc_dfi_t_rddata_en = 0x6
// .. .. reg_ddrc_dfi_t_ctrlup_min = 0x3
// .. .. reg_ddrc_dfi_t_ctrlup_max = 0x40
EMIT_MASKWRITE(0XF80060B8, 0x01FFFFFFU ,0x00200066U),
// .. .. Clear_Uncorrectable_DRAM_ECC_error = 0x0
// .. .. Clear_Correctable_DRAM_ECC_error = 0x0
EMIT_MASKWRITE(0XF80060C4, 0x00000003U ,0x00000000U),
// .. .. CORR_ECC_LOG_VALID = 0x0
// .. .. ECC_CORRECTED_BIT_NUM = 0x0
EMIT_MASKWRITE(0XF80060C8, 0x000000FFU ,0x00000000U),
// .. .. UNCORR_ECC_LOG_VALID = 0x0
EMIT_MASKWRITE(0XF80060DC, 0x00000001U ,0x00000000U),
// .. .. STAT_NUM_CORR_ERR = 0x0
// .. .. STAT_NUM_UNCORR_ERR = 0x0
EMIT_MASKWRITE(0XF80060F0, 0x0000FFFFU ,0x00000000U),
// .. .. reg_ddrc_ecc_mode = 0x0
// .. .. reg_ddrc_dis_scrub = 0x1
EMIT_MASKWRITE(0XF80060F4, 0x0000000FU ,0x00000008U),
// .. .. reg_phy_dif_on = 0x0
// .. .. reg_phy_dif_off = 0x0
EMIT_MASKWRITE(0XF8006114, 0x000000FFU ,0x00000000U),
// .. .. reg_phy_data_slice_in_use = 0x1
// .. .. reg_phy_rdlvl_inc_mode = 0x0
// .. .. reg_phy_gatelvl_inc_mode = 0x0
// .. .. reg_phy_wrlvl_inc_mode = 0x0
// .. .. reg_phy_bist_shift_dq = 0x0
// .. .. reg_phy_bist_err_clr = 0x0
// .. .. reg_phy_dq_offset = 0x40
EMIT_MASKWRITE(0XF8006118, 0x7FFFFFCFU ,0x40000001U),
// .. .. reg_phy_data_slice_in_use = 0x1
// .. .. reg_phy_rdlvl_inc_mode = 0x0
// .. .. reg_phy_gatelvl_inc_mode = 0x0
// .. .. reg_phy_wrlvl_inc_mode = 0x0
// .. .. reg_phy_bist_shift_dq = 0x0
// .. .. reg_phy_bist_err_clr = 0x0
// .. .. reg_phy_dq_offset = 0x40
EMIT_MASKWRITE(0XF800611C, 0x7FFFFFCFU ,0x40000001U),
// .. .. reg_phy_data_slice_in_use = 0x1
// .. .. reg_phy_rdlvl_inc_mode = 0x0
// .. .. reg_phy_gatelvl_inc_mode = 0x0
// .. .. reg_phy_wrlvl_inc_mode = 0x0
// .. .. reg_phy_bist_shift_dq = 0x0
// .. .. reg_phy_bist_err_clr = 0x0
// .. .. reg_phy_dq_offset = 0x40
EMIT_MASKWRITE(0XF8006120, 0x7FFFFFCFU ,0x40000001U),
// .. .. reg_phy_data_slice_in_use = 0x1
// .. .. reg_phy_rdlvl_inc_mode = 0x0
// .. .. reg_phy_gatelvl_inc_mode = 0x0
// .. .. reg_phy_wrlvl_inc_mode = 0x0
// .. .. reg_phy_bist_shift_dq = 0x0
// .. .. reg_phy_bist_err_clr = 0x0
// .. .. reg_phy_dq_offset = 0x40
EMIT_MASKWRITE(0XF8006124, 0x7FFFFFCFU ,0x40000001U),
// .. .. reg_phy_wrlvl_init_ratio = 0x0
// .. .. reg_phy_gatelvl_init_ratio = 0xa4
EMIT_MASKWRITE(0XF800612C, 0x000FFFFFU ,0x00029000U),
// .. .. reg_phy_wrlvl_init_ratio = 0x0
// .. .. reg_phy_gatelvl_init_ratio = 0xa4
EMIT_MASKWRITE(0XF8006130, 0x000FFFFFU ,0x00029000U),
// .. .. reg_phy_wrlvl_init_ratio = 0x0
// .. .. reg_phy_gatelvl_init_ratio = 0xa4
EMIT_MASKWRITE(0XF8006134, 0x000FFFFFU ,0x00029000U),
// .. .. reg_phy_wrlvl_init_ratio = 0x0
// .. .. reg_phy_gatelvl_init_ratio = 0xa4
EMIT_MASKWRITE(0XF8006138, 0x000FFFFFU ,0x00029000U),
// .. .. reg_phy_rd_dqs_slave_ratio = 0x35
// .. .. reg_phy_rd_dqs_slave_force = 0x0
// .. .. reg_phy_rd_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006140, 0x000FFFFFU ,0x00000035U),
// .. .. reg_phy_rd_dqs_slave_ratio = 0x35
// .. .. reg_phy_rd_dqs_slave_force = 0x0
// .. .. reg_phy_rd_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006144, 0x000FFFFFU ,0x00000035U),
// .. .. reg_phy_rd_dqs_slave_ratio = 0x35
// .. .. reg_phy_rd_dqs_slave_force = 0x0
// .. .. reg_phy_rd_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006148, 0x000FFFFFU ,0x00000035U),
// .. .. reg_phy_rd_dqs_slave_ratio = 0x35
// .. .. reg_phy_rd_dqs_slave_force = 0x0
// .. .. reg_phy_rd_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF800614C, 0x000FFFFFU ,0x00000035U),
// .. .. reg_phy_wr_dqs_slave_ratio = 0x80
// .. .. reg_phy_wr_dqs_slave_force = 0x0
// .. .. reg_phy_wr_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006154, 0x000FFFFFU ,0x00000080U),
// .. .. reg_phy_wr_dqs_slave_ratio = 0x80
// .. .. reg_phy_wr_dqs_slave_force = 0x0
// .. .. reg_phy_wr_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006158, 0x000FFFFFU ,0x00000080U),
// .. .. reg_phy_wr_dqs_slave_ratio = 0x80
// .. .. reg_phy_wr_dqs_slave_force = 0x0
// .. .. reg_phy_wr_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF800615C, 0x000FFFFFU ,0x00000080U),
// .. .. reg_phy_wr_dqs_slave_ratio = 0x80
// .. .. reg_phy_wr_dqs_slave_force = 0x0
// .. .. reg_phy_wr_dqs_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006160, 0x000FFFFFU ,0x00000080U),
// .. .. reg_phy_fifo_we_slave_ratio = 0xf9
// .. .. reg_phy_fifo_we_in_force = 0x0
// .. .. reg_phy_fifo_we_in_delay = 0x0
EMIT_MASKWRITE(0XF8006168, 0x001FFFFFU ,0x000000F9U),
// .. .. reg_phy_fifo_we_slave_ratio = 0xf9
// .. .. reg_phy_fifo_we_in_force = 0x0
// .. .. reg_phy_fifo_we_in_delay = 0x0
EMIT_MASKWRITE(0XF800616C, 0x001FFFFFU ,0x000000F9U),
// .. .. reg_phy_fifo_we_slave_ratio = 0xf9
// .. .. reg_phy_fifo_we_in_force = 0x0
// .. .. reg_phy_fifo_we_in_delay = 0x0
EMIT_MASKWRITE(0XF8006170, 0x001FFFFFU ,0x000000F9U),
// .. .. reg_phy_fifo_we_slave_ratio = 0xf9
// .. .. reg_phy_fifo_we_in_force = 0x0
// .. .. reg_phy_fifo_we_in_delay = 0x0
EMIT_MASKWRITE(0XF8006174, 0x001FFFFFU ,0x000000F9U),
// .. .. reg_phy_wr_data_slave_ratio = 0xc0
// .. .. reg_phy_wr_data_slave_force = 0x0
// .. .. reg_phy_wr_data_slave_delay = 0x0
EMIT_MASKWRITE(0XF800617C, 0x000FFFFFU ,0x000000C0U),
// .. .. reg_phy_wr_data_slave_ratio = 0xc0
// .. .. reg_phy_wr_data_slave_force = 0x0
// .. .. reg_phy_wr_data_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006180, 0x000FFFFFU ,0x000000C0U),
// .. .. reg_phy_wr_data_slave_ratio = 0xc0
// .. .. reg_phy_wr_data_slave_force = 0x0
// .. .. reg_phy_wr_data_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006184, 0x000FFFFFU ,0x000000C0U),
// .. .. reg_phy_wr_data_slave_ratio = 0xc0
// .. .. reg_phy_wr_data_slave_force = 0x0
// .. .. reg_phy_wr_data_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006188, 0x000FFFFFU ,0x000000C0U),
// .. .. reg_phy_bl2 = 0x0
// .. .. reg_phy_at_spd_atpg = 0x0
// .. .. reg_phy_bist_enable = 0x0
// .. .. reg_phy_bist_force_err = 0x0
// .. .. reg_phy_bist_mode = 0x0
// .. .. reg_phy_invert_clkout = 0x1
// .. .. reg_phy_sel_logic = 0x0
// .. .. reg_phy_ctrl_slave_ratio = 0x100
// .. .. reg_phy_ctrl_slave_force = 0x0
// .. .. reg_phy_ctrl_slave_delay = 0x0
// .. .. reg_phy_lpddr = 0x0
// .. .. reg_phy_cmd_latency = 0x0
EMIT_MASKWRITE(0XF8006190, 0x6FFFFEFEU ,0x00040080U),
// .. .. reg_phy_wr_rl_delay = 0x2
// .. .. reg_phy_rd_rl_delay = 0x4
// .. .. reg_phy_dll_lock_diff = 0xf
// .. .. reg_phy_use_wr_level = 0x1
// .. .. reg_phy_use_rd_dqs_gate_level = 0x1
// .. .. reg_phy_use_rd_data_eye_level = 0x1
// .. .. reg_phy_dis_calib_rst = 0x0
// .. .. reg_phy_ctrl_slave_delay = 0x0
EMIT_MASKWRITE(0XF8006194, 0x000FFFFFU ,0x0001FC82U),
// .. .. reg_arb_page_addr_mask = 0x0
EMIT_MASKWRITE(0XF8006204, 0xFFFFFFFFU ,0x00000000U),
// .. .. reg_arb_pri_wr_portn = 0x3ff
// .. .. reg_arb_disable_aging_wr_portn = 0x0
// .. .. reg_arb_disable_urgent_wr_portn = 0x0
// .. .. reg_arb_dis_page_match_wr_portn = 0x0
EMIT_MASKWRITE(0XF8006208, 0x000703FFU ,0x000003FFU),
// .. .. reg_arb_pri_wr_portn = 0x3ff
// .. .. reg_arb_disable_aging_wr_portn = 0x0
// .. .. reg_arb_disable_urgent_wr_portn = 0x0
// .. .. reg_arb_dis_page_match_wr_portn = 0x0
EMIT_MASKWRITE(0XF800620C, 0x000703FFU ,0x000003FFU),
// .. .. reg_arb_pri_wr_portn = 0x3ff
// .. .. reg_arb_disable_aging_wr_portn = 0x0
// .. .. reg_arb_disable_urgent_wr_portn = 0x0
// .. .. reg_arb_dis_page_match_wr_portn = 0x0
EMIT_MASKWRITE(0XF8006210, 0x000703FFU ,0x000003FFU),
// .. .. reg_arb_pri_wr_portn = 0x3ff
// .. .. reg_arb_disable_aging_wr_portn = 0x0
// .. .. reg_arb_disable_urgent_wr_portn = 0x0
// .. .. reg_arb_dis_page_match_wr_portn = 0x0
EMIT_MASKWRITE(0XF8006214, 0x000703FFU ,0x000003FFU),
// .. .. reg_arb_pri_rd_portn = 0x3ff
// .. .. reg_arb_disable_aging_rd_portn = 0x0
// .. .. reg_arb_disable_urgent_rd_portn = 0x0
// .. .. reg_arb_dis_page_match_rd_portn = 0x0
// .. .. reg_arb_set_hpr_rd_portn = 0x0
EMIT_MASKWRITE(0XF8006218, 0x000F03FFU ,0x000003FFU),
// .. .. reg_arb_pri_rd_portn = 0x3ff
// .. .. reg_arb_disable_aging_rd_portn = 0x0
// .. .. reg_arb_disable_urgent_rd_portn = 0x0
// .. .. reg_arb_dis_page_match_rd_portn = 0x0
// .. .. reg_arb_set_hpr_rd_portn = 0x0
EMIT_MASKWRITE(0XF800621C, 0x000F03FFU ,0x000003FFU),
// .. .. reg_arb_pri_rd_portn = 0x3ff
// .. .. reg_arb_disable_aging_rd_portn = 0x0
// .. .. reg_arb_disable_urgent_rd_portn = 0x0
// .. .. reg_arb_dis_page_match_rd_portn = 0x0
// .. .. reg_arb_set_hpr_rd_portn = 0x0
EMIT_MASKWRITE(0XF8006220, 0x000F03FFU ,0x000003FFU),
// .. .. reg_arb_pri_rd_portn = 0x3ff
// .. .. reg_arb_disable_aging_rd_portn = 0x0
// .. .. reg_arb_disable_urgent_rd_portn = 0x0
// .. .. reg_arb_dis_page_match_rd_portn = 0x0
// .. .. reg_arb_set_hpr_rd_portn = 0x0
EMIT_MASKWRITE(0XF8006224, 0x000F03FFU ,0x000003FFU),
// .. .. reg_ddrc_lpddr2 = 0x0
// .. .. reg_ddrc_derate_enable = 0x0
// .. .. reg_ddrc_mr4_margin = 0x0
EMIT_MASKWRITE(0XF80062A8, 0x00000FF5U ,0x00000000U),
// .. .. reg_ddrc_mr4_read_interval = 0x0
EMIT_MASKWRITE(0XF80062AC, 0xFFFFFFFFU ,0x00000000U),
// .. .. reg_ddrc_min_stable_clock_x1 = 0x5
// .. .. reg_ddrc_idle_after_reset_x32 = 0x12
// .. .. reg_ddrc_t_mrw = 0x5
EMIT_MASKWRITE(0XF80062B0, 0x003FFFFFU ,0x00005125U),
// .. .. reg_ddrc_max_auto_init_x1024 = 0xa8
// .. .. reg_ddrc_dev_zqinit_x32 = 0x12
EMIT_MASKWRITE(0XF80062B4, 0x0003FFFFU ,0x000012A8U),
// .. .. DONE = 1
EMIT_MASKPOLL(0XF8000B74, 0x00002000U),
// .. .. reg_ddrc_soft_rstb = 0x1
// .. .. reg_ddrc_powerdown_en = 0x0
// .. .. reg_ddrc_data_bus_width = 0x0
// .. .. reg_ddrc_burst8_refresh = 0x0
// .. .. reg_ddrc_rdwr_idle_gap = 1
// .. .. reg_ddrc_dis_rd_bypass = 0x0
// .. .. reg_ddrc_dis_act_bypass = 0x0
// .. .. reg_ddrc_dis_auto_refresh = 0x0
EMIT_MASKWRITE(0XF8006000, 0x0001FFFFU ,0x00000081U),
// .. .. ddrc_reg_operating_mode = 1
EMIT_MASKPOLL(0XF8006054, 0x00000007U),
EMIT_EXIT(),

```
## Appendix: complete DDR/MIO electrical initialization fields

```text
// .. UNLOCK_KEY = 0XDF0D
EMIT_WRITE(0XF8000008, 0x0000DF0DU),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x0
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x0
// .. DCI_TYPE = 0x0
// .. IBUF_DISABLE_MODE = 0x0
// .. TERM_DISABLE_MODE = 0x0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B40, 0x00000FFFU ,0x00000600U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x0
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x0
// .. DCI_TYPE = 0x0
// .. IBUF_DISABLE_MODE = 0x0
// .. TERM_DISABLE_MODE = 0x0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B44, 0x00000FFFU ,0x00000600U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x1
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x1
// .. DCI_TYPE = 0x3
// .. IBUF_DISABLE_MODE = 0
// .. TERM_DISABLE_MODE = 0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B48, 0x00000FFFU ,0x00000672U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x1
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x1
// .. DCI_TYPE = 0x3
// .. IBUF_DISABLE_MODE = 0
// .. TERM_DISABLE_MODE = 0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B4C, 0x00000FFFU ,0x00000672U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x2
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x1
// .. DCI_TYPE = 0x3
// .. IBUF_DISABLE_MODE = 0
// .. TERM_DISABLE_MODE = 0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B50, 0x00000FFFU ,0x00000674U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x2
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x1
// .. DCI_TYPE = 0x3
// .. IBUF_DISABLE_MODE = 0
// .. TERM_DISABLE_MODE = 0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B54, 0x00000FFFU ,0x00000674U),
// .. reserved_INP_POWER = 0x0
// .. INP_TYPE = 0x0
// .. DCI_UPDATE_B = 0x0
// .. TERM_EN = 0x0
// .. DCI_TYPE = 0x0
// .. IBUF_DISABLE_MODE = 0x0
// .. TERM_DISABLE_MODE = 0x0
// .. OUTPUT_EN = 0x3
// .. PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B58, 0x00000FFFU ,0x00000600U),
// .. reserved_DRIVE_P = 0x1c
// .. reserved_DRIVE_N = 0xc
// .. reserved_SLEW_P = 0x3
// .. reserved_SLEW_N = 0x3
// .. reserved_GTL = 0x0
// .. reserved_RTERM = 0x0
EMIT_MASKWRITE(0XF8000B5C, 0xFFFFFFFFU ,0x0018C61CU),
// .. reserved_DRIVE_P = 0x1c
// .. reserved_DRIVE_N = 0xc
// .. reserved_SLEW_P = 0x6
// .. reserved_SLEW_N = 0x1f
// .. reserved_GTL = 0x0
// .. reserved_RTERM = 0x0
EMIT_MASKWRITE(0XF8000B60, 0xFFFFFFFFU ,0x00F9861CU),
// .. reserved_DRIVE_P = 0x1c
// .. reserved_DRIVE_N = 0xc
// .. reserved_SLEW_P = 0x6
// .. reserved_SLEW_N = 0x1f
// .. reserved_GTL = 0x0
// .. reserved_RTERM = 0x0
EMIT_MASKWRITE(0XF8000B64, 0xFFFFFFFFU ,0x00F9861CU),
// .. reserved_DRIVE_P = 0x1c
// .. reserved_DRIVE_N = 0xc
// .. reserved_SLEW_P = 0x6
// .. reserved_SLEW_N = 0x1f
// .. reserved_GTL = 0x0
// .. reserved_RTERM = 0x0
EMIT_MASKWRITE(0XF8000B68, 0xFFFFFFFFU ,0x00F9861CU),
// .. VREF_INT_EN = 0x0
// .. VREF_SEL = 0x0
// .. VREF_EXT_EN = 0x3
// .. reserved_VREF_PULLUP_EN = 0x0
// .. REFIO_EN = 0x1
// .. reserved_REFIO_TEST = 0x0
// .. reserved_REFIO_PULLUP_EN = 0x0
// .. reserved_DRST_B_PULLUP_EN = 0x0
// .. reserved_CKE_PULLUP_EN = 0x0
EMIT_MASKWRITE(0XF8000B6C, 0x00007FFFU ,0x00000260U),
// .. .. RESET = 1
EMIT_MASKWRITE(0XF8000B70, 0x00000001U ,0x00000001U),
// .. .. RESET = 0
// .. .. reserved_VRN_OUT = 0x1
EMIT_MASKWRITE(0XF8000B70, 0x00000021U ,0x00000020U),
// .. .. RESET = 0x1
// .. .. ENABLE = 0x1
// .. .. reserved_VRP_TRI = 0x0
// .. .. reserved_VRN_TRI = 0x0
// .. .. reserved_VRP_OUT = 0x0
// .. .. reserved_VRN_OUT = 0x1
// .. .. NREF_OPT1 = 0x0
// .. .. NREF_OPT2 = 0x0
// .. .. NREF_OPT4 = 0x1
// .. .. PREF_OPT1 = 0x0
// .. .. PREF_OPT2 = 0x0
// .. .. UPDATE_CONTROL = 0x0
// .. .. reserved_INIT_COMPLETE = 0x0
// .. .. reserved_TST_CLK = 0x0
// .. .. reserved_TST_HLN = 0x0
// .. .. reserved_TST_HLP = 0x0
// .. .. reserved_TST_RST = 0x0
// .. .. reserved_INT_DCI_EN = 0x0
EMIT_MASKWRITE(0XF8000B70, 0x07FEFFFFU ,0x00000823U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000700, 0x00003FFFU ,0x00001600U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000704, 0x00003FFFU ,0x00001602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000708, 0x00003FFFU ,0x00000602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800070C, 0x00003FFFU ,0x00000602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000710, 0x00003FFFU ,0x00000602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000714, 0x00003FFFU ,0x00000602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000718, 0x00003FFFU ,0x00000602U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800071C, 0x00003FFFU ,0x00000600U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 0
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000720, 0x00003FFFU ,0x00000600U),
// .. TRI_ENABLE = 1
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000724, 0x00003F01U ,0x00001601U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 7
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000728, 0x00003FFFU ,0x000016E1U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 7
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800072C, 0x00003FFFU ,0x000016E0U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000730, 0x00003FFFU ,0x00001600U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000734, 0x00003FFFU ,0x00001600U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 2
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000738, 0x00003FFFU ,0x00001640U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 2
// .. Speed = 0
// .. IO_Type = 3
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800073C, 0x00003FFFU ,0x00001640U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000740, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000744, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000748, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800074C, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000750, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000754, 0x00003FFFU ,0x00001202U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000758, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800075C, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000760, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000764, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000768, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 1
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800076C, 0x00003FFFU ,0x00001203U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000770, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000774, 0x00003FFFU ,0x00001205U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000778, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800077C, 0x00003FFFU ,0x00001205U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000780, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000784, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000788, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800078C, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 1
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000790, 0x00003FFFU ,0x00001205U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000794, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF8000798, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 1
// .. L2_SEL = 0
// .. L3_SEL = 0
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF800079C, 0x00003FFFU ,0x00001204U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007A0, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007A4, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007A8, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007AC, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007B0, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007B4, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007B8, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007BC, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007C0, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007C4, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007C8, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007CC, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007D0, 0x00003FFFU ,0x00001280U),
// .. TRI_ENABLE = 0
// .. L0_SEL = 0
// .. L1_SEL = 0
// .. L2_SEL = 0
// .. L3_SEL = 4
// .. Speed = 0
// .. IO_Type = 1
// .. PULLUP = 1
// .. DisableRcvr = 0
EMIT_MASKWRITE(0XF80007D4, 0x00003FFFU ,0x00001280U),
// .. SDIO0_WP_SEL = 55
// .. SDIO0_CD_SEL = 9
EMIT_MASKWRITE(0XF8000830, 0x003F003FU ,0x00090037U),
// .. SDIO1_WP_SEL = 57
// .. SDIO1_CD_SEL = 58
EMIT_MASKWRITE(0XF8000834, 0x003F003FU ,0x003A0039U),
// .. LOCK_KEY = 0X767B
EMIT_WRITE(0XF8000004, 0x0000767BU),
EMIT_EXIT(),

```
