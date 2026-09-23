"""Extract the PL payload and inspect packets; does not recover routing."""
from pathlib import Path
import struct, json, hashlib, collections

root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent/'pl_bitstream'
out.mkdir(exist_ok=True)
source=root/'Board Analysis/Boot_Modified_RK7020/BOOT.bin'
boot=source.read_bytes()
ph=struct.unpack_from('<I',boot,0x9c)[0]
parts=[]
for i in range(4):
    w=struct.unpack_from('<16I',boot,ph+64*i)
    assert sum(w)&0xffffffff==0xffffffff
    parts.append(w)
pl=[w for w in parts if w[6]&0xf0==0x20]
assert len(pl)==1
w=pl[0];offset=w[5]*4;length=w[0]*4
payload=boot[offset:offset+length]
assert len(payload)==length
words=struct.unpack('<%dI'%(length//4),payload)
sync=words.index(0xaa995566)
big=struct.pack('>%dI'%len(words),*words)
(out/'pl_boot_word_order.bin').write_bytes(payload)
(out/'pl_configuration_be.bin').write_bytes(big)
p=sync+1;reg=None;packets=[];counts=collections.Counter();commands=collections.Counter()
while p<len(words):
    pos=p*4;h=words[p];p+=1
    if h in (0xffffffff,0x20000000,0):continue
    typ=h>>29;op=(h>>27)&3
    if typ==1:reg=(h>>13)&0x3fff;n=h&0x7ff
    elif typ==2:n=h&0x7ffffff
    else:raise ValueError(f'Unexpected packet at {pos:x}: {h:x}')
    assert op==2 and p+n<=len(words)
    data=words[p:p+n]
    counts[reg]+=1
    if reg==4:commands.update(data)
    packets.append({'payload_offset':hex(pos),'type':typ,'register':hex(reg),'word_count':n,'first_words':[hex(v) for v in data[:4]]})
    p+=n
assert p*4==length
summary={
 'source':str(source.relative_to(root)),
 'boot_offset':hex(offset),'length_bytes':length,
 'payload_sha256':hashlib.sha256(payload).hexdigest(),
 'big_endian_sha256':hashlib.sha256(big).hexdigest(),
 'sync_payload_offset':hex(sync*4),
 'idcode_writes':[x['first_words'] for x in packets if x['register']=='0xc'],
 'register_packet_counts':{hex(k):v for k,v in counts.items()},
 'command_counts':{hex(k):v for k,v in commands.items()},
 'multi_frame_write_compression':counts[10]>0,
 'decoded_to_end':True,
 'emio_package_pins_recovered':False,
 'notes':'BE file is raw configuration data, not a .bit file with a Xilinx metadata wrapper. No configuration CRC validation or route reconstruction performed.'}
(out/'manifest.json').write_text(json.dumps(summary,indent=2))
(out/'packets.json').write_text(json.dumps(packets,indent=2))
print(json.dumps(summary,indent=2))
