from pathlib import Path
from unittest import TestCase


class BootstrapTests(TestCase):
    def test_extends_botasaurus_bootstrap_timeout(self):
        source = Path("botpass/bootstrap.py").read_text()
        self.assertIn('kwargs["timeout"] = 30', source)
        self.assertIn("from botasaurus.request import Request", source)
