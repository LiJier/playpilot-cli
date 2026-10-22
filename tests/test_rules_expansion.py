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

    def test_new_sdk_signatures_present(self):
        scanner = DexScanner()
        sdk_ids = {s["id"] for s in scanner.signatures}
        self.assertGreaterEqual(len(sdk_ids), 50)
        self.assertIn("supabase_auth", sdk_ids)
        self.assertIn("auth0", sdk_ids)
        self.assertIn("aws_cognito", sdk_ids)
        self.assertIn("branch_metrics", sdk_ids)
        self.assertIn("posthog", sdk_ids)
        self.assertIn("tradplus", sdk_ids)
        self.assertIn("tencent_bugly", sdk_ids)
        self.assertIn("wechat_sdk", sdk_ids)

if __name__ == "__main__":
    unittest.main()
