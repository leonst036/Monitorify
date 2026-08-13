import os

# Database settings
DB_PATH = os.getenv("MONITORIFY_DB_PATH", "monitorify.db")

# Collection settings
DEFAULT_COLLECTION_INTERVAL = float(os.getenv("MONITORIFY_INTERVAL", "1.0"))

# Retention settings (default: 7 days in seconds)
RETENTION_SECONDS = float(os.getenv("MONITORIFY_RETENTION", str(7 * 24 * 3600)))
