# -*- coding: utf-8 -*-
import os
import sys
import struct
import zipfile
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzer.elf_scanner import ElfScanner

def make_mock_elf64(p_align=4096, e_machine=183):
    """Generates a minimal valid 64-bit ELF binary with specified PT_LOAD p_align."""
    ident = b"\x7fELF\x02\x01\x01\x00" + (b"\x00" * 8)
    ehdr = struct.pack("<16sHHIQQQIHHHHHH",
        ident, 3, e_machine, 1, 0, 64, 0, 0, 64, 56, 1, 0, 0, 0
    )
    phdr = struct.pack("<IIQQQQQQ", 1, 5, 0, 0, 0, 120, 120, p_align)
    return ehdr + phdr

def make_mock_elf32(p_align=4096, e_machine=40):
    """Generates a minimal valid 32-bit ELF binary."""
    ident = b"\x7fELF\x01\x01\x01\x00" + (b"\x00" * 8)
    ehdr = struct.pack("<16sHHIIIIIHHHHHH",
        ident, 3, e_machine, 1, 0, 52, 0, 0, 52, 32, 1, 0, 0, 0
    )
    phdr = struct.pack("<IIIIIIII", 1, 0, 0, 0, 84, 84, 5, p_align)
    return ehdr + phdr

class TestElfScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = ElfScanner()

    def test_parse_64bit_4kb_non_compliant(self):
        data = make_mock_elf64(p_align=4096, e_machine=183)
        res = self.scanner.parse_elf(data)
        self.assertTrue(res["is_valid_elf"])
        self.assertTrue(res["is_64bit"])
        self.assertEqual(res["abi"], "arm64-v8a")
        self.assertEqual(res["min_load_align"], 4096)
        self.assertFalse(res["is_16kb_aligned"])

    def test_parse_64bit_16kb_compliant(self):
        data = make_mock_elf64(p_align=16384, e_machine=183)
        res = self.scanner.parse_elf(data)
        self.assertTrue(res["is_valid_elf"])
        self.assertTrue(res["is_64bit"])
        self.assertEqual(res["min_load_align"], 16384)
        self.assertTrue(res["is_16kb_aligned"])

    def test_parse_64bit_64kb_compliant(self):
        data = make_mock_elf64(p_align=65536, e_machine=62)
        res = self.scanner.parse_elf(data)
        self.assertTrue(res["is_valid_elf"])
        self.assertTrue(res["is_64bit"])
        self.assertEqual(res["abi"], "x86_64")
        self.assertEqual(res["min_load_align"], 65536)
        self.assertTrue(res["is_16kb_aligned"])

    def test_parse_32bit_exempt(self):
        data = make_mock_elf32(p_align=4096, e_machine=40)
        res = self.scanner.parse_elf(data)
        self.assertTrue(res["is_valid_elf"])
        self.assertFalse(res["is_64bit"])
        self.assertEqual(res["abi"], "armeabi-v7a")
        self.assertTrue(res["is_16kb_aligned"])  # 32-bit not penalized

    def test_archive_scan_mixed(self):
        with tempfile.NamedTemporaryFile(suffix=".aab", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                # 1 compliant 64-bit so
                z.writestr("base/lib/arm64-v8a/libgood.so", make_mock_elf64(p_align=16384))
                # 1 non-compliant 64-bit so (4KB)
                z.writestr("base/lib/arm64-v8a/libbad.so", make_mock_elf64(p_align=4096))
                # 1 32-bit legacy so
                z.writestr("base/lib/armeabi-v7a/liblegacy.so", make_mock_elf32(p_align=4096))
                # 1 non-so file
                z.writestr("base/assets/readme.txt", b"hello world")

            res = self.scanner.scan(tmp_path)
            self.assertTrue(res["has_native_libs"])
            self.assertEqual(res["total_so_count"], 3)
            self.assertEqual(res["arm64_count"], 2)
            self.assertEqual(res["non_compliant_count"], 1)
            self.assertFalse(res["is_all_16kb_aligned"])

            non_comp = res["non_compliant_libs"][0]
            self.assertEqual(non_comp["name"], "libbad.so")
            self.assertEqual(non_comp["min_load_align"], 4096)
            self.assertEqual(non_comp["min_load_align_hex"], "0x1000")

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_archive_no_native_libs(self):
        with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                z.writestr("AndroidManifest.xml", b"<manifest/>")

            res = self.scanner.scan(tmp_path)
            self.assertFalse(res["has_native_libs"])
            self.assertEqual(res["total_so_count"], 0)
            self.assertEqual(res["non_compliant_count"], 0)
            self.assertTrue(res["is_all_16kb_aligned"])

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
