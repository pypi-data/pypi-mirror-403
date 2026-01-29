import os
from rich.console import Console

console = Console()

def inject_pqc_dependencies(project_path: str):
    """
    Ensures the project has the necessary PQC libraries installed.
    """
    req_file = os.path.join(project_path, "requirements.txt")
    pqc_library = "pqc-wrapper>=0.1.0" # This would be your helper library

    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            content = f.read()
        
        if pqc_library not in content:
            with open(req_file, "a") as f:
                f.write(f"\n{pqc_library}")
            console.print(f"📦 [bold green]Updated:[/bold green] Added {pqc_library} to requirements.txt")
    else:
        # Create it if it doesn't exist
        with open(req_file, "w") as f:
            f.write(pqc_library)
        console.print(f"📝 [bold blue]Created:[/bold blue] requirements.txt with {pqc_library}")