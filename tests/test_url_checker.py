import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyzer.url_checker import UrlChecker


class TestPrivacyUrlProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                status = 302 if self.path == "/redirect" else (200 if self.path == "/privacy" else 404)
                self.send_response(status)
                if status == 302:
                    self.send_header("Location", "/privacy")
                self.end_headers()

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_real_get_follows_redirect_and_accepts_success(self):
        result = UrlChecker.check_privacy_url(self.base_url + "/redirect")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["url"], self.base_url + "/privacy")

    def test_real_get_rejects_http_failure(self):
        result = UrlChecker.check_privacy_url(self.base_url + "/missing")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["status_code"], 404)


if __name__ == "__main__":
    unittest.main()
