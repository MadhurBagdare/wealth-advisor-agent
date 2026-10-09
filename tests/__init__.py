import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.disable(logging.CRITICAL)
root = logging.getLogger()
root.handlers = []
root.addHandler(logging.NullHandler())
