import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from memory import ShortTermMemory
from models import ClientProfile, Holding, Transaction, AnomalyType, RiskLevel
from agents.analyzer import AnalyzerAgent


def _make_profile(
    holdings=None,
    transactions=None,
    portfolio_value=1000000,
    annual_income=500000,
    risk_profile="moderate",
):
    return ClientProfile(
        client_id="TEST-001",
        name="Test Client",
        age=40,
        risk_profile=risk_profile,
        investment_horizon="10 years",
        annual_income=annual_income,
        holdings=holdings or [],
        transactions=transactions or [],
        goals=[],
        portfolio_value=portfolio_value,
    )


class TestAnalyzerAgent(unittest.TestCase):

    def _run_analyzer(self, profile):
        mem = ShortTermMemory()
        mem.set("client_profile", profile)
        agent = AnalyzerAgent(mem)
        return agent.run({})

    def test_happy_path_no_anomalies(self):
        profile = _make_profile(
            holdings=[
                Holding("equity", "Stock A", 300000),
                Holding("fixed_deposit", "FD", 300000),
                Holding("gold", "Gold ETF", 200000),
                Holding("mutual_fund", "MF", 200000),
            ],
            transactions=[
                Transaction("2026-01-01", "buy", "Stock A", 50000),
                Transaction("2026-02-01", "buy", "Stock A", 55000),
                Transaction("2026-03-01", "buy", "Stock A", 48000),
            ],
        )
        result = self._run_analyzer(profile)
        self.assertTrue(result.success)
        self.assertEqual(len(result.data.anomalies), 0)

    def test_large_transaction_detected(self):
        transactions = [
            Transaction("2026-01-01", "buy", "A", 10000),
            Transaction("2026-01-05", "buy", "B", 12000),
            Transaction("2026-01-10", "buy", "C", 11000),
            Transaction("2026-01-12", "buy", "E", 10500),
            Transaction("2026-01-14", "buy", "F", 11500),
            Transaction("2026-01-15", "buy", "D", 2000000),
        ]
        result = self._run_analyzer(_make_profile(transactions=transactions))
        large = [a for a in result.data.anomalies if a.type == AnomalyType.LARGE_TRANSACTION]
        self.assertGreater(len(large), 0)

    def test_risky_asset_crypto(self):
        transactions = [Transaction("2026-01-01", "buy", "Bitcoin Crypto Fund", 200000)]
        result = self._run_analyzer(_make_profile(transactions=transactions))
        risky = [a for a in result.data.anomalies if a.type == AnomalyType.RISKY_ASSET]
        self.assertEqual(len(risky), 1)

    def test_risky_asset_penny_stock(self):
        transactions = [Transaction("2026-01-01", "buy", "Penny Stock XYZ", 50000)]
        result = self._run_analyzer(_make_profile(transactions=transactions))
        risky = [a for a in result.data.anomalies if a.type == AnomalyType.RISKY_ASSET]
        self.assertEqual(len(risky), 1)

    def test_rapid_trading_detected(self):
        transactions = [
            Transaction("2026-01-01", "buy", "INFY", 100000),
            Transaction("2026-01-10", "sell", "INFY", 105000),
        ]
        result = self._run_analyzer(_make_profile(transactions=transactions))
        rapid = [a for a in result.data.anomalies if a.type == AnomalyType.RAPID_TRADING]
        self.assertEqual(len(rapid), 1)

    def test_no_rapid_trading_if_long_gap(self):
        transactions = [
            Transaction("2026-01-01", "buy", "INFY", 100000),
            Transaction("2026-06-01", "sell", "INFY", 105000),
        ]
        result = self._run_analyzer(_make_profile(transactions=transactions))
        rapid = [a for a in result.data.anomalies if a.type == AnomalyType.RAPID_TRADING]
        self.assertEqual(len(rapid), 0)

    def test_concentration_risk_by_asset_class(self):
        holdings = [
            Holding("equity", "Stock A", 200000),
            Holding("equity", "Stock B", 200000),
            Holding("fixed_deposit", "FD", 100000),
        ]
        # equity = 400k / 500k = 80%
        result = self._run_analyzer(_make_profile(holdings=holdings, portfolio_value=500000))
        conc = [a for a in result.data.anomalies if a.type == AnomalyType.CONCENTRATION_RISK]
        self.assertEqual(len(conc), 1)
        self.assertIn("equity", conc[0].description)

    def test_empty_transactions(self):
        result = self._run_analyzer(_make_profile(transactions=[]))
        self.assertTrue(result.success)
        self.assertEqual(len(result.data.anomalies), 0)

    def test_empty_holdings(self):
        result = self._run_analyzer(_make_profile(holdings=[], portfolio_value=0))
        self.assertTrue(result.success)
        self.assertEqual(result.data.asset_allocation, {})

    def test_missing_profile_fails(self):
        mem = ShortTermMemory()
        agent = AnalyzerAgent(mem)
        result = agent.run({})
        self.assertFalse(result.success)

    def test_risk_score_increases_with_severity(self):
        low_risk_txns = [
            Transaction("2026-01-01", "buy", "Stock A", 10000),
            Transaction("2026-01-05", "buy", "Stock B", 12000),
            Transaction("2026-01-10", "buy", "Stock C", 11000),
        ]
        high_risk_txns = low_risk_txns + [
            Transaction("2026-01-15", "buy", "Crypto Token", 900000, "speculative crypto"),
            Transaction("2026-01-20", "buy", "Penny Stock", 800000),
        ]
        low_result = self._run_analyzer(_make_profile(transactions=low_risk_txns))
        high_result = self._run_analyzer(_make_profile(transactions=high_risk_txns, annual_income=100000))
        self.assertGreater(high_result.data.risk_score, low_result.data.risk_score)

    def test_asset_allocation_sums_to_one(self):
        holdings = [
            Holding("equity", "A", 300000),
            Holding("fixed_deposit", "B", 500000),
            Holding("gold", "C", 200000),
        ]
        result = self._run_analyzer(_make_profile(holdings=holdings))
        total = sum(result.data.asset_allocation.values())
        self.assertAlmostEqual(total, 1.0, places=2)


class TestAnalyzerBenchmarks(unittest.TestCase):

    def test_benchmark_comparison_populated(self):
        mem = ShortTermMemory()
        profile = _make_profile(
            holdings=[Holding("equity", "A", 500000, {"symbol": "INFY"}),
                      Holding("fixed_deposit", "FD", 500000)],
        )
        mem.set("client_profile", profile)
        mem.set("benchmarks", {"NIFTY50": {"1y_return": 14.2}})
        mem.set("sector_data", {"INFY": {"sector": "IT", "beta": 0.78}})

        agent = AnalyzerAgent(mem)
        result = agent.run({})
        self.assertIn("nifty50_1y_return", result.data.benchmark_comparison)
        self.assertIn("portfolio_weighted_beta", result.data.benchmark_comparison)

    def test_no_benchmarks_returns_empty(self):
        mem = ShortTermMemory()
        mem.set("client_profile", _make_profile())
        agent = AnalyzerAgent(mem)
        result = agent.run({})
        self.assertEqual(result.data.benchmark_comparison, {})


if __name__ == "__main__":
    unittest.main()
