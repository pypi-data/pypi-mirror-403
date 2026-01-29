"""
POC 1: Formal Verification Engine
The Correctness Moat - Mathematical proofs for manifest validity

Uses Z3 SMT solver to:
1. Prove manifests have no internal contradictions
2. Prove constraints are satisfiable (at least one valid input exists)
3. Generate counterexamples when constraints are impossible
"""

from z3 import (
    Solver, Int, Real, Bool, And, Or, Not, sat, unsat
)
from typing import Dict, Any, Tuple, Optional
import json


class FormalVerifier:
    """
    Formal verification engine using Z3 SMT solver.
    Provides mathematical guarantees about manifest correctness.
    """
    
    def __init__(self) -> None:
        self.solver = Solver()
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
            # For string equality, we can't directly model in Z3
            # Use integer encoding as proxy
            var = self._create_variable(entity, "int")
            return var == hash(value) % 1000000
        elif operator == "IN" and isinstance(value, list):
            var = self._create_variable(entity, "int")
            return Or([var == (hash(v) % 1000000 if isinstance(v, str) else v) for v in value])
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
        z3_constraints = []
        for c in constraints:
            try:
                z3_constraint = self._constraint_to_z3(c)
                z3_constraints.append(z3_constraint)
                self.solver.add(z3_constraint)
            except Exception as e:
                return False, f"Failed to parse constraint {c['id']}: {e}"
        
        # Check satisfiability
        result = self.solver.check()
        
        if result == sat:
            return True, None
        elif result == unsat:
            # Get unsatisfiable core if possible
            return False, "Manifest contains contradictory constraints (unsatisfiable)"
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
            except Exception: # nosec B112
                continue
        
        result = self.solver.check()
        
        if result == sat:
            model = self.solver.model()
            example = {}
            for entity, var in self.variables.items():
                val = model.evaluate(var, model_completion=True)
                # Convert Z3 value to Python
                if hasattr(val, 'as_long'):
                    example[entity] = val.as_long()
                elif hasattr(val, 'as_decimal'):
                    example[entity] = float(val.as_decimal(10))
                elif hasattr(val, 'is_true'):
                    example[entity] = val.is_true()
                else:
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
            except Exception: # nosec B112
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
    
    def prove_implication(
        self,
        manifest: Dict[str, Any],
        given: Dict[str, Any],
        prove: str
    ) -> bool:
        """
        Prove that if `given` conditions hold for a valid input,
        then `prove` must also hold.
        
        Example: prove_implication(manifest, {"age": "> 65"}, "priority > 5")
        """
        self.solver.reset()
        self.variables = {}
        
        constraints = manifest.get("constraints", [])
        
        # Add manifest constraints
        for c in constraints:
            try:
                z3_constraint = self._constraint_to_z3(c)
                self.solver.add(z3_constraint)
            except Exception: # nosec B112
                continue
        
        # Add given conditions
        for entity, condition in given.items():
            parts = condition.split()
            if len(parts) == 2:
                op, value = parts
                var = self._create_variable(entity, "real")
                val = float(value)
                
                if op == ">":
                    self.solver.add(var > val)
                elif op == "<":
                    self.solver.add(var < val)
        
        # Add negation of what we want to prove
        parts = prove.split()
        if len(parts) == 3:
            entity, op, value = parts
            var = self._create_variable(entity, "real")
            val = float(value)
            
            if op == ">":
                self.solver.add(Not(var > val))
            elif op == "<":
                self.solver.add(Not(var < val))
        
        # If UNSAT, the implication holds
        result = self.solver.check()
        is_unsat: bool = result == unsat
        return is_unsat


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
