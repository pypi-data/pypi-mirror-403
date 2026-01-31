import json
import os
import random
from typing import List

from lnt_sovereign.core.kernel import ConstraintOperator, DomainManifest, ManifestConstraint


class ManifestFactory:
    """
    Generates test manifests with 1,000 rules across diverse domains.
    """
    def __init__(self, output_dir: str = "lnt_sovereign/manifests/mega") -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_domain(self, domain_id: str, domain_name: str, entities: List[str], rule_count: int = 1000) -> None:
        """
        Generates a massive manifest with a mix of simple, weighted, and dependent rules.
        """
        constraints = []
        
        # 1. Base Prerequisite Rules (Level 0)
        base_rules = []
        for i in range(50):
            rid = f"{domain_id}_BASE_{i:03d}"
            target_entity = random.choice(entities) # nosec B311
            constraints.append(ManifestConstraint(
                id=rid,
                entity=target_entity,
                operator=ConstraintOperator.REQUIRED,
                value=None,
                description=f"Base integrity check for {target_entity}",
                severity="IMPOSSIBLE",
                weight=1.0
            ))
            base_rules.append(rid)

        # 2. Complex Dependent Rules (Level 1+)
        for i in range(rule_count - 50):
            rid = f"{domain_id}_RULE_{i:04d}"
            target_entity = random.choice(entities) # nosec B311
            
            # Simple DAG dependency chain
            deps = random.sample(base_rules, random.randint(1, 3)) if random.random() > 0.7 else None # nosec B311
            
            # Random Logic
            op = random.choice([ConstraintOperator.GT, ConstraintOperator.LT, ConstraintOperator.RANGE]) # nosec B311
            val = random.randint(10, 500) if op != ConstraintOperator.RANGE else [10, 1000] # nosec B311
            
            constraints.append(ManifestConstraint(
                id=rid,
                entity=target_entity,
                operator=op,
                value=val,
                description=f"Logical constraint {rid} governing {target_entity}",
                severity=random.choice(["TOXIC", "WARNING", "IMPOSSIBLE"]), # nosec B311
                weight=round(random.uniform(0.1, 0.8), 2), # nosec B311
                conditional_on=deps
            ))

        manifest = DomainManifest(
            domain_id=domain_id,
            domain_name=domain_name,
            version="1.0.0-mega",
            entities=entities,
            constraints=constraints
        )

        path = os.path.join(self.output_dir, f"{domain_id.lower()}.json")
        with open(path, 'w') as f:
            json.dump(manifest.model_dump(), f, indent=4)
        
        print(f"Generated Mega-Manifest: {path} ({len(constraints)} rules)")

if __name__ == "__main__":
    factory = ManifestFactory()
    
    # 4. Energy Grid
    factory.generate_domain(
        "LNT_ENERGY_GRID", 
        "Energy Load Balancing & Grid Manifest", 
        ["load_kw", "freq_hz", "reactive_power", "temp_ambient", "storage_level"]
    )

    # 5. Supply Chain
    factory.generate_domain(
        "LNT_LOGISTICS", 
        "Global Supply Chain Integrity", 
        ["lat", "lon", "temp", "humidity", "shocks", "transit_time_min"]
    )

    # 6. Legal / Contract
    factory.generate_domain(
        "LNT_LEGAL_DAG", 
        "Autonomous Contract Logic Auditor", 
        ["clause_entropy", "liability_cap", "indemnity_depth", "termination_lookahead"]
    )

    # 7. Autonomous Driving
    factory.generate_domain(
        "LNT_DRIVE_CORE", 
        "L3 Autonomous Sensor Fusion Gatekeeper", 
        ["lidar_res", "radar_dist", "camera_confidence", "velocity", "steering_angle"]
    )

    # 8. AGI Safety
    factory.generate_domain(
        "LNT_AGI_GUARD", 
        "Neural-Symbolic Entropy Sentry", 
        ["token_entropy", "semantic_drift", "alignment_score", "prompt_injection_prob"]
    )

    # 9. LNT Reserve
    factory.generate_domain(
        "LNT_CENTRAL_BANK", 
        "Central Bank Macro-Audit Manifest", 
        ["m1_velocity", "inflation_delta", "curr_reserve", "treasury_spread"]
    )

    # 10. Immigration Research
    factory.generate_domain(
        "LNT_IMMIGRATION_PROTOTYPE", 
        "Immigration & Security Manifest Prototype", 
        ["is_terror_watch", "criminal_record", "funding_available", "language_clb", "years_exp"]
    )
