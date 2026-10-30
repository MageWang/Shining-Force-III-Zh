#!/usr/bin/env python3
"""Inspect exactly the Git index, including contents, before publishing."""
import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {'docs', 'tools', 'translations', 'data', 'assets', 'patches', 'tests', '.github'}
ROOT_FILES = {'.gitignore', '.gitattributes', 'README.md', 'LICENSE', 'NOTICE.md'}
DENIED = {'.bin', '.iso', '.cue', '.chd', '.ccd', '.mds', '.mdf', '.rom', '.bios', '.dll', '.exe',
          '.srm', '.bcr', '.bkr', '.smpc', '.sav', '.log', '.zip', '.7z', '.pyc', '.jpg', '.png',
          '.pem', '.key', '.pfx'}


def inspect_entry(name, content):
    path = PurePosixPath(name)
    issues = []
    if path.parts[0] not in DIRECTORIES and name not in ROOT_FILES:
        issues.append('outside public allowlist')
    if path.suffix.lower() in DENIED or re.search(r'\.state(?:\.|$)', name, re.I):
        issues.append('private/game/runtime file type')
    if any(part in {'build', 'dist', 'runtime', '__pycache__', '.env', '.venv'} for part in path.parts):
        issues.append('generated or private directory')
    if path.suffix.lower() == '.bps':
        if path.parts[:2] != ('patches', 'scenario1') or content[:4] != b'BPS1':
            issues.append('unexpected patch location/format')
    elif path.suffix.lower() == '.bdf':
        if path.parts[:2] != ('assets', 'fonts') or not content.startswith(b'STARTFONT '):
            issues.append('unexpected font location/format')
    else:
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            return issues + ['unexpected non-text content']
        if re.search(r'[A-Za-z]:[\\/](?:Users|project|RetroArch)', text, re.I):
            issues.append('personal absolute path')
        if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}', text):
            issues.append('possible credential')
        if path.parts[0] == 'translations' and path.suffix == '.json':
            try:
                rows = json.loads(text)
                for row in rows:
                    allowed = {'key', 'location', 'preserve'} if row.get('preserve') is True else {'key', 'location', 'zh'}
                    if set(row) != allowed:
                        issues.append('translation includes unexpected fields/source text')
                        break
            except (ValueError, TypeError, AttributeError):
                issues.append('invalid translation JSON')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    names = [name for name in names if name]
    if not names:
        print('Error: no staged/tracked public files')
        return 1
    # Read the index, not the working copy: catches accidentally staged old source data.
    process = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                             input=''.join(':' + name + '\n' for name in names).encode('utf-8'),
                             stdout=subprocess.PIPE, check=True)
    offset = 0
    failures = []
    for name in names:
        end = process.stdout.index(b'\n', offset)
        header = process.stdout[offset:end].split()
        if len(header) != 3 or header[1] != b'blob':
            raise ValueError(f'Unexpected Git index object: {name}')
        length = int(header[2])
        content = process.stdout[end + 1:end + 1 + length]
        offset = end + length + 2
        failures.extend(f'{name}: {issue}' for issue in inspect_entry(name, content))
    print(json.dumps({'files': len(names), 'issues': failures}, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
