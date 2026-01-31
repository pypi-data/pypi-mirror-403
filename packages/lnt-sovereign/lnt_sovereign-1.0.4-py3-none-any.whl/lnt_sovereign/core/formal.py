"""
POC 1: Formal Verification Engine
The Correctness Moat - Mathematical proofs for manifest validity

Uses Z3 SMT solver to:
1. Prove manifests have no internal contradictions
2. Prove constraints are satisfiable (at least one valid input exists)
3. Generate counterexamples when constraints are impossible
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from z3 import And, Bool, Int, Not, Or, Real, Solver, sat, unsat


class FormalVerifier:
    """
    Formal verification engine using Z3 SMT solver.
    Provides mathematical guarantees about manifest correctness.
    """
    
    def __init__(self, timeout_ms: int = 10000) -> None:
        self.solver = Solver()
        self.solver.set("timeout", timeout_ms)
        self.variables: Dict[str, Any] = {}
    
    def _create_variable(self, entity: str, var_type: str = "real") -> Any:
        """Create a Z3 variable for an entity."""
        if entity not in self.variables:
            if var_type == "int":
                self.variables[entity] = Int(entity)
            elif var_type == "bool":
                self.variables[entity] = Bool(entity)
            else:
                self.variables[entity] = Real(entity)
        return self.variables[entity]
    
    def _constraint_to_z3(self, constraint: Dict[str, Any]) -> Any:
        """Convert a manifest constraint to Z3 formula."""
        entity = constraint["entity"]
        operator = constraint["operator"]
        value = constraint["value"]
        
        # Determine variable type from operator/value
        if operator == "REQUIRED":
            var = self._create_variable(entity, "bool")
            return var
        elif operator == "EQ" and isinstance(value, bool):
            var = self._create_variable(entity, "bool")
            return var == value
        elif operator == "EQ" and isinstance(value, str):
            # For string equality, use deterministic SHA256 hashing
            var = self._create_variable(entity, "int")
            # Convert hash to int for Z3
            hash_int = int(hashlib.sha256(value.encode()).hexdigest(), 16) % 10**8
            return var == hash_int
        elif operator == "IN" and isinstance(value, list):
            var = self._create_variable(entity, "int")
            z3_values = []
            for v in value:
                if isinstance(v, str):
                    z3_v = int(hashlib.sha256(v.encode()).hexdigest(), 16) % 10**8
                else:
                    z3_v = v
                z3_values.append(var == z3_v)
            return Or(z3_values)
        else:
            # Numeric constraints
            var = self._create_variable(entity, "real")
            
            if operator == "GT":
                return var > value
            elif operator == "LT":
                return var < value
            elif operator == "EQ":
                return var == value
            elif operator == "GTE":
                return var >= value
            elif operator == "LTE":
                return var <= value
            elif operator == "RANGE":
                # value should be [min, max]
                return And(var >= value[0], var <= value[1])
            else:
                raise ValueError(f"Unknown operator: {operator}")
    
    def verify_consistency(self, manifest: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Prove that a manifest has no internal contradictions.
        
        Returns:
            (True, None) if manifest is consistent
            (False, explanation) if contradiction found
        """
        self.solver.reset()
        self.variables = {}
        
        constraints = manifest.get("constraints", [])
        
        # Add all constraints to solver
        # For conditional rules: Prerequisite => Constraint
        id_to_z3 = {}
        constraints = manifest.get("constraints", [])
        
        # First pass: map IDs and add non-conditional rules
        for c in constraints:
            try:
                z3_c = self._constraint_to_z3(c)
                id_to_z3[c["id"]] = z3_c
            except Exception as e:
                return False, f"Failed to parse constraint {c['id']}: {e}"
                
        # Second pass: Apply implications
        for c in constraints:
            z3_c = id_to_z3[c["id"]]
            if c.get("conditional_on"):
                # If all prerequisites pass, then this rule must also pass
                prereqs = [id_to_z3[pid] for pid in c["conditional_on"] if pid in id_to_z3]
                if prereqs:
                    # Implication: And(prereqs) => z3_c
                    # In Z3: Implies(And(prereqs), z3_c)
                    from z3 import Implies
                    self.solver.add(Implies(And(prereqs), z3_c))
                else:
                    self.solver.add(z3_c)
            else:
                self.solver.add(z3_c)
        
        # Check satisfiability
        result = self.solver.check()
        
        if result == sat:
            return True, None
        elif result == unsat:
            return False, "Manifest contains contradictory constraints (unsatisfiable logic path)"
        else:
            return False, "Could not determine satisfiability (timeout or unknown)"
    
    def verify_satisfiable(self, manifest: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Prove that at least one valid input exists for this manifest.
        
        Returns:
            (True, example_input) if satisfiable
            (False, None) if no valid input exists
        """
        self.solver.reset()
        self.variables = {}
        
        constraints = manifest.get("constraints", [])
        
        for c in constraints:
            try:
                z3_constraint = self._constraint_to_z3(c)
                self.solver.add(z3_constraint)
            except Exception:  # nosec B112  # noqa: S112
                continue
        
        result = self.solver.check()
        
        if result == sat:
            model = self.solver.model()
            example = {}
            for entity, var in self.variables.items():
                val = model.evaluate(var, model_completion=True)
                # Convert Z3 value to Python
                if hasattr(val, 'as_long') and val.is_int():
                    example[entity] = val.as_long()
                elif hasattr(val, 'as_decimal'):
                    example[entity] = float(val.as_decimal(10).replace("?", ""))
                elif hasattr(val, 'is_true'):
                    example[entity] = val.is_true()
                else:
                    try:
                        # Fallback for RatNum or other numeric types
                        example[entity] = float(val.as_fraction().numerator) / float(val.as_fraction().denominator)
                    except Exception:
                        example[entity] = str(val)
            return True, example
        else:
            return False, None
    
    def find_counterexample(
        self, 
        manifest: Dict[str, Any], 
        safety_property: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Find an input that satisfies all constraints but violates a safety property.
        
        Args:
            manifest: The manifest to check
            safety_property: A constraint that should ALWAYS hold (e.g., "age > 0")
            
        Returns:
            (True, counterexample) if safety can be violated
            (False, None) if safety always holds
        """
        self.solver.reset()
        self.variables = {}
        
        constraints = manifest.get("constraints", [])
        
        # Add all manifest constraints
        for c in constraints:
            try:
                z3_constraint = self._constraint_to_z3(c)
                self.solver.add(z3_constraint)
            except Exception:  # noqa: S112
                continue
        
        # Add NEGATION of safety property
        # Parse simple safety property format: "entity op value"
        parts = safety_property.split()
        if len(parts) == 3:
            entity, op, value = parts
            var = self._create_variable(entity, "real")
            val = float(value)
            
            if op == ">":
                self.solver.add(Not(var > val))
            elif op == "<":
                self.solver.add(Not(var < val))
            elif op == ">=":
                self.solver.add(Not(var >= val))
            elif op == "<=":
                self.solver.add(Not(var <= val))
            elif op == "==":
                self.solver.add(Not(var == val))
        
        result = self.solver.check()
        
        if result == sat:
            model = self.solver.model()
            counterexample = {}
            for entity, var in self.variables.items():
                val = model.evaluate(var, model_completion=True)
                if hasattr(val, 'as_long'):
                    counterexample[entity] = val.as_long()
                elif hasattr(val, 'as_decimal'):
                    counterexample[entity] = float(val.as_decimal(10))
                else:
                    counterexample[entity] = str(val)
            return True, counterexample
        else:
            return False, None
    
    def detect_dead_code(self, manifest: Dict[str, Any]) -> List[str]:
        """
        Identify rules that can NEVER be met because their prerequisites 
        and their own logic are mutually exclusive.
        
        Returns:
            List of rule IDs that are dead code.
        """
        dead_rules = []
        id_to_z3 = {}
        constraints = manifest.get("constraints", [])
        
        # Build Z3 map
        for c in constraints:
            id_to_z3[c["id"]] = self._constraint_to_z3(c)
            
        for c in constraints:
            self.solver.reset()
            rule_z3 = id_to_z3[c["id"]]
            prereqs = [id_to_z3[pid] for pid in c.get("conditional_on", []) if pid in id_to_z3]
            
            # Check if (Prerequisites AND Rule) is SAT
            if prereqs:
                self.solver.add(And(prereqs))
            self.solver.add(rule_z3)
            
            if self.solver.check() == unsat:
                dead_rules.append(c["id"])
                
        return dead_rules


def verify_manifest_file(filepath: str) -> Dict[str, Any]:
    """
    Verify a manifest file and return a formal verification report.
    """
    with open(filepath, 'r') as f:
        manifest = json.load(f)
    
    verifier = FormalVerifier()
    
    report = {
        "manifest": filepath,
        "domain": manifest.get("domain_id", "UNKNOWN"),
        "constraints_count": len(manifest.get("constraints", [])),
        "verification_results": {}
    }
    
    # Check consistency
    consistent, error = verifier.verify_consistency(manifest)
    report["verification_results"]["consistent"] = consistent
    if error:
        report["verification_results"]["consistency_error"] = error
    
    # Check satisfiability
    satisfiable, example = verifier.verify_satisfiable(manifest)
    report["verification_results"]["satisfiable"] = satisfiable
    if example:
        report["verification_results"]["example_valid_input"] = example
    
    # Overall verdict
    report["verified"] = consistent and satisfiable
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "lnt_sovereign/manifests/examples/healthcare_triage.json"
    
    print(f"Verifying manifest: {filepath}")
    print("-" * 50)
    
    report = verify_manifest_file(filepath)
    
    print(f"Domain: {report['domain']}")
    print(f"Constraints: {report['constraints_count']}")
    print(f"Consistent: {report['verification_results']['consistent']}")
    print(f"Satisfiable: {report['verification_results']['satisfiable']}")
    
    if report['verification_results'].get('example_valid_input'):
        print(f"Example valid input: {report['verification_results']['example_valid_input']}")
    
    print("-" * 50)
    print(f"VERIFIED: {report['verified']}")
