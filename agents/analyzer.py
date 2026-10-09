import statistics
from collections import Counter
from datetime import datetime

from .base import BaseAgent, AgentResult
from memory import ShortTermMemory
from models import (
    Anomaly,
    AnomalyType,
    RiskLevel,
    AnalysisResult,
    ClientProfile,
)
from config import (
    ANOMALY_Z_SCORE_THRESHOLD,
    CONCENTRATION_RISK_THRESHOLD,
    LARGE_TRANSACTION_MULTIPLIER,
)

RISKY_KEYWORDS = {"crypto", "penny", "speculative", "leveraged", "futures", "options"}


class AnalyzerAgent(BaseAgent):
    """Performs financial analysis and anomaly detection on client data."""

    def __init__(self, memory: ShortTermMemory):
        super().__init__("analyzer", memory)

    def run(self, context: dict) -> AgentResult:
        profile: ClientProfile | None = self.memory.get("client_profile")
        if profile is None:
            return self._failure("No client profile in memory — was DataFetcherAgent run?")

        self.logger.info("Starting analysis for %s", profile.name)

        anomalies: list[Anomaly] = []
        anomalies.extend(self._detect_large_transactions(profile))
        anomalies.extend(self._detect_risky_assets(profile))
        anomalies.extend(self._detect_rapid_trading(profile))
        anomalies.extend(self._detect_concentration_risk(profile))

        allocation = self._compute_allocation(profile)
        goal_progress = self._assess_goals(profile)
        risk_score = self._compute_risk_score(profile, anomalies)

        concentration_risks = [
            {"asset_class": cls, "weight": round(weight, 4)}
            for cls, weight in allocation.items()
            if weight > CONCENTRATION_RISK_THRESHOLD
        ]

        result = AnalysisResult(
            anomalies=anomalies,
            asset_allocation=allocation,
            risk_score=risk_score,
            concentration_risks=concentration_risks,
            goal_progress=goal_progress,
        )
        self.memory.set("analysis_result", result)

        self.logger.info(
            "Analysis complete — %d anomalies found, risk score: %.1f",
            len(anomalies),
            risk_score,
        )
        return self._success(result, anomaly_count=len(anomalies))

    # ------ anomaly detectors ------

    def _detect_large_transactions(self, profile: ClientProfile) -> list[Anomaly]:
        amounts = [t.amount for t in profile.transactions]
        if len(amounts) < 3:
            return []

        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        threshold = mean + ANOMALY_Z_SCORE_THRESHOLD * stdev if stdev else mean * LARGE_TRANSACTION_MULTIPLIER

        anomalies = []
        for txn in profile.transactions:
            if txn.amount > threshold:
                z = (txn.amount - mean) / stdev if stdev else 0
                anomalies.append(Anomaly(
                    type=AnomalyType.LARGE_TRANSACTION,
                    severity=RiskLevel.HIGH if z > 3 else RiskLevel.MODERATE,
                    description=f"Unusually large {txn.type} of ₹{txn.amount:,.0f} on {txn.date} ({txn.instrument})",
                    details={"z_score": round(z, 2), "transaction": txn.__dict__},
                ))
        return anomalies

    def _detect_risky_assets(self, profile: ClientProfile) -> list[Anomaly]:
        anomalies = []
        for txn in profile.transactions:
            combined = f"{txn.instrument} {txn.description}".lower()
            if any(kw in combined for kw in RISKY_KEYWORDS):
                severity = RiskLevel.CRITICAL if txn.amount > profile.annual_income * 0.2 else RiskLevel.HIGH
                anomalies.append(Anomaly(
                    type=AnomalyType.RISKY_ASSET,
                    severity=severity,
                    description=f"Transaction in potentially risky asset: {txn.instrument} (₹{txn.amount:,.0f})",
                    details={"transaction": txn.__dict__},
                ))
        return anomalies

    def _detect_rapid_trading(self, profile: ClientProfile) -> list[Anomaly]:
        instrument_actions: dict[str, list] = {}
        for txn in profile.transactions:
            instrument_actions.setdefault(txn.instrument, []).append(txn)

        anomalies = []
        for instrument, txns in instrument_actions.items():
            types = [t.type for t in txns]
            if "buy" in types and "sell" in types:
                dates = sorted(datetime.fromisoformat(t.date) for t in txns)
                span_days = (dates[-1] - dates[0]).days
                if span_days <= 30:
                    anomalies.append(Anomaly(
                        type=AnomalyType.RAPID_TRADING,
                        severity=RiskLevel.MODERATE,
                        description=f"Buy and sell of {instrument} within {span_days} days — possible churning",
                        details={"instrument": instrument, "span_days": span_days},
                    ))
        return anomalies

    def _detect_concentration_risk(self, profile: ClientProfile) -> list[Anomaly]:
        if not profile.holdings or profile.portfolio_value <= 0:
            return []

        anomalies = []
        for h in profile.holdings:
            weight = h.value / profile.portfolio_value
            if weight > CONCENTRATION_RISK_THRESHOLD:
                anomalies.append(Anomaly(
                    type=AnomalyType.CONCENTRATION_RISK,
                    severity=RiskLevel.HIGH,
                    description=f"{h.instrument} represents {weight:.1%} of portfolio — exceeds {CONCENTRATION_RISK_THRESHOLD:.0%} threshold",
                    details={"instrument": h.instrument, "weight": round(weight, 4)},
                ))
        return anomalies

    # ------ portfolio metrics ------

    def _compute_allocation(self, profile: ClientProfile) -> dict[str, float]:
        totals: dict[str, float] = {}
        for h in profile.holdings:
            totals[h.asset_class] = totals.get(h.asset_class, 0) + h.value
        total = sum(totals.values()) or 1
        return {cls: round(val / total, 4) for cls, val in sorted(totals.items())}

    def _assess_goals(self, profile: ClientProfile) -> list[dict]:
        progress = []
        for goal in profile.goals:
            target = goal["target"]
            pct = min(profile.portfolio_value / target, 1.0) if target else 0
            progress.append({
                "name": goal["name"],
                "target": target,
                "current_portfolio": profile.portfolio_value,
                "progress_pct": round(pct * 100, 1),
                "deadline": goal.get("deadline", "N/A"),
            })
        return progress

    def _compute_risk_score(self, profile: ClientProfile, anomalies: list[Anomaly]) -> float:
        severity_weights = {RiskLevel.LOW: 1, RiskLevel.MODERATE: 2, RiskLevel.HIGH: 4, RiskLevel.CRITICAL: 8}
        raw = sum(severity_weights.get(a.severity, 1) for a in anomalies)
        return min(round(raw / max(len(anomalies), 1) * 10 + len(anomalies) * 5, 1), 100)
