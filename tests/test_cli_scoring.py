import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli
from analyzer.scoring import calculate_score_and_categories


class TestSharedScoring(unittest.TestCase):
    def test_deductions_status_and_floor(self):
        findings = [
            {"rule_id": "fatal", "status": "FAIL", "severity": "FATAL"},
            {"rule_id": "high", "status": "FAIL", "severity": "HIGH"},
            {"rule_id": "warning", "status": "WARN", "severity": "HIGH"},
            {"rule_id": "passed", "status": "PASS", "severity": "FATAL"},
        ]
        self.assertEqual(calculate_score_and_categories({"findings": findings})[:4], (55, 1, 1, 1))
        self.assertEqual(calculate_score_and_categories({"findings": findings * 10})[0], 15)
        self.assertEqual(calculate_score_and_categories({"findings": []})[:4], (100, 0, 0, 0))

    def test_cli_privacy_url_probe_changes_finding_and_score(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "app.apk"
            package.write_bytes(b"package")
            for valid, expected_score in ((True, 100), (False, 75)):
                with self.subTest(valid=valid), contextlib.ExitStack() as stack:
                    stack.enter_context(mock.patch.object(sys, "argv", ["cli.py", str(package), "--privacy-url", "https://example.test/privacy"]))
                    stack.enter_context(mock.patch.object(cli.FrameworkDetector, "detect", return_value={}))
                    stack.enter_context(mock.patch.object(cli.ManifestParser, "parse", return_value={"target_sdk": 36, "permissions": [], "services": []}))
                    stack.enter_context(mock.patch.object(cli.DexScanner, "scan", return_value=[]))
                    stack.enter_context(mock.patch.object(cli.ElfScanner, "scan", return_value={}))
                    probe = stack.enter_context(mock.patch.object(cli.UrlChecker, "check_privacy_url", return_value={"is_valid": valid, "status_code": 200 if valid else 404}))
                    output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    cli.main()
                    probe.assert_called_once_with("https://example.test/privacy")
                    self.assertIn(f"COMPLIANCE SCORE: {expected_score} / 100", output.getvalue())

    def test_cli_without_privacy_url_does_not_make_request(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            package = Path(directory) / "app.apk"
            package.write_bytes(b"package")
            stack.enter_context(mock.patch.object(sys, "argv", ["cli.py", str(package)]))
            stack.enter_context(mock.patch.object(cli.FrameworkDetector, "detect", return_value={}))
            stack.enter_context(mock.patch.object(cli.ManifestParser, "parse", return_value={"target_sdk": 36}))
            stack.enter_context(mock.patch.object(cli.DexScanner, "scan", return_value=[]))
            stack.enter_context(mock.patch.object(cli.ElfScanner, "scan", return_value={}))
            probe = stack.enter_context(mock.patch.object(cli.UrlChecker, "check_privacy_url"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            cli.main()
            probe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
