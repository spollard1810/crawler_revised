import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = "netparse.db"):
        self.db_path = db_path
        self._init_db()
        self._lock = threading.Lock()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT,
                    ip TEXT UNIQUE,
                    serial TEXT,
                    platform TEXT,
                    state TEXT CHECK(state IN ('queued', 'connecting', 'collecting', 'discovered', 'enriched', 'done', 'error')),
                    last_seen TIMESTAMP,
                    enriched BOOLEAN DEFAULT FALSE,
                    error_msg TEXT,
                    claimed_by TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_neighbors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER,
                    neighbor_ip TEXT,
                    neighbor_hostname TEXT,
                    interface TEXT,
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_devices_state ON devices(state);
                CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip);
            """)

    @contextmanager
    def _get_connection(self):
        """Thread-safe connection management."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def add_device(self, ip: str, hostname: Optional[str] = None) -> bool:
        """Add a new device to the queue if it doesn't exist."""
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO devices (ip, hostname, state) VALUES (?, ?, 'queued')",
                    (ip, hostname)
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def claim_device(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Claim a queued device for processing."""
        with self._get_connection() as conn:
            device = conn.execute("""
                SELECT * FROM devices 
                WHERE state = 'queued' 
                ORDER BY created_at ASC 
                LIMIT 1
            """).fetchone()
            
            if device:
                conn.execute(
                    "UPDATE devices SET claimed_by = ?, state = 'connecting' WHERE id = ?",
                    (worker_id, device['id'])
                )
                return dict(device)
            return None

    def update_device_state(self, device_id: int, state: str, error_msg: Optional[str] = None):
        """Update device state and clear claim."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE devices 
                SET state = ?, 
                    error_msg = ?, 
                    claimed_by = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (state, error_msg, device_id))

    def update_device_info(self, device_id: int, **kwargs):
        """Update device information."""
        if not kwargs:
            return
            
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [device_id]
        
        with self._get_connection() as conn:
            conn.execute(f"""
                UPDATE devices 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)

    def add_neighbors(self, device_id: int, neighbors: List[Dict[str, str]]):
        """Add discovered neighbors for a device."""
        with self._get_connection() as conn:
            for neighbor in neighbors:
                conn.execute("""
                    INSERT INTO device_neighbors (device_id, neighbor_ip, neighbor_hostname, interface)
                    VALUES (?, ?, ?, ?)
                """, (device_id, neighbor['ip'], neighbor['hostname'], neighbor['interface']))

    def get_device_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Retrieve device by IP address."""
        with self._get_connection() as conn:
            device = conn.execute(
                "SELECT * FROM devices WHERE ip = ?",
                (ip,)
            ).fetchone()
            return dict(device) if device else None

    def increment_retry_count(self, device_id: int):
        """Increment the retry counter for a device."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE devices SET retry_count = retry_count + 1 WHERE id = ?",
                (device_id,)
            )

    def cleanup_stale_claims(self, timeout_seconds: int = 300):
        """Reset stale claims that haven't been updated."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE devices 
                SET claimed_by = NULL, 
                    state = 'queued',
                    retry_count = retry_count + 1
                WHERE claimed_by IS NOT NULL 
                AND updated_at < datetime('now', ?)
            """, (f"-{timeout_seconds} seconds",)) 