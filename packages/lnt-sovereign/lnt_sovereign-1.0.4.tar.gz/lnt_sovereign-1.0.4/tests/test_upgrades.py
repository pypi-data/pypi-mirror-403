
from lnt_sovereign.client import LNTClient


def test_sdk_requirements():
    client = LNTClient()
    reqs = client.get_requirements("healthcare_triage")
    
    assert reqs["domain"] == "HEALTHCARE_TRIAGE_V1"
    assert "heart_rate" in reqs["entities"]
    assert len(reqs["constraints"]) > 0
    print("SDK Requirements Test: PASSED")

def test_kernel_flexibility():
    import os

    from lnt_sovereign.core.kernel import KernelEngine
    
    engine = KernelEngine()
    # Path relative to project root
    manifest_path = os.path.join("lnt_sovereign", "manifests", "examples", "healthcare_triage.json")
    engine.load_manifest(manifest_path)
    
    # Proposal with extra fields
    proposal = {
        "heart_rate": 80.0,      # Manifest expects RANGE [40, 150]
        "oxygen_saturation": 98.0, # Manifest expects GT 88
        "glucose_mg_dl": 100.0,  # Manifest expects GT 50
        "age": 45,  # Extra (Un-governed)
        "mood": "happy" # Extra (Un-governed)
    }
    
    result = engine.trace_evaluate(proposal)
    assert result["status"] == "CERTIFIED"
    assert "age" in result["un_governed_signals"]
    assert "mood" in result["un_governed_signals"]
    print("Kernel Flexibility Test: PASSED")

if __name__ == "__main__":
    test_sdk_requirements()
    test_kernel_flexibility()
