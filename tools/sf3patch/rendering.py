"""Font loading, stable cached names, and dialogue layout."""
import json
import re
import shutil
import struct
from pathlib import Path
from .disc import Disc
from .sectors import rebuild_sector
TOKENS=re.compile(r"<[0-9A-F]{2}>|.",re.S)

def bdf(path):
    out={};code=None;bitmap=False;rows=[];box=None;advance=12
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('STARTCHAR '):code=None;bitmap=False;rows=[];box=None
        elif line.startswith('ENCODING '):code=int(line.split()[1])
        elif line.startswith('DWIDTH '):advance=int(line.split()[1])
        elif line.startswith('BBX '):box=list(map(int,line.split()[1:]))
        elif line=='BITMAP':bitmap=True
        elif line=='ENDCHAR':
            if code is not None and box:
                width,height,left,bottom=box
                raster=[0]*12;top=10-bottom-height
                bitswidth=((width+7)//8)*8
                for y,row in enumerate(rows):
                    if 0<=top+y<12:
                        value=int(row,16)
                        for x in range(width):
                            if 0<=left+x<16 and value&(1<<(bitswidth-1-x)):
                                raster[top+y]|=1<<(15-left-x)
                out[chr(code)]=(advance,raster)
            bitmap=False
        elif bitmap:rows.append(line)
    return out

def words_for(text,mapping):
    assert text.startswith('<00>')
    result=[]
    for token in TOKENS.findall(text[4:]):
        if re.fullmatch(r'<[0-9A-F]{2}>',token):result.append(int(token[1:3],16))
        elif ord(token)<128:result.append(ord(token))
        else:result.append(mapping[token])
    return result

def layout(words,widths,name_widths,max_width=204,punctuation_slots=()):
    # A coloured speaker heading has its own row, in addition to three body rows.
    heading=words[:4]==[9,4,8,6]
    out=[];width=0;line=0;i=0;limit=4 if heading else 3
    while i<len(words):
        value=words[i];unit=[value];i+=1
        if value in (8,9,17):unit.append(words[i]);i+=1
        if value in (1,2):line=0;width=0;limit=3
        elif value==3:
            if line>=limit-1:unit=[1];line=0;limit=3
            else:line+=1
            width=0
        elif value>=32 or value in (16,17,18,19,20,22,23,24,25,26):
            advance=name_widths.get(unit[1],96) if value==17 else (96 if value<32 else widths[value])
            if heading and line==0 and value>=32 and (not punctuation_slots or limit==4):advance+=1
            # In later milestones, keep a name/word and its closing punctuation together.
            following=widths[words[i]] if punctuation_slots and i<len(words) and words[i] in punctuation_slots else 0
            if width and width+advance+following>max_width:
                if line<limit-1:out.append(3);line+=1
                else:out.append(1);line=0;limit=3
                width=0
            width+=advance
        out.extend(unit)
    return out

def patch_dialog_confirm(data):
    """Page waits read newly-pressed buttons instead of currently-held buttons.

    1ST.BIN 06011900..06011910 computes FC4C=(previous XOR held) AND held.
    X003's 01/02 page waits and optional 05/06 pauses read these two literals.
    Text rendering, movement, menus and battle input code are left intact.
    """
    patched=bytearray(data);edits=[]
    for address in (0x06035D98,0x06035ED8):
        offset=address-0x06034B00
        assert struct.unpack_from('>I',patched,offset)[0]==0x0601FC48
        struct.pack_into('>I',patched,offset,0x0601FC4C)
        edits.append(dict(file='X003.BIN',offset=offset,address=f'{address:08X}',
                          before='0601FC48',after='0601FC4C'))
    return bytes(patched),edits

def write_image(source,target,changes):
    disc=Disc(source);shutil.copyfile(source,target)
    count=0
    with target.open('r+b') as fp:
        def sector_write(lba,offset,blob):
            fp.seek(lba*2352);sector=bytearray(fp.read(2352))
            sector[16+offset:16+offset+len(blob)]=blob
            fp.seek(lba*2352);fp.write(rebuild_sector(sector))
        next_lba=source.stat().st_size//2352
        for name,data in changes.items():
            rec=next(r for r in disc.files if r['name']==name)
            lba=next_lba
            for pos in range(0,len(data),2048):
                sector=bytearray(2352);sector[0:12]=b'\0'+b'\xff'*10+b'\0'
                number=next_lba+150
                for off,val in [(12,number//4500),(13,(number//75)%60),(14,number%75)]:sector[off]=(val//10)*16+val%10
                sector[15]=1;chunk=data[pos:pos+2048];sector[16:16+len(chunk)]=chunk
                fp.seek(next_lba*2352);fp.write(rebuild_sector(sector));next_lba+=1;count+=1
            extent=struct.pack('<I',lba)+struct.pack('>I',lba)
            size=struct.pack('<I',len(data))+struct.pack('>I',len(data))
            sector_write(rec['dir_lba'],rec['dir_offset']+2,extent)
            sector_write(rec['dir_lba'],rec['dir_offset']+10,size)
        # ISO9660 volume space size, both-endian value.
        sector_write(16,80,struct.pack('<I',next_lba)+struct.pack('>I',next_lba))
    check=Disc(target)
    for name,data in changes.items():
        rec=next(r for r in check.files if r['name']==name)
        assert check.read(rec['lba'],rec['size'])==data
    return count
