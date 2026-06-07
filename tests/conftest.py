import sys
import os
import tempfile
from pathlib import Path


os.environ.setdefault("SENTINELA_DB_PATH", str(Path(tempfile.gettempdir()) / "sentinela_test.db"))

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
