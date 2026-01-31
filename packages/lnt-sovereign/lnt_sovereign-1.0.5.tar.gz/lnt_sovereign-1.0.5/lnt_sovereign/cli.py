import json
import os
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lnt_sovereign.core.formal import FormalVerifier
from lnt_sovereign.core.kernel import KernelEngine
from lnt_sovereign.core.telemetry import TelemetryManager

app = typer.Typer(
    help="LNT: Logic Neutrality Tool - Experimental Neuro-Symbolic Validation",
    rich_markup_mode="rich"
)
console = Console()

def print_suggestion(message: str, command: Optional[str] = None) -> None:
    """Prints a pretty suggestion for the user."""
    markup = f"\n[bold cyan]💡 Suggestion:[/bold cyan] {message}"
    if command:
        markup += f"\n   [dim]Try running:[/dim] [bold white]{command}[/bold white]"
    
    console.print(Panel(Text.from_markup(markup), border_style="cyan"))

@app.command()
def doctor() -> None:
    """
    Check the health of your LNT environment and dependencies.
    """
    console.print(Panel("[bold cyan]LNT Environment Health Check[/bold cyan]", border_style="cyan"))
    
    checks = []
    
    # 1. Python Version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python Version", py_version, sys.version_info.major >= 3 and sys.version_info.minor >= 10))
    
    # 2. Z3 Solver
    try:
        import z3
        checks.append(("Z3 SMT Solver", f"Installed ({z3.get_version_string()})", True))
    except ImportError:
        checks.append(("Z3 SMT Solver", "Not Found", False))
        
    # 3. NumPy
    try:
        import numpy as np
        checks.append(("NumPy (BELM Core)", f"Installed ({np.__version__})", True))
    except ImportError:
        checks.append(("NumPy (BELM Core)", "Not Found", False))

    # 4. Workspace
    manifests_exist = os.path.exists("manifests")
    checks.append(("Local Workspace", "Initialized" if manifests_exist else "Empty", manifests_exist))

    table = Table(box=None)
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Health", justify="center")

    all_pass = True
    for component, status, passed in checks:
        icon = "[green]✔[/green]" if passed else "[red]✘[/red]"
        table.add_row(component, status, icon)
        if not passed:
            all_pass = False

    console.print(table)
    
    if all_pass:
        console.print("\n[bold green]✔ Environment check successful.[/bold green]")
    else:
        console.print("\n[bold red]✘ Some checks failed.[/bold red]")
        if not any(c[0] == "Z3 SMT Solver" and c[2] for c in checks):
            print_suggestion("Z3 is missing. Mathematical verification will fail.", "pip install z3-solver")
        if not manifests_exist:
            print_suggestion("No manifests found. Start by creating one.", "lnt init")

@app.command()
def init(
    name: str = typer.Option(None, "--name", help="Name of the domain"),
    output: str = typer.Option("manifests/my_domain.json", "--output", "-o", help="Where to save the manifest")
) -> None:
    """
    Interactive wizard to create a new logic manifest.
    """
    console.print(Panel("[bold cyan]LNT Manifest Wizard[/bold cyan]", border_style="cyan"))
    
    if not name:
        name = typer.prompt("What is the name of your AI Domain? (e.g. Healthcare Triage)")
    
    domain_id = name.upper().replace(" ", "_")
    entities_input = typer.prompt("Enter the entities/signals you want to track (comma-separated, e.g. age, income, is_human)")
    entities = [e.strip() for e in entities_input.split(",") if e.strip()]
    
    if not entities:
        console.print("[bold red]Error:[/bold red] You must provide at least one entity.")
        raise typer.Abort()

    console.print(f"\n[dim]Creating basic manifold for {domain_id}...[/dim]")
    
    # Create a template manifest
    manifest = {
        "domain_id": domain_id,
        "domain_name": name,
        "version": "1.0.0",
        "entities": entities,
        "constraints": [
            {
                "id": f"RULE_{entities[0].upper()}_BASIC",
                "entity": entities[0],
                "operator": "GT",
                "value": 0,
                "description": f"Basic safety check for {entities[0]}",
                "severity": "WARNING",
                "weight": 1.0
            }
        ]
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    with open(output, 'w') as f:
        json.dump(manifest, f, indent=4)
        
    console.print(f"\n[bold green]✔ Manifest created at {output}[/bold green]")
    print_suggestion("Verify your logic before running audits.", f"lnt verify --manifest {output}")

@app.command()
def check(
    manifest: str = typer.Option(..., "--manifest", "-m", help="Path to the logic manifest JSON"),
    input_file: str = typer.Option(..., "--input", "-i", help="Path to the input proposal JSON"),
    fail_under: float = typer.Option(0.0, "--fail-under", help="Exit with code 1 if score is below this threshold"),
    fail_on_toxic: bool = typer.Option(False, "--fail-on-toxic", help="Exit with code 1 if any TOXIC violation occurs"),
    advisory: bool = typer.Option(False, "--advisory", help="Soft governance mode: always exit with code 0"),
    json_report: Optional[str] = typer.Option(None, "--json-report", help="Path to export the full machine-readable audit report"),
    no_telemetry: bool = typer.Option(False, "--no-telemetry", help="Opt-out of telemetry for this run")
) -> None:
    """
    Evaluate an AI proposal against a symbolic logic manifest.
    """
    start_time = time.perf_counter()
    telemetry = TelemetryManager()
    if no_telemetry:
        telemetry.opt_out = True

    if not os.path.exists(manifest):
        console.print(f"[bold red]Error:[/bold red] Manifest file '{manifest}' not found.")
        print_suggestion("Create a manifest first or check the path.", "lnt init")
        raise typer.Exit(code=1)
    
    if not os.path.exists(input_file):
        console.print(f"[bold red]Error:[/bold red] Input file '{input_file}' not found.")
        print_suggestion("Generate a valid sample for this manifest to get started.", f"lnt solve --manifest {manifest} --output proposal.json")
        raise typer.Exit(code=1)

    try:
        with open(input_file, 'r') as f:
            proposal = json.load(f)
    except Exception as e:
        console.print(Panel(f"[bold red]JSON Parse Error:[/bold red]\n{str(e)}", title="Input Failure", border_style="red"))
        print_suggestion("Ensure your input file is a valid JSON dictionary.")
        raise typer.Exit(code=1)

    # Initialize Engine
    engine = KernelEngine()
    try:
        engine.load_manifest(manifest)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to load manifest: {str(e)}")
        print_suggestion("Your manifest might have internal logical contradictions.", f"lnt verify --manifest {manifest}")
        raise typer.Exit(code=1)

    # Run Audit
    results = engine.trace_evaluate(proposal)
    score = results["score"]
    violations = results["violations"]
    status = results["status"]

    # --- UI Reporting ---
    domain_id = "UNKNOWN"
    domain_name = "UNKNOWN"
    domain_version = "UNKNOWN"
    
    if engine.manifest:
        domain_id = engine.manifest.domain_id
        domain_name = engine.manifest.domain_name
        domain_version = engine.manifest.version

    console.print(Panel(
        f"[bold blue]Domain:[/bold blue] {domain_name} ({domain_id})\n"
        f"[bold blue]Version:[/bold blue] {domain_version}\n"
        f"[bold blue]Status:[/bold blue] {status}",
        title="LNT Audit Summary",
        border_style="cyan"
    ))

    table = Table(title="Validation Breakdown", border_style="bright_blue")
    table.add_column("Rule ID", style="dim")
    table.add_column("Violation", style="bold")
    table.add_column("Severity", justify="center")
    
    for v in violations:
        severity_style = "red" if v["severity"] in ["TOXIC", "IMPOSSIBLE"] else "yellow"
        table.add_row(
            v["id"],
            v["description"],
            Text(v["severity"], style=severity_style)
        )

    if violations:
        console.print(table)
    else:
        console.print("[bold green]✔ All symbolic constraints satisfied. No violations found.[/bold green]")

    score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
    console.print(f"\n[bold]Logic Health Score:[/bold] [{score_color}]{score}%[/{score_color}]")

    # --- Enforcement Logic ---
    reasons = []
    
    # Calculate potential failures
    if fail_on_toxic:
        has_toxic = any(v["severity"] in ["TOXIC", "IMPOSSIBLE"] for v in violations)
        if has_toxic:
            reasons.append("Critical violations detected in --fail-on-toxic mode.")

    if score < fail_under:
        reasons.append(f"Score {score}% is below the threshold of {fail_under}%.")

    exit_code = 0
    if not advisory and reasons:
        exit_code = 1

    # --- Export Report ---
    if json_report:
        try:
            with open(json_report, 'w') as f:
                json.dump(results, f, indent=4)
            console.print(f"[dim]Audit report exported to {json_report}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Warning:[/bold red] Could not export report: {str(e)}")

    if exit_code != 0:
        console.print("\n[bold red]✖ ENFORCEMENT FAILURE:[/bold red]")
        for r in reasons:
            console.print(f"  - {r}")
        
        if status == "REJECTED_TOXIC":
            print_suggestion("Toxic violations detected. This proposal is legally unsafe.")
        elif score < fail_under:
            print_suggestion("The score is too low. Refine your proposal to meet the threshold.")
            
        raise typer.Exit(code=exit_code)
    else:
        if reasons and advisory:
            console.print("\n[bold yellow]⚠ ADVISORY WARNING (Bypassed):[/bold yellow]")
            for r in reasons:
                console.print(f"  - {r}")
        console.print("\n[bold green]✔ Compliance Validation Successful.[/bold green]")
    
    # Log Telemetry
    latency = (time.perf_counter() - start_time) * 1000
    telemetry.log_event(
        command="check",
        success=exit_code == 0,
        latency_ms=latency,
        error_type="ENFORCEMENT_FAILURE" if exit_code != 0 else None,
        metadata={"score": score, "domain": domain_id}
    )

@app.command()
def verify(
    manifest: str = typer.Option(..., "--manifest", "-m", help="Path to the logic manifest JSON"),
    dead_code: bool = typer.Option(True, "--dead-code", help="Perform dead code detection"),
    no_telemetry: bool = typer.Option(False, "--no-telemetry", help="Opt-out of telemetry for this run")
) -> None:
    """
    Prove the mathematical integrity of a manifest.
    """
    start_time = time.perf_counter()
    telemetry = TelemetryManager()
    if no_telemetry:
        telemetry.opt_out = True
        
    if not os.path.exists(manifest):
        console.print(f"[bold red]Error:[/bold red] Manifest file '{manifest}' not found.")
        print_suggestion("Check the file path or create a new manifest.", "lnt init")
        raise typer.Exit(code=1)

    with open(manifest, 'r') as f:
        data = json.load(f)
    
    verifier = FormalVerifier()
    console.print(Panel(f"[bold cyan]Formal Verification: {data.get('domain_id', 'Unknown')}[/bold cyan]", border_style="cyan"))
    
    # 1. Consistency
    with console.status("[bold blue]Proving consistency...[/bold blue]"):
        consistent, error = verifier.verify_consistency(data)
    
    if consistent:
        console.print("[green]✔ Logic is consistent (No internal paradoxes).[/green]")
    else:
        console.print(f"[red]✘ Logic contradiction detected:[/red] {error}")
        print_suggestion("A rule contradicts another. Review your constraints.")
        raise typer.Exit(code=1)

    # 2. Satisfiability
    with console.status("[bold blue]Checking satisfiability...[/bold blue]"):
        satisfiable, example = verifier.verify_satisfiable(data)
    
    if satisfiable:
        console.print("[green]✔ Logic is satisfiable (At least one valid input exists).[/green]")
    else:
        console.print("[red]✘ Logic is impossible (No input can satisfy these rules).[/red]")
        print_suggestion("Your constraints have created a total deadlock.")
        raise typer.Exit(code=1)

    # 3. Dead Code
    if dead_code:
        with console.status("[bold blue]Scanning for dead code...[/bold blue]"):
            dead_rules = verifier.detect_dead_code(data)
        
        if not dead_rules:
            console.print("[green]✔ No dead code detected (All rules reachable).[/green]")
        else:
            console.print(f"[yellow]⚠ Detected {len(dead_rules)} unreachable rules:[/yellow]")
            for rid in dead_rules:
                console.print(f"  - [dim]{rid}[/dim]")
            print_suggestion("Dead rules are triggered by prerequisites that make their own logic impossible.")

    console.print("\n[bold green]✔ Manifest consistency check passed.[/bold green]")
    
    # Log Telemetry
    latency = (time.perf_counter() - start_time) * 1000
    telemetry.log_event(
        command="verify",
        success=True,
        latency_ms=latency,
        metadata={"dead_code_scan": dead_code}
    )

@app.command()
def version() -> None:
    """Display LNT Engine Version info."""
    console.print(Panel(
        "[bold cyan]LNT (Logic Neutrality Tool)[/bold cyan] [white]v1.1.0-alpha[/white]\n"
        "[dim]Experimental Neuro-Symbolic Validation Prototype[/dim]\n\n"
        "Engine: [bold blue]Vectorized Logic Kernel[/bold blue]\n"
        "Verification: [bold green]Z3 SMT Check (Experimental)[/bold green]\n"
        "Status: [bold yellow]Alpha / Research Prototype[/bold yellow]",
        border_style="cyan",
        title="Software version"
    ))

# Telemetry Command Group
telemetry_app = typer.Typer(help="Manage LNT Telemetry & Opt-Out settings")
app.add_typer(telemetry_app, name="telemetry")

@telemetry_app.command("status")
def telemetry_status() -> None:
    """Show current telemetry usage and opt-out status."""
    manager = TelemetryManager()
    status = "[red]Opted-Out[/red]" if manager.opt_out else "[green]Active (Anonymous Improvement)[/green]"
    console.print(Panel(
        f"Remote Telemetry: {status}\n"
        f"Local Database: [blue]{manager.db_path}[/blue]\n"
        f"Environment: [dim]LNT_NO_TELEMETRY={os.getenv('LNT_NO_TELEMETRY', '0')}[/dim]",
        title="Telemetry Status",
        border_style="cyan"
    ))

@telemetry_app.command("list")
def telemetry_list(limit: int = typer.Option(10, "--limit", help="Number of entries to show")) -> None:
    """List recent local telemetry events."""
    manager = TelemetryManager()
    stats = manager.get_local_stats()
    
    if not stats:
        console.print("[dim]No telemetry data found.[/dim]")
        return
        
    table = Table(title="Recent Activity (Local-First)")
    table.add_column("Timestamp", style="dim")
    table.add_column("Command", style="bold")
    table.add_column("Success")
    table.add_column("Latency (ms)", justify="right")
    
    for s in stats[:limit]:
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s['timestamp']))
        success = "[green]YES[/green]" if s['success'] else "[red]NO[/red]"
        table.add_row(ts, s['command'], success, f"{s['latency_ms']:.2f}")
        
    console.print(table)

@telemetry_app.command("clear")
def telemetry_clear() -> None:
    """Purge all local telemetry data."""
    if typer.confirm("Are you sure you want to delete all local telemetry history?"):
        TelemetryManager().clear_local_stats()
        console.print("[bold green]✔ Local telemetry database purged.[/bold green]")

if __name__ == "__main__":
    app()
