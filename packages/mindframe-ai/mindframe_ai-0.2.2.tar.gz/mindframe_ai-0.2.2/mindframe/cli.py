import argparse
import sys
from .generator import create_project

def main():
    parser = argparse.ArgumentParser(description="Mindframe CLI - GenAI Project Scaffolder")
    subparsers = parser.add_subparsers(dest="command")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project structure")
    init_parser.add_argument("name", help="Name of the project")
    init_parser.add_argument("--type", choices=["genai", "agentic"], default="genai", help="Type of project structure (default: genai)")

    args = parser.parse_args()

    if args.command == "init":
        try:
            create_project(args.name, args.type)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
