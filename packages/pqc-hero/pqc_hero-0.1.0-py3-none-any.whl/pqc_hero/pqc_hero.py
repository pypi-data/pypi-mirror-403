import sys
import os
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Internal Imports
from engine.transformers.crypto_transformer import PQCTransformer
from .engine.transformers.crypto_transformer import PQCTransformer
from engine.transformers.import_manager import ImportUpdater
from engine.reports.visual_diff import generate_local_report
import libcst as cst
from engine.reports.audit_generator import generate_audit_report
from engine.simulations.threat_actor import run_sndl_simulation
from engine.transformers.dependency_manager import inject_pqc_dependencies

@app.command()
def simulate():
    """Simulates a 'Store Now, Decrypt Later' attack to show the risk."""
    run_sndl_simulation()

app = typer.Typer()
console = Console()

def refactor_logic(original_code: str) -> str:
    """The internal engine that runs the transformation."""
    tree = cst.parse_module(original_code)
    wrapper = cst.MetadataWrapper(tree)
    
    # Apply Step 1: Fix the Imports
    tree = wrapper.visit(ImportUpdater())
    # Apply Step 2: Fix the Logic (RSA -> ML-KEM)
    tree = tree.visit(PQCTransformer())
    
    return tree.code

@app.command()
def scan(path: str = "."):
    """
    Main entry point: Scans directory for Quantum Vulnerabilities.
    """
    console.print(f"🚀 [bold cyan]PQC-Hero:[/bold cyan] Scanning {path} for Quantum Debt...", style="italic")

    python_files = list(Path(path).rglob("*.py"))
    findings = []

    for file_path in python_files:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # In a real unicorn product, we use AST matchers here, but string search works for the MVP hook
        if "rsa.generate_private_key" in code:
            findings.append(file_path)

    if not findings:
        console.print("✅ [bold green]No Quantum Debt found![/bold green] Your code is safe... for now.")
        return

    # Snyk-style UI
    table = Table(title="Quantum Vulnerabilities Found")
    table.add_column("File Path", style="magenta")
    table.add_column("Issue", style="red")
    table.add_column("Risk Level", style="bold red")

    for f in findings:
        table.add_row(str(f), "Legacy RSA Key Gen", "CRITICAL")

    console.print(table)
    # NEW: Generate Audit Report after scanning
    audit_file = generate_audit_report(findings, len(python_files))
    if typer.confirm("Do you want to Auto-Fix these issues locally?"):
        # 1. Inject Dependencies first
        inject_pqc_dependencies(path)
        for f in findings:
            with open(f, "r", encoding="utf-8") as file:
                original_code = file.read()
            
            upgraded_code = refactor_logic(original_code)
            
            # Generate the 'Viral' Local Visual Report
            report_path = generate_local_report(f.name, original_code, upgraded_code)
            
            with open(f, "w", encoding="utf-8") as file:
                file.write(upgraded_code)
            
            console.print(f"✨ Fixed {f.name}! Visual report: [bold underline]{report_path}[/bold underline]")
            console.print(f"✨ Fixed {f.name} and updated environment.")
            # ... existing table display ...
            console.print(f"\n📊 [bold yellow]Audit Complete:[/bold yellow] Business risk report saved to [bold underline]{audit_file}[/bold underline]")
    
if __name__ == "__main__":
    app()