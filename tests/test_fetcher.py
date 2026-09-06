from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

from botpass.fetcher import FetchSettings, Fetcher


class FetcherTests(TestCase):
    def test_botasaurus_request_disables_json_output_for_raw_bytes(self):
        source = Path("botpass/fetcher.py").read_text()
        self.assertIn("@request(max_retry=3, output=None)", source)

    @patch(
        "botpass.fetcher.validate_url",
        side_effect=["https://public.test/a", ValueError("destination address is not public")],
    )
    def test_rejects_unsafe_redirect(self, _validate):
        fetcher = Fetcher(FetchSettings(), store=None, request_factory=lambda: None)
        with self.assertRaises(ValueError):
            fetcher.follow_redirects(
                "https://public.test/a",
                lambda _: (302, {"location": "http://127.0.0.1/"}, b""),
            )
