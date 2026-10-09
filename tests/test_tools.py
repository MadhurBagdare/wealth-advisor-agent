import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import tempfile
import unittest
from tools import DataLoaderTool, CRMApiTool, MarketDataTool


class TestDataLoaderTool(unittest.TestCase):

    def test_load_valid_file(self):
        data = {
            "client_id": "T-1", "name": "Test", "age": 30,
            "risk_profile": "low", "investment_horizon": "5 years",
            "annual_income": 100000,
            "portfolio": {"total_value": 50000, "holdings": []},
            "transactions": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name

        result = DataLoaderTool().execute(file_path=path)
        self.assertTrue(result.success)
        self.assertEqual(result.data.client_id, "T-1")
        Path(path).unlink()

    def test_file_not_found(self):
        result = DataLoaderTool().execute(file_path="/nonexistent/file.json")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{broken json")
            path = f.name

        result = DataLoaderTool().execute(file_path=path)
        self.assertFalse(result.success)
        self.assertIn("Invalid JSON", result.error)
        Path(path).unlink()


class TestCRMApiTool(unittest.TestCase):

    def test_known_client(self):
        result = CRMApiTool().execute(client_id="CLT-2847")
        self.assertTrue(result.success)
        self.assertEqual(result.data.account_tier, "platinum")

    def test_unknown_client_gets_stub(self):
        result = CRMApiTool().execute(client_id="UNKNOWN-999")
        self.assertTrue(result.success)
        self.assertEqual(result.data.relationship_manager, "Unassigned")
        self.assertIn("missing_kyc_review", result.data.compliance_flags)


class TestMarketDataTool(unittest.TestCase):

    def test_benchmarks(self):
        result = MarketDataTool().execute(query_type="benchmarks")
        self.assertTrue(result.success)
        self.assertIn("NIFTY50", result.data)

    def test_sector_exposure(self):
        result = MarketDataTool().execute(query_type="sector_exposure", symbols=["HDFCBANK"])
        self.assertTrue(result.success)
        self.assertEqual(result.data["HDFCBANK"]["sector"], "Banking")

    def test_unknown_query_type(self):
        result = MarketDataTool().execute(query_type="invalid")
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
