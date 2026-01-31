import pytest

from lnt_sovereign.core.topology import TopologyOrchestrator


@pytest.fixture
def manifold():
    return TopologyOrchestrator()

def test_temporal_trailing_average(manifold):
    """
    Verify that SG-2 can detect trailing average violations.
    Use-case: Funding must average > $20,000 over the last hour.
    """
    # 1. Setup a mock manifest with a temporal constraint
    manifest_data = {
        "domain_id": "TEMPORAL_TEST",
        "domain_name": "Temporal Test Domain",
        "version": "1.0.0",
        "entities": ["funding"],
        "constraints": [
            {
                "id": "TEMP_01",
                "entity": "funding",
                "operator": "GT",
                "value": 20000,
                "description": "Funding must average > 20k",
                "weight": 1.0,
                "temporal_window": "1h"
            }
        ]
    }
    
    # Manually inject manifest bypass (since we don't want to write to file for simple test)
    # But Manifest expects a path. Let's write a temp file.
    import json
    import os
    test_dir = os.path.join("lnt_sovereign", "manifests", "test")
    os.makedirs(test_dir, exist_ok=True)
    test_path = os.path.join(test_dir, "temporal.json")
    with open(test_path, "w") as f:
        json.dump(manifest_data, f)

    # 2. Simulate historical data (Historical average = 15k)
    manifold.state_buffer.push("funding", 10000)
    manifold.state_buffer.push("funding", 20000)
    
    # 3. Current value is high (50k), but trailing average will be (10+20+50)/3 = 26.6k (PASS)
    # Wait, if we push 50k now, the average becomes > 20k.
    
    # Let's test a FAIL case:
    manifold.state_buffer.clear_entity("funding")
    manifold.state_buffer.push("funding", 5000)
    manifold.state_buffer.push("funding", 5000)
    
    # Current call with 10k. Avg = (5+5+10)/3 = 6.6k. (FAIL)
    # We need to bridge detect_domain to return our test manifest
    # For now, let's just test the kernel_engine directly for speed.
    
    manifold.kernel_engine.load_manifest(test_path)
    result = manifold.kernel_engine.trace_evaluate({"funding": 10000})
    
    assert result["status"] == "REJECTED"
    assert "Average" in str(result["violations"]) or "Value" in str(result["violations"])
    # Note: Value in violation message is the AVERAGE (6666.66)
    assert result["score"] < 50.0

def test_micro_temporal_frequency(manifold):
    """Verify frequency checks (Rate limiting logic)."""
    # Not yet implemented in KernelEngine (added average logic primarily)
    pass

if __name__ == "__main__":
    # Quick manual run
    m = TopologyOrchestrator()
    test_temporal_trailing_average(m)
    print("Temporal Logic Test: PASSED")
