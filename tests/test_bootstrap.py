import json
import tempfile
import unittest
from pathlib import Path

from drama_factory.bootstrap import create_project
from drama_factory.project import load_project
from drama_factory.validator import validate
from drama_factory.rendering import create_plan, run_plan


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

    def test_candidate_immutability_failure_and_plan_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pilot"
            create_project(str(root), "demo-drama", "Demo Drama", "test")
            plan_one, plan_path = create_plan(str(root), "shot-001", "mock", "synthetic-video", 4, "1024x576", 24)
            _, candidate_one = run_plan(str(root), plan_one)
            artifact = root / "project/shots/shot-001/candidates" / candidate_one / "candidate.mock"
            checksum_before = __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
            contract = root / "project/shots/shot-001/shot-contract.json"
            original_plan = plan_path.read_bytes()
            contract.write_text(contract.read_text().replace("limited natural movement", "edited after planning"))
            self.assertEqual(original_plan, plan_path.read_bytes())
            plan_two, _ = create_plan(str(root), "shot-001", "mock", "synthetic-video", 4, "1024x576", 24)
            _, candidate_two = run_plan(str(root), plan_two)
            self.assertNotEqual(candidate_one, candidate_two)
            self.assertEqual(checksum_before, __import__("hashlib").sha256(artifact.read_bytes()).hexdigest())
            plan_three, _ = create_plan(str(root), "shot-001", "mock", "synthetic-video", 4, "1024x576", 24)
            with self.assertRaises(RuntimeError): run_plan(str(root), plan_three, "before-output")
            self.assertFalse((root / "project/shots/shot-001/candidates/cand-shot-001-003").exists())
