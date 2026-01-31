import json

from typer.testing import CliRunner

from lnt_sovereign.cli import app

runner = CliRunner()

def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "LNT" in result.stdout

def test_cli_check_advisory(tmp_path):
    # Create mock manifest and input
    manifest_path = tmp_path / "manifest.json"
    input_path = tmp_path / "input.json"
    
    manifest_data = {
        "domain_id": "TEST_DOMAIN",
        "domain_name": "Test Domain",
        "version": "1.0.0",
        "entities": ["score"],
        "constraints": [
            {
                "id": "T01",
                "entity": "score",
                "operator": "GT",
                "value": 50,
                "description": "Score must be above 50",
                "severity": "TOXIC"
            }
        ]
    }
    
    input_data = {"score": 10} # Should fail T01
    
    manifest_path.write_text(json.dumps(manifest_data))
    input_path.write_text(json.dumps(input_data))
    
    # Run CLI in advisory mode (should exit 0 even with toxic violations)
    result = runner.invoke(app, [
        "check", 
        "--manifest", str(manifest_path), 
        "--input", str(input_path), 
        "--advisory",
        "--fail-on-toxic"
    ])
    
    assert result.exit_code == 0
    assert "REJECTED" in result.stdout
    assert "ADVISORY WARNING" in result.stdout

def test_cli_check_fail_on_toxic(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    input_path = tmp_path / "input.json"
    
    manifest_data = {
        "domain_id": "TEST_DOMAIN",
        "domain_name": "Test Domain",
        "version": "1.0.0",
        "entities": ["score"],
        "constraints": [
            {
                "id": "T01",
                "entity": "score",
                "operator": "GT",
                "value": 50,
                "description": "Score must be above 50",
                "severity": "TOXIC"
            }
        ]
    }
    
    input_data = {"score": 10}
    
    manifest_path.write_text(json.dumps(manifest_data))
    input_path.write_text(json.dumps(input_data))
    
    # Run CLI in fail-on-toxic mode (should exit 1)
    result = runner.invoke(app, [
        "check", 
        "--manifest", str(manifest_path), 
        "--input", str(input_path), 
        "--fail-on-toxic"
    ])
    
    assert result.exit_code == 1
    assert "ENFORCEMENT FAILURE" in result.stdout
    assert "Critical violations detected" in result.stdout

def test_cli_check_fail_under(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    input_path = tmp_path / "input.json"
    
    manifest_data = {
        "domain_id": "TEST_DOMAIN",
        "domain_name": "Test Domain",
        "version": "1.0.0",
        "entities": ["score"],
        "constraints": [{"id": "T01", "entity": "score", "operator": "GT", "value": 50, "description": "Score must be above 50", "severity": "WARNING"}]
    }
    
    input_data = {"score": 40}
    
    manifest_path.write_text(json.dumps(manifest_data))
    input_path.write_text(json.dumps(input_data))
    
    # Should exit 1 because score is 0% (fails the only rule) and threshold is 50%
    result = runner.invoke(app, [
        "check", 
        "--manifest", str(manifest_path), 
        "--input", str(input_path), 
        "--fail-under", "50"
    ])
    
    assert result.exit_code == 1
    assert "below the threshold" in result.stdout
