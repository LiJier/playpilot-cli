import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analyzer.rules_engine import RulesEngine
from analyzer.dex_scanner import DexScanner

class TestRulesExpansion(unittest.TestCase):

    def setUp(self):
        self.engine = RulesEngine()

    def test_query_all_packages_fatal(self):
        manifest_violating = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET", "android.permission.QUERY_ALL_PACKAGES"],
            "services": []
        }
        res = self.engine.evaluate(manifest_violating, [], lang="zh")
        finding = [f for f in res["findings"] if f["rule_id"] == "RULE_QUERY_ALL_PACKAGES"][0]
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["severity"], "FATAL")
        self.assertIn("<queries>", finding["code_diff"])
        self.assertIn("QUERY_ALL_PACKAGES", finding["prompt"])

        # Test clean manifest
        manifest_clean = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET"],
            "services": []
        }
        res_clean = self.engine.evaluate(manifest_clean, [], lang="zh")
        finding_clean = [f for f in res_clean["findings"] if f["rule_id"] == "RULE_QUERY_ALL_PACKAGES"][0]
        self.assertEqual(finding_clean["status"], "PASS")

    def test_account_deletion_policy(self):
        # 1. App has auth SDK, no deletion URL -> HIGH FAIL
        manifest_with_auth = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET"],
            "services": [],
            "activities": ["com.app.MainActivity", "com.app.AuthActivity"]
        }
        res_fail = self.engine.evaluate(
            manifest_with_auth, 
            [{"id": "supabase_auth", "category": "Authentication and Database"}],
            account_deletion_url=None,
            lang="en"
        )
        finding_fail = [f for f in res_fail["findings"] if f["rule_id"] == "RULE_ACCOUNT_DELETION_POLICY"][0]
        self.assertEqual(finding_fail["status"], "FAIL")
        self.assertEqual(finding_fail["severity"], "HIGH")
        self.assertIn("delete-account", finding_fail["code_diff"])

        # 2. App has auth SDK and provides deletion URL -> PASS
        res_pass = self.engine.evaluate(
            manifest_with_auth, 
            [{"id": "supabase_auth", "category": "Authentication and Database"}],
            account_deletion_url="https://myapp.com/delete-account",
            lang="en"
        )
        finding_pass = [f for f in res_pass["findings"] if f["rule_id"] == "RULE_ACCOUNT_DELETION_POLICY"][0]
        self.assertEqual(finding_pass["status"], "PASS")

        # 3. Clean app with no auth -> PASS
        manifest_no_auth = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET"],
            "services": [],
            "activities": ["com.app.MainActivity"]
        }
        res_exempt = self.engine.evaluate(manifest_no_auth, [], lang="en")
        finding_exempt = [f for f in res_exempt["findings"] if f["rule_id"] == "RULE_ACCOUNT_DELETION_POLICY"][0]
        self.assertEqual(finding_exempt["status"], "PASS")

    def test_storage_photo_picker_policy(self):
        # 1. MANAGE_EXTERNAL_STORAGE -> FATAL
        manifest_manage = {
            "target_sdk": 34,
            "permissions": ["android.permission.MANAGE_EXTERNAL_STORAGE"],
            "services": []
        }
        res_manage = self.engine.evaluate(manifest_manage, [], lang="zh")
        finding_manage = [f for f in res_manage["findings"] if f["rule_id"] == "RULE_STORAGE_PHOTO_PICKER"][0]
        self.assertEqual(finding_manage["status"], "FAIL")
        self.assertEqual(finding_manage["severity"], "FATAL")
        self.assertIn("PickVisualMedia", finding_manage["code_diff"])

        # 2. Legacy storage on targetSdk 34 -> HIGH
        manifest_legacy = {
            "target_sdk": 34,
            "permissions": ["android.permission.READ_EXTERNAL_STORAGE"],
            "services": []
        }
        res_legacy = self.engine.evaluate(manifest_legacy, [], lang="zh")
        finding_legacy = [f for f in res_legacy["findings"] if f["rule_id"] == "RULE_STORAGE_PHOTO_PICKER"][0]
        self.assertEqual(finding_legacy["status"], "FAIL")
        self.assertEqual(finding_legacy["severity"], "HIGH")

        # 3. Clean storage
        manifest_clean = {
            "target_sdk": 34,
            "permissions": ["android.permission.READ_MEDIA_IMAGES"],
            "services": []
        }
        res_clean = self.engine.evaluate(manifest_clean, [], lang="zh")
        finding_clean = [f for f in res_clean["findings"] if f["rule_id"] == "RULE_STORAGE_PHOTO_PICKER"][0]
        self.assertEqual(finding_clean["status"], "PASS")

    def test_exact_alarm_policy(self):
        # 1. SCHEDULE_EXACT_ALARM on targetSdk 34 -> HIGH FAIL
        manifest_exact = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET", "android.permission.SCHEDULE_EXACT_ALARM"],
            "services": []
        }
        res = self.engine.evaluate(manifest_exact, [], lang="zh")
        finding = [f for f in res["findings"] if f["rule_id"] == "RULE_EXACT_ALARM"][0]
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["severity"], "HIGH")
        self.assertIn("WorkManager", finding["code_diff"])

        # 2. USE_EXACT_ALARM -> WARN
        manifest_use_exact = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET", "android.permission.USE_EXACT_ALARM"],
            "services": []
        }
        res_use = self.engine.evaluate(manifest_use_exact, [], lang="zh")
        finding_use = [f for f in res_use["findings"] if f["rule_id"] == "RULE_EXACT_ALARM"][0]
        self.assertEqual(finding_use["status"], "WARN")

        # 3. Clean
        manifest_clean = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET"],
            "services": []
        }
        res_clean = self.engine.evaluate(manifest_clean, [], lang="zh")
        finding_clean = [f for f in res_clean["findings"] if f["rule_id"] == "RULE_EXACT_ALARM"][0]
        self.assertEqual(finding_clean["status"], "PASS")

    def test_full_screen_intent_policy(self):
        # 1. USE_FULL_SCREEN_INTENT on targetSdk 34 -> HIGH FAIL
        manifest_fsi = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET", "android.permission.USE_FULL_SCREEN_INTENT"],
            "services": []
        }
        res = self.engine.evaluate(manifest_fsi, [], lang="zh")
        finding = [f for f in res["findings"] if f["rule_id"] == "RULE_FULL_SCREEN_INTENT"][0]
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["severity"], "HIGH")

        # 2. Clean
        manifest_clean = {
            "target_sdk": 34,
            "permissions": ["android.permission.INTERNET"],
            "services": []
        }
        res_clean = self.engine.evaluate(manifest_clean, [], lang="zh")
        finding_clean = [f for f in res_clean["findings"] if f["rule_id"] == "RULE_FULL_SCREEN_INTENT"][0]
        self.assertEqual(finding_clean["status"], "PASS")

    def test_new_sdk_signatures_present(self):
        scanner = DexScanner()
        sdk_ids = {s["id"] for s in scanner.signatures}
        self.assertGreaterEqual(len(sdk_ids), 80)
        self.assertIn("fyber", sdk_ids)
        self.assertIn("yandex_ads", sdk_ids)
        self.assertIn("kwai_ads", sdk_ids)
        self.assertIn("adapty", sdk_ids)
        self.assertIn("qonversion", sdk_ids)
        self.assertIn("superwall", sdk_ids)
        self.assertIn("flurry", sdk_ids)
        self.assertIn("intercom", sdk_ids)
        self.assertIn("zendesk", sdk_ids)
        self.assertIn("clerk_auth", sdk_ids)

    def test_framework_detector(self):
        import zipfile
        import tempfile
        from analyzer.framework_detector import FrameworkDetector

        # Test Flutter detection
        with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                z.writestr("lib/arm64-v8a/libflutter.so", b"mock flutter binary")
                z.writestr("assets/flutter_assets/AssetManifest.json", b"{}")
            fw = FrameworkDetector.detect(tmp_path)
            self.assertEqual(fw["id"], "flutter")
            self.assertTrue(fw["is_cross_platform"])
            self.assertEqual(fw["name"], "Flutter")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Test React Native detection
        with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                z.writestr("lib/arm64-v8a/libreactnativejni.so", b"mock rn binary")
                z.writestr("assets/index.android.bundle", b"mock bundle")
            fw = FrameworkDetector.detect(tmp_path)
            self.assertEqual(fw["id"], "react_native")
            self.assertTrue(fw["is_cross_platform"])
            self.assertEqual(fw["name"], "React Native")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Test Native fallback
        with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with zipfile.ZipFile(tmp_path, "w") as z:
                z.writestr("classes.dex", b"mock dex")
            fw = FrameworkDetector.detect(tmp_path)
            self.assertEqual(fw["id"], "native")
            self.assertFalse(fw["is_cross_platform"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()

