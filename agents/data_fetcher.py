from .base import BaseAgent, AgentResult
from tools import DataLoaderTool, CRMApiTool, MarketDataTool
from memory import ShortTermMemory


class DataFetcherAgent(BaseAgent):
    """Retrieves and assembles all data needed for analysis.

    Coordinates three tools — file loader, CRM API, and market data —
    and stores the combined results in short-term memory.
    """

    def __init__(self, memory: ShortTermMemory):
        super().__init__("data_fetcher", memory)
        self._loader = DataLoaderTool()
        self._crm = CRMApiTool()
        self._market = MarketDataTool()

    def run(self, context: dict) -> AgentResult:
        file_path = context.get("file_path")
        if not file_path:
            return self._failure("No file_path provided in context")

        # Step 1 — load client financial data
        self.logger.info("Loading client data from %s", file_path)
        load_result = self._loader.execute(file_path=file_path)
        if not load_result.success:
            return self._failure(f"Data load failed: {load_result.error}")
        profile = load_result.data
        self.memory.set("client_profile", profile)

        # Step 2 — enrich with CRM data
        self.logger.info("Fetching CRM data for %s", profile.client_id)
        crm_result = self._crm.execute(client_id=profile.client_id)
        if crm_result.success:
            self.memory.set("crm_data", crm_result.data)
        else:
            self.logger.warning("CRM fetch failed, proceeding without it: %s", crm_result.error)
            self.memory.set("crm_data", None)

        # Step 3 — fetch market benchmarks
        self.logger.info("Fetching market benchmarks")
        bench_result = self._market.execute(query_type="benchmarks")
        if bench_result.success:
            self.memory.set("benchmarks", bench_result.data)

        # Step 4 — fetch sector exposure for equity holdings
        equity_symbols = [
            h.metadata.get("symbol")
            for h in profile.holdings
            if h.asset_class == "equity" and h.metadata.get("symbol")
        ]
        if equity_symbols:
            sector_result = self._market.execute(query_type="sector_exposure", symbols=equity_symbols)
            if sector_result.success:
                self.memory.set("sector_data", sector_result.data)

        self.logger.info("Data fetching complete for client %s", profile.name)
        return self._success(
            {"profile": profile, "crm": crm_result.data if crm_result.success else None},
            sources=["file", "crm", "market"],
        )
