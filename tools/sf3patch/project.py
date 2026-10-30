"""Repository data validation and source-dependent translation reconstruction."""
import hashlib
import json
import re
from pathlib import Path

from .codec import read_words
from .controls import canonical
from .disc import Disc
from .rendering import TOKENS

ROOT = Path(__file__).resolve().parents[2]
CONTROL = re.compile(r'<[0-9A-F]{2}>')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def manifest():
    return json.loads((ROOT / 'data/scenario1.json').read_text(encoding='utf-8'))


def translation_rows(config):
    seen = set()
    for stem in config['translation_stems']:
        rows = json.loads((ROOT / 'translations/scenario1' / (stem + '.json')).read_text(encoding='utf-8'))
        for row in rows:
            fields = {'key', 'location', 'preserve'} if row.get('preserve') is True else {'key', 'location', 'zh'}
            if set(row) != fields:
                raise ValueError(f'Invalid translation fields: {stem}:{row.get("key")}')
            if not re.fullmatch(r'[0-9a-f]{16}', row['key']) or row['key'] in seen:
                raise ValueError(f'Invalid or duplicate translation key: {row["key"]}')
            seen.add(row['key'])
            if not re.fullmatch(r'X5[A-Z0-9_]+\.BIN:[0-9A-F]{2}:[0-9A-F]{2}', row['location']):
                raise ValueError(f'Invalid location: {row["location"]}')
            if 'zh' in row:
                text = row['zh']
                if not isinstance(text, str) or not text.startswith('<00>') or not text.endswith('<00>'):
                    raise ValueError(f'Missing translation boundaries: {row["key"]}')
                tokens = TOKENS.findall(text)
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    i += 1
                    if token in ('<08>', '<09>', '<11>'):
                        if i >= len(tokens) or not CONTROL.fullmatch(tokens[i]):
                            raise ValueError(f'Separated control argument: {row["key"]}')
                        i += 1
            yield row


def verify():
    config = manifest()
    for path, expected in {config['patch']: config['patch_sha256'], **config['fonts']}.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f'Hash mismatch: {path}')
    if set(config['bank_order']) != set(config['banks']) or len(config['bank_order']) != len(config['banks']):
        raise ValueError('Invalid bank order')
    rows = list(translation_rows(config))
    names = json.loads((ROOT / 'data/name-glyph-map.json').read_text(encoding='utf-8'))
    slots = list(names.values())
    if len(slots) != len(set(slots)) or not all(128 <= v < 256 and v not in (222, 223) for v in slots):
        raise ValueError('Invalid fixed name glyph slots')
    return {'release': config['release'], 'banks': len(config['banks']), 'entries': len(rows),
            'preserved': sum(row.get('preserve', False) for row in rows), 'hashes': 'OK'}


def require_source(source, config):
    if sha(source) != config['source_sha256']:
        raise ValueError('Wrong source: expected the English v24 MODE1/2352 Track 1 SHA-256 in data/scenario1.json')


def source_records(source, config):
    disc = Disc(source)
    try:
        files = {r['name']: r for r in disc.files}
        banks = {}
        locations = {}
        for name in config['bank_order']:
            rec = files[name]
            data = disc.read(rec['lba'], rec['size'])
            records = read_words(data)
            banks[name] = (data, records)
            for row in records:
                locations[name + ':' + row['id']] = b'\0' + bytes(row['words'])
        engine = files['X003.BIN']
        return banks, locations, disc.read(engine['lba'], engine['size'])
    finally:
        disc.fp.close()


def reconstruct(config, locations):
    result = {}
    for row in translation_rows(config):
        raw = locations[row['location']]
        if hashlib.sha256(raw).hexdigest()[:16] != row['key']:
            raise ValueError(f'Source key mismatch: {row["location"]}')
        original = canonical(raw)
        text = original if row.get('preserve') else row['zh']
        if CONTROL.findall(original) != CONTROL.findall(text):
            raise ValueError(f'Control sequence mismatch: {row["key"]}')
        result[raw] = text
    return result
