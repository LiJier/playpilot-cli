# Reproducible inspection examples

[Main README](../README.md) · [中文说明](../README_ZH.md)

## Public APK: an old target SDK

`hello-world-cli.txt` is actual stdout from running PlayPilot against Androguard's public `hello-world.apk` on 2026-10-28, with line endings and trailing whitespace normalized. It is not a customer application, a fabricated transcript, or a Google Play approval result.

- [Upstream APK at the recorded commit](https://github.com/androguard/androguard/blob/581f7a3251545a97f66ee92b674dd810ee380a00/tests/data/APK/hello-world.apk)
- [Source URL, SHA-256, size and command](hello-world-source.json)
- [Complete recorded stdout](hello-world-cli.txt)
- Core implementation at capture: [`f2f2c24`](https://github.com/LiJier/playpilot-cli/commit/f2f2c243800b7ff4ae66e655345746e1a7570bfb); Python 3.13.7 on Windows. The documentation release does not change the analyzer.

After installing the project dependencies, reproduce and compare:

```bash
python -X utf8 examples/reproduce_hello_world.py --download --check
```

The helper downloads only this pinned upstream file when absent, checks its SHA-256 before running the CLI, and stores it in ignored `downloads/`. It does not install or execute the APK. The APK is not redistributed in this repository or Release. Future rule/dependency changes can change output; `--check` reports a diff rather than replacing the saved evidence.

Observed facts: package `de.rhab.helloworld`, target SDK 25, minimum SDK 21, zero recognized SDK signatures, no native libraries, one fatal target SDK finding, score 75/100. No privacy URL was supplied, so this run did not test a privacy website. Zero SDK matches does not establish that no data is collected. “Safe” in the native-library progress line only describes that scan's absence of libraries.

## Synthetic ELF headers: locate an alignment risk

```bash
python -X utf8 examples/elf_alignment_demo.py
```

The helper creates two minimal ELF64 headers in a temporary ZIP, runs the real `ElfScanner`, prints the results and removes the generated files. It does not create an installable APK or usable `.so` implementation.

```text
Synthetic ELF headers; not an APK or runtime compatibility test.
lib/arm64-v8a/lib4kb.so | PT_LOAD 0x1000 | FAIL
lib/arm64-v8a/lib16kb.so | PT_LOAD 0x4000 | PASS
Libraries: 2; require review: 1
```

Use this to understand an ELF finding, then check your actual package's ZIP alignment and behavior on a 16 KB device separately. See the [ELF alignment guide](../docs/16kb-elf-alignment.md).
