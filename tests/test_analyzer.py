import os
import sys
import zipfile
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


from analyzer.manifest_parser import ManifestParser
from analyzer.dex_scanner import DexScanner
from analyzer.data_safety_mapper import DataSafetyMapper
from analyzer.rules_engine import RulesEngine
from analyzer.prompt_generator import PromptGenerator

class TestAnalyzer(unittest.TestCase):
    def test_xml_manifest_parsing(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            package="com.playpilot.test"
            android:versionCode="10"
            android:versionName="1.0.0">
            <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />
            <uses-permission android:name="android.permission.INTERNET" />
            <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
            <application>
                <service android:name=".MyService" android:foregroundServiceType="dataSync" />
                <activity android:name=".MainActivity" />
            </application>
        </manifest>"""
        parser = ManifestParser()
        result = parser._parse_xml_string(sample_xml)
        self.assertEqual(result["package_name"], "com.playpilot.test")
        self.assertEqual(result["target_sdk"], 34)
        self.assertIn("android.permission.INTERNET", result["permissions"])
        self.assertIn("android.permission.FOREGROUND_SERVICE", result["permissions"])
        self.assertEqual(len(result["services"]), 1)
        self.assertTrue(result["services"][0]["has_fgs_type"])

    def test_dex_scanner(self):
        # Create a mock zip with a simulated classes.dex containing AdMob and Firebase strings
        with tempfile.NamedTemporaryFile(suffix=".aab", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                # write a dummy dex containing byte patterns
                dummy_dex = b"DEX\n035\x00" + b"some_code_padding" + b"Lcom/google/android/gms/ads/AdView;" + b"padding" + b"Lio/sentry/Sentry;"
                z.writestr("base/dex/classes.dex", dummy_dex)

            scanner = DexScanner()
            detected = scanner.scan(tmp_path)
            detected_ids = [d["id"] for d in detected]
            self.assertIn("admob", detected_ids)
            self.assertIn("sentry", detected_ids)
            self.assertNotIn("adjust", detected_ids)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_rules_engine_pass(self):
        engine = RulesEngine()
        manifest = {
            "package_name": "com.compliant.app",
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET", "com.google.android.gms.permission.AD_ID"],
            "services": []
        }
        detected_sdks = [
            {"id": "admob", "name": "AdMob", "category": "Advertising"}
        ]
        # Test Chinese
        res_zh = engine.evaluate(manifest, detected_sdks, {"is_valid": True, "status_code": 200, "url": "https://example.com"}, lang="zh")
        self.assertEqual(res_zh["counts"]["fatal"], 0)
        self.assertEqual(res_zh["overall_status"], "PASSED")
        self.assertIn("核心合规项全数通过", res_zh["status_text"])

        # Test English
        res_en = engine.evaluate(manifest, detected_sdks, {"is_valid": True, "status_code": 200, "url": "https://example.com"}, lang="en")
        self.assertEqual(res_en["counts"]["fatal"], 0)
        self.assertEqual(res_en["overall_status"], "PASSED")
        self.assertIn("All Core Compliance Checks Passed", res_en["status_text"])

    def test_rules_engine_fatal_target_sdk(self):
        engine = RulesEngine()
        manifest = {
            "package_name": "com.outdated.app",
            "target_sdk": 33, # below 34!
            "permissions": ["android.permission.INTERNET"],
            "services": []
        }
        # Chinese evaluation and prompt
        res_zh = engine.evaluate(manifest, [], None, lang="zh")
        self.assertEqual(res_zh["counts"]["fatal"], 1)
        self.assertEqual(res_zh["overall_status"], "FATAL_BLOCKER")
        prompt_zh = PromptGenerator.generate_all_in_one_prompt(manifest, res_zh["findings"], lang="zh")
        self.assertIn("targetSdkVersion 不合规", prompt_zh)
        self.assertIn("com.outdated.app", prompt_zh)

        # English evaluation and prompt
        res_en = engine.evaluate(manifest, [], None, lang="en")
        self.assertEqual(res_en["counts"]["fatal"], 1)
        self.assertEqual(res_en["overall_status"], "FATAL_BLOCKER")
        prompt_en = PromptGenerator.generate_all_in_one_prompt(manifest, res_en["findings"], lang="en")
        self.assertIn("non-compliant targetSdkVersion", prompt_en)
        self.assertIn("com.outdated.app", prompt_en)

    def test_data_safety_mapper(self):
        sdks = [
            {
                "id": "admob",
                "name": "Google AdMob",
                "category": "Advertising",
                "data_safety": {
                    "collected_data": ["Device or other IDs", "Approximate location"],
                    "purposes": ["Advertising or marketing", "Analytics"],
                    "shared_with_third_parties": True
                }
            }
        ]
        # Test Chinese
        report_zh = DataSafetyMapper.generate_report(sdks, lang="zh")
        self.assertEqual(report_zh["sdk_count"], 1)
        self.assertTrue(report_zh["has_third_party_sharing"])
        self.assertTrue(any("粗略位置" in dt for dt in report_zh["data_types_summary"]))
        self.assertTrue(any("商业广告或营销" in p for p in report_zh["purposes_summary"]))

        # Test English
        report_en = DataSafetyMapper.generate_report(sdks, lang="en")
        self.assertEqual(report_en["sdk_count"], 1)
        self.assertTrue(report_en["has_third_party_sharing"])
        self.assertIn("Approximate location", report_en["data_types_summary"])
        self.assertIn("Advertising or marketing", report_en["purposes_summary"])

    def test_rules_engine_16kb_page_alignment(self):
        engine = RulesEngine()
        manifest_api35 = {"package_name": "com.test.so", "target_sdk": 35, "permissions": ["android.permission.INTERNET"], "services": []}
        manifest_api34 = {"package_name": "com.test.so", "target_sdk": 34, "permissions": ["android.permission.INTERNET"], "services": []}

        # 1. Non-compliant .so under Target SDK 35 (Android 15) -> FATAL
        bad_elf = {
            "has_native_libs": True,
            "total_so_count": 1,
            "non_compliant_count": 1,
            "non_compliant_libs": [{"name": "libbad.so", "abi": "arm64-v8a", "min_load_align_hex": "0x1000"}]
        }
        res_35 = engine.evaluate(manifest_api35, [], None, lang="zh", elf_result=bad_elf)
        finding_35 = next(f for f in res_35["findings"] if f["rule_id"] == "RULE_16KB_PAGE_ALIGNMENT")
        self.assertEqual(finding_35["status"], "FAIL")
        self.assertEqual(finding_35["severity"], "FATAL")
        self.assertIn("16KB 内存页面对齐", finding_35["message"])

        # 2. Non-compliant .so under Target SDK 34 -> HIGH warning
        res_34 = engine.evaluate(manifest_api34, [], None, lang="en", elf_result=bad_elf)
        finding_34 = next(f for f in res_34["findings"] if f["rule_id"] == "RULE_16KB_PAGE_ALIGNMENT")
        self.assertEqual(finding_34["status"], "FAIL")
        self.assertEqual(finding_34["severity"], "HIGH")
        self.assertIn("16KB", finding_34["message"])

        # 3. All compliant .so -> PASS
        good_elf = {
            "has_native_libs": True,
            "total_so_count": 2,
            "non_compliant_count": 0,
            "non_compliant_libs": []
        }
        res_good = engine.evaluate(manifest_api35, [], None, lang="zh", elf_result=good_elf)
        finding_good = next(f for f in res_good["findings"] if f["rule_id"] == "RULE_16KB_PAGE_ALIGNMENT")
        self.assertEqual(finding_good["status"], "PASS")

        # 4. No native libraries -> PASS
        no_elf = {
            "has_native_libs": False,
            "total_so_count": 0,
            "non_compliant_count": 0,
            "non_compliant_libs": []
        }
        res_none = engine.evaluate(manifest_api35, [], None, lang="zh", elf_result=no_elf)
        finding_none = next(f for f in res_none["findings"] if f["rule_id"] == "RULE_16KB_PAGE_ALIGNMENT")
        self.assertEqual(finding_none["status"], "PASS")
        self.assertIn("未检测到 C/C++", finding_none["message"])

if __name__ == "__main__":
    unittest.main()

