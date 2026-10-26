<p align="center">
  <img src="https://play.ljcan.com/logo.svg" alt="PlayPilot Logo" width="96" height="96" />
</p>

<h1 align="center">PlayPilot CLI</h1>

<p align="center">
  <strong>Google Play Pre-flight Compliance Inspector · Pure-static Auditor for Android AAB & APK</strong><br />
  <em>Catch policy rejection risks and 16KB page alignment issues before submission</em>
</p>

<p align="center">
  <a href="https://play.ljcan.com"><img src="https://img.shields.io/badge/🌐%20Live%20Web%20App-play.ljcan.com-00C853?style=for-the-badge&logo=googleplay&logoColor=white" alt="Live Web App" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

<p align="center">
  <strong>English</strong> | <a href="README.md">简体中文</a>
</p>

---

> ### 🌐 Instant Web Version (No Installation Needed)
> If you prefer not to set up local Python or Java environments, use our free online web app directly:  
> 👉 **[https://play.ljcan.com](https://play.ljcan.com)**  
> *Upload your package to inspect · Uploaded packages deleted when the page session ends · Export Play Console Data Safety CSVs · Generate AI fix suggestions*

---

## 🌟 Key Capabilities (Features)

* ⚡ **Pure-Static & Fast Analysis**: Directly inspects APK and AAB binaries without requiring physical Android devices or emulators.
* 🛡️ **Zero File Retention & Privacy**: All audits run 100% locally on your machine. Packages are never uploaded to any external server.
* 📐 **16KB Page Alignment Inspection**: Statically parses 64-bit `.so` native libraries' ELF headers (`PT_LOAD` segment `p_align >= 0x4000`), preventing launch crashes on Android 15.
* 📋 **Data Safety CSV Export**: Automatically maps 50+ popular third-party SDKs (e.g., AdMob, Firebase, Adjust, AppsFlyer) and exports official Google Play Console-compatible CSVs for instant batch import.
* 💡 **Actionable AI Fix Suggestions**: Produces structured code remediation prompts tailored for AI coding assistants (Cursor, Claude Code, GitHub Copilot, Windsurf) to fix manifest and code declarations.
* 🎯 **Comprehensive Google Play Policy Coverage**:
  * Target SDK compliance (API 36 for ordinary new apps and updates)
  * 64-bit native library 16KB page alignment
  * Android 14 Foreground Service types (`foregroundServiceType`) validation
  * Advertising ID (`AD_ID`) permission vs. SDK declaration matching
  * Account deletion policy & public deletion URL accessibility
  * Granular media permissions & Photo Picker migration guidance
  * Privacy policy URL responsiveness and status validation

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.10+
- Java Runtime Environment (JRE 11+): Required only when parsing `.aab` bundles (uses bundled `bundletool.jar`)

### 2. Installation
```bash
git clone https://github.com/LiJier/playpilot-cli.git
cd playpilot-cli
pip install -r requirements.txt
```

### 3. Usage

#### Basic Audit
```bash
python cli.py path/to/app-release.aab
```

#### Chinese Output Mode
```bash
python cli.py path/to/app-release.apk --lang zh
```

#### With Policy URLs Verification
```bash
python cli.py path/to/app-release.aab \
  --lang en \
  --privacy-url "https://example.com/privacy" \
  --account-del-url "https://example.com/delete-account"
```

---


## Scoring and privacy URL checks

Web and CLI share the same score: start at 100, deduct 25 for fatal failures, 15 for high-risk failures and 5 for warnings, with a minimum of 15. This summarizes detected risks, not approval probability.

`--privacy-url` makes an HTTP request and checks status, redirects and HTTPS certificate validation. No request is made when omitted. The CLI reads your local package without deleting it; Web uploads are deleted when their page session ends, with connection checks and expiry cleanup for abnormal disconnects.

Ordinary new apps and updates require API 36; required Manifest device features identify Wear OS/Automotive (35) and TV/XR (34) exceptions. Extension and private-app eligibility need separate Play Console review. [Official requirements](https://developer.android.com/google/play/requirements/target-sdk)


## 🤖 CI/CD Automation (GitHub Actions)

Easily integrate PlayPilot CLI into your build & release pipelines to catch policy issues before submitting to the Play Store:

```yaml
name: Google Play Pre-flight Compliance Check

on:
  push:
    branches: [ release/**, main ]
  pull_request:
    branches: [ main ]

jobs:
  compliance-audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run PlayPilot Compliance Audit
        run: |
          python cli.py build/outputs/bundle/release/app-release.aab --lang en
```

---

## 🧪 Running Unit Tests

Run the complete CLI test suite:

```bash
python -m unittest discover tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
