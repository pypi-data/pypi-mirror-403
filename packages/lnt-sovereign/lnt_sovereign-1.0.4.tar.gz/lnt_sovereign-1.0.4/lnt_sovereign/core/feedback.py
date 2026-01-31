import json
import os
from datetime import datetime
from typing import Any, Dict, List


class FeedbackFlywheel:
    """
    The Sovereign Scribe.
    Captures 'Negative Proofs' where Neural proposals clash with Symbolic Law.
    This dataset is used for DPO (Direct Preference Optimization) to align the SLM.
    """
    def __init__(self, log_dir: str = "flywheel_logs") -> None:
        self.log_dir: str = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log_rejection(self, domain_id: str, neural_proposal: Dict[str, Any], violations: List[Dict[str, Any]]) -> None:
        """
        Logs a 'Logit Clash' event. 
        Stores the raw input, the failed neural thought, and the symbolic rejection.
        """
        timestamp: str = datetime.now().isoformat()
        log_entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "domain_id": domain_id,
            "neural_proposal": neural_proposal,
            "symbolic_rejections": [
                {
                    "rule_id": v.get("id", "UNKNOWN"),
                    "description": v.get("description", "No description"),
                    "logic_error": v.get("logic_error", "N/A"),
                    "severity": v.get("severity", "TOXIC")
                } for v in violations
            ]
        }
        
        filename: str = f"rejection_{datetime.now().strftime('%Y%m%d')}.jsonl"
        filepath: str = os.path.join(self.log_dir, filename)
        
        with open(filepath, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_dpo_dataset(self) -> List[Dict[str, Any]]:
        """
        Aggregates logs into a (Prompt, Chosen, Rejected) format for alignment.
        """
        # In production, this would perform a complex transformation
        return []
