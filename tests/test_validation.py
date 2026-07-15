import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from drama_factory.project import load_project
from drama_factory.validator import validate

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples" / "v2.1-minimal-project"


class ValidationTest(unittest.TestCase):
    def copied_project(self):
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "project"
        shutil.copytree(EXAMPLE, target)
        return temp, target

    def findings(self, project, level="structure"):
        return validate(load_project(str(project)), level)

    def test_valid_neutral_sample_history(self):
        temp, project = self.copied_project()
        self.addCleanup(temp.cleanup)
        self.assertEqual([], self.findings(project))

    def test_duplicate_candidate_id(self):
        temp, project = self.copied_project(); self.addCleanup(temp.cleanup)
        source = project / "project/shots/shot-001/candidates/cand-shot-001-001/candidate.json"
        duplicate = project / "project/shots/shot-001/candidates/cand-shot-001-002/duplicate.json"
        duplicate.write_text(source.read_text())
        self.assertTrue(self.findings(project))

    def test_duplicate_candidate_version(self):
        temp, project = self.copied_project(); self.addCleanup(temp.cleanup)
        candidate = project / "project/shots/shot-001/candidates/cand-shot-001-002/candidate.json"
        data = json.loads(candidate.read_text()); data["version"] = 1; candidate.write_text(json.dumps(data))
        self.assertTrue(any(item.field == "version" for item in self.findings(project)))

    def test_rejected_candidate_selected_and_missing_cut_reference(self):
        temp, project = self.copied_project(); self.addCleanup(temp.cleanup)
        selection = project / "project/shots/shot-001/selections/sel-shot-001-001.json"
        data = json.loads(selection.read_text()); data["candidate_id"] = "cand-shot-001-001"; selection.write_text(json.dumps(data))
        cut = project / "project/cuts/rough-cut/cut-rough-002.json"
        data = json.loads(cut.read_text()); data["timeline"][0]["candidate_id"] = "cand-shot-001-999"; cut.write_text(json.dumps(data))
        fields = {item.field for item in self.findings(project)}
        self.assertIn("candidate_id", fields); self.assertIn("timeline.candidate_id", fields)

    def test_path_traversal_invalid_timestamp_and_unsupported_version(self):
        temp, project = self.copied_project(); self.addCleanup(temp.cleanup)
        candidate = project / "project/shots/shot-001/candidates/cand-shot-001-002/candidate.json"
        data = json.loads(candidate.read_text()); data["video_path"] = "../secret"; data["created_at"] = "2026-07-15T18:30:00"; data["schema_version"] = "9.9"; candidate.write_text(json.dumps(data))
        fields = {item.field for item in self.findings(project)}
        self.assertTrue({"video_path", "created_at", "schema_version"}.issubset(fields))

    def test_checksum_mismatch_and_failed_job(self):
        temp, project = self.copied_project(); self.addCleanup(temp.cleanup)
        media = project / "project/shots/shot-001/candidates/cand-shot-001-002/video.placeholder"
        media.write_text("tiny fixture")
        candidate = media.with_name("candidate.json")
        data = json.loads(candidate.read_text()); data["checksum"] = "0" * 64; candidate.write_text(json.dumps(data))
        job = project / "project/shots/shot-001/jobs/job-shot-001-002.json"
        job_data = json.loads(job.read_text()); job_data["status"] = "FAILED"; job.write_text(json.dumps(job_data))
        findings = self.findings(project, "files")
        self.assertTrue(any(item.field == "checksum" for item in findings))
        self.assertTrue(any(item.field == "render_job_id" for item in findings))
