# Use SDK detection to review Google Play Data Safety declarations

**English** · [简体中文](sdk-data-safety-review.zh.md) · [README](../README.md) · [Target SDK and manifest](target-sdk-manifest.md) · [Recorded example](../examples/README.md)

An SDK fingerprint is a reason to investigate data behavior. It does not prove that every SDK feature is enabled, which data leaves the device, or whether a transfer meets Google's definition of sharing.

## Collect a review checklist

```bash
python -X utf8 cli.py path/to/app-release.apk --lang en
```

The CLI shows recognized SDK names and relevant rule findings. It scans DEX bytes for known signature prefixes, rather than running the application or proving a library version. Obfuscation, dynamic loading and unknown SDKs can fall outside its coverage. First-party code, WebViews and backend transfers need independent review.

The public hello-world sample returned zero recognized SDKs. That observation must not be converted into “this app collects no data.”

For candidate metadata from the same signature database, run this from the repository root with your actual file path:

```python
import json
import sys
sys.path.insert(0, "src")
from analyzer.dex_scanner import DexScanner

for sdk in DexScanner().scan("path/to/app-release.apk"):
    print(sdk["name"])
    print(json.dumps(sdk.get("data_safety", {}), indent=2))
```

These are SDK-level suggestions. Do not copy the union of purposes to every data type or treat a `shared_with_third_parties` signature flag as a final Google Play declaration.

## Confirm the actual configuration

For each relevant data type, record the enabled feature, collection timing, destination, recipient role, collection purpose, sharing purpose, user choice and supporting evidence. Include your own code and backend behavior.

| Question | Evidence to review |
| --- | --- |
| Is it collected, shared, both, or neither under Google's definitions? | Actual data flows, provider guidance, contracts and the sharing exceptions |
| Is collection optional for every relevant user? | Consent/configuration and usable opt-out or opt-in paths |
| Is it processed ephemerally? | Whether it stays only in memory for a real-time request, including server/SDK handling |
| Is all relevant data encrypted in transit? | Every endpoint and transfer path, not just the app's main API |
| What deletion options exist? | Actual account/data deletion paths and retention practices |

The [official Data Safety guidance](https://support.google.com/googleplay/android-developer/answer/10787469), checked on 2026-10-28, defines collection/sharing and explains exceptions. Developers are responsible for complete and accurate declarations, including their SDKs.

## Complete the questionnaire in the Web app or Play Console

The CLI has no interactive questionnaire, answer-file input or CSV export flag. The repository includes a shared generator for programmatic use, but no terminal answer-collection flow is added by this release.

Use the [Web workbench](https://play.ljcan.com/en/) to review SDK candidates and manually confirm questionnaire answers. You can add data types missed by the scan, set collection and sharing purposes separately, and compare a CSV template exported from your target Play Console account.

Unknown facts remain blank in a draft. Confirmed export requires applicable answers and local validation. Never infer “all transfers encrypted,” “no account creation” or “deleted within 90 days” from the absence of an SDK match or URL.

Before importing, export a backup of your Console answers: import replaces them. Review the result in Console afterwards. A matching template and valid CSV do not establish accurate facts or approval. The project's export has not been certified through a real import into your target account.

[Web Data Safety walkthrough](https://play.ljcan.com/en/guides/google-play-data-safety/)
