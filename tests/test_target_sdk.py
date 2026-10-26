import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyzer.manifest_parser import ManifestParser
from analyzer.rules_engine import RulesEngine


class TestTargetSdk(unittest.TestCase):
    def test_submission_boundaries_and_localized_remediation(self):
        engine = RulesEngine()
        for lang in ("zh", "en"):
            for sdk in (34, 35, 36, 37):
                with self.subTest(lang=lang, sdk=sdk):
                    result = engine.evaluate({"target_sdk": sdk}, [], lang=lang, framework_info={"id": "flutter", "is_cross_platform": True})
                    finding = next(f for f in result["findings"] if f["rule_id"] == "RULE_TARGET_SDK")
                    self.assertEqual(finding["status"], "PASS" if sdk >= 36 else "FAIL")
                    if sdk < 36:
                        for field in ("remediation", "code_diff", "prompt", "framework_hint"):
                            self.assertIn("36", finding[field])
                            self.assertNotIn("{min_target_sdk}", finding[field])

    def test_device_exception_requires_required_feature(self):
        engine = RulesEngine()
        for feature, minimum in (("android.hardware.type.watch", 35), ("android.hardware.type.automotive", 35),
                                 ("android.software.leanback", 34), ("android.software.xr.api.spatial", 34)):
            for required in (True, False):
                with self.subTest(feature=feature, required=required):
                    manifest = {"target_sdk": minimum, "uses_features": [{"name": feature, "required": required}]}
                    result = engine.evaluate(manifest, [], lang="en")
                    finding = next(f for f in result["findings"] if f["rule_id"] == "RULE_TARGET_SDK")
                    self.assertEqual(finding["status"], "PASS" if required else "FAIL")

    def test_parser_preserves_feature_required_flag(self):
        manifest = ManifestParser()._parse_xml_string('''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
            <uses-feature android:name="android.hardware.type.watch" />
            <uses-feature android:name="android.software.leanback" android:required="false" />
        </manifest>''')
        self.assertEqual(manifest["uses_features"], [
            {"name": "android.hardware.type.watch", "required": True},
            {"name": "android.software.leanback", "required": False},
        ])


if __name__ == "__main__":
    unittest.main()
