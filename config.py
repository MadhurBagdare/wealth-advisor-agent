import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
MEMORY_DIR = BASE_DIR / "memory" / "store"

OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

CRM_API_BASE_URL = os.getenv("CRM_API_URL", "http://mock-crm.local/api/v1")
CRM_API_TIMEOUT = int(os.getenv("CRM_API_TIMEOUT", "5"))

ANOMALY_Z_SCORE_THRESHOLD = 2.0
CONCENTRATION_RISK_THRESHOLD = 0.35
LARGE_TRANSACTION_MULTIPLIER = 3.0

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s"

HUMAN_IN_LOOP_ENABLED = os.getenv("HUMAN_IN_LOOP", "true").lower() == "true"
