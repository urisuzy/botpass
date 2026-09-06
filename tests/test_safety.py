from unittest import TestCase
from unittest.mock import patch

from botpass.safety import validate_url


class UrlValidationTests(TestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            validate_url("file:///etc/passwd")

    @patch(
        "botpass.safety.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("127.0.0.1", 0))],
    )
    def test_rejects_resolved_loopback_address(self, _resolve):
        with self.assertRaises(ValueError):
            validate_url("https://example.test/feed.xml")
