import json
from pathlib import Path

from .base import BaseTool, ToolResult
from models import ClientProfile, Holding, Transaction


class DataLoaderTool(BaseTool):
    """Loads and parses client financial data from JSON files."""

    def __init__(self):
        super().__init__("data_loader")

    def execute(self, *, file_path: str) -> ToolResult:
        if not self.validate_params(required=["file_path"], provided={"file_path": file_path}):
            return ToolResult(success=False, error="file_path is required")

        path = Path(file_path)
        if not path.exists():
            self.logger.error("File not found: %s", file_path)
            return ToolResult(success=False, error=f"File not found: {file_path}")

        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            self.logger.error("Invalid JSON in %s: %s", file_path, exc)
            return ToolResult(success=False, error=f"Invalid JSON: {exc}")

        try:
            profile = self._parse_profile(raw)
        except (KeyError, TypeError) as exc:
            self.logger.error("Schema mismatch: %s", exc)
            return ToolResult(success=False, error=f"Schema mismatch: {exc}")

        self.logger.info(
            "Loaded profile for %s — %d holdings, %d transactions",
            profile.name,
            len(profile.holdings),
            len(profile.transactions),
        )
        return ToolResult(success=True, data=profile)

    def _parse_profile(self, raw: dict) -> ClientProfile:
        holdings = [
            Holding(
                asset_class=h["asset_class"],
                instrument=h["instrument"],
                value=h["value"],
                metadata={k: v for k, v in h.items() if k not in ("asset_class", "instrument", "value")},
            )
            for h in raw.get("portfolio", {}).get("holdings", [])
        ]

        transactions = [
            Transaction(
                date=t["date"],
                type=t["type"],
                instrument=t["instrument"],
                amount=t["amount"],
                description=t.get("description", ""),
            )
            for t in raw.get("transactions", [])
        ]

        return ClientProfile(
            client_id=raw["client_id"],
            name=raw["name"],
            age=raw["age"],
            risk_profile=raw["risk_profile"],
            investment_horizon=raw["investment_horizon"],
            annual_income=raw["annual_income"],
            holdings=holdings,
            transactions=transactions,
            goals=raw.get("goals", []),
            portfolio_value=raw.get("portfolio", {}).get("total_value", 0),
        )
