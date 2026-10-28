# Inspect target SDK and AndroidManifest permissions before Google Play submission

**English** · [简体中文](target-sdk-manifest.zh.md) · [README](../README.md) · [Recorded APK run](../examples/README.md) · [16 KB ELF guide](16kb-elf-alignment.md)

The source manifest and Gradle configuration describe the intended build. Inspect the actual APK or AAB to see what reached the release artifact after manifest merging and dependency packaging.

## Run a package inspection

```bash
python -X utf8 cli.py path/to/app-release.apk --lang en
```

PlayPilot prints the package name, minimum SDK, target SDK, recognized SDK names and selected rule findings. APK parsing uses `pyaxmlparser`; AAB manifest extraction uses the bundled `bundletool.jar` and a compatible Java runtime.

If the package name is `unknown.apk`, the SDK level is `0`, or parsing reports a problem, investigate parsing before relying on the remaining findings. A missing parsed value is not evidence that the manifest is compliant.

## Interpret the target SDK finding

The current rule defaults to API 36 for ordinary new submissions and updates. Required device features identify Wear OS/Automotive API 35 and TV/XR API 34 exceptions. Optional features do not lower the ordinary-app threshold.

Existing-app availability, permanently private distribution and extension eligibility need separate checks in Play Console. Review the [official target API requirements](https://developer.android.com/google/play/requirements/target-sdk), verified for this document on 2026-10-28, before acting on a policy date.

The [recorded public test APK](../examples/README.md) targets API 25. The actual CLI run reports:

```text
  COMPLIANCE SCORE: 75 / 100
  Findings: 1 Fatal | 0 High Risk | 0 Warnings
```

That score is the tool's risk summary, not a percentage chance of Google Play approval. The sample has no native libraries and does not demonstrate native-library compatibility.

## Review permissions and foreground services

Open the individual finding and trace each permission to your code or a dependency's merged manifest. Depending on the artifact and SDK fingerprints, rules review selected restricted permissions, broad package visibility, storage/media access, advertising ID, exact alarms, full-screen intent and foreground-service declarations.

Do not remove a permission or choose a foreground-service type merely to make a check pass. Confirm the app's core use case, Android runtime behavior and any declaration required by Google Play, then rebuild and inspect again. Static matches do not establish your eligibility to use restricted permissions.

You can inspect the parsed manifest without changing the CLI:

```python
import json
import sys
sys.path.insert(0, "src")
from analyzer.manifest_parser import ManifestParser

print(json.dumps(ManifestParser().parse("path/to/app-release.apk"), indent=2))
```

## Privacy URLs and automation

```bash
python -X utf8 cli.py path/to/app-release.apk --lang en --privacy-url https://example.com/privacy
```

Replace the example with your real policy page. This option makes an HTTP request and checks reachability, redirects and TLS verification; it does not establish that the policy text is complete or legally sufficient. `--account-del-url` supplies an account-deletion URL to the rule engine; the CLI does not verify the deletion workflow.

The current CLI can finish with exit code `0` even when findings fail. It does not provide a policy-based nonzero exit gate or structured-report flag. A CI command that only runs the CLI is an inspection step, not enforcement that the build passed every rule.

[Web policy reference](https://play.ljcan.com/en/policies/) · [Data Safety review guide](sdk-data-safety-review.md)
