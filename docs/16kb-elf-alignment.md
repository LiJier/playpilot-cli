# Check 16 KB ELF alignment in an Android APK or AAB

[README](../README.md) · [Reproducible examples](../examples/README.md) · [Target SDK guide](target-sdk-manifest.md)

An Android application can include native code directly or through a framework or SDK. Raising `targetSdk` does not rebuild precompiled native libraries.

## Inspect the release artifact

After [installing PlayPilot](../README.md#installation), run:

```bash
python -X utf8 cli.py path/to/app-release.apk --lang en
# Or inspect the publishing bundle (requires Java and the bundled bundletool):
python -X utf8 cli.py path/to/app-release.aab --lang en
```

The CLI prints a native-library scan summary and a rule finding. To get library paths and alignment values from the same scanner, run this from the repository root, replacing the input path:

```python
import sys
sys.path.insert(0, "src")
from analyzer.elf_scanner import ElfScanner

result = ElfScanner().scan("path/to/app-release.apk")
for lib in result["libraries"]:
    print(lib["path"], lib["abi"], lib["min_load_align_hex"], lib["is_16kb_aligned"])
```

The scanner examines ELF `PT_LOAD` alignment and address/offset congruence, with a 16 KB threshold of `0x4000`. It flags non-aligned 64-bit libraries. Known target ABI directories include `arm64-v8a` and `x86_64`; library count and parse success should be reviewed before treating an empty result as meaningful. Malformed libraries may be skipped.

For a reproducible demonstration using synthetic headers:

```bash
python -X utf8 examples/elf_alignment_demo.py
```

This produces a failure for `0x1000` and a pass for `0x4000`. It demonstrates the scanner, not an application's runtime compatibility.

## Verify ELF, ZIP packaging and runtime separately

Extract the affected `.so` from your actual package, then use tools from the Android NDK and SDK Build Tools:

```bash
llvm-readelf -lW libexample.so
zipalign -c -P 16 -v 4 app-release.apk
```

Inspect the `LOAD` entries' `Align` column. PlayPilot's ELF check does not run `zipalign`. An AAB is a publishing container; also inspect the APKs generated from it and test application startup and relevant flows in a 16 KB environment.

## Find the owner and rebuild

- Own native code: follow the Android guide for NDK, linker and packaging settings, then rebuild.
- Vendor SDK: obtain a compatible native build and verify that older libraries no longer enter the final artifact.
- Flutter, React Native, Unity or other engines: check the engine and each native plugin; a framework label is a fingerprint, not a compatibility result.

Re-run inspection after rebuilding and retain the exact artifact and validation results for your release process.

As checked on 2026-10-28, the Android guide covers API 35+ apps on 64-bit devices and lists February 1, 2027 as the blocking date for incompatible updates. Recheck the current official guide and your Play Console notice; a static pass is not an approval guarantee.

[Android: support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes) · [Web walkthrough](https://play.ljcan.com/en/guides/16kb-page-alignment/)
