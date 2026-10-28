import unittest
import csv
import io
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analyzer.data_safety_csv_exporter import (
    DataSafetyCsvExporter as Exporter, DataSafetyValidationError,
    answer_key as key, COLLECTS, ACCOUNTS, DELETION, OUTSIDE,
)
from analyzer.report_exporter import ReportExporter
from analyzer.rules_engine import RulesEngine
from analyzer.data_safety_mapper import DataSafetyMapper
from analyzer.prompt_generator import PromptGenerator


def no_data_answers():
    return {key(COLLECTS): False, key(ACCOUNTS, "PSL_ACM_NONE"): True,
            key(DELETION, "DATA_DELETION_NO"): True, key(OUTSIDE): False}


def data_answers(shared=False, collected=True):
    answers = no_data_answers()
    answers.update({key(COLLECTS): True, key("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT"): False,
                    key("PSL_DATA_TYPES_IDENTIFIERS", "PSL_DEVICE_ID"): True})
    base = "PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:"
    answers[key(base + "PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_COLLECTED")] = collected
    answers[key(base + "PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_SHARED")] = shared
    if collected:
        answers.update({key(base + "PSL_DATA_USAGE_EPHEMERAL"): False,
                        key(base + "DATA_USAGE_USER_CONTROL", "PSL_DATA_USAGE_USER_CONTROL_OPTIONAL"): True,
                        key(base + "DATA_USAGE_COLLECTION_PURPOSE", "PSL_ANALYTICS"): True})
    if shared:
        answers[key(base + "DATA_USAGE_SHARING_PURPOSE", "PSL_FRAUD_PREVENTION_SECURITY")] = True
    return answers


class TestDataSafetyCsvExporter(unittest.TestCase):
    SDK = [{"name": "Auth SDK", "data_safety": {"collected_data": ["User IDs"],
           "purposes": ["Account management"], "shared_with_third_parties": True}}]

    def parsed(self, **kwargs):
        rows = list(csv.reader(io.StringIO(Exporter.export_csv(**kwargs))))
        self.assertEqual(rows[0], Exporter._get_template()[0])
        self.assertEqual(len(rows), len(Exporter._get_template()))
        self.assertTrue(all(len(row) == 5 for row in rows))
        return {key(row[0], row[1]): row[2] for row in rows[1:]}

    def final(self, answers, **kwargs):
        return self.parsed(answers=answers, confirmed=True, template_id=Exporter.template_id(), **kwargs)

    def test_draft_without_sdk_does_not_invent_facts(self):
        self.assertTrue(all(value == "" for value in self.parsed(detected_sdks=[]).values()))

    def test_sdk_hints_never_become_answers(self):
        self.assertTrue(all(value == "" for value in self.parsed(detected_sdks=self.SDK).values()))
        review = Exporter.review(detected_sdks=self.SDK)
        self.assertIn("PSL_USER_ACCOUNT", review["suggestions"])
        self.assertEqual(review["answers"], {})

    def test_deletion_url_preserved_in_draft_without_sdk(self):
        rows = self.parsed(account_deletion_url="https://example.test/delete")
        self.assertEqual(rows[key("PSL_ACCOUNT_DELETION_URL")], "https://example.test/delete")
        self.assertEqual(rows[key(ACCOUNTS, "PSL_ACM_NONE")], "")
        self.assertEqual(rows[key(DELETION, "DATA_DELETION_NO_AUTO_DELETED")], "")

    def test_final_rejects_unanswered_facts_and_stale_template(self):
        for kwargs in ({}, {"answers": no_data_answers(), "template_id": "old"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(DataSafetyValidationError):
                Exporter.export_csv(confirmed=True, **kwargs)

    def test_explicit_no_data_even_with_sdk_is_user_decision(self):
        rows = self.final(no_data_answers(), detected_sdks=self.SDK)
        self.assertEqual(rows[key(COLLECTS)], "FALSE")
        self.assertEqual(rows[key(DELETION, "DATA_DELETION_NO_AUTO_DELETED")], "")

    def test_optional_collection_and_negative_encryption_preserved(self):
        rows = self.final(data_answers(shared=True))
        base = "PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:"
        self.assertEqual(rows[key("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT")], "FALSE")
        self.assertEqual(rows[key(base + "DATA_USAGE_USER_CONTROL", "PSL_DATA_USAGE_USER_CONTROL_OPTIONAL")], "TRUE")
        self.assertEqual(rows[key(base + "DATA_USAGE_USER_CONTROL", "PSL_DATA_USAGE_USER_CONTROL_REQUIRED")], "")
        self.assertEqual(rows[key(base + "DATA_USAGE_COLLECTION_PURPOSE", "PSL_ANALYTICS")], "TRUE")
        self.assertEqual(rows[key(base + "DATA_USAGE_SHARING_PURPOSE", "PSL_ANALYTICS")], "")
        self.assertEqual(rows[key(base + "DATA_USAGE_SHARING_PURPOSE", "PSL_FRAUD_PREVENTION_SECURITY")], "TRUE")

    def test_shared_only_does_not_declare_collection(self):
        rows = self.final(data_answers(shared=True, collected=False))
        base = "PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:"
        self.assertEqual(rows[key(base + "PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_COLLECTED")], "FALSE")
        self.assertEqual(rows[key(base + "PSL_DATA_USAGE_EPHEMERAL")], "")
        self.assertEqual(rows[key(base + "DATA_USAGE_USER_CONTROL", "PSL_DATA_USAGE_USER_CONTROL_REQUIRED")], "")

    def test_account_method_exclusivity(self):
        answers = no_data_answers(); answers[key(ACCOUNTS, "PSL_ACM_OAUTH")] = True
        with self.assertRaises(DataSafetyValidationError): self.final(answers)

    def test_account_and_data_deletion_require_separate_urls(self):
        answers = no_data_answers(); del answers[key(ACCOUNTS, "PSL_ACM_NONE")]
        answers.update({key(ACCOUNTS, "PSL_ACM_OTHER"): True, key("PSL_ACM_SPECIFY"): "Custom identity",
                        key("PSL_ACCOUNT_DELETION_URL"): "https://example.test/account",
                        key(DELETION, "DATA_DELETION_YES"): True})
        del answers[key(DELETION, "DATA_DELETION_NO")]
        with self.assertRaises(DataSafetyValidationError): self.final(answers)
        answers[key("PSL_DATA_DELETION_URL")] = "https://example.test/data"
        rows = self.final(answers)
        self.assertEqual(rows[key("PSL_ACCOUNT_DELETION_URL")], "https://example.test/account")
        self.assertEqual(rows[key("PSL_DATA_DELETION_URL")], "https://example.test/data")

    def test_invalid_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "/delete", "https://user:pass@example.test", "https://example.test/a b", "https://example.test:bad"):
            with self.subTest(url=url), self.assertRaises(DataSafetyValidationError):
                self.parsed(account_deletion_url=url)

    def test_auto_delete_requires_explicit_selection(self):
        answers = no_data_answers(); del answers[key(DELETION, "DATA_DELETION_NO")]
        answers[key(DELETION, "DATA_DELETION_NO_AUTO_DELETED")] = True
        self.assertEqual(self.final(answers)[key(DELETION, "DATA_DELETION_NO_AUTO_DELETED")], "TRUE")

    def test_single_choice_and_value_validation(self):
        for extra in ({key(DELETION, "DATA_DELETION_YES"): True}, {key(COLLECTS): "false"},
                      {key(COLLECTS): 0}, {"invented|": True}, {key("PSL_ACM_SPECIFY"): "=HYPERLINK(x)"}):
            with self.subTest(extra=extra), self.assertRaises(DataSafetyValidationError):
                self.final({**no_data_answers(), **extra})

    def test_missing_type_usage_and_purpose_are_blocked(self):
        for remove in (key("PSL_DATA_TYPES_IDENTIFIERS", "PSL_DEVICE_ID"),
                       key("PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_COLLECTED"),
                       key("PSL_DATA_USAGE_RESPONSES:PSL_DEVICE_ID:DATA_USAGE_COLLECTION_PURPOSE", "PSL_ANALYTICS")):
            answers = data_answers(); del answers[remove]
            with self.subTest(remove=remove), self.assertRaises(DataSafetyValidationError): self.final(answers)

    def test_hidden_answers_are_removed_when_branches_change(self):
        answers = data_answers(shared=True); answers[key(COLLECTS)] = False
        rows = self.final(answers)
        self.assertEqual(rows[key("PSL_DATA_TYPES_IDENTIFIERS", "PSL_DEVICE_ID")], "")
        self.assertTrue(all(v == "" for k, v in rows.items() if k.startswith("PSL_DATA_USAGE_RESPONSES:")))
        self.assertEqual(rows[key("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT")], "")

    def test_external_account_conditional_questions(self):
        answers = no_data_answers(); answers[key(OUTSIDE)] = True
        with self.assertRaises(DataSafetyValidationError): self.final(answers)
        answers[key("PSL_OUTSIDE_APP_ACCOUNT_TYPES", "PSL_OUTSIDE_APP_ACCOUNT_TYPE_OTHER")] = True
        with self.assertRaises(DataSafetyValidationError): self.final(answers)
        answers[key("PSL_OUTSIDE_APP_ACCOUNT_TYPE_SPECIFY")] = "Existing membership"
        self.final(answers)

    def test_console_template_comparison_ignores_answers_not_fields(self):
        output = io.StringIO(); rows = json.loads(json.dumps(Exporter._get_template()))
        rows[1][2] = "TRUE"; csv.writer(output).writerows(rows)
        self.final(no_data_answers(), template_csv=output.getvalue())
        for mutation in ("missing", "extra", "requirement", "duplicate", "header"):
            changed = json.loads(json.dumps(rows))
            if mutation == "missing": changed.pop()
            if mutation == "extra": changed.append(["NEW_FIELD", "", "", "REQUIRED", "new"])
            if mutation == "requirement": changed[1][3] = "OPTIONAL"
            if mutation == "duplicate": changed.append(changed[1])
            if mutation == "header": changed[0][0] = "changed"
            output = io.StringIO(); csv.writer(output).writerows(changed)
            with self.subTest(mutation=mutation), self.assertRaises(DataSafetyValidationError):
                self.final(no_data_answers(), template_csv=output.getvalue())

    def test_bilingual_schema_has_same_fields(self):
        en = Exporter.review(data_answers(shared=True), lang="en")
        zh = Exporter.review(data_answers(shared=True), lang="zh")
        self.assertEqual([q["id"] for q in en["questions"]], [q["id"] for q in zh["questions"]])
        self.assertNotEqual(en["questions"][0]["label"], zh["questions"][0]["label"])

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
