from typing import Any, Dict


class BiasAuditor:
    """
    Statistical Fairness Auditor: Monitors automated decisions for disparate impact.
    Ensures Bill C-27 / AIDA compliance by detecting bias in outcomes.
    Uses statistical parity and the 80% rule.
    """
    def __init__(self) -> None:
        # Stats tracking: {trait: {value: {approved: int, rejected: int}}}
        self.stats: Dict[str, Dict[str, Dict[str, int]]] = {}
        self.fairness_threshold: float = 0.8  # 80% Rule for Disparate Impact

    def record_decision(self, traits: Dict[str, str], result_status: str) -> None:
        """Updates internal stats for demographic parity tracking."""
        for trait_name, trait_value in traits.items():
            if trait_name not in self.stats:
                self.stats[trait_name] = {}
            if trait_value not in self.stats[trait_name]:
                self.stats[trait_name][trait_value] = {"approved": 0, "rejected": 0}
            
            if result_status == "CERTIFIED" or result_status == "APPROVED":
                self.stats[trait_name][trait_value]["approved"] += 1
            else:
                self.stats[trait_name][trait_value]["rejected"] += 1

    def get_fairness_report(self) -> Dict[str, Any]:
        """Generates a summary for AIDA compliance officers."""
        report: Dict[str, Any] = {}
        for trait, values in self.stats.items():
            trait_report = {}
            rates = []
            for val, counts in values.items():
                total = counts["approved"] + counts["rejected"]
                rate = (counts["approved"] / total) if total > 0 else 0.0
                trait_report[val] = {
                    "total": total,
                    "approval_rate": f"{rate:.2%}"
                }
                if total >= 5: # Reliability threshold
                    rates.append(rate)
            
            # Check disparate impact if we have multiple groups
            status = "COMPLIANT"
            if len(rates) >= 2:
                max_rate = max(rates)
                min_rate = min(rates)
                ratio = (min_rate / max_rate) if max_rate > 0 else 1.0
                if ratio < self.fairness_threshold:
                    status = "INVESTIGATION_REQUIRED"
                trait_report["disparate_impact_ratio"] = round(ratio, 2) # type: ignore
            
            trait_report["status"] = status # type: ignore
            report[trait] = trait_report
            
        return report

    def check_disparate_impact(self) -> bool:
        """Implements the 80% rule for federal auditing."""
        report = self.get_fairness_report()
        return not any(r.get("status") == "INVESTIGATION_REQUIRED" for r in report.values())
