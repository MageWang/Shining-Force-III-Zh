"""MODE1 CD sector EDC/ECC repair."""
import hashlib
import struct
from pathlib import Path

def checksum_tables():
    edc=[]; fwd=[]; back=[0]*256
    for i in range(256):
        n=i
        for _ in range(8): n=(n>>1)^(0xD8018001 if n&1 else 0)
        edc.append(n)
        j=(i<<1)^(0x11D if i&128 else 0)
        fwd.append(j); back[i^j]=i
    return edc,fwd,back

EDC,FWD,BACK=checksum_tables()

def ecc(data, major_count, minor_count, major_mult, minor_inc):
    result=bytearray(major_count*2); size=major_count*minor_count
    for major in range(major_count):
        index=(major>>1)*major_mult+(major&1); a=b=0
        for _ in range(minor_count):
            val=data[index]; index=(index+minor_inc)%size
            a^=val; b^=val; a=FWD[a]
        a=BACK[FWD[a]^b]
        result[major]=a; result[major+major_count]=a^b
    return result

def rebuild_sector(sector):
    s=bytearray(sector)
    assert len(s)==2352 and s[15]==1
    value=0
    for byte in s[:2064]: value=(value>>8)^EDC[(value^byte)&255]
    s[2064:2068]=struct.pack('<I',value); s[2068:2076]=b'\0'*8
    s[2076:2248]=ecc(s[12:2076],86,24,2,86)
    s[2248:2352]=ecc(s[12:2248],52,43,86,88)
    return bytes(s)
