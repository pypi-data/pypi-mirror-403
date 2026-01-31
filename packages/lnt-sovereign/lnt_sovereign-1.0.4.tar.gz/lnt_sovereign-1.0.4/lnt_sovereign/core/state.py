import os
import time
from typing import List

import lmdb
import numpy as np


class StateEntry:
    def __init__(self, value: float, timestamp: float) -> None:
        self.value = value
        self.timestamp = timestamp

class LNTStateBuffer:
    """
    Experimental state buffer for temporal logic evaluation.
    Uses LMDB for local persistence.
    """
    def __init__(self, db_path: str = ".lnt_state", map_size: int = 10485760) -> None: # 10MB default
        os.makedirs(db_path, exist_ok=True)
        self.env = lmdb.open(db_path, map_size=map_size, metasync=False, sync=False)
        self._warmup()

    def _warmup(self) -> None:
        """Ensures index is ready."""
        with self.env.begin(write=True) as txn:
            if not txn.get(b"__lnt_version__"):
                txn.put(b"__lnt_version__", b"1.0.3")

    def push(self, entity: str, value: float) -> None:
        """Pushes a new state entry into the persistent LMDB store."""
        timestamp = time.time()
        # Add a random suffix to ensure uniqueness even during sub-ms bursts
        suffix = os.urandom(2).hex()
        key = f"{entity}:{timestamp}:{suffix}".encode()
        val = str(float(value)).encode()
        
        with self.env.begin(write=True) as txn:
            txn.put(key, val)

    def get_window_data(self, entity: str, window_seconds: float) -> List[float]:
        """Retrieves values within the specified time window from LMDB."""
        now = time.time()
        cutoff = now - window_seconds
        prefix = f"{entity}:".encode()
        
        values: List[float] = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            if cursor.set_range(prefix):
                for key, val in cursor:
                    if not key.startswith(prefix):
                        break
                    
                    # Extract timestamp from key "entity:timestamp:suffix"
                    try:
                        # Split by colon, the timestamp is the second part
                        # entity:timestamp:suffix -> parts[1]
                        parts = key.decode().split(":")
                        if len(parts) >= 2:
                            ts_str = parts[1]
                            ts = float(ts_str)
                            if ts >= cutoff:
                                values.append(float(val.decode()))
                    except (ValueError, IndexError):
                        continue
        return values

    def calculate_average(self, entity: str, window_seconds: float) -> float:
        """Calculates trailing average over a window using persistent data."""
        data = self.get_window_data(entity, window_seconds)
        if not data:
            return 0.0
        return float(np.mean(data))

    def calculate_frequency(self, entity: str, window_seconds: float) -> int:
        """Calculates frequency of events over a window using persistent data."""
        return len(self.get_window_data(entity, window_seconds))

    def parse_window(self, window_str: str) -> float:
        """Parses window strings like '30d', '5m', '500ms' into seconds."""
        window_str = window_str.lower().strip()
        if window_str.endswith('ms'):
            return float(window_str[:-2]) / 1000.0
        if window_str.endswith('s'):
            return float(window_str[:-1])
        if window_str.endswith('m'):
            return float(window_str[:-1]) * 60.0
        if window_str.endswith('h'):
            return float(window_str[:-1]) * 3600.0
        if window_str.endswith('d'):
            return float(window_str[:-1]) * 86400.0
        return 0.0

    def clear_entity(self, entity: str) -> None:
        """Removes all history for a specific entity."""
        prefix = f"{entity}:".encode()
        with self.env.begin(write=True) as txn:
            cursor = txn.cursor()
            if cursor.set_range(prefix):
                for key, _ in cursor:
                    if not key.startswith(prefix):
                        break
                    txn.delete(key)

    def close(self) -> None:
        """Safely closes the LMDB environment."""
        self.env.close()
