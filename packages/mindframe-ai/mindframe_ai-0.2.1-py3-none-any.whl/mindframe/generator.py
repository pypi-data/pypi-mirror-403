import shutil
from pathlib import Path
from rich.console import Console

console = Console()

def create_project(project_name: str, project_type: str = "genai"):
    template_dir = Path(__file__).parent / "templates" / "project"
    target_dir = Path.cwd() / project_name

    if target_dir.exists():
        raise FileExistsError(f"Project directory '{project_name}' already exists.")

    with console.status(f"[bold green]Generating Mindframe {project_type} project: {project_name}...", spinner="dots"):
        shutil.copytree(template_dir, target_dir)

        # If it's not an agentic project, remove the agent-specific folders
        if project_type != "agentic":
            orchestration_dir = target_dir / "src" / "orchestration"
            
            if orchestration_dir.exists():
                shutil.rmtree(orchestration_dir)

    console.print(f"\n[bold green]✅ Success![/bold green] Created project structure at [cyan]{target_dir}[/cyan]")
    console.print("\n[bold blue]Next steps:[/bold blue]")
    console.print(f" 1. cd {project_name}")
    console.print(" 2. pip install -r requirements.txt")
    console.print(" 3. Start building! 🚀")
