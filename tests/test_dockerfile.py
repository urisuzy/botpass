from pathlib import Path
from unittest import TestCase


class DockerfileTests(TestCase):
    def test_warms_botasaurus_before_starting_api(self):
        self.assertIn("RUN until python -m botpass.bootstrap", Path("Dockerfile").read_text())
