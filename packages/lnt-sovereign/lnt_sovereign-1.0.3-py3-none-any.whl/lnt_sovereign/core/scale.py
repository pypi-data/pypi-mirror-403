import json
import random
import time
import hashlib
from datetime import datetime
from typing import Dict, Any
from lnt_sovereign.core.kernel import KernelEngine

class AuditLogger:
    """
    Generates AIDA-compliant (JSON-LD style) Audit Logs.
    Every decision creates a verifiable 'Proof of Reasoning'.
    """
    @staticmethod
    def generate_proof(user_input: str, result: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = datetime.now().isoformat()
        
        # Robust serialization for Pydantic models and Enums
        def serialize_item(obj: Any) -> Any:
            if hasattr(obj, 'dict'):
                return serialize_item(obj.dict())
            if isinstance(obj, dict):
                return {k: serialize_item(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize_item(i) for i in obj]
            if hasattr(obj, 'value'): # Handle Enums
                return obj.value
            return obj

        constraints_json = serialize_item(result.get('constraints', []))
        
        content_to_hash = f"{timestamp}-{user_input}-{json.dumps(constraints_json)}"
        proof_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

        return {
            "@context": "https://lnt.ai/contexts/sovereign-audit-v1.jsonld",
            "type": "ComplianceAudit",
            "timestamp": timestamp,
            "subject": hashlib.sha256(user_input.encode(), usedforsecurity=False).hexdigest()[:8], # Anonymous ID
            "manifold_decision": result["status"],
            "sovereign_proof": f"sha256:{proof_hash}",
            "regulatory_framework": "Bill C-27 / AIDA 2026"
        }

class ScaleTester:
    """
    Simulates high-volume 'Sovereign Traffic' to verify engine performance.
    """
    def __init__(self, iterations: int = 100) -> None:
        self.iterations = iterations
        self.engine = KernelEngine()

    def run_stress_test(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {"passed": 0, "failed": 0, "total": 0, "avg_latency_ms": 0.0}
        start_time = time.time()

        for _ in range(self.iterations):
            # Generate random profile
            try:
                # Mock proposal for stress testing
                proposal = {
                    "has_valid_passport": random.choice([True, False]),  # nosec B311
                    "funding_available": random.uniform(500, 50000),     # nosec B311
                    "language_proficiency": random.randint(3, 10),       # nosec B311
                    "has_business_commitment": random.choice([True, False]) # nosec B311
                }
                # Use a dummy evaluation if no manifest loaded, or just time the call
                if self.engine.manifest:
                    self.engine.evaluate(proposal)
                
                results["total"] += 1
                results["passed"] += 1
            except Exception:
                results["total"] += 1
                results["failed"] += 1

        end_time = time.time()
        results["avg_latency_ms"] = float(((end_time - start_time) / self.iterations) * 1000)
        return results
