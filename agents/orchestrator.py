import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .base import BaseAgent, AgentResult
from .data_fetcher import DataFetcherAgent
from .analyzer import AnalyzerAgent
from .advisor import AdvisorAgent
from memory import ShortTermMemory, LongTermMemory
from models import AdvisoryReport, RiskLevel
import config as cfg
from config import OUTPUT_DIR


class OrchestratorAgent(BaseAgent):
    """Central coordinator that manages the full advisory pipeline.

    Execution flow:
        1. DataFetcherAgent  — ingest client data + CRM + market context
        2. AnalyzerAgent     — run anomaly detection and portfolio analysis
        3. (checkpoint)      — human-in-the-loop review if critical anomalies found
        4. AdvisorAgent      — generate the final advisory report
        5. persist           — save report + store long-term memory
    """

    def __init__(self):
        stm = ShortTermMemory()
        super().__init__("orchestrator", stm)
        self.long_term_memory = LongTermMemory()

        self._agents = {
            "data_fetcher": DataFetcherAgent(stm),
            "analyzer": AnalyzerAgent(stm),
            "advisor": AdvisorAgent(stm),
        }

    def run(self, context: dict) -> AgentResult:
        self.logger.info("=== Orchestrator starting pipeline ===")
        pipeline = [
            ("data_fetcher", "Ingesting client data and fetching external context"),
            ("analyzer", "Running financial analysis and anomaly detection"),
        ]

        for agent_name, description in pipeline:
            self.logger.info(">> Stage: %s — %s", agent_name, description)
            result = self._agents[agent_name].run(context)
            if not result.success:
                self.logger.error("Pipeline aborted at %s: %s", agent_name, result.error)
                return self._failure(f"Pipeline failed at {agent_name}: {result.error}")

        # Human-in-the-loop checkpoint
        if cfg.HUMAN_IN_LOOP_ENABLED:
            proceed = self._human_checkpoint()
            if not proceed:
                self.logger.info("Pipeline halted by human reviewer")
                return self._success({"status": "halted_by_reviewer"})

        # Final stage — advisory report
        self.logger.info(">> Stage: advisor — Generating advisory report")
        advisor_result = self._agents["advisor"].run(context)
        if not advisor_result.success:
            return self._failure(f"Advisory generation failed: {advisor_result.error}")

        report: AdvisoryReport = advisor_result.data
        output_path = self._save_report(report)
        self._store_long_term_summary(report)

        self.logger.info("=== Pipeline complete — report saved to %s ===", output_path)
        return self._success({"report": report, "output_path": str(output_path)})

    def _human_checkpoint(self) -> bool:
        analysis = self.memory.get("analysis_result")
        if analysis is None:
            return True

        critical = [a for a in analysis.anomalies if a.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        if not critical:
            self.logger.info("No critical anomalies — skipping human checkpoint")
            return True

        print("\n" + "=" * 60)
        print("  HUMAN-IN-THE-LOOP CHECKPOINT")
        print("=" * 60)
        print(f"  {len(critical)} high/critical anomalies detected:\n")
        for i, anomaly in enumerate(critical, 1):
            print(f"  [{anomaly.severity.value.upper()}] {i}. {anomaly.description}")
        print()

        while True:
            response = input("  Proceed with generating the advisory report? (yes/no): ").strip().lower()
            if response in ("yes", "y"):
                self.logger.info("Human reviewer approved continuation")
                return True
            if response in ("no", "n"):
                self.logger.info("Human reviewer rejected continuation")
                return False
            print("  Please enter 'yes' or 'no'.")

    def _save_report(self, report: AdvisoryReport) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"advisory_report_{report.client_id}_{timestamp}.json"
        path = OUTPUT_DIR / filename

        data = asdict(report)
        path.write_text(json.dumps(data, indent=2, default=str))
        self.logger.info("Report saved: %s", path)
        return path

    def _store_long_term_summary(self, report: AdvisoryReport) -> None:
        summary = {
            "client_id": report.client_id,
            "client_name": report.client_name,
            "risk_assessment": report.risk_assessment,
            "anomaly_count": len(report.anomalies),
            "recommendation_count": len(report.recommendations),
            "requires_review": report.requires_review,
            "generated_at": report.generated_at,
        }
        self.long_term_memory.store(
            category="advisory_report",
            content=summary,
            tags=[report.client_id, "report"],
        )
