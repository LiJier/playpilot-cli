import unittest
import csv
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analyzer.data_safety_csv_exporter import DataSafetyCsvExporter
from analyzer.report_exporter import ReportExporter
from analyzer.rules_engine import RulesEngine
from analyzer.data_safety_mapper import DataSafetyMapper
from analyzer.prompt_generator import PromptGenerator

class TestDataSafetyCsvExporter(unittest.TestCase):

    def test_clean_app_csv(self):
        csv_str = DataSafetyCsvExporter.export_csv([])
        reader = list(csv.reader(io.StringIO(csv_str)))
        
        self.assertEqual(len(reader), 783)
        self.assertEqual(reader[0], [
            "Question ID (machine readable)",
            "Response ID (machine readable)",
            "Response value",
            "Answer requirement",
            "Human-friendly question label"
        ])

        # Check top-level personal data declaration
        top_row = [r for r in reader if r[0] == "PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA"][0]
        self.assertEqual(top_row[2], "false")

        # Check account none
        acm_row = [r for r in reader if r[0] == "PSL_SUPPORTED_ACCOUNT_CREATION_METHODS" and r[1] == "PSL_ACM_NONE"][0]
        self.assertEqual(acm_row[2], "true")

    def test_admob_app_csv(self):
        sample_sdks = [
            {
                "id": "admob",
                "name": "Google AdMob",
                "data_safety": {
                    "collected_data": ["Device or other IDs", "Approximate location", "App interactions"],
                    "purposes": ["Advertising or marketing", "Analytics"],
                    "shared_with_third_parties": True,
                    "ephemeral": False
                }
            }
        ]
        csv_str = DataSafetyCsvExporter.export_csv(sample_sdks)
        reader = list(csv.reader(io.StringIO(csv_str)))

        self.assertEqual(len(reader), 783)

        # Personal data is collected
        top_row = [r for r in reader if r[0] == "PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA"][0]
        self.assertEqual(top_row[2], "true")

        # Encryption in transit
        enc_row = [r for r in reader if r[0] == "PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT"][0]
        self.assertEqual(enc_row[2], "true")

        # Device ID collected
        dev_id_row = [r for r in reader if r[0] == "PSL_DATA_TYPES_IDENTIFIERS" and r[1] == "PSL_DEVICE_ID"][0]
        self.assertEqual(dev_id_row[2], "true")

        # Device ID usage shared
        shared_row = [r for r in reader if "PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:PSL_DATA_USAGE_COLLECTION_AND_SHARING" in r[0] and r[1] == "PSL_DATA_USAGE_ONLY_SHARED"][0]
        self.assertEqual(shared_row[2], "true")

        # Advertising purpose
        ad_row = [r for r in reader if "PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:DATA_USAGE_COLLECTION_PURPOSE" in r[0] and r[1] == "PSL_ADVERTISING"][0]
        self.assertEqual(ad_row[2], "true")

class TestReportExporter(unittest.TestCase):

    def test_generate_markdown_report_bilingual(self):
        manifest = {
            "package_name": "com.example.testapp",
            "version_name": "1.0.0",
            "version_code": "1",
            "min_sdk": 24,
            "target_sdk": 33,
            "permissions": ["android.permission.INTERNET"],
            "services": []
        }
        detected_sdks = [
            {
                "id": "admob",
                "name": "Google AdMob",
                "category": "Advertising and Monetization",
                "data_safety": {
                    "collected_data": ["Device or other IDs"],
                    "purposes": ["Advertising or marketing"],
                    "shared_with_third_parties": True
                }
            }
        ]
        engine = RulesEngine()
        eval_result = engine.evaluate(manifest, detected_sdks, lang="zh")
        safety_report = DataSafetyMapper.generate_report(detected_sdks, lang="zh")
        prompt = PromptGenerator.generate_all_in_one_prompt(manifest, eval_result["findings"], lang="zh")

        # Generate Chinese report
        zh_report = ReportExporter.generate_markdown_report(
            manifest, eval_result, detected_sdks, safety_report, prompt, lang="zh"
        )
        self.assertIn("com.example.testapp", zh_report)
        self.assertIn("Target SDK 等级合规性检查", zh_report)
        self.assertIn("```diff", zh_report)
        self.assertIn("Google AdMob", zh_report)

        # Generate English report
        en_eval = engine.evaluate(manifest, detected_sdks, lang="en")
        en_safety = DataSafetyMapper.generate_report(detected_sdks, lang="en")
        en_prompt = PromptGenerator.generate_all_in_one_prompt(manifest, en_eval["findings"], lang="en")
        en_report = ReportExporter.generate_markdown_report(
            manifest, en_eval, detected_sdks, en_safety, en_prompt, lang="en"
        )
        self.assertIn("com.example.testapp", en_report)
        self.assertIn("Target SDK Version Compliance Check", en_report)
        self.assertIn("```diff", en_report)
        self.assertIn("Executive Summary", en_report)

if __name__ == "__main__":
    unittest.main()
