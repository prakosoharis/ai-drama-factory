import json
import tempfile
import unittest
from pathlib import Path

from drama_factory.bootstrap import create_project
from drama_factory.project import load_project
from drama_factory.validator import validate


class BootstrapTest(unittest.TestCase):
    def test_create_is_safe_and_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "pilot"
            created = create_project(str(target), "demo-drama", "Demo Drama", "test")
            self.assertTrue((target / "drama-factory.project.json").exists())
            self.assertEqual([], validate(load_project(str(target))))
            self.assertFalse(any("project-film" in path.read_text() for path in created if path.suffix in (".md", ".json")))
            with self.assertRaises(Exception):
                create_project(str(target), "demo-drama", "Demo Drama", "test")

    def test_empty_directory_requires_force_and_json_output_data_is_relative(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "empty"; target.mkdir()
            with self.assertRaises(Exception): create_project(str(target), "demo-drama", "Demo Drama", "test")
            create_project(str(target), "demo-drama", "Demo Drama", "test", force_empty=True)
            manifest = json.loads((target / "drama-factory.project.json").read_text())
            self.assertFalse(any(str(value).startswith("/") for value in manifest["paths"].values()))
