import time
import signal
import sys
from monitorify.collector import Manager
from monitorify.storage import Database
from monitorify import config


def main():
    print("Starting Monitorify background metrics collector daemon...")
    db = Database(config.DB_PATH)
    manager = Manager(db=db, interval=config.DEFAULT_COLLECTION_INTERVAL)

    def signal_handler(sig, frame):
        print("\nStopping Monitorify daemon...")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    manager.start()
    print(
        f"Metrics collector running (Interval: {config.DEFAULT_COLLECTION_INTERVAL}s, DB: {config.DB_PATH}). Press Ctrl+C to stop."
    )

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
