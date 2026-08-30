import sqlite3
import json
import os
from typing import List, Optional
from monitorify.collector.schema import MetricSnapshot
from monitorify import config

class Database:
    def __init__(self, path: str = config.DB_PATH):
        self.path = path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self):
        dir_name = os.path.dirname(self.path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                print(f"Error creating directory: {e}")

        # check_same_thread=False enables background worker threads to write safely
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                timestamp REAL PRIMARY KEY,
                cpu REAL,
                ram REAL,
                network_rx REAL,
                network_tx REAL,
                processes_count INTEGER,
                disk_io TEXT,
                disk_storage TEXT
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT DEFAULT 'root',
                password TEXT,
                key_filename TEXT
            )
            """
        )
        self._connection.commit()

        # Migrate existing table schema if columns are missing
        cursor = self._connection.cursor()
        cursor.execute("PRAGMA table_info(metrics)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "disk_io" not in columns:
            self._connection.execute("ALTER TABLE metrics ADD COLUMN disk_io TEXT")
        if "disk_storage" not in columns:
            self._connection.execute("ALTER TABLE metrics ADD COLUMN disk_storage TEXT")
        self._connection.commit()

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _ensure_connected(self):
        if self._connection is None:
            self.connect()

    def save(self, metric_snapshot: MetricSnapshot):
        self._ensure_connected()
        try:
            disk_io_json = json.dumps(metric_snapshot.disk_io) if metric_snapshot.disk_io is not None else None
            disk_storage_json = json.dumps(metric_snapshot.disk_storage) if metric_snapshot.disk_storage is not None else None

            self._connection.execute(
                """
                INSERT INTO metrics (timestamp, cpu, ram, network_rx, network_tx, processes_count, disk_io, disk_storage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metric_snapshot.timestamp,
                    metric_snapshot.cpu,
                    metric_snapshot.ram,
                    metric_snapshot.network[0],
                    metric_snapshot.network[1],
                    metric_snapshot.processes_count,
                    disk_io_json,
                    disk_storage_json,
                )
            )
            self._connection.commit()
        except Exception as e:
            print(f"Error saving metrics: {e}")

    def get_history(self, limit: int = 100, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[MetricSnapshot]:
        """Fetch historical metric snapshots."""
        self._ensure_connected()
        query = "SELECT timestamp, cpu, ram, network_rx, network_tx, processes_count, disk_io, disk_storage FROM metrics"
        params = []
        conditions = []

        if start_time is not None:
            conditions.append("timestamp >= ?")
            params.append(start_time)
        if end_time is not None:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            snapshots = []
            for row in reversed(rows):  # Return chronological order
                disk_io = json.loads(row["disk_io"]) if ("disk_io" in row.keys() and row["disk_io"]) else None
                disk_storage = json.loads(row["disk_storage"]) if ("disk_storage" in row.keys() and row["disk_storage"]) else None

                snapshots.append(
                    MetricSnapshot(
                        timestamp=row["timestamp"],
                        cpu=row["cpu"],
                        ram=row["ram"],
                        network=(row["network_rx"], row["network_tx"]),
                        processes_count=row["processes_count"],
                        disk_io=disk_io,
                        disk_storage=disk_storage,
                    )
                )
            return snapshots
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []


    def get_latest(self) -> Optional[MetricSnapshot]:
        """Fetch the most recent metric snapshot."""
        history = self.get_history(limit=1)
        return history[0] if history else None

    def prune_old_metrics(self, max_age_seconds: float):
        """Remove metrics older than specified seconds."""
        self._ensure_connected()
        cutoff_time = os.time.time() if hasattr(os, 'time') else sqlite3.connect  # time reference
        import time
        cutoff = time.time() - max_age_seconds
        try:
            self._connection.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
            self._connection.commit()
        except Exception as e:
            print(f"Error pruning metrics: {e}")

    def save_host(
        self,
        ip: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
    ) -> int:
        """Save a remote host to the database and return its ID."""
        self._ensure_connected()
        try:
            cursor = self._connection.execute(
                """
                INSERT INTO hosts (ip, port, username, password, key_filename)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ip, port, username, password, key_filename),
            )
            self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving host: {e}")
            return -1

    def get_hosts(self) -> List[dict]:
        """Fetch all saved remote hosts."""
        self._ensure_connected()
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT id, ip, port, username, password, key_filename FROM hosts ORDER BY id ASC")
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "ip": row["ip"],
                    "port": row["port"],
                    "username": row["username"],
                    "password": row["password"],
                    "key_filename": row["key_filename"],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error fetching hosts: {e}")
            return []

    def get_host(self, host_id: int) -> Optional[dict]:
        """Fetch a specific remote host by ID."""
        self._ensure_connected()
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT id, ip, port, username, password, key_filename FROM hosts WHERE id = ?",
                (host_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "ip": row["ip"],
                    "port": row["port"],
                    "username": row["username"],
                    "password": row["password"],
                    "key_filename": row["key_filename"],
                }
            return None
        except Exception as e:
            print(f"Error fetching host {host_id}: {e}")
            return None

    def delete_host(self, host_id: int) -> bool:
        """Delete a remote host by ID."""
        self._ensure_connected()
        try:
            self._connection.execute("DELETE FROM hosts WHERE id = ?", (host_id,))
            self._connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting host {host_id}: {e}")
            return False