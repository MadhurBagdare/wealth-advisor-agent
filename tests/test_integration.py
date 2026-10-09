import json
import unittest
from pathlib import Path

from config import DATA_DIR
from agents import OrchestratorAgent


class TestFullPipeline(unittest.TestCase):

    def test_end_to_end_with_sample_data(self):
        import config
        config.HUMAN_IN_LOOP_ENABLED = False

        orchestrator = OrchestratorAgent()
        result = orchestrator.run({"file_path": str(DATA_DIR / "sample_client.json")})

        self.assertTrue(result.success)
        report = result.data["report"]

        self.assertEqual(report.client_id, "CLT-2847")
        self.assertEqual(report.client_name, "Rajesh Mehta")
        self.assertGreater(len(report.anomalies), 0)
        self.assertGreater(len(report.recommendations), 0)
        self.assertGreater(len(report.next_steps), 0)
        self.assertIn("real_estate", report.asset_allocation)
        self.assertTrue(report.requires_review)

        output_path = Path(result.data["output_path"])
        self.assertTrue(output_path.exists())

        saved = json.loads(output_path.read_text())
        self.assertEqual(saved["client_id"], "CLT-2847")
        self.assertIn("anomalies", saved)
        self.assertIn("recommendations", saved)
        self.assertIn("asset_allocation", saved)

        output_path.unlink()

    def test_pipeline_fails_on_missing_file(self):
        import config
        config.HUMAN_IN_LOOP_ENABLED = False

        orchestrator = OrchestratorAgent()
        result = orchestrator.run({"file_path": "/nonexistent/data.json"})

        self.assertFalse(result.success)
        self.assertIn("Data load failed", result.error)

    def test_pipeline_fails_on_missing_context(self):
        orchestrator = OrchestratorAgent()
        result = orchestrator.run({})

        self.assertFalse(result.success)

    def test_report_contains_goal_tracking(self):
        import config
        config.HUMAN_IN_LOOP_ENABLED = False

        orchestrator = OrchestratorAgent()
        result = orchestrator.run({"file_path": str(DATA_DIR / "sample_client.json")})

        report = result.data["report"]
        self.assertGreater(len(report.goal_tracking), 0)
        goal_names = [g["name"] for g in report.goal_tracking]
        self.assertIn("Retirement Corpus", goal_names)

        Path(result.data["output_path"]).unlink()

    def test_report_json_is_valid(self):
        import config
        config.HUMAN_IN_LOOP_ENABLED = False

        orchestrator = OrchestratorAgent()
        result = orchestrator.run({"file_path": str(DATA_DIR / "sample_client.json")})

        output_path = Path(result.data["output_path"])
        saved = json.loads(output_path.read_text())

        required_keys = [
            "client_id", "client_name", "summary", "risk_assessment",
            "anomalies", "recommendations", "goal_tracking",
            "asset_allocation", "next_steps", "generated_at",
        ]
        for key in required_keys:
            self.assertIn(key, saved, f"Missing key in report: {key}")

        output_path.unlink()


if __name__ == "__main__":
    unittest.main()
