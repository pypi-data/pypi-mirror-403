import argparse
import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from .generator import create_project

console = Console()

def main():
    console.print(Panel("[bold blue]🧠 Mindframe[/bold blue]\n[italic]Structure first. Intelligence second.[/italic]", expand=False))
    
    parser = argparse.ArgumentParser(description="Mindframe CLI - GenAI Project Scaffolder")
    subparsers = parser.add_subparsers(dest="command")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project structure")
    init_parser.add_argument("name", nargs="?", help="Name of the project")
    init_parser.add_argument("--type", choices=["genai", "agentic"], help="Type of project structure")
    init_parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    if args.command == "init" or (not args.command and len(sys.argv) == 1):
        try:
            name = args.name
            project_type = args.type

            if not name or args.interactive or not project_type:
                if not name:
                    name = questionary.text("What is your project name?", default="my_ai_project").ask()
                
                if not project_type:
                    project_type = questionary.select(
                        "Select project type:",
                        choices=[
                            questionary.Choice("Standard GenAI (RAG)", value="genai"),
                            questionary.Choice("Agentic AI (Agents + Memory)", value="agentic"),
                        ]
                    ).ask()
            
            if not name:
                console.print("[red]❌ Error: Project name is required.[/red]")
                sys.exit(1)

            create_project(name, project_type)
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
