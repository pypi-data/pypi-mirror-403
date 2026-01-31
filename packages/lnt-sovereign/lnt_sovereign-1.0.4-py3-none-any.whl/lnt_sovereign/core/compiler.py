from typing import Any, Dict, List, cast

import numpy as np
from pydantic import BaseModel, ConfigDict

from lnt_sovereign.core.exceptions import ManifestContradictionError, TypeMismatchError
from lnt_sovereign.core.formal import FormalVerifier
from lnt_sovereign.core.kernel import DomainManifest


class CompiledManifest(BaseModel):
    """
    Data structure containing pre-computed matrices for the OptimizedKernel.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    
    domain_id: str
    entity_map: Dict[str, int]
    bounds: np.ndarray
    severities: np.ndarray
    dependency_matrix: np.ndarray # Matrix [i, j] = 1 if rule j depends on rule i
    metadata: List[Dict[str, Any]]

class LNTCompiler:
    """
    Compiles a high-level DomainManifest into a high-performance CompiledManifest.
    """
    def __init__(self, verify: bool = True) -> None:
        self.verify: bool = verify
        self.verifier: FormalVerifier = FormalVerifier()

    def compile(self, manifest: DomainManifest) -> CompiledManifest:
        """
        Transforms a declarative manifest into optimized matrices for vectorized logic execution.
        If verification is enabled, uses Z3 to prove manifest consistency.
        """
        if self.verify:
            is_consistent, error = self.verifier.verify_consistency(manifest.model_dump())
            if not is_consistent:
                raise ManifestContradictionError(f"Logic contradiction detected in domain {manifest.domain_id}: {error}")

        entities = manifest.entities
        entity_map = {entity: i for i, entity in enumerate(entities)}
        
        n_constraints = len(manifest.constraints)
        bounds = np.zeros((n_constraints, 2), dtype=np.float64)
        severities = np.zeros(n_constraints, dtype=np.int32) # Encoding severity as int
        metadata = []
        
        severity_map = {"CRITICAL": 2, "FATAL": 2, "WARNING": 1}
        
        op_idx_map = {
            "GT": 0, "LT": 1, "EQ": 2, "GTE": 3, "LTE": 4, "RANGE": 5, "REQUIRED": 6
        }
        
        for i, constraint in enumerate(manifest.constraints):
            # Extract bounds (Default: infinity)
            low, high = -np.inf, np.inf
            
            try:
                if constraint.operator == "GT":
                    low = float(constraint.value)
                elif constraint.operator == "LT":
                    high = float(constraint.value)
                elif constraint.operator == "EQ":
                    if isinstance(constraint.value, (int, float)):
                        low = high = float(constraint.value)
                    else:
                        low = high = 0.0
                elif constraint.operator == "RANGE":
                    low, high = map(float, constraint.value)
                elif constraint.operator == "REQUIRED":
                    low, high = 1e-9, np.inf
            except (ValueError, TypeError) as e:
                raise TypeMismatchError(f"Invalid threshold value for {constraint.id}: {constraint.value}") from e
            
            bounds[i] = [low, high]
            severities[i] = severity_map.get(constraint.severity, 0)
            
            metadata.append({
                "id": constraint.id,
                "entity": constraint.entity,
                "entity_idx": entity_map.get(constraint.entity, 0),
                "operator_idx": op_idx_map.get(constraint.operator, 2), # Default to EQ
                "description": constraint.description,
                "severity_label": constraint.severity,
                "weight": constraint.weight,
                "evidence": constraint.evidence_source,
                "conditional_on": constraint.conditional_on or []
            })
            
        # Build Dependency Matrix
        dep_matrix = np.zeros((n_constraints, n_constraints), dtype=np.bool_)
        id_to_idx = {m["id"]: i for i, m in enumerate(metadata)}
        
        for i, m in enumerate(metadata):
            for dep_id in cast(List[str], m["conditional_on"]):
                if dep_id in id_to_idx:
                    dep_idx = id_to_idx[dep_id]
                    dep_matrix[dep_idx, i] = True # i depends on dep_idx
                    
        return CompiledManifest(
            domain_id=manifest.domain_id,
            entity_map=entity_map,
            bounds=bounds,
            severities=severities,
            dependency_matrix=dep_matrix,
            metadata=metadata
        )
