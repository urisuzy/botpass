import os
from unittest import TestCase

from fastapi.testclient import TestClient

os.environ["FETCH_API_KEY"] = "secret"

from botpass.app import create_app  # noqa: E402


class ApiTests(TestCase):
    def test_fetch_returns_raw_body_and_content_type(self):
        app = create_app(
            fetch=lambda _: (200, {"content-type": "application/rss+xml"}, b"<rss/>")
        )
        response = TestClient(app).get(
            "/fetch",
            params={"url": "https://example.com/feed"},
            headers={"X-API-Key": "secret"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"<rss/>")
        self.assertEqual(response.headers["content-type"], "application/rss+xml")

    def test_fetch_rejects_missing_api_key(self):
        response = TestClient(create_app(fetch=lambda _: (200, {}, b""))).get(
            "/fetch", params={"url": "https://example.com/feed"}
        )
        self.assertEqual(response.status_code, 401)
