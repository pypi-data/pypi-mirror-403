import json
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryEvent:
    event_id: str
    timestamp: float
    command: str
    success: bool
    latency_ms: float
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TelemetryManager:
    """
    LNT Telemetry Service.
    Handles local-first observability and anonymous quality pings for research.
    """
    _instance = None
    _lock = threading.Lock()
    _initialized: bool

    def __new__(cls) -> "TelemetryManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TelemetryManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.home_dir = Path.home() / ".lnt"
        self.telemetry_dir = self.home_dir / "telemetry"
        self.db_path = self.telemetry_dir / "stats.db"
        
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        # Check Opt-Out
        self.opt_out = os.getenv("LNT_NO_TELEMETRY", "0") == "1"
        self._load_config()
        
        self._init_db()
        self._initialized = True

    def _load_config(self) -> None:
        config_path = self.home_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if config.get("telemetry") is False:
                        self.opt_out = True
            except Exception:  # noqa: S110
                pass

    def _init_db(self) -> None:
        """Initialize the local SQLite store."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                timestamp REAL,
                command TEXT,
                success INTEGER,
                latency_ms REAL,
                error_type TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_event(
        self, 
        command: str, 
        success: bool, 
        latency_ms: float, 
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Main entry point for logging engine events."""
        event = TelemetryEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            command=command,
            success=success,
            latency_ms=latency_ms,
            error_type=error_type,
            metadata=metadata
        )
        
        # 1. Local Storage (Always if not globally disabled)
        self._save_local(event)
        
        # 2. Remote Dispatch (Only if Opt-Out is False)
        if not self.opt_out:
            threading.Thread(target=self._dispatch_remote, args=(event,), daemon=True).start()

    def _save_local(self, event: TelemetryEvent) -> None:
        """Save event to local SQLite DB."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.timestamp,
                    event.command,
                    1 if event.success else 0,
                    event.latency_ms,
                    event.error_type,
                    json.dumps(event.metadata or {})
                )
            )
            conn.commit()
            conn.close()
        except Exception:  # noqa: S110
            pass

    def _dispatch_remote(self, event: TelemetryEvent) -> None:
        """
        Send anonymous metadata to the improvement endpoint.
        NOTE: This is a stub for the quality improvement research.
        In production, this would ping an LNT endpoint.
        """
        # Scrubbed metadata for remote improvemnt
        # For now, we remain a silent observer.
        pass

    def get_local_stats(self) -> List[Dict[str, Any]]:
        """Retrieve local history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_local_stats(self) -> None:
        """Purge local telemetry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events")
        conn.commit()
        conn.close()
