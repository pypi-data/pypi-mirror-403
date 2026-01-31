import shutil
from pathlib import Path

def create_project(project_name: str, project_type: str = "genai"):
    template_dir = Path(__file__).parent / "templates" / "project"
    target_dir = Path.cwd() / project_name

    if target_dir.exists():
        raise FileExistsError(f"Project directory '{project_name}' already exists.")

    print(f"🚀 Initializing new Mindframe {project_type} project: {project_name}...")
    shutil.copytree(template_dir, target_dir)

    # If it's not an agentic project, remove the agent-specific folders
    if project_type != "agentic":
        orchestration_dir = target_dir / "src" / "orchestration"
        
        if orchestration_dir.exists():
            shutil.rmtree(orchestration_dir)

    print(f"✅ Created {project_type} project at {target_dir}")
