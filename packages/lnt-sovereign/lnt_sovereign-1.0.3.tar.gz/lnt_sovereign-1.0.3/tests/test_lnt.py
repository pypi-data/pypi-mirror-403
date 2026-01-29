from lnt_sovereign.core.kernel import KernelEngine

def test_kernel_healthcare_pass():
    """Test that valid vitals pass healthcare triage"""
    engine = KernelEngine("lnt_sovereign/manifests/examples/healthcare_triage.json")
    
    proposal = {
        "heart_rate": 75,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "oxygen_saturation": 98,
        "glucose_mg_dl": 100
    }
    
    violations = engine.evaluate(proposal)
    assert len(violations) == 0, "Valid vitals should have no violations"

def test_kernel_healthcare_fail():
    """Test that critical vitals are rejected"""
    engine = KernelEngine("lnt_sovereign/manifests/examples/healthcare_triage.json")
    
    proposal = {
        "heart_rate": 200,  # Dangerously high
        "blood_pressure_systolic": 90,
        "blood_pressure_diastolic": 60,
        "oxygen_saturation": 85,  # Too low
        "glucose_mg_dl": 100
    }
    
    violations = engine.evaluate(proposal)
    assert len(violations) > 0, "Critical vitals should trigger violations"
    assert any("heart_rate" in v["entity"] for v in violations)

def test_kernel_visa_pass():
    """Test that valid visa application passes"""
    engine = KernelEngine("lnt_sovereign/manifests/examples/visa_application.json")
    
    proposal = {
        "has_valid_passport": True,
        "funding_available": 25000,
        "language_proficiency": 8,
        "has_business_commitment": True
    }
    
    violations = engine.evaluate(proposal)
    assert len(violations) == 0, "Valid visa application should pass"

def test_kernel_visa_fail_funding():
    """Test that insufficient funding is rejected"""
    engine = KernelEngine("lnt_sovereign/manifests/examples/visa_application.json")
    
    proposal = {
        "has_valid_passport": True,
        "funding_available": 500,  # Too low
        "language_proficiency": 8,
        "has_business_commitment": True
    }
    
    violations = engine.evaluate(proposal)
    assert len(violations) > 0, "Low funding should trigger violation"
    assert any("funding" in v["entity"] for v in violations)
