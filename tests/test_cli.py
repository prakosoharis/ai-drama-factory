import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from drama_factory.cli import main


class CliTest(unittest.TestCase):
    def test_inspect_validate_and_shot_show(self):
        root = Path(__file__).parents[1] / "examples/v2.1-minimal-project"
        for args in (("inspect",), ("validate",), ("shot", "show", "shot-011")):
            stream = io.StringIO()
            with redirect_stdout(stream):
                result = main([*args, "--project", str(root)])
            self.assertEqual(0, result, stream.getvalue())
