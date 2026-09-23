**Superseded by [the consolidated report](RK-ZYNQ7020-F_Consolidated_Report.md).** The ODS comparison corrects MIO47/49 labels and supplies the physical pin tables.

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
