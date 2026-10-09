from datetime import datetime

from .base import BaseAgent, AgentResult
from memory import ShortTermMemory
from models import (
    ClientProfile,
    CRMData,
    AnalysisResult,
    AdvisoryReport,
    RiskLevel,
)


class AdvisorAgent(BaseAgent):
    """Synthesises analysis results into a structured advisory report."""

    def __init__(self, memory: ShortTermMemory):
        super().__init__("advisor", memory)

    def run(self, context: dict) -> AgentResult:
        profile: ClientProfile | None = self.memory.get("client_profile")
        analysis: AnalysisResult | None = self.memory.get("analysis_result")

        if not profile or not analysis:
            return self._failure("Missing profile or analysis in memory")

        crm: CRMData | None = self.memory.get("crm_data")

        self.logger.info("Generating advisory report for %s", profile.name)

        report = AdvisoryReport(
            client_id=profile.client_id,
            client_name=profile.name,
            summary=self._build_summary(profile, analysis),
            risk_assessment=self._assess_risk(analysis),
            anomalies=[
                {
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "description": a.description,
                    "details": a.details,
                }
                for a in analysis.anomalies
            ],
            recommendations=self._generate_recommendations(profile, analysis, crm),
            goal_tracking=analysis.goal_progress,
            asset_allocation=analysis.asset_allocation,
            next_steps=self._suggest_next_steps(analysis, crm),
            generated_at=datetime.now().isoformat(),
            requires_review=any(a.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL) for a in analysis.anomalies),
        )

        self.memory.set("advisory_report", report)
        self.logger.info("Advisory report generated — requires review: %s", report.requires_review)
        return self._success(report)

    def _build_summary(self, profile: ClientProfile, analysis: AnalysisResult) -> str:
        critical = sum(1 for a in analysis.anomalies if a.severity == RiskLevel.CRITICAL)
        high = sum(1 for a in analysis.anomalies if a.severity == RiskLevel.HIGH)
        parts = [
            f"Portfolio review for {profile.name} (ID: {profile.client_id}).",
            f"Total portfolio value: ₹{profile.portfolio_value:,.0f}.",
            f"Risk score: {analysis.risk_score}/100.",
            f"Anomalies detected: {len(analysis.anomalies)} ({critical} critical, {high} high severity).",
        ]
        if analysis.concentration_risks:
            classes = ", ".join(r["asset_class"] for r in analysis.concentration_risks)
            parts.append(f"Concentration risk in: {classes}.")
        return " ".join(parts)

    def _assess_risk(self, analysis: AnalysisResult) -> str:
        score = analysis.risk_score
        if score >= 70:
            return "ELEVATED — Immediate advisor review recommended. Multiple high-severity anomalies detected."
        if score >= 40:
            return "MODERATE — Several anomalies warrant attention. Schedule review within the week."
        return "LOW — Portfolio within normal parameters. Routine review sufficient."

    def _generate_recommendations(
        self,
        profile: ClientProfile,
        analysis: AnalysisResult,
        crm: CRMData | None,
    ) -> list[str]:
        recs = []

        for anomaly in analysis.anomalies:
            if anomaly.type.value == "risky_asset":
                recs.append(
                    f"Review exposure to {anomaly.details.get('transaction', {}).get('instrument', 'unknown asset')} "
                    f"— high-risk asset class not aligned with '{profile.risk_profile}' risk profile."
                )
            elif anomaly.type.value == "rapid_trading":
                inst = anomaly.details.get("instrument", "unknown")
                recs.append(f"Investigate rapid buy-sell pattern in {inst}. Confirm this is intentional and not churning.")
            elif anomaly.type.value == "large_transaction":
                recs.append(
                    f"Large transaction flagged: {anomaly.description}. Verify source of funds and intent."
                )

        if analysis.concentration_risks:
            for cr in analysis.concentration_risks:
                recs.append(
                    f"Rebalance {cr['asset_class']} allocation (currently {cr['weight']:.1%}) "
                    f"to below {35}% for better diversification."
                )

        # Goal-based recommendations
        for goal in analysis.goal_progress:
            if goal["progress_pct"] < 50 and goal["deadline"] != "N/A":
                recs.append(f"Goal '{goal['name']}' is at {goal['progress_pct']}% — consider increasing SIP contributions.")

        if crm and crm.notes:
            for note in crm.notes:
                if "esg" in note.lower():
                    recs.append("Client has expressed interest in ESG funds — present ESG-compliant alternatives during review.")
                    break

        return recs

    def _suggest_next_steps(self, analysis: AnalysisResult, crm: CRMData | None) -> list[str]:
        steps = []
        if any(a.severity == RiskLevel.CRITICAL for a in analysis.anomalies):
            steps.append("URGENT: Escalate critical anomalies to compliance team within 24 hours.")
        steps.append("Schedule portfolio review meeting with client.")
        if crm and crm.compliance_flags:
            steps.append(f"Address compliance flags: {', '.join(crm.compliance_flags)}.")
        steps.append("Update CRM with latest review notes after advisory meeting.")
        return steps
