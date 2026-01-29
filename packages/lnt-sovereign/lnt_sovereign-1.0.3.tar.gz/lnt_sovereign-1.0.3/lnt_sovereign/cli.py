import typer
import json
import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from lnt_sovereign.core.kernel import KernelEngine

app = typer.Typer(help="LNT: Logic Neutrality Tensor - Symbolic Verification for AI Foundations")
console = Console()

@app.command()
def check(
    manifest: str = typer.Option(..., "--manifest", "-m", help="Path to the logic manifest JSON"),
    input_file: str = typer.Option(..., "--input", "-i", help="Path to the input proposal JSON"),
    fail_under: float = typer.Option(0.0, "--fail-under", help="Exit with code 1 if score is below this threshold"),
    fail_on_toxic: bool = typer.Option(False, "--fail-on-toxic", help="Exit with code 1 if any TOXIC violation occurs"),
    advisory: bool = typer.Option(False, "--advisory", help="Soft governance mode: always exit with code 0"),
    json_report: Optional[str] = typer.Option(None, "--json-report", help="Path to export the full machine-readable audit report")
) -> None:
    """
    Evaluate an AI proposal against a symbolic logic manifest.
    """
    if not os.path.exists(manifest):
        console.print(f"[bold red]Error:[/bold red] Manifest file '{manifest}' not found.")
        raise typer.Exit(code=1)
    
    if not os.path.exists(input_file):
        console.print(f"[bold red]Error:[/bold red] Input file '{input_file}' not found.")
        raise typer.Exit(code=1)

    try:
        with open(input_file, 'r') as f:
            proposal = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to parse input JSON: {str(e)}")
        raise typer.Exit(code=1)

    # Initialize Engine
    engine = KernelEngine()
    try:
        engine.load_manifest(manifest)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to load manifest: {str(e)}")
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
        title="LNT Sovereign Audit Summary",
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
    console.print(f"\n[bold]Sovereign Manifold Score:[/bold] [{score_color}]{score}%[/{score_color}]")

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
        raise typer.Exit(code=exit_code)
    else:
        if reasons and advisory:
            console.print("\n[bold yellow]⚠ ADVISORY WARNING (Bypassed):[/bold yellow]")
            for r in reasons:
                console.print(f"  - {r}")
        console.print("\n[bold green]✔ Compliance Validation Successful.[/bold green]")

@app.command()
def version() -> None:
    """Display LNT Engine Version info."""
    console.print("LNT Sovereign [bold cyan]v1.0.3[/bold cyan]")
    console.print("Core Technology: BELM (Bit-Encoded Logic Manifolds)")
    console.print("Compliance Grade: Sovereign / AIDA-Ready")

if __name__ == "__main__":
    app()
