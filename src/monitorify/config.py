import os
from pathlib import Path
from platformdirs import user_data_dir, user_runtime_dir

# Data directory for database storage
DATA_DIR = Path(user_data_dir("monitorify", appauthor=False))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Runtime directory for PID files
try:
    RUNTIME_DIR = Path(user_runtime_dir("monitorify", appauthor=False))
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    RUNTIME_DIR = DATA_DIR

# Database settings
DB_PATH = os.getenv("MONITORIFY_DB_PATH", str(DATA_DIR / "monitorify.db"))

# Daemon PID file path
DAEMON_PIDFILE = Path(os.getenv("MONITORIFY_PID_PATH", str(RUNTIME_DIR / "daemon.pid")))

# Collection settings (seconds)
DEFAULT_COLLECTION_INTERVAL = float(os.getenv("MONITORIFY_INTERVAL", "1.0"))

# Retention settings (default: 7 days in seconds)
RETENTION_SECONDS = float(os.getenv("MONITORIFY_RETENTION", str(7 * 24 * 3600)))
