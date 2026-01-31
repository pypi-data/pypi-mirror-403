import time
from typing import Any, Dict, List

import numpy as np
from numba import boolean, float64, int64, jit, prange

from lnt_sovereign.core.compiler import CompiledManifest

# Operator codes for JIT signatures (Fixed constants for compiled stability)
OP_GT: int = 0
OP_LT: int = 1
OP_EQ: int = 2
OP_GTE: int = 3
OP_LTE: int = 4
OP_RANGE: int = 5
OP_REQUIRED: int = 6

@jit(nopython=True, cache=True, fastmath=True)
def evaluate_constraint_jit(
    value: float64,
    operator: int64,
    threshold: float64,
    threshold_high: float64 = 0.0
) -> boolean:
    """
    Sub-microsecond primitive for single constraint evaluation.
    Designed for inlining within the parallel prange loop.
    """
    if operator == OP_GT:
        return value > threshold
    elif operator == OP_LT:
        return value < threshold
    elif operator == OP_EQ:
        return value == threshold
    elif operator == OP_GTE:
        return value >= threshold
    elif operator == OP_LTE:
        return value <= threshold
    elif operator == OP_RANGE:
        return value >= threshold and value <= threshold_high
    elif operator == OP_REQUIRED:
        return value != 0.0
    return True

@jit(nopython=True, cache=True, fastmath=True, parallel=True)
def evaluate_all_constraints_jit(
    values: np.ndarray,
    operators: np.ndarray,
    thresholds_low: np.ndarray,
    thresholds_high: np.ndarray,
    entity_indices: np.ndarray
) -> np.ndarray:
    """
    Parallelized evaluation of the entire manifold logic cage.
    Uses SIMD vectorization and multi-threading for O(1) perceived latency.
    """
    n_constraints = len(operators)
    results = np.empty(n_constraints, dtype=np.bool_)
    
    for i in prange(n_constraints):
        entity_idx = entity_indices[i]
        value = values[entity_idx]
        operator = operators[i]
        threshold_low = thresholds_low[i]
        threshold_high = thresholds_high[i]
        
        results[i] = evaluate_constraint_jit(
            value, operator, threshold_low, threshold_high
        )
    
    return results

class JITKernel:
    """
    The Silicon-Level Logic Gatekeeper.
    Compiled to LLVM machine code at runtime for extreme performance.
    """
    def __init__(self, compiled: CompiledManifest) -> None:
        self.manifest: CompiledManifest = compiled
        self.entities: List[str] = list(compiled.entity_map.keys())
        self.entity_map: Dict[str, int] = compiled.entity_map
        
        # Extract pre-computed matrices for JIT execution
        self.operators: np.ndarray = np.array([m.get("operator_idx", 0) for m in compiled.metadata], dtype=np.int64)
        self.thresholds_low: np.ndarray = compiled.bounds[:, 0]
        self.thresholds_high: np.ndarray = compiled.bounds[:, 1]
        self.entity_indices: np.ndarray = np.array([m['entity_idx'] for m in compiled.metadata], dtype=np.int64)
        
        self.metadata: List[Dict[str, Any]] = compiled.metadata
        self._warmup()

    def _warmup(self) -> None:
        """Triggers the first-call JIT compilation and caches machine code."""
        dummy_values = np.zeros(len(self.entity_map), dtype=np.float64)
        evaluate_all_constraints_jit(
            dummy_values, self.operators, self.thresholds_low, 
            self.thresholds_high, self.entity_indices
        )

    def evaluate(self, proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes the compiled symbolic logic against the proposal vector.
        """
        values = np.zeros(len(self.entity_map), dtype=np.float64)
        for entity, val in proposal.items():
            if entity in self.entity_map:
                try:
                    values[self.entity_map[entity]] = float(val)
                except (ValueError, TypeError):
                    continue

        results = evaluate_all_constraints_jit(
            values, self.operators, self.thresholds_low, 
            self.thresholds_high, self.entity_indices
        )
        
        violations: List[Dict[str, Any]] = []
        for i, satisfied in enumerate(results):
            if not satisfied:
                meta = self.metadata[i]
                violations.append({
                    "id": meta["id"],
                    "entity": meta["entity"],
                    "description": meta["description"],
                    "severity": meta["severity_label"]
                })
        
        return violations

    def benchmark(self, iterations: int = 100000) -> Dict[str, Any]:
        """
        Performance audit of the compiled kernel.
        """
        values = np.zeros(len(self.entity_map), dtype=np.float64)
        times: List[float] = []
        
        for _ in range(iterations):
            start = time.perf_counter_ns()
            evaluate_all_constraints_jit(
                values, self.operators, self.thresholds_low, 
                self.thresholds_high, self.entity_indices
            )
            times.append(float(time.perf_counter_ns() - start))
            
        times_arr = np.array(times)
        return {
            "mean_us": np.mean(times_arr) / 1000.0,
            "p99_us": np.percentile(times_arr, 99) / 1000.0,
            "throughput": int(1e9 / np.mean(times_arr))
        }
