"""Read MODE1/2352 ISO9660 files without mounting an image."""
from pathlib import Path

class Disc:
    def __init__(self, path):
        self.path = Path(path)
        self.fp = self.path.open('rb')
        self.fp.seek(16 * 2352 + 16)
        pvd = self.fp.read(2048)
        if pvd[0:7] != b'\x01CD001\x01':
            raise ValueError('Expected MODE1/2352 ISO9660 image')
        self.volume = pvd[40:72].decode('ascii').strip()
        root = self.record(pvd[156:])
        self.files = []
        self.walk(root, '')

    @staticmethod
    def record(buf):
        n = buf[32]
        return dict(lba=int.from_bytes(buf[2:6], 'little'),
                    size=int.from_bytes(buf[10:14], 'little'),
                    flags=buf[25], name=buf[33:33+n])

    def read(self, lba, size):
        out = bytearray()
        while size:
            self.fp.seek(lba * 2352 + 16)
            chunk = self.fp.read(min(size, 2048))
            if not chunk:
                raise EOFError('Truncated image')
            out.extend(chunk)
            size -= len(chunk)
            lba += 1
        return bytes(out)

    def walk(self, directory, parent):
        data = self.read(directory['lba'], directory['size'])
        pos = 0
        while pos < len(data):
            length = data[pos]
            if not length:
                pos = (pos // 2048 + 1) * 2048
                continue
            rec = self.record(data[pos:pos+length])
            rec['dir_lba'] = directory['lba'] + pos // 2048
            rec['dir_offset'] = pos % 2048
            pos += length
            if rec['name'] in (b'\0', b'\1'):
                continue
            name = rec['name'].decode('ascii').split(';')[0]
            rec['name'] = parent + name
            if rec['flags'] & 2:
                self.walk(rec, rec['name'] + '/')
            else:
                self.files.append(rec)
