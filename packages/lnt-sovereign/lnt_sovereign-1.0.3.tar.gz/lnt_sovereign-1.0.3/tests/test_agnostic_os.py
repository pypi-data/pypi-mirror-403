import pytest
from lnt_sovereign.core.topology import SynthesisManifold

@pytest.fixture
def manifold():
    return SynthesisManifold()

def test_healthcare_triage_agnostic(manifold):
    """Verify that the Agnostic Kernel handles Healthcare Triage via manifest."""
    user_input = "Patient status. hr: 110. spo2: 82. bp: 120/80. REJECTED."
    result = manifold.process_application(user_input)
    assert result["domain"] == "HEALTHCARE_TRIAGE_V1"
    assert result["status"] == "REJECTED_BY_SOVEREIGN_LOGIC"

def test_visa_application_agnostic(manifold):
    """Verify that the Agnostic Kernel handles Visa Applications via manifest."""
    # Low funding case
    user_input = "Visa application. Rejected Case."
    result = manifold.process_application(user_input)
    assert result["domain"] == "VISA_APPLICATION_V1"
    assert result["status"] == "REJECTED_BY_SOVEREIGN_LOGIC"

def test_crs_profile_agnostic(manifold):
    """Verify that the Agnostic Kernel handles CRS Audits via manifest."""
    user_input = "Express Entry crs profile. rejected."
    result = manifold.process_application(user_input)
    assert result["domain"] == "CRS_PROFILE_V1"
    assert result["status"] == "REJECTED_BY_SOVEREIGN_LOGIC"

def test_healthy_pass_agnostic(manifold):
    """Verify successful certification across domains."""
    # Healthcare Pass
    health_input = "Healthy patient. hr: 72. spo2: 99."
    health_res = manifold.process_application(health_input)
    assert health_res["status"] == "CERTIFIED"

    # Visa Pass
    visa_input = "Visa. passport: true. funding: 50000. clb: 9."
    visa_res = manifold.process_application(visa_input)
    assert visa_res["status"] == "CERTIFIED"
