from .base import BaseTool, ToolResult

# Simulated market benchmark data.
_MOCK_BENCHMARKS = {
    "NIFTY50": {"1y_return": 14.2, "3y_cagr": 12.8, "pe_ratio": 22.5},
    "NIFTY_MIDCAP": {"1y_return": 18.6, "3y_cagr": 16.1, "pe_ratio": 28.3},
    "GOLD": {"1y_return": 8.5, "3y_cagr": 10.2},
    "FD_RATE": {"current": 7.1, "1y_ago": 6.5},
}

_MOCK_SECTOR_EXPOSURE = {
    "HDFCBANK": {"sector": "Banking", "beta": 0.95, "market_cap_cr": 1150000},
    "RELIANCE": {"sector": "Conglomerate", "beta": 1.10, "market_cap_cr": 1700000},
    "INFY": {"sector": "IT Services", "beta": 0.78, "market_cap_cr": 620000},
}


class MarketDataTool(BaseTool):
    """Provides market benchmarks and sector data for comparative analysis."""

    def __init__(self):
        super().__init__("market_data")

    def execute(self, *, query_type: str, symbols: list[str] | None = None) -> ToolResult:
        self.logger.info("Market data query: %s", query_type)

        if query_type == "benchmarks":
            return ToolResult(success=True, data=_MOCK_BENCHMARKS)

        if query_type == "sector_exposure":
            if not symbols:
                return ToolResult(success=False, error="symbols required for sector_exposure query")
            result = {s: _MOCK_SECTOR_EXPOSURE.get(s, {"sector": "Unknown", "beta": 1.0}) for s in symbols}
            return ToolResult(success=True, data=result)

        return ToolResult(success=False, error=f"Unknown query type: {query_type}")
