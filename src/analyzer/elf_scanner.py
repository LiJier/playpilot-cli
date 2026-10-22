# -*- coding: utf-8 -*-
"""
PlayPilot ELF Page Alignment Scanner
Pure static binary byte-stream analyzer for ELF .so shared libraries.
Inspects PT_LOAD segments for 16KB (0x4000) page alignment required by Android 15+.
Memory consumption < 5MB, execution speed < 50ms.
"""

import os
import struct
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class ElfScanner:
    """
    Scans AAB/APK packages for native shared libraries (.so) and verifies
    whether 64-bit binaries (arm64-v8a, x86_64) comply with Android 15+ 16KB page alignment.
    """

    # Constants
    PAGE_SIZE_16KB = 16384  # 0x4000
    ELF_MAGIC = b"\x7fELF"

    # Supported 64-bit ABIs targeted by Android 15 16KB requirement
    TARGET_64BIT_ABIS = {"arm64-v8a", "x86_64"}

    def __init__(self):
        pass

    def scan(self, archive_path: str) -> Dict[str, Any]:
        """
        Scans all .so files within the given APK or AAB archive.
        Returns detailed alignment analysis and non-compliant library list.
        """
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        if not zipfile.is_zipfile(archive_path):
            return {
                "has_native_libs": False,
                "total_so_count": 0,
                "arm64_count": 0,
                "x86_64_count": 0,
                "non_compliant_count": 0,
                "is_all_16kb_aligned": True,
                "non_compliant_libs": [],
                "libraries": []
            }

        libraries: List[Dict[str, Any]] = []
        non_compliant_libs: List[Dict[str, Any]] = []
        arm64_count = 0
        x86_64_count = 0

        with zipfile.ZipFile(archive_path, "r") as z:
            for item in z.infolist():
                filename = item.filename
                # Match .so files anywhere in the package
                # APK: lib/arm64-v8a/libfoo.so
                # AAB: base/lib/arm64-v8a/libfoo.so, feature/lib/...
                if filename.lower().endswith(".so"):
                    abi = self._extract_abi(filename)
                    if "arm64-v8a" in abi:
                        arm64_count += 1
                    elif "x86_64" in abi:
                        x86_64_count += 1

                    try:
                        with z.open(item) as f:
                            # Read initial 4KB chunk (covers ELF header + program headers)
                            header_bytes = f.read(4096)
                            parse_res = self.parse_elf(header_bytes, filename)
                            
                            if parse_res["is_valid_elf"]:
                                # If program header table extends beyond 4KB, re-read exact size
                                required_size = parse_res.get("required_header_bytes", 4096)
                                if required_size > len(header_bytes):
                                    f.seek(0)
                                    extended_bytes = f.read(required_size)
                                    parse_res = self.parse_elf(extended_bytes, filename)

                                lib_info = {
                                    "name": Path(filename).name,
                                    "path": filename,
                                    "abi": abi or parse_res.get("abi", "unknown"),
                                    "is_64bit": parse_res["is_64bit"],
                                    "min_load_align": parse_res["min_load_align"],
                                    "min_load_align_hex": hex(parse_res["min_load_align"]),
                                    "is_16kb_aligned": parse_res["is_16kb_aligned"],
                                    "file_size": item.file_size
                                }
                                libraries.append(lib_info)

                                # Android 15 16KB policy specifically mandates 64-bit architectures
                                is_target_64bit = parse_res["is_64bit"] or (abi in self.TARGET_64BIT_ABIS)
                                if is_target_64bit and not parse_res["is_16kb_aligned"]:
                                    non_compliant_libs.append(lib_info)
                    except Exception:
                        # Malformed or encrypted .so, skip safely
                        pass

        has_native = len(libraries) > 0
        return {
            "has_native_libs": has_native,
            "total_so_count": len(libraries),
            "arm64_count": arm64_count,
            "x86_64_count": x86_64_count,
            "non_compliant_count": len(non_compliant_libs),
            "is_all_16kb_aligned": (len(non_compliant_libs) == 0),
            "non_compliant_libs": non_compliant_libs,
            "libraries": libraries
        }

    def parse_elf(self, data: bytes, file_hint: str = "") -> Dict[str, Any]:
        """
        Parses ELF binary bytes to extract PT_LOAD segment alignment.
        """
        if len(data) < 52 or not data.startswith(self.ELF_MAGIC):
            return {
                "is_valid_elf": False,
                "is_64bit": False,
                "min_load_align": 0,
                "is_16kb_aligned": True,
                "abi": "unknown"
            }

        ei_class = data[4]  # 1 = 32-bit, 2 = 64-bit
        ei_data = data[5]   # 1 = little endian, 2 = big endian

        is_64bit = (ei_class == 2)
        endian = "<" if ei_data == 1 else ">"

        abi = "unknown"
        min_load_align = 0
        pt_load_count = 0
        all_aligned = True
        required_bytes = 4096

        try:
            if is_64bit:
                # 64-bit ELF Header
                # Offset 18: e_machine (2 bytes, uint16)
                # Offset 32: e_phoff (8 bytes, uint64)
                # Offset 54: e_phentsize (2 bytes, uint16)
                # Offset 56: e_phnum (2 bytes, uint16)
                if len(data) < 64:
                    return {"is_valid_elf": False, "is_64bit": True, "min_load_align": 0, "is_16kb_aligned": False}

                e_machine = struct.unpack_from(f"{endian}H", data, 18)[0]
                e_phoff = struct.unpack_from(f"{endian}Q", data, 32)[0]
                e_phentsize = struct.unpack_from(f"{endian}H", data, 54)[0]
                e_phnum = struct.unpack_from(f"{endian}H", data, 56)[0]

                abi = self._machine_to_abi(e_machine, is_64bit=True)
                required_bytes = e_phoff + (e_phnum * e_phentsize)

                # Iterate through program headers
                min_load_align = None
                for i in range(e_phnum):
                    offset = e_phoff + (i * e_phentsize)
                    if offset + 56 > len(data):
                        break

                    # Elf64_Phdr layout:
                    # uint32 p_type   (offset 0)
                    # uint32 p_flags  (offset 4)
                    # uint64 p_offset (offset 8)
                    # uint64 p_vaddr  (offset 16)
                    # uint64 p_paddr  (offset 24)
                    # uint64 p_filesz (offset 32)
                    # uint64 p_memsz  (offset 40)
                    # uint64 p_align  (offset 48)
                    p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from(
                        f"{endian}IIQQQQQQ", data, offset
                    )

                    # PT_LOAD = 1
                    if p_type == 1:
                        pt_load_count += 1
                        if min_load_align is None or p_align < min_load_align:
                            min_load_align = p_align

                        # Check 16KB boundary: p_align must be >= 0x4000 (16384 bytes)
                        # and (p_vaddr - p_offset) % p_align must be 0
                        if p_align < self.PAGE_SIZE_16KB:
                            all_aligned = False
                        elif p_align > 0 and ((p_vaddr - p_offset) % p_align != 0):
                            all_aligned = False

                if min_load_align is None:
                    min_load_align = 0
            else:
                # 32-bit ELF Header
                # Offset 18: e_machine (2 bytes)
                # Offset 28: e_phoff (4 bytes, uint32)
                # Offset 42: e_phentsize (2 bytes)
                # Offset 44: e_phnum (2 bytes)
                if len(data) < 52:
                    return {"is_valid_elf": False, "is_64bit": False, "min_load_align": 0, "is_16kb_aligned": True}

                e_machine = struct.unpack_from(f"{endian}H", data, 18)[0]
                e_phoff = struct.unpack_from(f"{endian}I", data, 28)[0]
                e_phentsize = struct.unpack_from(f"{endian}H", data, 42)[0]
                e_phnum = struct.unpack_from(f"{endian}H", data, 44)[0]

                abi = self._machine_to_abi(e_machine, is_64bit=False)
                required_bytes = e_phoff + (e_phnum * e_phentsize)

                min_load_align = None
                for i in range(e_phnum):
                    offset = e_phoff + (i * e_phentsize)
                    if offset + 32 > len(data):
                        break

                    # Elf32_Phdr layout:
                    # uint32 p_type   (offset 0)
                    # uint32 p_offset (offset 4)
                    # uint32 p_vaddr  (offset 8)
                    # uint32 p_paddr  (offset 12)
                    # uint32 p_filesz (offset 16)
                    # uint32 p_memsz  (offset 20)
                    # uint32 p_flags  (offset 24)
                    # uint32 p_align  (offset 28)
                    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
                        f"{endian}IIIIIIII", data, offset
                    )
                    if p_type == 1:
                        pt_load_count += 1
                        if min_load_align is None or p_align < min_load_align:
                            min_load_align = p_align

                if min_load_align is None:
                    min_load_align = 0
                # 32-bit binaries are not enforced under 16KB policy
                all_aligned = True

        except Exception:
            all_aligned = False

        return {
            "is_valid_elf": True,
            "is_64bit": is_64bit,
            "abi": abi,
            "pt_load_count": pt_load_count,
            "min_load_align": min_load_align if min_load_align is not None else 0,
            "is_16kb_aligned": all_aligned,
            "required_header_bytes": required_bytes
        }

    @staticmethod
    def _extract_abi(filepath: str) -> str:
        parts = filepath.replace("\\", "/").split("/")
        for part in parts:
            if part in ["arm64-v8a", "x86_64", "armeabi-v7a", "x86"]:
                return part
        return ""

    @staticmethod
    def _machine_to_abi(e_machine: int, is_64bit: bool) -> str:
        if e_machine == 183:  # EM_AARCH64
            return "arm64-v8a"
        if e_machine == 62:   # EM_X86_64
            return "x86_64"
        if e_machine == 40:   # EM_ARM
            return "armeabi-v7a"
        if e_machine == 3:    # EM_386
            return "x86"
        return "64-bit" if is_64bit else "32-bit"
