"""HTTP regression tests: the browser routes must call the shared translator."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from web_app import Handler


class BrowserInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_reports_dictionary_loaded(self):
        with urlopen(self.base + "/api/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["status"], "ok")
        self.assertGreater(payload["dictionary_rows"], 5000)

    def test_lookup_api_finds_girl(self):
        with urlopen(self.base + "/api/lookup?word=girl&direction=english_to_izon", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["matches"])
        self.assertEqual(payload["matches"][0]["izon"], "ụ́")

    def test_json_translation_api_uses_sentence_engine(self):
        body = json.dumps({"source": "The girl eats yam.", "direction": "english_to_izon"}).encode("utf-8")
        request = Request(self.base + "/api/translate", data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["translation"], "Ụ́ bi burú ị́ị.")

    def test_browser_form_translates_complete_sentence(self):
        body = urlencode({"source": "The girl eats yam.", "direction": "english_to_izon"}).encode("utf-8")
        request = Request(self.base + "/translate", data=body,
                          headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with urlopen(request, timeout=5) as response:
            page = response.read().decode("utf-8")
        self.assertIn("Ụ́ bi burú ị́ị.", page)
        self.assertIn("The girl eats yam.", page)


if __name__ == "__main__":
    unittest.main()
