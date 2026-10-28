# PlayPilot CLI — Google Play Preflight Checker for APK & AAB

Inspect Android release packages locally for target SDK, selected manifest permissions, SDK fingerprints and 16 KB ELF segment-alignment risks before submission.

**English** · [简体中文](README_ZH.md) · [Guides](#practical-guides) · [Release notes](CHANGELOG.md) · MIT

After [installation](#installation), inspect your release package:

```bash
python -X utf8 cli.py path/to/app-release.apk --lang en
```

## Actual inspection output

The following excerpts were captured from Androguard's public hello-world test APK on 2026-10-28. This old sample is deliberately useful for demonstrating a target SDK finding; it is not a customer deployment or a current compliant application.

```text
[2/5] Parsing AndroidManifest...
  + Package Name : de.rhab.helloworld
  + Target SDK   : 25
  + Min SDK      : 21
```

```text
  COMPLIANCE SCORE: 75 / 100
  Findings: 1 Fatal | 0 High Risk | 0 Warnings
============================================================
  [FATAL]  Target SDK Version Compliance Check
           Tip: Update targetSdk and compileSdk in your build.gradle to 36 or higher....
```

[Full output, fixed source and SHA-256](examples/README.md) · Reproduce with `python -X utf8 examples/reproduce_hello_world.py --download --check`.

The result is 75/100 because one fatal finding deducts 25 points. A score is a risk summary, not an approval probability. The sample has no native libraries and no recognized SDK signatures; those results do not establish runtime compatibility or absence of data collection.

## Scope and limits

| Inspects | Requires separate review |
| --- | --- |
| APK/AAB manifests and selected target SDK/permission rules | Complete policy applicability, store listing and account eligibility |
| Known DEX SDK prefixes and framework file signatures | Runtime behavior, library configuration/version and first-party/backend data flows |
| ELF load-segment alignment in native libraries | Final APK ZIP alignment and testing on a 16 KB device |
| A supplied privacy URL's HTTP reachability and TLS | Accuracy/completeness of policy text and deletion workflows |

The CLI reads your local package without uploading it or deleting your original file. Supplying `--privacy-url` makes a network request to that URL. Unknown SDKs and parser fallbacks need review. The command has no interactive Data Safety questionnaire or CSV export flags, and may return exit code `0` even when findings fail.

## Web workbench

For a visual report, remediation prompts and a manually reviewed Data Safety CSV, use **[PlayPilot Web](https://play.ljcan.com/en/)**. Uploaded packages are temporary to the page session and deleted when it ends. SDK candidates are not preselected declaration answers; confirm actual data practices and review any import in Play Console.

## Installation

Python 3.10+ is required by the source. The release was verified with Python 3.13.7 on Windows; it is not a full compatibility-matrix claim. AAB manifest parsing additionally needs a Java runtime compatible with the bundled bundletool. APK inspection does not require Java.

```bash
git clone https://github.com/LiJier/playpilot-cli.git
cd playpilot-cli
python -m pip install -r requirements.txt
python -X utf8 cli.py path/to/app-release.apk --lang en
```

Use `-X utf8` for the CLI's Unicode output, particularly on Windows. If inspecting AABs, check the bundled tool before running an inspection:

```bash
java -jar src/bin/bundletool.jar version
python -X utf8 cli.py path/to/app-release.aab --lang en
```

## Options

| Input | Behavior |
| --- | --- |
| `file` | Path to an existing APK or AAB |
| `--lang en` / `--lang zh` | English (default) or Chinese findings |
| `--privacy-url URL` | Actually probes the supplied URL; omission makes no privacy-page request |
| `--account-del-url URL` | Supplies the deletion link to the rule engine; does not test the deletion workflow |

```bash
python -X utf8 cli.py path/to/app-release.apk --lang zh
python -X utf8 cli.py path/to/app-release.apk --privacy-url https://example.com/privacy
```

Replace `example.com` with your own page. Run `python -X utf8 cli.py --help` for the current command options.

## Practical guides

- [Check 16 KB ELF alignment in an APK or AAB](docs/16kb-elf-alignment.md): locate affected libraries and separate ELF, ZIP and runtime checks.
- [Inspect target SDK and AndroidManifest permissions](docs/target-sdk-manifest.md): interpret parsed values, required-device exceptions and selected permission findings.
- [Use SDK detection for Data Safety review](docs/sdk-data-safety-review.md): turn candidates into an evidence checklist without assuming collection or sharing facts.
- [Reproduce real and synthetic inspection examples](examples/README.md): fixed public APK capture and temporary ELF-header demonstration.

## Scoring and current policy baseline

Web and CLI share the same score: start at 100, subtract 25 per fatal failure, 15 per high-risk failure and 5 per warning, with a floor of 15.

As verified on 2026-10-28, ordinary new apps/updates require target API 36; required-device features identify Wear OS/Automotive 35 and TV/XR 34 exceptions. Existing-app availability and extensions are separate. Recheck [Google's target API requirements](https://developer.android.com/google/play/requirements/target-sdk) and your Console before submission.

## Development and releases

```bash
python -m unittest discover tests
python -X utf8 examples/elf_alignment_demo.py
```

[v0.1.0 release notes](CHANGELOG.md) record the included functionality, actual validation and known limits. This initial CLI release number is independent of the Web backend version. Install from source; the project does not currently distribute a PyPI package or compiled CLI binary.

The shared Data Safety modules support programmatic use, but are not a terminal questionnaire. Changes and reproducible reports are welcome through [Issues](https://github.com/LiJier/playpilot-cli/issues) and pull requests; describe the command, version and minimal reproduction.

## License

[MIT](LICENSE). The public APK example links to its upstream source and is not bundled in this repository or release.
