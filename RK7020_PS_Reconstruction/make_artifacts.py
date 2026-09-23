"""Produce reviewable register and pin inventories from extracted evidence."""
from pathlib import Path
import json,re,csv,struct
P=Path(__file__).resolve().parent
R=P.parents[1]
tables=json.loads((P/'Board Analysis__Boot_Modified_RK7020__BOOT.bin.tables.json').read_text())
get=lambda offset:next(t['ops'] for t in tables if t['offset']==offset)
names={0:'GPIO: ps_key1',1:'QSPI0 CS0#',2:'QSPI0 DQ0',3:'QSPI0 DQ1',4:'QSPI0 DQ2',5:'QSPI0 DQ3',6:'QSPI0 SCLK',7:'GPIO: ps_led2',8:'GPIO: ps_led1 (QSPI feedback clock not selected)',9:'SD0 card detect (input tap)',10:'UART0 RX',11:'UART0 TX',12:'GPIO: ps_key2',13:'GPIO: USB0 PHY reset',14:'I2C0 SCL',15:'I2C0 SDA'}
names.update(dict(enumerate(['GEM0 TX_CLK','GEM0 TXD0','GEM0 TXD1','GEM0 TXD2','GEM0 TXD3','GEM0 TX_CTL','GEM0 RX_CLK','GEM0 RXD0','GEM0 RXD1','GEM0 RXD2','GEM0 RXD3','GEM0 RX_CTL'],16)))
names.update(dict(enumerate(['USB0 ULPI D4','USB0 ULPI DIR','USB0 ULPI STP','USB0 ULPI NXT','USB0 ULPI D0','USB0 ULPI D1','USB0 ULPI D2','USB0 ULPI D3','USB0 ULPI CLK','USB0 ULPI D5','USB0 ULPI D6','USB0 ULPI D7'],28)))
names.update(dict(enumerate(['SD0 CLK','SD0 CMD','SD0 D0','SD0 D1','SD0 D2','SD0 D3','SD1 D0','SD1 CMD','SD1 CLK','SD1 D1','SD1 D2','SD1 D3','GEM0 MDC','GEM0 MDIO'],40)))
rows=[]
for code,a,mask,v in [op for op in get(0x12534) if len(op)==4 and 0xf8000700<=op[1]<=0xf80007d4]:
 n=(a-0xf8000700)//4
 rows.append([n,names[n],500 if n<16 else 501,f'0x{a:08X}',f'0x{mask:08X}',f'0x{v:08X}',{1:'LVCMOS18',2:'LVCMOS25',3:'LVCMOS33',4:'HSTL'}[(v>>9)&7],(v>>12)&1,(v>>8)&1,v&1])
assert len(rows)==54 and len(set(row[0] for row in rows))==54
with (P/'mio_pinout.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['MIO','function','PS_IO_bank','register','mask','value','IO_standard','pullup','fast_slew','TRI_ENABLE']);w.writerows(rows)
(P/'mio_pinout.md').write_text('| MIO | Function | PS bank | Standard | Pull-up | TRI_ENABLE | Init value |\n|---|---|---|---|---|---|---|\n'+'\n'.join(f'| {n} | {fun} | {bank} | {io} | {pu} | {tri} | `{v}` |' for n,fun,bank,a,m,v,io,pu,s,tri in rows)+'\n')
# Recover all complete initialization arrays, preserving upstream licensing and code.
source=R/'buildroot_custom/buildroot_external/board/zynq/RK-ZYNQ7020-F/ps7_init/ps7_init_gpl.c'
c=source.read_text()
for group in ['ddr','mio','clock','pll']:
 body=re.search(r'unsigned long ps7_'+group+r'_init_data_3_0\[\] = \{(.*?)\};',c,re.S)[1]
 lines=[line.strip() for line in body.splitlines() if re.search(r'// .* = |EMIT_',line) and '==>' not in line and 'MASK :' not in line]
 (P/(group+'_annotated.txt')).write_text('\n'.join(lines)+'\n')
opnames={0x11:'CLEAR',0x22:'WRITE',0x33:'MASKWRITE',0x42:'MASKPOLL',0x52:'MASKDELAY'}
for version,offset in [('1_0',0x1038c),('2_0',0x110b8),('3_0',0x11e04)]:
 body='\n'+ '\n'.join('    EMIT_'+opnames[op[0]]+'('+', '.join(f'0x{x:08X}U' for x in op[1:])+'),' for op in get(offset))+'\n    EMIT_EXIT(),\n'
 c=re.sub(r'(unsigned long ps7_clock_init_data_'+version+r'\[\] = \{).*?(\};)',lambda m:m[1]+body+m[2],c,flags=re.S)
c='/* Reconstructed from supplied BOOT.bin. Clock tables corrected from binary;\n * all initialization arrays verified byte-for-byte. Not hardware-tested.\n * Companion header: existing RK-ZYNQ7020-F/ps7_init/ps7_init_gpl.h.\n */\n'+c
(P/'recovered_ps7_init_gpl.c').write_text(c)
b=(R/'Board Analysis/Boot_Modified_RK7020/BOOT.bin').read_bytes(); fsbl=b[0x1700:0x19708]
codes={v:k for k,v in opnames.items()};codes['EXIT']=0
checks=[]
for name,body in re.findall(r'unsigned long\s+(\w+)\[\]\s*=\s*\{(.*?)\};',c,re.S):
 words=[]
 for op,args in re.findall(r'EMIT_(\w+)\((.*?)\)',body):words+=[codes[op]]+[int(x.strip().rstrip('UuLl'),0) for x in args.split(',') if x.strip()]
 raw=struct.pack('<'+'I'*len(words),*words);offset=fsbl.find(raw)
 assert offset>=0,name
 checks.append(f'{name}: matched at FSBL+0x{offset:X}, {len(raw)} bytes')
assert sum(struct.unpack_from('<11I',b,0x20))&0xffffffff==0xffffffff
checks+=['BOOT header checksum verified','54 MIO entries accounted for','Reconstructed 21 initialization arrays all found verbatim in supplied FSBL']
(P/'verification.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
