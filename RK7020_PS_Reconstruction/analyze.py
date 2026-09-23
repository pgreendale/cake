"""Read-only extraction of FDTs and Zynq PS7 initialization bytecode."""
from pathlib import Path
import struct, re, json, hashlib

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
def u32(b, off): return struct.unpack_from('<I', b, off)[0]
def fdt(b):
    h=struct.unpack_from('>10I', b)
    assert h[0]==0xd00dfeed and h[1]<=len(b)
    pos=h[2]; strings=b[h[3]:h[3]+h[8]]; stack=[]; lines=['/dts-v1/;']; nodes={}
    while True:
        token=struct.unpack_from('>I',b,pos)[0]; pos+=4
        if token==1:
            end=b.index(0,pos); name=b[pos:end].decode(); pos=(end+4)&~3
            stack.append(name); nodes['/'.join(stack) or '/']={}
            lines.append('\t'*(len(stack)-1)+(name or '/')+' {')
        elif token==2:
            stack.pop(); lines.append('\t'*len(stack)+'};')
        elif token==3:
            size,noff=struct.unpack_from('>II',b,pos); pos+=8
            name=strings[noff:strings.index(0,noff)].decode(); v=b[pos:pos+size]; pos=(pos+size+3)&~3
            if v and v[-1]==0 and all(part and all(32<=x<127 for x in part) for part in v[:-1].split(b'\0')):
                value=v[:-1].decode().split('\0'); rendered=', '.join(json.dumps(x) for x in value)
            elif size%4==0:
                value=list(struct.unpack('>'+str(size//4)+'I',v)); rendered='<'+ ' '.join(f'0x{x:x}' for x in value)+'>'
            else: value=v.hex(); rendered='['+v.hex(' ')+']'
            nodes['/'.join(stack) or '/'][name]=value
            lines.append('\t'*len(stack)+name+(' = '+rendered if size else '')+';')
        elif token==9: break
        elif token!=4: raise ValueError(token)
    return '\n'.join(lines)+'\n',nodes

def scan(b):
    tables=[]; pos=0
    argc={0:0,0x11:1,0x22:2,0x33:3,0x42:2,0x52:2}
    while pos+4<=len(b):
        start=pos; p=pos; ops=[]
        while p+4<=len(b):
            code=u32(b,p)
            if code not in argc or p+4*(argc[code]+1)>len(b): break
            args=list(struct.unpack_from('<'+'I'*argc[code],b,p+4)); p+=4*(argc[code]+1)
            if code==0:
                if len(ops)>=3: tables.append({'offset':start,'end':p,'ops':ops})
                break
            if not (0xe0000000<=args[0]<=0xf9000000): break
            ops.append([code,*args])
        pos=p if tables and tables[-1]['offset']==start else start+4
    return tables

def main():
    manifest={}; boots={}
    paths=list((ROOT/'Board Analysis').rglob('*'))
    for p in paths:
        if p.is_file() and (p.suffix.lower()=='.dtb' or p.name.lower() in ('boot.bin','_boot.bin')):
            b=p.read_bytes(); rel=p.relative_to(ROOT).as_posix(); tag=rel.replace('/','__')
            manifest[rel]={'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
            if p.suffix.lower()=='.dtb':
                dts,nodes=fdt(b); (OUT/(tag+'.dts')).write_text(dts); (OUT/(tag+'.json')).write_text(json.dumps(nodes,indent=2))
            else:
                source=u32(b,0x30); length=u32(b,0x40)
                manifest[rel]['header']={hex(x):hex(u32(b,x)) for x in range(0x20,0x50,4)}
                fsbl=b[source:source+length]; tables=scan(fsbl)
                manifest[rel]['fsbl_sha256']=hashlib.sha256(fsbl).hexdigest()
                manifest[rel]['tables']=[{'offset':hex(t['offset']),'ops':len(t['ops'])} for t in tables]
                boots[rel]=fsbl
                (OUT/(tag+'.tables.json')).write_text(json.dumps(tables,indent=2))
                lines=[]
                for t in tables:
                    lines.append(f"TABLE FSBL+0x{t['offset']:x} BOOT+0x{source+t['offset']:x}")
                    for op in t['ops']: lines.append(' '.join(f'0x{x:08X}' for x in op))
                (OUT/(tag+'.registers.txt')).write_text('\n'.join(lines))
    c=(ROOT/'buildroot_custom/buildroot_external/board/zynq/RK-ZYNQ7020-F/ps7_init/ps7_init_gpl.c').read_text()
    matches={}
    codes={'EXIT':0,'CLEAR':0x11,'WRITE':0x22,'MASKWRITE':0x33,'MASKPOLL':0x42,'MASKDELAY':0x52}
    for name,body in re.findall(r'unsigned long\s+(\w+)\[\]\s*=\s*\{(.*?)\};',c,re.S):
        words=[]
        for op,args in re.findall(r'EMIT_(\w+)\((.*?)\)',body):
            words+=[codes[op]]+[int(x.strip().rstrip('UuLl'),0) for x in args.split(',') if x.strip()]
        raw=struct.pack('<'+'I'*len(words),*words)
        matches[name]={k:v.find(raw) for k,v in boots.items()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT/'local_init_comparison.json').write_text(json.dumps(matches,indent=2))
    fit=(ROOT/'Board Analysis/Filesystem/opt/image/image.ub').read_bytes()
    start=1
    while True:
        off=fit.find(bytes.fromhex('d00dfeed'),start)
        if off<0: break
        start=off+4
        try:
            size=struct.unpack_from('>I',fit,off+4)[0]
            if size>100000: continue
            raw=fit[off:off+size]; dts,nodes=fdt(raw)
            if '/cpus/cpu@0' not in nodes: continue
            (OUT/'fit_system-top.dts').write_text(dts)
            (OUT/'fit_dtb_identity.json').write_text(json.dumps({'offset':hex(off),'size':size,'sha256':hashlib.sha256(raw).hexdigest()},indent=2))
        except (ValueError,AssertionError,struct.error): pass
    print(json.dumps(manifest,indent=2)); print('LOCAL INIT MATCHES',json.dumps(matches,indent=2))
if __name__=='__main__': main()
