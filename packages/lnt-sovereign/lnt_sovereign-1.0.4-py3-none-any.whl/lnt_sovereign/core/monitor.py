import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional


class LNTMonitor:
    """
    Tracks the health and compliance of the LNT engine.
    Measures the 'Reasoning Gap' between Neural and Symbolic layers.
    """
    def __init__(self, window_size: int = 100) -> None:
        self.history: Deque[Dict[str, Any]] = deque(maxlen=window_size)
        self.rejections: int = 0
        self.approvals: int = 0
        self.total_latency: float = 0.0

    def log_transaction(
        self, 
        domain: str, 
        is_safe: bool, 
        score: float = 0.0, 
        violations: Optional[List[Dict[str, Any]]] = None,
        latency_ms: float = 0.0
    ) -> None:
        """Standardized logging for agnostic domain events with rich metrics."""
        if is_safe:
            self.approvals += 1
        else:
            self.rejections += 1
        
        self.total_latency += latency_ms / 1000.0 # Convert ms back to seconds for existing total_latency
        
        self.history.append({
            "domain": domain,
            "is_safe": is_safe,
            "score": score,
            "violations": violations or [],
            "latency_ms": latency_ms,
            "timestamp": time.time()
        })

    @property
    def hallucination_rate(self) -> float:
        """Percentage of neural proposals rejected by symbolic logic."""
        total = self.approvals + self.rejections
        if total == 0:
            return 0.0
        return (self.rejections / total) * 100.0

    @property
    def avg_latency(self) -> float:
        total = len(self.history)
        if total == 0:
            return 0.0
        return (self.total_latency / total) * 1000.0 # returns in ms

    def get_ops_report(self) -> Dict[str, Any]:
        return {
            "approvals": self.approvals,
            "rejections": self.rejections,
            "hallucination_rate": f"{self.hallucination_rate:.2f}%",
            "avg_latency": f"{self.avg_latency:.2f}ms",
            "uptime": "100.00%",
            "status": "COMPLIANT" if self.hallucination_rate < 50 else "DEGRADED"
        }
