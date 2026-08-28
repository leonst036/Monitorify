import time
import signal
import sys
from monitorify.collector import Manager
from monitorify.storage import Database
from monitorify import config
from monitorify.config.configManager import configManager


def get_collection_interval() -> float:
    try:
        cfg = configManager(str(config.CONFIG_PATH))
        for key in ("update_interval", "collection_interval", "interval"):
            val = cfg.get(key)
            if val is not None:
                return float(val)
    except Exception:
        pass
    return config.DEFAULT_COLLECTION_INTERVAL


def main():
    print("Starting Monitorify background metrics collector daemon...")
    db = Database(config.DB_PATH)
    interval = get_collection_interval()
    manager = Manager(db=db, interval=get_collection_interval)

    def signal_handler(sig, frame):
        print("\nStopping Monitorify daemon...")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    manager.start()
    print(
        f"Metrics collector running (Interval: {interval}s, DB: {config.DB_PATH}). Press Ctrl+C to stop."
    )

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
