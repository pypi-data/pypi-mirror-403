import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from lnt_sovereign.core.exceptions import EvaluationError


class ConstraintOperator(str, Enum):
    GT = "GT"
    LT = "LT"
    GTE = "GTE"
    LTE = "LTE"
    EQ = "EQ"
    IN = "IN"
    NIN = "NIN"
    RANGE = "RANGE"
    REQUIRED = "REQUIRED"

class ManifestConstraint(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str
    entity: str
    operator: ConstraintOperator
    value: Any
    description: str
    severity: str = "CRITICAL"  # CRITICAL, FATAL, WARNING
    weight: float = 1.0     # 0.0 to 1.0 for weighted manifests
    conditional_on: Optional[List[str]] = None # IDs of prerequisite rules
    temporal_window: Optional[str] = None      # e.g., '30d', '500ms'
    evidence_source: Optional[str] = None

class DomainManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    domain_id: str
    domain_name: str
    version: str
    entities: List[str]
    constraints: List[ManifestConstraint]

    @field_validator("constraints")
    @classmethod
    def validate_entities(cls, v: List[ManifestConstraint], info: Any) -> List[ManifestConstraint]:
        entities = info.data.get("entities", [])
        for constraint in v:
            if constraint.entity not in entities:
                raise ValueError(f"Constraint {constraint.id} uses undefined entity: {constraint.entity}")
        return v

class KernelEngine:
    """
    The Agnostic Logic Kernel.
    Drives LNT decisions via Dynamic Manifest Injection.
    """
    def __init__(self, manifest_path: Optional[str] = None, state_buffer: Optional[Any] = None) -> None:
        self.manifest: Optional[DomainManifest] = None
        self.state_buffer = state_buffer
        if manifest_path:
            self.load_manifest(manifest_path)

    def load_manifest(self, path: str) -> DomainManifest:
        """Loads a manifest from a JSON file and validates it against the schema."""
        with open(path, 'r') as f:
            data = json.load(f)
            self.manifest = DomainManifest(**data)
            return self.manifest

    def evaluate(self, proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluates a proposal against the loaded manifest. Returns only violations."""
        res = self.trace_evaluate(proposal)
        violations: List[Dict[str, Any]] = res["violations"]
        return violations

    def trace_evaluate(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic Logic (DL-1) evaluation.
        Executes logic based on DAG dependencies and calculates weighted score.
        """
        if not self.manifest:
            return {"status": "NO_MANIFEST", "violations": [], "passes": [], "score": 0.0}

        violations: List[Dict[str, Any]] = []
        passes: List[str] = []
        
        # Mapping to track pass/fail for DAG pruning
        results_map: Dict[str, bool] = {} 
        
        total_weight = sum(c.weight for c in self.manifest.constraints)
        deducted_weight = 0.0

        # Track un-governed signals (Flexibility Feature)
        manifest_entities = set(self.manifest.entities)
        proposal_entities = set(proposal.keys())
        un_governed = proposal_entities - manifest_entities

        for constraint in self.manifest.constraints:
            # 0. Dependency Check (DAG Pruning)
            if constraint.conditional_on:
                prerequisites_passed = all(results_map.get(pid, False) for pid in constraint.conditional_on)
                if not prerequisites_passed:
                    continue # Skip this rule; context not met

            entity_val = proposal.get(constraint.entity)
            
            # 1. State Persistence (Level 2)
            if self.state_buffer and entity_val is not None:
                try:
                    self.state_buffer.push(constraint.entity, float(entity_val))
                except Exception:  # noqa: S110
                    pass

            # 2. Temporal Context Resolution
            actual_val = entity_val
            if constraint.temporal_window and self.state_buffer:
                win_sec = self.state_buffer.parse_window(constraint.temporal_window)
                actual_val = self.state_buffer.calculate_average(constraint.entity, win_sec)

            # 3. Existence Check
            if actual_val is None:
                is_missing_required = (constraint.operator == ConstraintOperator.REQUIRED)
                # Strict Mode: If it's not present, it's a violation for any constraint 
                # because we can't verify the logic.
                violation_msg = "Missing required entity" if is_missing_required else f"Signal '{constraint.entity}' not found in proposal"
                violations.append(self._create_violation(constraint, violation_msg))
                deducted_weight += constraint.weight
                results_map[constraint.id] = False
                continue

            # 4. Logic Evaluation
            is_violation = False
            msg = ""

            try:
                if constraint.operator == ConstraintOperator.GT:
                    if not (actual_val > constraint.value):
                        is_violation = True
                        msg = f"Value {actual_val} not greater than {constraint.value}"
                
                elif constraint.operator == ConstraintOperator.LT:
                    if not (actual_val < constraint.value):
                        is_violation = True
                        msg = f"Value {actual_val} not less than {constraint.value}"

                elif constraint.operator == ConstraintOperator.GTE:
                    if not (actual_val >= constraint.value):
                        is_violation = True
                        msg = f"Value {actual_val} not greater than or equal to {constraint.value}"

                elif constraint.operator == ConstraintOperator.LTE:
                    if not (actual_val <= constraint.value):
                        is_violation = True
                        msg = f"Value {actual_val} not less than or equal to {constraint.value}"
                
                elif constraint.operator == ConstraintOperator.EQ:
                    if not (actual_val == constraint.value):
                        is_violation = True
                        msg = f"Value {actual_val} does not equal {constraint.value}"
                
                elif constraint.operator == ConstraintOperator.IN:
                    if actual_val not in constraint.value:
                        is_violation = True
                        msg = f"Value {actual_val} not in allowed set {constraint.value}"
                
                elif constraint.operator == ConstraintOperator.RANGE:
                    if not (constraint.value[0] <= actual_val <= constraint.value[1]):
                        is_violation = True
                        msg = f"Value {actual_val} outside allowed range {constraint.value}"

            except TypeError:
                # Instead of crashing, report as violation
                is_violation = True
                msg = f"Type Mismatch: Expected compatible type for '{constraint.entity}', got {type(actual_val).__name__}"
            except Exception as e:
                raise EvaluationError(f"Unexpected error during symbolic evaluation of {constraint.id}: {str(e)}") from e

            if is_violation:
                violations.append(self._create_violation(constraint, msg))
                deducted_weight += constraint.weight
                results_map[constraint.id] = False
            else:
                passes.append(constraint.id)
                results_map[constraint.id] = True

        # Calculate Logic Health Score (0-100)
        score = max(0.0, 100.0 * (1.0 - (deducted_weight / total_weight))) if total_weight > 0 else 100.0
        
        status = "CERTIFIED" if not violations else "REJECTED"
        return {
            "status": status,
            "violations": violations,
            "passes": passes,
            "score": round(score, 2),
            "un_governed_signals": list(un_governed)
        }

    def _create_violation(self, constraint: ManifestConstraint, msg: str) -> Dict[str, Any]:
        """Creates a violation dictionary for audit logging."""
        return {
            "id": constraint.id,
            "entity": constraint.entity,
            "description": constraint.description,
            "logic_error": msg,
            "severity": constraint.severity,
            "evidence": constraint.evidence_source
        }

    def is_safe(self, violations: List[Dict[str, Any]]) -> bool:
        """Determines if the violations permit a safe action (no CRITICAL/FATAL)."""
        return not any(v["severity"] in ["CRITICAL", "FATAL"] for v in violations)
