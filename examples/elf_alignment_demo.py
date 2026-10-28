"""Inspect two synthetic ELF headers; these are not runnable shared libraries."""

from pathlib import Path
import struct
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyzer.elf_scanner import ElfScanner


def elf_header(alignment):
    ident = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 3, 183, 1, 0, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    load = struct.pack("<IIQQQQQQ", 1, 5, 0, 0, 0, 120, 120, alignment)
    return header + load


def main():
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "synthetic-elf.zip"
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("lib/arm64-v8a/lib4kb.so", elf_header(0x1000))
            package.writestr("lib/arm64-v8a/lib16kb.so", elf_header(0x4000))
        result = ElfScanner().scan(str(archive))
    print("Synthetic ELF headers; not an APK or runtime compatibility test.")
    for library in result["libraries"]:
        status = "PASS" if library["is_16kb_aligned"] else "FAIL"
        print(f"{library['path']} | PT_LOAD {library['min_load_align_hex']} | {status}")
    print(f"Libraries: {result['total_so_count']}; require review: {result['non_compliant_count']}")


if __name__ == "__main__":
    main()
