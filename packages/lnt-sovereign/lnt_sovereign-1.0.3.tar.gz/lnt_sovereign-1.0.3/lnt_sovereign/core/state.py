import time
from collections import deque
from typing import Dict, List, Deque
import numpy as np

class StateEntry:
    def __init__(self, value: float, timestamp: float) -> None:
        self.value = value
        self.timestamp = timestamp

class SovereignStateBuffer:
    """
    High-performance, in-memory state buffer for Temporal Sovereign Logic.
    Supports sliding windows for averages and frequency detection.
    """
    def __init__(self, max_history: int = 10000) -> None:
        self.buffer: Dict[str, Deque[StateEntry]] = {} # entity_id -> deque[StateEntry]
        self.max_history = max_history

    def push(self, entity: str, value: float) -> None:
        """Pushes a new state entry into the entity buffer."""
        if entity not in self.buffer:
            self.buffer[entity] = deque(maxlen=self.max_history)
        
        entry = StateEntry(value=float(value), timestamp=time.time())
        self.buffer[entity].append(entry)

    def get_window_data(self, entity: str, window_seconds: float) -> List[float]:
        """Returns values within the specified time window."""
        if entity not in self.buffer:
            return []
        
        now = time.time()
        cutoff = now - window_seconds
        
        # We assume buffer is sorted by timestamp (it is as we only push 'now')
        return [e.value for e in self.buffer[entity] if e.timestamp >= cutoff]

    def calculate_average(self, entity: str, window_seconds: float) -> float:
        """Calculates the trailing average for an entity over a window."""
        data = self.get_window_data(entity, window_seconds)
        if not data:
            return 0.0
        return float(np.mean(data))

    def calculate_frequency(self, entity: str, window_seconds: float) -> int:
        """Calculates the frequency (count) of events for an entity over a window."""
        data = self.get_window_data(entity, window_seconds)
        return len(data)

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
