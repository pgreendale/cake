"""Read local ODS data and consolidate the evidence; never execute board content."""
from pathlib import Path
import csv, hashlib, json, re, zipfile
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parent
root = base.parent.parent
ods = root / '1_hardware/ZYNQ7020-F V1.0 V1.1 管脚定义.ods'
ns = {'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0', 'x':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
with zipfile.ZipFile(ods) as z:
    xml = ET.fromstring(z.read('content.xml'))
records = []
for tab in xml.findall('.//t:table', ns):
    groups = {}
    rowno = 0
    for row in tab.findall('t:table-row', ns):
        rowno += 1
        cells = []
        for cell in row:
            value = ' '.join(''.join(p.itertext()) for p in cell.findall('.//x:p', ns))
            repeat = int(cell.get('{'+ns['t']+'}number-columns-repeated', '1'))
            cells.extend([value]*min(repeat, 100))
        for col in (0,4,8):
            v = (cells[col:col+3]+['','',''])[:3]
            if v[0] and not v[1] and not v[2]: groups[col] = v[0]
            if re.fullmatch(r'[A-Z]{1,2}[0-9]+',v[0]) and v[1] and v[2]:
                records.append(dict(sheet=tab.get('{'+ns['t']+'}name'), row=rowno,
                                    group=groups.get(col,''), pin=v[0], name=v[1], net=v[2]))
        rowno += int(row.get('{'+ns['t']+'}number-rows-repeated','1'))-1
assert len({r['pin'] for r in records}) == len(records), 'Unexpected duplicate package pins'
ps = {int(re.search(r'PS_MIO(\d+)',r['name'])[1]):r for r in records if r['sheet']=='PS'}
assert set(ps)==set(range(54))
nets = {r['net']:r['pin'] for r in records}
expected = dict(LCD_SCL='V18',LCD_SDA='U19',LCD_CS='AA13',LCD_DC='W13',LCD_RST='AA18',LCD_LED='Y13',PL_LED1='V15',PL_LED2='V13',PL_KEY1='W18',PL_KEY2='V14',PL_CLK='W17')
assert all(nets[k]==v for k,v in expected.items())
xdc = (root/'Constraints_FoundClock_20260710.xdc').read_text(encoding='utf-8-sig')
header_matches = 0
for r in records:
    if r['sheet']=='40 PIN':
        n,pol = re.fullmatch(r'IO(\d+)_([NP])',r['net']).groups()
        contact = 2*int(n)+(1 if pol=='N' else 2)
        assert re.search(r'PACKAGE_PIN\s+'+r['pin']+r'\s+[^\n]*#Pin\s+0*'+str(contact)+r'\b',xdc), r
        header_matches += 1

# Correct interpretation labels, keeping the underlying FSBL values untouched.
p=base/'make_artifacts.py'
s=p.read_text(encoding='utf8').replace("'SD1 D0','SD1 D1','SD1 CLK','SD1 CMD'", "'SD1 D0','SD1 CMD','SD1 CLK','SD1 D1'")
p.write_text(s,encoding='utf8')
p=base/'mio_pinout.csv'
with p.open(encoding='utf8',newline='') as f: rows=list(csv.DictReader(f))
for r in rows:
    if r['MIO']=='47': r['function']='SD1 CMD'
    if r['MIO']=='49': r['function']='SD1 D1'
with p.open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
p=base/'mio_pinout.md'
s=p.read_text(encoding='utf8').replace('| 47 | SD1 D1 |','| 47 | SD1 CMD |').replace('| 49 | SD1 CMD |','| 49 | SD1 D1 |')
p.write_text(s,encoding='utf8')

old=(base/'REPORT.md').read_text(encoding='utf8')
old=old.replace('CMD=MIO49, DAT0=MIO46, DAT1=MIO47','CMD=MIO47, DAT0=MIO46, DAT1=MIO49')
old=old.replace('| 46, 47 | SD1 D0, D1 |\n| 48, 49 | SD1 CLK, CMD |','| 46, 47 | SD1 D0, CMD |\n| 48, 49 | SD1 CLK, D1 |')
old=old.replace('Physical SCL/SDA PL pins unknown.','ODS: SCL=AA16, SDA=AB16; DT-to-board association inferred.')
old=old.replace('Physical TX/RX pins unknown.','ODS: board CAN1 RX/TX=Y14/AA14, CAN2 RX/TX=W15/Y15; PS controller-to-board channel order remains unproven.')
old=old.replace('Physical EMIO package pins are not established by the supplied device trees or the extracted initialization code.','Physical board nets are now documented by the supplied ODS. Their internal EMIO/AXI routing must be distinguished from package-pin wiring.')
old=re.sub(r'Additional user-supplied source:.*?\n\nFollow-up EMIO investigation:.*?\n\n', 'The supplied ODS has been parsed and compared; the complete pin tables and verification results are included below. The bitstream packet analysis itself recovered no routes.\n\n',old,flags=re.S)
old=old.replace('| 4 | 58 | pl_prsnt, heartbeat output |','| 4 | 58 | Standalone DT only: pl_prsnt heartbeat output; absent from successful-boot FIT DT. FMC_PRSNT=AB14 is only a name-based candidate, not verified routing. |')
old=old.replace('and PL net-to-package constraints for CAN0/1, SPI0, I2C1, GPIO EMIO and the other PL peripherals.', 'and original internal PL routing/channel assignments. Physical peripheral nets are listed in the ODS tables below.')
old=old.replace('The column field names', 'The column field names')
# Remove old title, retain the detailed evidence, settings and citations.
old=old.split('\n',1)[1].lstrip()
display=(base/'display_analysis.md').read_text(encoding='utf8')
display=display.replace('| Physical PL package pins / backlight wiring | Not established by these files |','| Physical package pins (ODS) | SCLK V18, MOSI U19, CS AA13, D/C W13, reset AA18, backlight Y13; original backlight control source unresolved |')
display=display.replace('together with the original PL pin constraints.', 'with the ODS package assignments above.')

intro='''# RK-ZYNQ7020-F — consolidated hardware, PS, PL and BSP findings

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

'''
out=intro+old+'\n\n## Display and application findings\n\n'+display
out+='''
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

'''
for sheet in dict.fromkeys(r['sheet'] for r in records):
    out+='### '+sheet+'\n\n'
    out+='| Group | Package ball | Device pin name | Board net | ODS row |\n|---|---|---|---|---|\n'
    for r in records:
        if r['sheet']==sheet: out+='| '+' | '.join(str(r[k]) for k in ('group','pin','name','net','row'))+' |\n'
    out+='\n'
out+='## Complete MIO electrical settings with package balls\n\n'
out+='| MIO | Ball | Function | Standard | Pullup | TRI_ENABLE | Register | Mask | Value |\n|---|---|---|---|---|---|---|---|---|\n'
for r in rows:
    out+='| '+' | '.join([r['MIO'],ps[int(r['MIO'])]['pin'],r['function'],r['IO_standard'],r['pullup'],r['TRI_ENABLE'],r['register'],r['mask'],r['value']])+' |\n'
out+='''
## Vivado reconstruction and remaining limits

Select `xc7z020clg484-2`, reproduce the PS settings and 11-bit GPIO EMIO bus above, and route the documented board nets to appropriate ports. The 50 MHz PL oscillator is W17, separate from PS_CLK and FCLK outputs. Implement compatible AXI addresses, interrupts, DMA memory paths and video clocks for the chosen DT. Replace matching `Unused_*` placeholder constraints before assigning peripheral ports to those same balls; active project constraints were not changed here.

The original M_AXI_GP0-based peripheral map is recoverable, but exact HP/ACP port choices, AXI topology, interrupt concatenation and all internal control-bit assignments remain unknown. The compressed PL bitstream was extracted and packet-parsed: IDCODE 0x03727093, 4484 MFWR writes, 2489280 bytes. Configuration CRCs, decompressed frames and routing have not been validated. Packet parsing does not recover original HDL or named nets.

The ODS does not provide DDR dedicated-pin wiring, trace lengths, PCB delay inputs, measured supply voltage, a silicon temperature suffix, or an exact Vivado memory-part selection. The likely D9SHD memory identification and recovered timings remain as described above. Other schematic/revision PDFs now exist under `1_hardware/V1.1`; their contents were not evaluated for this ODS comparison and are not cited as corroboration.

Compare regenerated PS initialization against the recovered arrays before hardware testing. In particular retain FCLK1=153.333 MHz and CAN clock enables; the older local source's clock arrays differ. None of this establishes a complete vendor XSA/HDF, board preset or buildable factory project.

## Source provenance and validation

'''
out+=f'ODS SHA256: `{hashlib.sha256(ods.read_bytes()).hexdigest()}`. Extracted {len(records)} pin records, including 54 MIOs; package balls are unique. Header comparison: {header_matches}/34. Prior eleven-pin comparison: 11/11.\n\n'
out+='Original XLS SHA256: `cf681cef4630a2d1e21696e2943ba7918248d22f9924a3eb0611f2d0800b0f82`. The ODS conversion was supplied by the user; binary equivalence of the two formats is not claimed.\n\n'
out+='[Supplied ODS](../../1_hardware/ZYNQ7020-F%20V1.0%20V1.1%20管脚定义.ods). Public cross-checks: [LCD XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/ps_axi_pins.xdc), [board XDC](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/constraints/rk_zynq7020_f_v11.xdc), [pinout](https://github.com/megalloid/SPI-Master-Controller/blob/master/spi_xilinx/docs/pinout.md). Downloaded reference files are retained beside this report. No external document instructions were executed.\n\n'
out+='## Appendix: complete decoded DDR initialization fields\n\n```text\n'+(base/'ddr_annotated.txt').read_text(encoding='utf8')+'\n```\n'
out+='## Appendix: complete DDR/MIO electrical initialization fields\n\n```text\n'+(base/'mio_annotated.txt').read_text(encoding='utf8')+'\n```\n'
target=base/'RK-ZYNQ7020-F_Consolidated_Report.md'
target.write_text(out,encoding='utf8')
# Correct old report too, and clearly direct readers to the consolidated authority.
(base/'REPORT.md').write_text('**Superseded by [the consolidated report](RK-ZYNQ7020-F_Consolidated_Report.md).** The ODS comparison corrects MIO47/49 labels and supplies the physical pin tables.\n\n'+old,encoding='utf8')
for name in ('internet_pin_findings.md','display_analysis.md','pl_bitstream/README.md'):
    p=base/name; txt=p.read_text(encoding='utf8')
    link='../RK-ZYNQ7020-F_Consolidated_Report.md' if '/' in name else 'RK-ZYNQ7020-F_Consolidated_Report.md'
    if not txt.startswith('**Historical'):
        p.write_text(f'**Historical analysis: superseded by [the consolidated ODS-verified report]({link}).** Statements below about missing physical pins or unreviewed spreadsheets describe the earlier investigation.\n\n'+txt,encoding='utf8')
(base/'vendor_ods_pin_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print(f'{len(records)} records; 54 MIO; {header_matches}/34 header matches; 11/11 prior pins match; report {len(out)} characters')
