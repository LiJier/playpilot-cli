# Changelog

## v0.1.0 — 2026-10-28

First tagged CLI release of the existing open-source inspector. This is a CLI release number, independent of the Web backend version.

### Included

- Static APK/AAB manifest inspection, DEX SDK fingerprints, framework hints and 64-bit ELF segment-alignment checks.
- Current target API rules with required-device-feature exceptions, selected manifest/permission checks and a shared Web/CLI risk score.
- Actual privacy-URL probing when `--privacy-url` is supplied; the original local package is not deleted or uploaded.
- Shared Data Safety candidate/questionnaire/CSV modules with explicit answers, conditional validation and template comparison. The CLI command itself has no questionnaire or CSV export flags.
- English default README, Chinese README, three problem-focused guides, a pinned public APK capture with SHA-256 and a synthetic ELF demo.

### Validation

- 50 CLI unit tests passed on Windows with Python 3.13.7.
- A real static inspection of Androguard's pinned public hello-world APK reproduced the committed stdout; provenance is in `examples/hello-world-source.json`.
- Synthetic 4 KB and 16 KB ELF headers exercise the actual scanner; they are not runnable libraries or a runtime-compatibility test.
- Bundled bundletool 1.17.2 started successfully with the installed Java 24 runtime. This release does not claim an end-to-end AAB build test or a full OS/Python/Java support matrix.

### Known limits

- Checks cover selected static indicators, not all policies, runtime behavior, data flows, APK ZIP alignment or Google Play approval.
- A finished CLI inspection may return `0` even with failed findings; it is not a CI policy gate.
- Parser fallbacks, malformed libraries and SDK signature coverage require review; empty scan results do not prove compliance.
- No terminal questionnaire, CSV command, package-manager distribution or compiled application is introduced. Install from source. GitHub supplies source archives; no third-party APK is attached.
