import unittest
from pathlib import Path

from drama_factory.project import load_project
from drama_factory.validator import validate


class PathSafetyTest(unittest.TestCase):
    def test_manifest_rejects_absolute_project_path(self):
        root = Path(__file__).parents[1] / "examples/v2.1-minimal-project"
        index = load_project(str(root))
        index.manifest["paths"]["project"] = "/tmp/not-a-project"
        self.assertTrue(any(item.field == "paths.project" for item in validate(index)))
