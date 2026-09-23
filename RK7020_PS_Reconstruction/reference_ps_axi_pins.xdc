# =============================================================================
# ps_axi_pins.xdc -- PL SPI + LCD GPIO on the onboard ST7789V
#
# SPI and DC/RST/BL pins match factory other.xdc (SPI_0_0_* / LCD_*).
# MISO is tied high inside the block design (panel has no return path).
# Wrapper port names (create_bd_port) have no _0 suffix.
# =============================================================================

set_property PACKAGE_PIN V18      [get_ports spi_sclk]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_sclk]

set_property PACKAGE_PIN U19      [get_ports spi_mosi]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_mosi]

set_property PACKAGE_PIN AA13     [get_ports spi_cs_n]
set_property IOSTANDARD  LVCMOS33 [get_ports spi_cs_n]

# lcd_gpio[0]=DC (W13), [1]=RST (AA18), [2]=LED/BL (Y13)
set_property PACKAGE_PIN W13      [get_ports {lcd_gpio[0]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {lcd_gpio[0]}]

set_property PACKAGE_PIN AA18     [get_ports {lcd_gpio[1]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {lcd_gpio[1]}]

set_property PACKAGE_PIN Y13      [get_ports {lcd_gpio[2]}]
set_property IOSTANDARD  LVCMOS33 [get_ports {lcd_gpio[2]}]

set_property CFGBVS VCCO        [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
