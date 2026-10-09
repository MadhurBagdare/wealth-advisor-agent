from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    LARGE_TRANSACTION = "large_transaction"
    RAPID_TRADING = "rapid_trading"
    CONCENTRATION_RISK = "concentration_risk"
    RISKY_ASSET = "risky_asset"


@dataclass
class Holding:
    asset_class: str
    instrument: str
    value: float
    metadata: dict = field(default_factory=dict)


@dataclass
class Transaction:
    date: str
    type: str
    instrument: str
    amount: float
    description: str = ""


@dataclass
class Anomaly:
    type: AnomalyType
    severity: RiskLevel
    description: str
    details: dict = field(default_factory=dict)


@dataclass
class ClientProfile:
    client_id: str
    name: str
    age: int
    risk_profile: str
    investment_horizon: str
    annual_income: float
    holdings: list[Holding] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)
    portfolio_value: float = 0.0


@dataclass
class CRMData:
    client_id: str
    relationship_manager: str
    account_tier: str
    last_review_date: str
    notes: list[str] = field(default_factory=list)
    compliance_flags: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    anomalies: list[Anomaly] = field(default_factory=list)
    asset_allocation: dict = field(default_factory=dict)
    risk_score: float = 0.0
    concentration_risks: list[dict] = field(default_factory=list)
    goal_progress: list[dict] = field(default_factory=list)
    benchmark_comparison: dict = field(default_factory=dict)


@dataclass
class AdvisoryReport:
    client_id: str
    client_name: str
    summary: str
    risk_assessment: str
    anomalies: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    goal_tracking: list[dict] = field(default_factory=list)
    asset_allocation: dict = field(default_factory=dict)
    next_steps: list[str] = field(default_factory=list)
    generated_at: str = ""
    requires_review: bool = False
