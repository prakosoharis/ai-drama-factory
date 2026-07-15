import unittest
from pathlib import Path
from drama_factory.project import load_project
from drama_factory.validator import validate

ROOT = Path(__file__).parents[1]

class ReviewSelectionTest(unittest.TestCase):
    def test_existing_review_selection_fixture_is_valid(self):
        self.assertEqual([], validate(load_project(str(ROOT / "examples/v2.1-minimal-project"))))

    def test_missing_supersession_target_is_reported(self):
        index = load_project(str(ROOT / "examples/v2.1-minimal-project"))
        selection = next(iter(index.entities["selection"].values()))
        selection["supersedes_selection_id"] = "sel-shot-001-999"
        self.assertTrue(any(f.field == "supersedes_selection_id" for f in validate(index)))
