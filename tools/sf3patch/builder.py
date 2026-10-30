"""Rebuild the frozen B30-R2 release using public inputs and a local base disc."""
import hashlib
import json
import struct

from .codec import BASE, build_bank, read_words, u32
from .project import ROOT, reconstruct, source_records
from .rendering import bdf, layout, patch_dialog_confirm, words_for, write_image


def build(source, target, config):
    banks, locations, engine = source_records(source, config)
    tr = reconstruct(config, locations)
    shared = json.loads((ROOT / 'data/name-glyph-map.json').read_text(encoding='utf-8'))
    glyphs = {}
    # Ark Pixel takes precedence; the remaining characters use Fusion Pixel.
    for path in reversed(list(config['fonts'])):
        glyphs.update(bdf(ROOT / path))
    changes = {}
    stats = []
    for name, (data, records) in banks.items():
        applicable = {b'\0' + bytes(r['words']): tr[b'\0' + bytes(r['words'])] for r in records
                      if b'\0' + bytes(r['words']) in tr and not (r['page'] == 1 and 0x37 <= r['line'] <= 0x4e)}
        chars = sorted({c for text in applicable.values() for c in text if ord(c) >= 128} | set(shared))
        missing = set(chars) - set(glyphs)
        if missing:
            raise ValueError(f'{name}: missing font glyphs {sorted(missing)}')
        slots = (i for i in range(128, 32768) if i not in (222, 223) and i not in shared.values())
        mapping = dict(shared)
        mapping.update({c: next(slots) for c in chars if c not in mapping})
        punctuation = {mapping[c] for c in '。！？，、：；' if c in mapping}
        widths = {i: struct.unpack_from('>H', data, 48 + (i - 32) * 26)[0] for i in range(32, 128)}
        widths.update({slot: glyphs[c][0] for c, slot in mapping.items()})
        name_widths = {}
        for row in records:
            if row['page'] == 1 and 0x37 <= row['line'] <= 0x72:
                raw = b'\0' + bytes(row['words'])
                words = words_for(tr[raw], mapping) if row['line'] > 0x4e and raw in tr else row['words']
                name_widths[row['line'] - 0x36] = sum(widths.get(v, 0) for v in words)
        name_widths[1] = 96
        for row in records:
            raw = b'\0' + bytes(row['words'])
            if row['page'] == 1 and 0x37 <= row['line'] <= 0x4e:
                continue
            if raw in tr:
                words = words_for(tr[raw], mapping)
                if row['page'] >= 8 and any(v in row['words'] for v in (1, 2, 3)):
                    words = layout(words, widths, name_widths, punctuation_slots=punctuation)
                row['words'] = words
        font = bytearray(data[48:u32(data, 12) - BASE])
        required = (max(mapping.values()) - 31) * 26
        if len(font) < required:
            font.extend(b'\0' * (required - len(font)))
        for char, slot in mapping.items():
            at = (slot - 32) * 26
            font[at:at + 26] = struct.pack('>13H', glyphs[char][0], *glyphs[char][1])
        updated, summary = build_bank(data, records, font)
        if len(updated) > 65536 or read_words(updated) != records:
            raise ValueError(f'{name}: capacity or codec roundtrip failed')
        if hashlib.sha256(updated).hexdigest() != config['bank_sha256'][name]:
            raise ValueError(f'{name}: differs from frozen R2; review changes and create a new release manifest')
        changes[name] = updated
        stats.append({'bank': name, 'bytes': len(updated), **summary})
    changes['X003.BIN'], edits = patch_dialog_confirm(engine)
    sectors = write_image(source, target, changes)
    return {'banks': stats, 'engine_edits': edits, 'appended_sectors': sectors}
