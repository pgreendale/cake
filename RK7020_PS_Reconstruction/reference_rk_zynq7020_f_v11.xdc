# =============================================================================
# rk_zynq7020_f_v11.xdc -- Board constraints for TZT RK-ZYNQ7020-F v1.1
#
# Device : xc7z020clg484-2
# Top    : spi_zynq_top  (PS-less bring-up build)
#
# -----------------------------------------------------------------------------
# PROVENANCE OF EVERY PIN NUMBER
#
# No pin in this file was inferred from the board name or guessed. Each one comes
# from the vendor's own factory Vivado project, which is authoritative because it
# is the design the board ships programmed with:
#
#   .../RK-ZYNQ7020-F/5. Factory Image/factory/vivado/image_7020/
#       image_7020.xpr                        -> part = xc7z020clg484-2
#       image_7020.srcs/constrs_1/new/other.xdc     -> clock, LEDs, keys, LCD SPI
#       image_7020.srcs/constrs_1/new/io_40pin.xdc  -> 40-pin expansion header
#       image_7020.srcs/sources_1/bd/design_1/design_1.bd
#                                             -> clk_in1 FREQ_HZ = 50000000
#
# Every pin was then cross-checked against the DEVICE database with
# scripts/query_pins.tcl, which confirms the pin exists in clg484, reports its
# bank, and reports its dedicated function (MRCC/SRCC). Output of that check is
# reproduced in docs/pinout.md.
#
# IOSTANDARD is LVCMOS33 throughout. This is not a default that was assumed: the
# vendor sets LVCMOS33 on every one of these pins, and gengral.xdc declares
# CONFIG_VOLTAGE 3.3 / CFGBVS VCCO, so VCCO of banks 13 and 33 is 3.3 V.
#
# Polarities are CONFIRMED, not assumed: the vendor's factory Linux device tree
# (5. Factory Image/factory/linux/system-user.dtsi) declares PL_LED1/PL_LED2 as
# GPIO_ACTIVE_HIGH and PL_KEY1/PL_KEY2 as GPIO_ACTIVE_LOW.
#
# -----------------------------------------------------------------------------
# WHAT IS STILL AN ASSUMPTION (do not treat as verified)
#
#   1. VCCO of banks 13 and 33 is 3.3 V. This is the board DEFAULT, but on the
#      40-pin header and FMC it is SELECTABLE by fitting different RA resistors
#      (1.8 / 2.5 / 3.3 V, per the user manual). LVCMOS33 below is only correct
#      while the default is in place. If those resistors were ever changed,
#      every IOSTANDARD in the bank-13 section must change with them.
#   2. The exact J1 contact number within each differential pair. The pair
#      grouping is solid (IOn occupies J1 contacts 2n+1 and 2n+2), but the
#      odd/even assignment inside a pair comes from an auto-parsed schematic
#      dump and should be confirmed visually before inserting the loopback
#      jumper. FPGA pin numbers themselves are authoritative -- they come from
#      the vendor XDC and are what the bitstream depends on.
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Clock
#
# W17 carries the 50 MHz PL oscillator and is IO_L13P_T2_MRCC_33, i.e. a
# clock-capable pin. Because the clock arrives on an MRCC pin, Vivado inserts
# the global clock buffer automatically -- there is deliberately no BUFG
# instantiated in the RTL, and no MMCM/PLL, because the design needs neither:
# it is single-domain and derives SCLK by counting, not by clock division.
#
# 50 MHz is exactly the Altera reference frequency, so timing results and every
# CLK_DIV value carry over directly.
# -----------------------------------------------------------------------------
set_property PACKAGE_PIN W17      [get_ports clk]
set_property IOSTANDARD  LVCMOS33 [get_ports clk]

create_clock -name pl_clk_50m -period 20.000 [get_ports clk]

# -----------------------------------------------------------------------------
# 2. Reset
#
# PL_KEY1 on W18. Note this pin is also MRCC-capable (IO_L13N_T2_MRCC_33); that
# is harmless for an ordinary input and costs nothing here, but it is worth
# knowing that using it does consume one clock-capable pin of bank 33.
# -----------------------------------------------------------------------------
set_property PACKAGE_PIN W18      [get_ports reset_btn]
set_property IOSTANDARD  LVCMOS33 [get_ports reset_btn]

# -----------------------------------------------------------------------------
# 3. SPI on the 40-pin expansion header (connector IO_40PIN1, bank 13)
#
# WHY THE HEADER AND NOT THE BOARD'S OWN SPI DISPLAY
#
# The board already has an SPI interface wired to an on-board LCD
# (SCK = V18, MOSI = U19, SS = AA13, plus LCD_DC/LCD_RST/LCD_LED). It was
# considered as the bring-up target and rejected as the PRIMARY one for two
# reasons:
#   * It has no MISO. The vendor XDC exposes only io0 (MOSI), which is normal
#     for an SPI TFT panel. With no return path, the entire receive half of the
#     controller -- the half that contains the synchroniser and the only known
#     defect (A-3) -- would go unverified.
#   * It is not electrically free: a real display is attached, so arbitrary
#     patterns are being sent to a device that will interpret them.
#
# The header gives four genuinely free pins with a real MISO, and it enables the
# single most valuable zero-hardware test available: a jumper from MOSI to MISO
# turns the controller into a loopback, in which the received word must equal
# the transmitted word. That verifies the full path -- shift-out, pin, pad,
# synchroniser, sample timing, bit ordering -- with nothing attached but a wire.
# See docs/bringup.md step 8.
#
# FPGA pin numbers below are taken verbatim from io_40pin.xdc:
#   IO_40PIN1[0]=V8  [1]=W8  [2]=W11 [3]=W10 [4]=V12 [5]=W12 [6]=U12 [7]=U11
#
# Physical position on connector J1, cross-referenced from the schematic net
# names (net IOn occupies J1 contacts 2n+1 and 2n+2):
#
#   spi_sclk     V8   = net IO9_P   -> J1 contact 19 or 20
#   spi_mosi     W8   = net IO9_N   -> J1 contact 19 or 20 (the other of the pair)
#   spi_miso     W11  = net IO10_P  -> J1 contact 21 or 22
#   spi_cs_n[0]  W10  = net IO10_N  -> J1 contact 21 or 22 (the other of the pair)
#
# So MOSI and MISO sit in ADJACENT pin pairs: the loopback jumper spans at most
# a few contacts. Confirm the exact contact visually before fitting it (see
# assumption 2 above).
#
# Worth knowing: SCLK and MOSI land on the two halves of one differential pair
# (IO9_P / IO9_N), i.e. tightly coupled traces carrying clock next to data. At
# the 1 MHz used for bring-up this is irrelevant. If SCLK is ever pushed towards
# the 8.33 MHz ceiling, moving SCLK to a different pair is the cheap precaution.
# -----------------------------------------------------------------------------
set_property PACKAGE_PIN V8       [get_ports spi_sclk]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_sclk]

set_property PACKAGE_PIN W8       [get_ports spi_mosi]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_mosi]

set_property PACKAGE_PIN W11      [get_ports spi_miso]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_miso]

# Weak pull-up on MISO, mirroring the Altera board wiring. Without it a floating
# MISO is indeterminate and the received byte is meaningless noise; with it an
# absent slave reads as 0xFF, which is precisely the condition the
# slave_present heuristic in spi_selftest.v is written to recognise.
set_property PULLTYPE PULLUP      [get_ports spi_miso]

set_property PACKAGE_PIN W10      [get_ports {spi_cs_n[0]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {spi_cs_n[0]}]
set_property PACKAGE_PIN V12      [get_ports {spi_cs_n[1]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {spi_cs_n[1]}]
set_property PACKAGE_PIN W12      [get_ports {spi_cs_n[2]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {spi_cs_n[2]}]
set_property PACKAGE_PIN U12      [get_ports {spi_cs_n[3]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {spi_cs_n[3]}]

# -----------------------------------------------------------------------------
# 4. Indicators (bank 33)
# -----------------------------------------------------------------------------
set_property PACKAGE_PIN V15      [get_ports {led[0]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {led[0]}]
set_property PACKAGE_PIN V13      [get_ports {led[1]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {led[1]}]

# =============================================================================
# TIMING EXCEPTIONS
#
# The migration brief requires that every exception be justified individually
# and forbids carrying them over automatically from the Quartus SDC. There are
# exactly two, and neither is inherited.
# =============================================================================

# -----------------------------------------------------------------------------
# Exception 1: spi_miso is an asynchronous input.
#
# This replaces the Altera SDC's `set_input_delay -clock spi_sclk_gen`, which
# asserted a source-synchronous relationship the design does not use.
#
# Justification from the RTL, not from convenience: spi_engine captures MISO
# through a 2-stage ASYNC_REG synchroniser chain, and the CLK_DIV >= 2 rule
# exists specifically to absorb that chain's latency (see finding A-3 in
# docs/migration.md). The architecture therefore deliberately does NOT rely on a
# timing relationship between SCLK and MISO; declaring one would produce
# meaningless STA numbers.
#
# Cost of this exception, stated plainly: STA does not check the MISO path.
# Correct reception is guaranteed by the CLK_DIV >= 2 rule instead, which is why
# that rule is asserted by test 25 rather than left as advice.
# -----------------------------------------------------------------------------
set_false_path -from [get_ports spi_miso]

# -----------------------------------------------------------------------------
# Exception 2: reset_btn is asynchronous by construction.
#
# It feeds the async-assert path of spi_reset_sync, whose entire purpose is to
# make the deassertion synchronous. Timing the button against the clock is
# meaningless: a human press has no phase relationship to a 50 MHz oscillator.
# This is the one exception carried over from the Altera SDC, and it is carried
# over because it was correct there for the same reason.
# -----------------------------------------------------------------------------
set_false_path -from [get_ports reset_btn]

# -----------------------------------------------------------------------------
# NOT declared, and why -- so that their absence is a decision on record rather
# than an omission:
#
#   * No `create_generated_clock` on spi_sclk. It is a registered output, not a
#     clock, and its divisor is programmable at run time so no fixed ratio would
#     be truthful. Full argument in docs/migration.md, section C-2.
#
#   * No `set_output_delay` on spi_sclk / spi_mosi / spi_cs_n. These need the
#     tSU/tH of a SPECIFIC slave, and no slave has been chosen yet: the delivered
#     bring-up uses loopback. Inventing numbers would be exactly the fabricated
#     constraint the brief forbids. When a slave is selected, add:
#
#         set_output_delay -clock pl_clk_50m -max <tSU_slave> \
#             [get_ports {spi_mosi spi_sclk spi_cs_n[*]}]
#         set_output_delay -clock pl_clk_50m -min -<tH_slave> \
#             [get_ports {spi_mosi spi_sclk spi_cs_n[*]}]
#
#     Consequence to be aware of: check_timing reports these as `no_output_delay`.
#     That is an unconstrained EXTERNAL (board) relationship, not an
#     unconstrained internal path -- the path from flop to pad is fully timed by
#     pl_clk_50m. The metric that must be zero, and is zero, is
#     `unconstrained_internal_endpoints`.
#
#   * No `set_false_path` on the LEDs. They are ordinary registered outputs and
#     meet timing trivially; an exception would be an unjustified one.
#
#   * No multicycle paths anywhere. The design is single-cycle throughout, so
#     none is needed. The brief requires justification for each, and there is no
#     path for which a justification could be constructed.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Bitstream settings, matching the vendor's gengral.xdc so the board's
# configuration voltage banks are declared consistently.
# -----------------------------------------------------------------------------
set_property CFGBVS VCCO         [current_design]
set_property CONFIG_VOLTAGE 3.3  [current_design]
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
