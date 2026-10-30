"""BPS encoder/applicator with mandatory CRC validation."""
import json
import struct
import zlib
from pathlib import Path

def number(value):
    if value<0:raise ValueError('BPS integers must be nonnegative')
    out=bytearray()
    while True:
        byte=value&127;value>>=7
        if not value:out.append(byte|128);return out
        out.append(byte);value-=1

def read_number(data,pos,limit=None):
    limit=len(data) if limit is None else limit
    result=0;shift=1
    while True:
        if pos>=limit or shift>1<<63:raise ValueError('Invalid BPS integer')
        value=data[pos];pos+=1;result+=(value&127)*shift
        if value&128:return result,pos
        shift<<=7;result+=shift

def make(source,target,metadata):
    a=Path(source).read_bytes();b=Path(target).read_bytes()
    meta=json.dumps(metadata,ensure_ascii=False).encode('utf-8')
    out=bytearray(b'BPS1')+number(len(a))+number(len(b))+number(len(meta))+meta
    run=0
    for pos in range(0,len(b),2352):
        chunk=b[pos:pos+2352]
        if a[pos:pos+2352]==chunk:
            run+=len(chunk)
        else:
            if run:out.extend(number((run-1)<<2));run=0
            out.extend(number(((len(chunk)-1)<<2)|1));out.extend(chunk)
    if run:out.extend(number((run-1)<<2))
    out.extend(struct.pack('<II',zlib.crc32(a),zlib.crc32(b)))
    out.extend(struct.pack('<I',zlib.crc32(out)))
    return bytes(out)

def apply(source,patch):
    data=bytes(patch);a=bytes(source)
    if len(data)<19 or data[:4]!=b'BPS1':raise ValueError('Not BPS')
    limit=len(data)-12
    if zlib.crc32(data[:-4])!=struct.unpack_from('<I',data,len(data)-4)[0]:raise ValueError('Patch CRC mismatch')
    if zlib.crc32(a)!=struct.unpack_from('<I',data,len(data)-12)[0]:raise ValueError('Wrong source image (CRC mismatch)')
    expected_source,pos=read_number(data,4,limit);expected_target,pos=read_number(data,pos,limit);meta_size,pos=read_number(data,pos,limit)
    if len(a)!=expected_source:raise ValueError('Wrong source size')
    if meta_size>limit-pos:raise ValueError('Truncated BPS metadata')
    pos+=meta_size;out=bytearray();source_relative=target_relative=0
    while len(out)<expected_target:
        action,pos=read_number(data,pos,limit);length=(action>>2)+1;kind=action&3
        if length>expected_target-len(out):raise ValueError('BPS action exceeds target size')
        if kind==0:
            if len(out)+length>len(a):raise ValueError('BPS source read out of range')
            out.extend(a[len(out):len(out)+length])
        elif kind==1:
            if length>limit-pos:raise ValueError('Truncated BPS target data')
            out.extend(data[pos:pos+length]);pos+=length
        else:
            delta,pos=read_number(data,pos,limit);delta=-(delta>>1) if delta&1 else delta>>1
            if kind==2:
                source_relative+=delta
                if source_relative<0 or source_relative+length>len(a):raise ValueError('BPS source copy out of range')
                out.extend(a[source_relative:source_relative+length]);source_relative+=length
            else:
                target_relative+=delta
                if not 0<=target_relative<len(out):raise ValueError('BPS target copy out of range')
                for _ in range(length):out.append(out[target_relative]);target_relative+=1
    if pos!=limit:raise ValueError('Unexpected BPS trailing actions')
    if zlib.crc32(out)!=struct.unpack_from('<I',data,len(data)-8)[0]:raise ValueError('Target CRC mismatch')
    return bytes(out)
