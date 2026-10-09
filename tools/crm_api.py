import random
from datetime import datetime, timedelta

from .base import BaseTool, ToolResult
from models import CRMData

# Simulated CRM database — in production this would call the actual CRM REST API.
_MOCK_CRM_STORE = {
    "CLT-2847": {
        "relationship_manager": "Priya Sharma",
        "account_tier": "platinum",
        "last_review_date": "2026-06-15",
        "notes": [
            "Client prefers conservative rebalancing approach",
            "Expressed interest in ESG funds during last review",
            "Daughter starting college in 2030 — education goal is priority",
        ],
        "compliance_flags": [],
    },
}


class CRMApiTool(BaseTool):
    """Simulates a CRM REST API for fetching client relationship data."""

    def __init__(self):
        super().__init__("crm_api")

    def execute(self, *, client_id: str) -> ToolResult:
        self.logger.info("Fetching CRM data for client %s", client_id)

        record = _MOCK_CRM_STORE.get(client_id)

        if record is None:
            # Simulate a plausible fallback for unknown clients
            self.logger.warning("Client %s not in CRM — generating stub", client_id)
            record = self._generate_stub(client_id)

        try:
            crm_data = CRMData(
                client_id=client_id,
                relationship_manager=record["relationship_manager"],
                account_tier=record["account_tier"],
                last_review_date=record["last_review_date"],
                notes=record.get("notes", []),
                compliance_flags=record.get("compliance_flags", []),
            )
        except KeyError as exc:
            self.logger.error("Malformed CRM record for %s: %s", client_id, exc)
            return ToolResult(success=False, error=f"CRM record malformed: {exc}")

        self.logger.info("CRM data retrieved — tier: %s, RM: %s", crm_data.account_tier, crm_data.relationship_manager)
        return ToolResult(success=True, data=crm_data)

    @staticmethod
    def _generate_stub(client_id: str) -> dict:
        return {
            "relationship_manager": "Unassigned",
            "account_tier": "standard",
            "last_review_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "notes": ["Auto-generated stub — no CRM record found"],
            "compliance_flags": ["missing_kyc_review"],
        }
