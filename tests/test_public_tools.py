"""Synthetic fixtures only: no game, original dialogue, BIOS or saves."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from sf3patch import bps
from check_public_tree import inspect_entry
from sf3patch.project import verify


def patch_for(source, target, actions):
    patch = bytearray(b'BPS1') + bps.number(len(source)) + bps.number(len(target)) + bps.number(0) + actions
    patch += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
    return patch + struct.pack('<I', zlib.crc32(patch))


class BpsTests(unittest.TestCase):
    def test_roundtrip_and_corruption_rejection(self):
        source = b'A' * 2352 + bytes(range(256)) * 10
        target = source[:2352] + b'B' * 2352 + b'tail'
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'source', Path(directory) / 'target'
            a.write_bytes(source)
            b.write_bytes(target)
            patch = bps.make(a, b, {'test': True})
        self.assertEqual(bps.apply(source, patch), target)
        with self.assertRaisesRegex(ValueError, 'Wrong source'):
            bps.apply(b'wrong', patch)
        with self.assertRaisesRegex(ValueError, 'Patch CRC'):
            bps.apply(source, patch[:-1] + bytes([patch[-1] ^ 1]))

    def test_overlapping_target_copy(self):
        actions = bps.number(1) + b'a' + bps.number((3 - 1) * 4 + 3) + bps.number(0)
        self.assertEqual(bps.apply(b'', patch_for(b'', b'aaaa', actions)), b'aaaa')

    def test_out_of_bounds_source_copy(self):
        actions = bps.number(2) + bps.number(3)  # source offset -1
        with self.assertRaisesRegex(ValueError, 'out of range'):
            bps.apply(b'a', patch_for(b'a', b'a', actions))

    def test_truncated_integer_with_valid_crc(self):
        patch = b'BPS1' + b'\x00'
        patch += struct.pack('<II', 0, 0)
        patch += struct.pack('<I', zlib.crc32(patch))
        with self.assertRaises(ValueError):
            bps.apply(b'', patch)


class PublicTreeTests(unittest.TestCase):
    def test_release_hashes_and_schema(self):
        self.assertEqual(verify()['banks'], 82)

    def test_runtime_files_are_rejected_even_if_force_added(self):
        for name in ('assets/game.bin', 'tools/private.key', 'docs/test.state.1', 'research/context.json'):
            self.assertTrue(inspect_entry(name, b'local test'))

    def test_original_script_fields_are_rejected(self):
        self.assertTrue(inspect_entry('translations/scenario1/test.json',
                                     b'[{"key":"id","source":"synthetic fixture","zh":"x"}]'))


if __name__ == '__main__':
    unittest.main()
