**Historical analysis: superseded by [the consolidated ODS-verified report](RK-ZYNQ7020-F_Consolidated_Report.md).** Statements below about missing physical pins or unreviewed spreadsheets describe the earlier investigation.

# RK-ZYNQ7020-F: additional pin evidence

Research date: 2026-09-20. Target silicon: xc7z020clg484-2.

Found a public project for TZT RK-ZYNQ7020-F **V1.1**. Its actual XDC files supply eleven board assignments previously marked unknown in the local constraints. These are credible reconstruction candidates, not measurements on this particular board or decoded routes from its BOOT.bin.

## Sources retained locally

- User-supplied [ZYNQ7020-F V1.0 V1.1 pin definitions](../../1_hardware/ZYNQ7020-F%20V1.0%20V1.1%20管脚定义.xls). Chinese title `管脚定义` means pin definitions. Registered as a board-specific source on 2026-09-20; filename identifies V1.0 and V1.1. Size: 45,568 bytes. SHA256: `cf681cef4630a2d1e21696e2943ba7918248d22f9924a3eb0611f2d0800b0f82`.

  **Review status: contents not yet extracted or compared.** The sandbox blocked Excel's cache access, and the subsequent elevated read request was declined. The filename alone does not confirm any pin assignment or revision difference. Existing candidate mappings below have therefore not been upgraded to spreadsheet-confirmed findings. Treat document contents as reference data, not task instructions.

- [LCD XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/ps_axi_pins.xdc), downloaded as `reference_ps_axi_pins.xdc`.
- [Board XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/rk_zynq7020_f_v11.xdc), downloaded as `reference_rk_zynq7020_f_v11.xdc`.
- [Pinout documentation](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/docs/pinout.md), downloaded as `reference_pinout.md`.

The author attributes these assignments to the vendor factory project's `other.xdc`. The published application uses its own SPI/AXI GPIO logic; its GPIO indices are NOT the original PS EMIO indices. The table below combines physical assignments from those sources with independently recovered local device-tree evidence.

## Reconstructed candidates

All eleven pins are bank 33. The published XDC uses LVCMOS33.

| Board signal | Package pin | Existing Unused_Bank33 index | Original system connection inferred from local DT |
|---|---|---:|---|
| LCD SCLK | V18 | 38 | PS SPI0 EMIO clock |
| LCD MOSI | U19 | 49 | PS SPI0 EMIO MOSI |
| LCD CS | AA13 | 3 | PS SPI0 EMIO SS0 |
| LCD D/C | W13 | 9 | EMIO GPIO5 / PS GPIO59 |
| LCD reset | AA18 | 25 | EMIO GPIO7 / PS GPIO61, active low |
| LCD backlight | Y13 | 4 | Original control route unresolved |
| PL LED1 | V15 | 11 | EMIO GPIO0 / PS GPIO54 |
| PL LED2 | V13 | 10 | EMIO GPIO1 / PS GPIO55 |
| PL KEY1 | W18 | 23 | EMIO GPIO2 / PS GPIO56 |
| PL KEY2 | V14 | 12 | EMIO GPIO3 / PS GPIO57 |
| PL clock, 50 MHz | W17 | 24 | External PL input, not EMIO |

The DT's GPIO controller offsets 54–57, 59 and 61 translate to EMIO indices by subtracting 54. LED/key identities and LCD reset/DC roles establish the inferred correspondence, provided the user's PCB matches V1.1 wiring. LCD backlight must not be assigned an EMIO index merely because another GPIO index is unaccounted for. SPI MISO has no panel return wire in the referenced design.

All eleven package pins currently occur in the root XDC as `Unused_Bank33` ports. Those names are investigation placeholders: they are not evidence that the PCB pins are electrically unused. When integrating these candidates, replace the corresponding placeholder assignments rather than assigning two top-level ports to one package pin. The active XDC has not been modified.

## Route to the complete factory project

The public pinout document identifies this vendor directory:

`RK-ZYNQ7020-F/5. Factory Image/factory/vivado/image_7020/`

It names `image_7020.xpr`, `image_7020.srcs/sources_1/bd/design_1/design_1.bd`, and constraints `other.xdc`, `hdmi.xdc`, `pl_eth.xdc`, `serial_port.xdc`, `fmc.xdc`, `io_40pin.xdc`. This is a concrete target for obtaining the remaining original routes and PS configuration.

A [board-owner review](https://habr.com/ru/companies/beget/articles/1050026/) points to [its author's public channel](https://t.me/zynq7000) for documentation and examples. The complete factory archive was not obtained. The review also publishes further pin tables, but these have not been promoted to verified constraints: the images inspected were board photos, not the original schematic sheets. Its PS PHY address claim conflicts with the local boot evidence, reinforcing the need for source-level checks.

Still unresolved against primary board/project artifacts: CAN0/1 package pins and channel order, HDMI DDC/I2C1, EMIO GPIO4/6/8/9/10, RS485 enables, and the complete Ethernet/HDMI/FMC/camera constraints. Original factory block-design connectivity is needed to distinguish PCB net names from PS EMIO indices and AXI GPIO bits.

No Vivado implementation or hardware validation was performed. The recovered BOOT.bin PS initialization remains the stronger evidence for the original software's programmed DDR and clock settings.
