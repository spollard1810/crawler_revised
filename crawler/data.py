import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from .fsm import DeviceState, StateTransition

class Database:
    def __init__(self, db_path: str = "network_crawl.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT NOT NULL UNIQUE,
                    ip TEXT,
                    serial TEXT,
                    platform TEXT,
                    state TEXT NOT NULL,
                    last_seen TIMESTAMP NOT NULL,
                    enriched BOOLEAN DEFAULT FALSE,
                    error_msg TEXT,
                    claimed_by TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    error_msg TEXT,
                    FOREIGN KEY (device_id) REFERENCES devices (id)
                )
            """)

    @contextmanager
    def _get_connection(self):
        """Get a thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def add_device(self, hostname: str) -> int:
        """Add a new device to the queue."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO devices (hostname, state, last_seen)
                VALUES (?, ?, ?)
                ON CONFLICT (hostname) DO NOTHING
                RETURNING id
            """, (hostname, DeviceState.QUEUED.name, datetime.utcnow()))
            
            result = cursor.fetchone()
            if result:
                return result['id']
            return None

    def get_next_queued_device(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get the next queued device and claim it for processing."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE devices
                SET claimed_by = ?, state = ?, last_seen = ?
                WHERE id = (
                    SELECT id FROM devices
                    WHERE state = ? AND (claimed_by IS NULL OR last_seen < datetime('now', '-5 minutes'))
                    ORDER BY created_at ASC
                    LIMIT 1
                )
                RETURNING *
            """, (worker_id, DeviceState.CONNECTING.name, datetime.utcnow(), DeviceState.QUEUED.name))
            
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_device_state(self, device_id: int, transition: StateTransition) -> None:
        """Update device state and record the transition."""
        with self._get_connection() as conn:
            # Update device state
            conn.execute("""
                UPDATE devices
                SET state = ?, last_seen = ?, error_msg = ?, updated_at = ?
                WHERE id = ?
            """, (transition.to_state.name, datetime.utcnow(), 
                  transition.error_msg, datetime.utcnow(), device_id))
            
            # Record state transition
            conn.execute("""
                INSERT INTO state_transitions (device_id, from_state, to_state, timestamp, error_msg)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, transition.from_state.name, transition.to_state.name,
                  transition.timestamp, transition.error_msg))

    def update_device_info(self, device_id: int, info: Dict[str, Any]) -> None:
        """Update device information."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE devices
                SET hostname = ?, serial = ?, platform = ?, updated_at = ?
                WHERE id = ?
            """, (info.get('hostname'), info.get('serial'), 
                  info.get('platform'), datetime.utcnow(), device_id))

    def release_device(self, device_id: int) -> None:
        """Release a device from being claimed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE devices
                SET claimed_by = NULL
                WHERE id = ?
            """, (device_id,))

    def increment_retry_count(self, device_id: int) -> None:
        """Increment the retry count for a device."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE devices
                SET retry_count = retry_count + 1
                WHERE id = ?
            """, (device_id,))

    def get_device_retry_count(self, device_id: int) -> int:
        """Get the current retry count for a device."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT retry_count FROM devices WHERE id = ?
            """, (device_id,))
            result = cursor.fetchone()
            return result['retry_count'] if result else 0 