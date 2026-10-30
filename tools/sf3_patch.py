#!/usr/bin/env python3
"""Apply or reproduce the SF3 Scenario 1 Traditional Chinese B30-R2 patch."""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from sf3patch import bps
from sf3patch.builder import build
from sf3patch.controls import canonical
from sf3patch.project import ROOT, manifest, reconstruct, require_source, sha, source_records, translation_rows, verify


def package(source, audio, out, config, rebuild=False):
    require_source(source, config)
    if audio is not None:
        if not audio.is_file() or audio.stat().st_size % 2352:
            raise ValueError('Audio must be a raw 2352-byte-sector Track 2 file')
        if sha(audio) != config['source_audio_sha256']:
            raise ValueError('Wrong audio Track 2: SHA-256 mismatch')
    # Exclusive destination: avoids replacing any source image, saves, or prior build.
    out.mkdir(parents=True, exist_ok=False)
    prefix = config['prefix']
    with tempfile.TemporaryDirectory(prefix='sf3-', dir=out) as temporary:
        work = Path(temporary)
        target = work / (prefix + '-Track1.bin')
        if rebuild:
            report = build(source, target, config)
            patch = bps.make(source, target, dict(game=config['game'], base=config['base'],
                             language='zh-TW', milestone='B30-R2 integrated progress'))
            if hashlib.sha256(patch).hexdigest() != config['patch_sha256']:
                raise ValueError('Rebuilt BPS differs from frozen R2')
            (work / (prefix + '.bps')).write_bytes(patch)
        else:
            target.write_bytes(bps.apply(source.read_bytes(), (ROOT / config['patch']).read_bytes()))
            report = {}
        if sha(target) != config['target_sha256']:
            raise ValueError('Target SHA-256 mismatch')
        require_source(source, config)
        if audio:
            shutil.copyfile(audio, work / (prefix + '-Track2.bin'))
            (work / (prefix + '.cue')).write_text(
                f'FILE "{prefix}-Track1.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
                f'FILE "{prefix}-Track2.bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 00 00:00:00\n    INDEX 01 00:02:00\n', encoding='ascii')
        report.update(release=config['release'], source_sha256=config['source_sha256'],
                      target_sha256=config['target_sha256'], audio_included=audio is not None,
                      mode='build' if rebuild else 'apply')
        (work / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for path in work.iterdir():
            path.rename(out / path.name)
    return {'output': str(out), 'target_sha256': config['target_sha256'], 'cue_created': audio is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('verify', help='Check repository data and release hashes, without a game image')
    for command in ('apply', 'build', 'context'):
        sub = commands.add_parser(command)
        sub.add_argument('--source', type=Path, required=True, help='English v24 raw Track 1 BIN')
        sub.add_argument('--out', type=Path, required=True, help='New output directory (context: new JSON file in build/)')
        if command != 'context':
            sub.add_argument('--audio', type=Path, help='Matching raw Track 2; required to produce a two-track CUE')
    args = parser.parse_args()
    try:
        checked = verify()
        config = manifest()
        if args.command == 'verify':
            result = checked
        elif args.command == 'context':
            # Keep extracted original English scripts out of the public Git tree.
            out = args.out.resolve()
            if not out.is_relative_to(ROOT / 'build'):
                raise ValueError('context output must be under this repository\'s ignored build/ directory')
            require_source(args.source, config)
            _, locations, _ = source_records(args.source, config)
            reconstruct(config, locations)
            context = [{**row, 'source': canonical(locations[row['location']])} for row in translation_rows(config)]
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open('x', encoding='utf-8') as stream:
                json.dump(context, stream, ensure_ascii=False, indent=2)
            result = {'context': str(out), 'entries': len(context), 'local_only': True}
        else:
            result = package(args.source.resolve(), args.audio.resolve() if args.audio else None,
                             args.out.resolve(), config, args.command == 'build')
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, IndexError, AssertionError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
