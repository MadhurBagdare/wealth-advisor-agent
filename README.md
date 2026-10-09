# Wealth Advisor Assistant — Multi-Agent System

A lightweight multi-agent system that acts as a Wealth Advisor Assistant. It ingests client financial data, enriches it with CRM and market context, detects anomalies, and produces structured advisory reports.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                     │
│         (coordinates pipeline, manages flow)             │
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│   │  Data     │───▶│ Analyzer │───▶│ Advisor  │          │
│   │  Fetcher  │    │  Agent   │    │  Agent   │          │
│   └────┬─────┘    └──────────┘    └──────────┘          │
│        │                                                 │
│   ┌────▼─────────────────────────────┐                  │
│   │         Tool Layer               │                  │
│   │  ┌───────┐ ┌───────┐ ┌────────┐ │                  │
│   │  │Data   │ │CRM    │ │Market  │ │                  │
│   │  │Loader │ │API    │ │Data    │ │                  │
│   │  └───────┘ └───────┘ └────────┘ │                  │
│   └──────────────────────────────────┘                  │
│                                                         │
│   ┌──────────────────────────────────┐                  │
│   │        Memory Layer              │                  │
│   │  ┌────────────┐ ┌─────────────┐  │                  │
│   │  │ Short-Term │ │ Long-Term   │  │                  │
│   │  │ (session)  │ │ (persisted) │  │                  │
│   │  └────────────┘ └─────────────┘  │                  │
│   └──────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Agent Interactions and Flow

1. **Orchestrator Agent** kicks off the pipeline and coordinates execution order.
2. **Data Fetcher Agent** uses three tools (DataLoader, CRM API, MarketData) to gather all inputs and writes them to short-term memory.
3. **Analyzer Agent** reads the assembled data from memory, runs anomaly detection algorithms (z-score on transactions, risky-asset keyword matching, rapid-trading pattern detection, concentration risk analysis), and writes the `AnalysisResult` back to memory.
4. **Human-in-the-loop checkpoint** — if critical anomalies are found, the pipeline pauses and asks the operator to approve or halt.
5. **Advisor Agent** reads both the client profile and analysis from memory, synthesises an `AdvisoryReport` with recommendations and next steps.
6. The orchestrator persists the report to disk and stores a summary in long-term memory.

### Anomaly Detection

| Detector | Method | What it catches |
|---|---|---|
| Large transactions | Z-score (σ > 2.0) | Outlier amounts relative to the client's own transaction history |
| Risky assets | Keyword matching | Crypto, penny stocks, leveraged/speculative instruments |
| Rapid trading | Buy-sell gap analysis | Same instrument bought and sold within 30 days |
| Concentration risk | Asset-class weight | Any asset class exceeding 35% of total portfolio value |

## Key Decisions and Trade-offs

| Decision | Rationale |
|---|---|
| **Pure Python, no external dependencies** | The assignment values a runnable system with clear setup. Zero-dependency means `python3 main.py` just works — no pip install, no API keys, no Docker. |
| **Mock tools instead of real APIs** | Keeps the project self-contained while demonstrating the same tool abstraction that would wrap a live REST client. Swapping in a real CRM SDK means implementing `BaseTool.execute()` — no agent code changes. |
| **Short-term memory as OrderedDict with eviction** | Simple, fast, and sufficient for a sequential pipeline. If agents ran in parallel, this would need locking or an actor model — but for a linear flow it avoids unnecessary complexity. |
| **Long-term memory as a JSON file** | Good enough for a demo; in production this would be a database. The interface is identical, so migrating is a one-file change. |
| **Z-score for anomaly detection** | Statistically grounded, easy to explain to advisors, and doesn't require training data. The threshold is configurable in `config.py`. |
| **Human-in-the-loop at the analysis→advisory boundary** | This is the highest-leverage checkpoint: the system has found problems but hasn't yet committed to recommendations. An advisor can reject a false positive before it enters the report. |

## Assumptions

- Client data follows the schema in `data/sample_client.json`. The loader validates structure but doesn't enforce every field.
- All monetary values are in INR (₹).
- The CRM API is simulated with a static lookup — in production, this would be an HTTP client with retry logic.
- Market data is static mock data — a production system would integrate with a market data provider.
- The system processes one client at a time. Batch processing would require wrapping `main.py` in a loop or adding a queue.

## Project Structure

```
wealth-advisor-agent/
├── main.py              # Entry point
├── config.py            # Centralised configuration
├── agents/
│   ├── base.py          # Abstract base agent
│   ├── orchestrator.py  # Pipeline coordinator
│   ├── data_fetcher.py  # Data ingestion agent
│   ├── analyzer.py      # Analysis + anomaly detection
│   └── advisor.py       # Report generation
├── tools/
│   ├── base.py          # Tool interface (BaseTool)
│   ├── data_loader.py   # JSON file loader
│   ├── crm_api.py       # Mock CRM API client
│   └── market_data.py   # Mock market data provider
├── memory/
│   ├── short_term.py    # Session-scoped key-value store
│   └── long_term.py     # Persistent JSON-backed store
├── models/
│   └── schemas.py       # Dataclasses and enums
├── data/
│   └── sample_client.json
├── tests/
│   ├── test_analyzer.py # Anomaly detection + analysis tests
│   ├── test_tools.py    # Tool layer tests
│   └── test_memory.py   # Memory subsystem tests
├── pyproject.toml       # Project metadata
└── output/              # Generated reports land here
```

## Setup and Running

### Prerequisites

- Python 3.11 or higher

### Run

```bash
cd wealth-advisor-agent

# Default run with sample data (includes human-in-the-loop prompt)
python3 main.py

# Skip the human review checkpoint
python3 main.py --no-human-review

# Use a custom input file
python3 main.py --input path/to/client.json

# Verbose logging
python3 main.py --verbose --no-human-review
```

### Tests

```bash
python3 -m unittest discover tests -v
```

Runs 34 tests across unit tests (analyzer, tools, memory) and integration tests (full pipeline end-to-end).

### CI

GitHub Actions runs all tests on Python 3.11, 3.12, and 3.13 on every push and pull request. See `.github/workflows/ci.yml`.

### Sample Output

Running with the included sample data produces a report like:

```
============================================================
  ADVISORY REPORT SUMMARY
============================================================
  Client:     Rajesh Mehta (CLT-2847)
  Risk:       ELEVATED — Immediate advisor review recommended. Multiple high-severity anomalies detected.
  Anomalies:  5
  Saved to:   output/advisory_report_CLT-2847_20261009_114834.json

  Recommendations:
    1. Large transaction flagged: Unusually large withdrawal of
       ₹2,500,000 on 2026-09-03 (Savings Account). Verify source
       of funds and intent.
    2. Review exposure to Unknown Crypto Token — high-risk asset class
       not aligned with 'moderate' risk profile.
    3. Review exposure to Penny Stock XYZ — high-risk asset class
       not aligned with 'moderate' risk profile.
    4. Investigate rapid buy-sell pattern in HDFCBANK. Confirm this
       is intentional and not churning.
    5. Rebalance real_estate allocation (currently 48.1%) to below
       35% for better diversification.
    6. Goal 'Retirement Corpus' is at 37.0% — consider increasing
       SIP contributions.
    7. Client has expressed interest in ESG funds — present
       ESG-compliant alternatives during review.

  Next Steps:
    • URGENT: Escalate critical anomalies to compliance team within 24 hours.
    • Schedule portfolio review meeting with client.
    • Update CRM with latest review notes after advisory meeting.
```

The full JSON report is saved to `output/` with all anomaly details, asset allocation breakdowns, and goal tracking.
