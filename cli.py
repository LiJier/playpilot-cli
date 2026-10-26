#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlayPilot CLI - Google Play Pre-flight Compliance Inspector
Pure-static, zero-retention compliance auditor for Android APK & AAB.

Online Web App: https://play.ljcan.com
"""

import sys
import os
import argparse
from pathlib import Path

# Resolve analyzer modules from src
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from analyzer.manifest_parser import ManifestParser
from analyzer.dex_scanner import DexScanner
from analyzer.elf_scanner import ElfScanner
from analyzer.framework_detector import FrameworkDetector
from analyzer.rules_engine import RulesEngine
from analyzer.scoring import calculate_score_and_categories
from analyzer.url_checker import UrlChecker
from analyzer.data_safety_mapper import DataSafetyMapper
from analyzer.prompt_generator import PromptGenerator

def print_banner():
    banner = r"""
  ____  _             ____  _ _       _   
 |  _ \| | __ _ _   _|  _ \(_) | ___ | |_ 
 | |_) | |/ _` | | | | |_) | | |/ _ \| __|
 |  __/| | (_| | |_| |  __/| | | (_) | |_ 
 |_|   |_|\__,_|\__, |_|   |_|_|\___/ \__|
                |___/  Pre-flight Inspector
    """
    print(banner)
    print("  Google Play Policy & Pre-flight Compliance Auditor (Pure-Static)")
    print("  Web Version: https://play.ljcan.com\n" + "-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="PlayPilot - Pure-static Google Play compliance auditor for .aab and .apk"
    )
    parser.add_argument("file", help="Path to .aab or .apk file")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="Output language (en/zh)")
    parser.add_argument("--privacy-url", default="", help="Optional Privacy Policy URL")
    parser.add_argument("--account-del-url", default="", help="Optional Account Deletion URL")

    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    target_file = os.path.abspath(args.file)

    if not os.path.exists(target_file):
        print(f"[-] Error: File not found: {target_file}")
        sys.exit(1)

    print_banner()
    print(f"[*] Target Package: {os.path.basename(target_file)}")
    print(f"[*] Package Size   : {os.path.getsize(target_file) / (1024*1024):.2f} MB")
    print(f"[*] Language       : {args.lang.upper()}\n")

    print("[1/5] Detecting Application Framework Architecture...")
    framework_info = FrameworkDetector.detect(target_file)
    print(f"  + Framework    : {framework_info.get('icon', '🤖')} {framework_info.get('name', 'Native Android')}")
    if framework_info.get("is_cross_platform"):
        print(f"  + Cross-Platform Engine detected: {', '.join(framework_info.get('evidence', []))}")

    print("\n[2/5] Parsing AndroidManifest...")
    manifest_parser = ManifestParser()
    try:
        manifest = manifest_parser.parse(target_file)
        print(f"  + Package Name : {manifest.get('package_name', 'N/A')}")
        print(f"  + Target SDK   : {manifest.get('target_sdk_version', manifest.get('target_sdk', 'N/A'))}")
        print(f"  + Min SDK      : {manifest.get('min_sdk_version', manifest.get('min_sdk', 'N/A'))}")
    except Exception as e:
        print(f"  [-] Manifest parsing warning: {e}")
        manifest = {}

    print("\n[3/5] Scanning DEX bytefingerprints for 80+ third-party SDKs...")
    dex_scanner = DexScanner()
    detected_sdks = dex_scanner.scan(target_file)
    sdk_names = [s.get("name", s.get("id")) if isinstance(s, dict) else str(s) for s in detected_sdks]
    print(f"  + Detected SDKs: {len(detected_sdks)} found ({', '.join(sdk_names[:6])}{'...' if len(sdk_names) > 6 else ''})")

    print("\n[4/5] Scanning 64-bit ELF shared libraries (.so) for 16KB page alignment...")
    elf_scanner = ElfScanner()
    elf_result = elf_scanner.scan(target_file)
    so_total = elf_result.get("total_so_count", elf_result.get("total_64bit_so_count", 0))
    so_unaligned = len(elf_result.get("non_compliant_libs", [])) if "non_compliant_libs" in elf_result else elf_result.get("unaligned_so_count", 0)
    if so_total > 0:
        if so_unaligned == 0:
            print(f"  + 16KB Page Alignment: [PASS] All {so_total} native .so libraries aligned.")
        else:
            print(f"  + 16KB Page Alignment: [FAIL] {so_unaligned} of {so_total} .so libraries NOT aligned (Android 15 risk)!")
    else:
        print("  + No native libraries (.so) found (Safe).")

    print("\n[5/5] Evaluating Google Play Compliance Rules...")
    privacy_probe = UrlChecker.check_privacy_url(args.privacy_url) if args.privacy_url else None
    engine = RulesEngine()
    eval_result = engine.evaluate(
        manifest=manifest,
        detected_sdks=detected_sdks,
        elf_result=elf_result,
        privacy_url_result=privacy_probe,
        account_deletion_url=args.account_del_url,
        lang=args.lang,
        framework_info=framework_info
    )

    findings = eval_result.get("findings", [])
    score, fatal_cnt, high_cnt, warn_cnt, _ = calculate_score_and_categories(eval_result)

    print("\n" + "=" * 60)
    print(f"  COMPLIANCE SCORE: {score} / 100")
    print(f"  Findings: {fatal_cnt} Fatal | {high_cnt} High Risk | {warn_cnt} Warnings")
    print("=" * 60)

    for f in findings:
        status = f.get("status", "FAIL")
        severity = f.get("severity", "INFO")
        title = f.get("title", "")
        icon = "[PASS]" if status == "PASS" else f"[{severity}]"
        print(f"  {icon:<8} {title}")
        if status != "PASS" and f.get("remediation"):
            print(f"           Tip: {f.get('remediation')[:85]}...")

    print("\n" + "=" * 60)
    print("🚀 Want full AI remediation prompts & Google Play Data Safety CSV?")
    print("👉 Try PlayPilot Online: https://play.ljcan.com")
    print("   • 1-Click Universal AI Agent Prompts for Cursor / Claude Code / Copilot")
    print("   • Official 783-line Data Safety CSV auto-export for Play Console")
    print("   • Zero File Retention (Temporary packages deleted when the page session ends)")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
