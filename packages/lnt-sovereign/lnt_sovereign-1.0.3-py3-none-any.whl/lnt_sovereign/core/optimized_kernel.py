import numpy as np
from typing import Dict, Any, List
from lnt_sovereign.core.compiler import CompiledManifest

class OptimizedKernel:
    """
    The High-Speed Execution Engine for LNT.
    Uses Vectorized Matrix Math to enforce Sovereign Law.
    """
    def __init__(self, compiled: CompiledManifest) -> None:
        self.manifest: CompiledManifest = compiled
        self.indices: Dict[str, int] = compiled.entity_map
        self.bounds: np.ndarray = compiled.bounds
        self.severities: np.ndarray = compiled.severities
        self.metadata: List[Dict[str, Any]] = compiled.metadata
        self.weights: np.ndarray = np.array([m.get("weight", 1.0) for m in self.metadata])
        
        # PRE-COMPUTED: Map each constraint in bounds to its index in state_vec
        self._c_indices: np.ndarray = np.array([m['entity_idx'] for m in self.metadata], dtype=int)
        self._state_vec: np.ndarray = np.zeros(len(self.indices))

    def evaluate(self, proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Standard evaluation: Returns only violations."""
        res = self.trace_evaluate(proposal)
        violations: List[Dict[str, Any]] = res["violations"]
        return violations

    def trace_evaluate(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-performance trace evaluation with Weighted Sovereign Scoring.
        Note: For SG-1, we use full-matrix evaluation for maximum SIMD throughput.
        """
        # 1. Update state vector
        self._state_vec.fill(0.0) 
        for key, val in proposal.items():
            if key in self.indices:
                try:
                    self._state_vec[self.indices[key]] = float(val)
                except (ValueError, TypeError):
                    continue 

        # 2. Vectorized Bounds Check
        c_state = self._state_vec[self._c_indices]
        lower_bounds = self.bounds[:, 0]
        upper_bounds = self.bounds[:, 1]
        
        violation_mask = (c_state < lower_bounds) | (c_state > upper_bounds)
        
        # 3. Weighted Scoring (Sovereign Manifold Score)
        total_weight = np.sum(self.weights)
        deducted_weight = np.dot(violation_mask.astype(float), self.weights)
        score = max(0.0, 100.0 * (1.0 - (deducted_weight / total_weight))) if total_weight > 0 else 100.0

        # 4. Extract Passes and Violations
        violations: List[Dict[str, Any]] = []
        passes: List[str] = []
        
        for idx in range(len(violation_mask)):
            meta = self.metadata[idx]
            if violation_mask[idx]:
                val = c_state[idx]
                lower, upper = self.bounds[idx]
                violations.append({
                    "id": meta["id"],
                    "entity": meta["entity"],
                    "description": meta["description"],
                    "logic_error": f"Value {val} outside bounds [{lower}, {upper}]",
                    "severity": meta["severity_label"],
                    "evidence": meta["evidence"]
                })
            else:
                passes.append(meta["id"])
            
        status = "CERTIFIED" if not violations else "REJECTED"
        return {
            "status": status,
            "violations": violations,
            "passes": passes,
            "score": round(float(score), 2)
        }
