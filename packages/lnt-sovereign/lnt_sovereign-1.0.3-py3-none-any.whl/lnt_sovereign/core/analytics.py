from typing import Dict, Any, List
from collections import Counter
from datetime import datetime
from lnt_sovereign.core.monitor import SovereignMonitor

class SovereignAnalyticsEngine:
    """
    Advanced decision analytics for the LNT engine.
    Computes trends, frequency heatmaps, and performance distributions.
    """
    def __init__(self, monitor: SovereignMonitor) -> None:
        self.monitor = monitor

    def get_score_trends(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the trend of Sovereign Scores over time."""
        trends = []
        for entry in list(self.monitor.history)[-limit:]:
            trends.append({
                "timestamp": entry.get("timestamp"),
                "score": entry.get("score", 0.0),
                "domain": entry.get("domain")
            })
        return trends

    def get_violation_heatmap(self) -> Dict[str, int]:
        """identifies which rules are triggered most frequently."""
        all_violations = []
        for entry in self.monitor.history:
            violations = entry.get("violations", [])
            for v in violations:
                all_violations.append(v.get("id", "unknown"))
        
        return dict(Counter(all_violations))

    def get_performance_stats(self) -> Dict[str, Any]:
        """Calculates latency distribution and throughput."""
        history = list(self.monitor.history)
        if not history:
            return {"avg_latency": 0.0, "p95_latency": 0.0, "throughput": 0.0}
        
        latencies = [e.get("latency_ms", 0.0) for e in history]
        latencies.sort()
        
        avg = sum(latencies) / len(latencies)
        p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0.0
        
        # Simple throughput calculation (ops per sec)
        if len(history) > 1:
            timespan = history[-1]["timestamp"] - history[0]["timestamp"]
            throughput = len(history) / timespan if timespan > 0 else 0.0
        else:
            throughput = 0.0

        return {
            "avg_latency_ms": round(avg, 3),
            "p95_latency_ms": round(p95, 3),
            "throughput_ops_sec": round(throughput, 2)
        }

    def generate_health_summary(self) -> Dict[str, Any]:
        """High-level summary for the Sovereign Portal."""
        ops = self.monitor.get_ops_report()
        heatmap = self.get_violation_heatmap()
        perf = self.get_performance_stats()
        
        top_violation = max(heatmap, key=lambda k: heatmap[k]) if heatmap else "None"
        
        return {
            "overall_status": ops["sovereign_status"],
            "hallucination_rate": ops["hallucination_rate"],
            "critical_rules_triggered": len(heatmap),
            "top_violation_id": top_violation,
            "performance": perf,
            "timestamp": datetime.now().isoformat()
        }
