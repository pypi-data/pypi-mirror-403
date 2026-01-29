from typing import Dict, Any, List, DefaultDict
from collections import defaultdict

class BiasAuditor:
    """
    Sovereign Bias Auditor: Monitors neuro-symbolic decisions for fairness.
    Ensures Bill C-27 / AIDA compliance by detecting disparate impact.
    """
    def __init__(self) -> None:
        # We simulate demographic monitoring by parsing typical 'Region' or 'Group' traits 
        self.approval_stats: DefaultDict[str, Dict[str, int]] = defaultdict(lambda: {"approved": 0, "rejected": 0})
        self.fairness_threshold: float = 0.8  # 80% Rule for Disparate Impact

    def analyze_proposal(self, user_text: str, neural_proposal: Dict[str, Any]) -> float:
        """
        Calculates a 'Fairness Score' for the current proposal.
        """
        # Simulated trait extraction
        # (Demographic traits tracked via record_decision)
        
        # Scoring logic: 1.0 is perfectly fair, 0.0 is high risk.
        score = 1.0
        if "sensitive_region" in user_text.lower():
            score = 0.75 # Flag for closer symbolic inspection
        
        return score

    def record_decision(self, user_text: str, result_status: str) -> None:
        """Updates internal stats for demographic parity tracking."""
        trait = self._extract_demographic_traits(user_text)
        if result_status == "APPROVED":
            self.approval_stats[trait]["approved"] += 1
        else:
            self.approval_stats[trait]["rejected"] += 1

    def _extract_demographic_traits(self, text: str) -> str:
        """Simulates demographic trait extraction for federal auditing."""
        text_lower = text.lower()
        if "asia" in text_lower or "east" in text_lower:
            return "Region_A"
        if "europe" in text_lower or "west" in text_lower:
            return "Region_B"
        return "Unknown"

    def get_fairness_report(self) -> Dict[str, Any]:
        """Generates a summary for AIDA compliance officers."""
        report: Dict[str, Any] = {}
        for trait, stats in self.approval_stats.items():
            total = stats["approved"] + stats["rejected"]
            rate = (stats["approved"] / total) if total > 0 else 0.0
            report[trait] = {
                "total_cases": total,
                "approval_rate": f"{rate:.2%}",
                "fairness_status": "COMPLIANT" if rate > self.fairness_threshold or total < 5 else "INVESTIGATION_REQUIRED"
            }
        return report

    def check_disparate_impact(self) -> bool:
        """Implements the 80% rule for federal auditing."""
        rates: List[float] = []
        for stats in self.approval_stats.values():
            total = stats["approved"] + stats["rejected"]
            if total > 5:
                rates.append(stats["approved"] / total)
        
        if len(rates) < 2:
            return True # Not enough data for impact analysis
            
        max_rate = max(rates)
        min_rate = min(rates)
        
        return (min_rate / max_rate) >= self.fairness_threshold if max_rate > 0 else True
