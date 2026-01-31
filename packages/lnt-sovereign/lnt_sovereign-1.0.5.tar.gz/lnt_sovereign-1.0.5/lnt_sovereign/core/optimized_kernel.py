from typing import Any, Dict, List

import numpy as np

from lnt_sovereign.core.compiler import CompiledManifest


class OptimizedKernel:
    """
    The High-Speed Execution Engine for LNT.
    Uses Vectorized Matrix Math to enforce logical constraints.
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

        # BIT-MASK: 2 for CRITICAL/FATAL, 1 for WARNING
        self._critical_mask: np.ndarray = (self.severities == 2)
        self._weight_mask: np.ndarray = self.weights
        self._dep_matrix: np.ndarray = compiled.dependency_matrix

    def evaluate(self, proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fast evaluation: Just returns violations."""
        self._update_state(proposal)
        violation_mask = self._get_violation_mask()
        
        # Apply dependency pruning
        violation_mask = self._apply_dependency_pruning(violation_mask)
        
        if not np.any(violation_mask):
            return []
            
        return self._build_violations(violation_mask)

    def trace_evaluate(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-performance trace evaluation with logic-based scoring.
        Note: For DL-1, we use full-matrix evaluation for maximum SIMD throughput.
        """
        self._update_state(proposal)
        violation_mask = self._get_violation_mask()
        
        # 3. Dependency Pruning (Vectorized DAG resolution)
        # We prune rules whose prerequisites have failed.
        # Pruned rules are considered 'NOT_EVALUATED' and don't count towards score/violations.
        effective_mask, pruned_mask = self._apply_dependency_pruning(violation_mask, return_pruned=True)
        
        # 4. Logic Health Score
        total_weight = np.sum(self._weight_mask[~pruned_mask])
        deducted_weight = np.dot(effective_mask.astype(float), self._weight_mask)
        score = max(0.0, 100.0 * (1.0 - (deducted_weight / total_weight))) if total_weight > 0 else 100.0

        # Instant Critical Rejection Check
        has_critical = np.any(effective_mask & self._critical_mask)
        
        # 5. Extract Passes and Violations
        violations = self._build_violations(effective_mask)
        passes = [
            self.metadata[i]["id"] 
            for i in range(len(effective_mask)) 
            if not effective_mask[i] and not pruned_mask[i]
        ]
            
        status = "CERTIFIED" if not violations else "REJECTED"
        if has_critical:
            status = "REJECTED_CRITICAL"

        return {
            "status": status,
            "violations": violations,
            "passes": passes,
            "pruned": [self.metadata[i]["id"] for i in range(len(pruned_mask)) if pruned_mask[i]],
            "score": round(float(score), 2)
        }

    def _apply_dependency_pruning(self, violation_mask: np.ndarray, return_pruned: bool = False) -> Any:
        """
        Matrix-based DAG pruning. 
        If Rule A fails, all rules depending on A (directly or indirectly) are pruned.
        """
        pruned_mask = np.zeros_like(violation_mask, dtype=np.bool_)
        
        # We need to resolve dependencies. Since we have an adjacency matrix, 
        # we can find rules that depend on failed rules.
        # Note: This currently handles 1-level deep dependencies efficiently.
        # For multi-level DAGs, we'd iterate or use powers of the adjacency matrix.
        failed_indices = np.where(violation_mask)[0]
        
        if failed_indices.size > 0:
            # Rules that depend on any failed rule
            depends_on_failed = np.any(self._dep_matrix[failed_indices, :], axis=0)
            pruned_mask |= depends_on_failed
            
        effective_mask = violation_mask & (~pruned_mask)
        
        if return_pruned:
            return effective_mask, pruned_mask
        return effective_mask

    def _update_state(self, proposal: Dict[str, Any]) -> None:
        """Efficiently update the internal state vector."""
        self._state_vec.fill(0.1) # Default 'Missing' value that likely fails strict checks
        for key, val in proposal.items():
            if key in self.indices:
                try:
                    self._state_vec[self.indices[key]] = float(val)
                except (ValueError, TypeError):
                    continue

    def _get_violation_mask(self) -> np.ndarray:
        """Matrix-based bounds check."""
        c_state = self._state_vec[self._c_indices]
        return (c_state < self.bounds[:, 0]) | (c_state > self.bounds[:, 1]) # type: ignore

    def _build_violations(self, violation_mask: np.ndarray) -> List[Dict[str, Any]]:
        """Convert mask back to readable violations."""
        violations = []
        violation_indices = np.where(violation_mask)[0]
        c_state = self._state_vec[self._c_indices]
        
        for idx in violation_indices:
            meta = self.metadata[idx]
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
        return violations
