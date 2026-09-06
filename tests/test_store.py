from time import time
from unittest import TestCase

from botpass.store import live_cookies


class StoreTests(TestCase):
    def test_expired_cookie_is_not_returned(self):
        cookies = live_cookies([
            {"name": "expired", "value": "x", "expires": time() - 1},
            {"name": "session", "value": "y"},
        ])
        self.assertEqual(cookies, [{"name": "session", "value": "y"}])
