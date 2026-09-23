**Historical analysis: superseded by [the consolidated ODS-verified report](RK-ZYNQ7020-F_Consolidated_Report.md).** Statements below about missing physical pins or unreviewed spreadsheets describe the earlier investigation.

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
| Physical PL package pins / backlight wiring | Not established by these files |

To reproduce the existing Linux interface, use the kernel's [FBTFT ST7789V driver](https://github.com/torvalds/linux/blob/v6.1/drivers/staging/fbtft/fb_st7789v.c) and enable `CONFIG_FB_TFT` and `CONFIG_FB_TFT_ST7789V`, together with their framebuffer, SPI, GPIO and backlight dependencies. Module name: `fb_st7789v`. See [Kconfig](https://github.com/torvalds/linux/blob/v6.1/drivers/staging/fbtft/Kconfig). Preserve the board's existing DT node from `fit_system-top.dts` or the decompiled standalone DTB, including GPIO polarities and geometry.

This identifies the driver already working in the supplied log. The original kernel source was not supplied, so possible vendor modifications to panel initialization, gamma, inversion or display-window offsets remain unverified. A generic ST7789V driver may require panel-specific adjustments for this 172-pixel-wide module. Do not substitute a different ST7789V driver solely on the controller name without checking its pixel transport and framebuffer interface.

For Vivado, the display requires PS SPI0 through EMIO and GPIO EMIO5/7, together with the original PL pin constraints. I2C1 is assigned to HDMI EDID in the device tree; it is a separate function from this SPI framebuffer display.

On the running board, `cat /sys/class/graphics/fb0/name` can confirm which driver currently owns fb0, since framebuffer numbering can change between builds. No executable from the supplied filesystem was run during this analysis.
