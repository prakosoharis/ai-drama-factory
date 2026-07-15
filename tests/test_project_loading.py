import unittest
from pathlib import Path

from drama_factory.project import discover_project, load_project


class ProjectLoadingTest(unittest.TestCase):
    def test_discovers_parent_manifest_and_indexes_entities(self):
        root = Path(__file__).parents[1] / "examples/v2.1-minimal-project"
        manifest = discover_project(str(root / "project/shots"))
        index = load_project(str(manifest))
        self.assertEqual("demo-drama", index.manifest["project_id"])
        self.assertEqual(2, index.count("candidate"))
