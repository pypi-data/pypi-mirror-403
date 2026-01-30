import argparse
import sys
from pathlib import Path
import shutil

# Locate templates relative to this script location
TEMPLATES_DIR = Path(__file__).parent.parent / "00-Documentation-Standards" / "Decision-Templates"

def interactive_init():
    print("🛡️  ASVS Compliance Starter Kit - Init Wizard")
    print("===========================================")
    
    project_name = input("Project Name: ").strip()
    if not project_name:
        print("Project name required.")
        return
    
    print("\nSelect ASVS Assurance Level:")
    print("1) Level 1 (Basic - Automated)")
    print("2) Level 2 (Standard - Sensitive Data)")
    print("3) Level 3 (Critical - Defense in Depth)")
    level_choice = input("Choice [2]: ").strip() or "2"
    
    output_dir = input("\nOutput directory for docs [./docs]: ").strip() or "./docs"
    output_path = Path(output_dir)
    
    # Create logic
    print(f"\nInitializing {project_name} at {output_path} (Level {level_choice})...")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Copy templates
    if TEMPLATES_DIR.exists():
        for item in TEMPLATES_DIR.glob("*.md"):
            dest = output_path / item.name
            if not dest.exists():
                content = item.read_text(encoding="utf-8")
                # Simple templating
                content = content.replace("[Project Name]", project_name)
                dest.write_text(content, encoding="utf-8")
                print(f"  + Created {item.name}")
            else:
                print(f"  ! Skipped {item.name} (Exists)")
    else:
        print(f"  Warning: Templates directory not found at {TEMPLATES_DIR}")
    
    # Generate evidence.yml stub
    evidence_path = Path("evidence.yml")
    if not evidence_path.exists():
        evidence_content = f"""# Evidence Manifest for {project_name}
# Map your code files to ASVS requirements here.

requirements:
  # Example: Verify HTTP Security Headers are installed
  V14.4:
    checks:
      - type: file_exists
        path: "package.json"
      # - type: content_match
      #   path: "package.json"
      #   pattern: "helmet"
"""
        evidence_path.write_text(evidence_content, encoding="utf-8")
        print("  + Created evidence.yml")

    print("\n✅ Initialization complete!")
    print(f"Next step: Review documents in {output_dir}")
    print(f"Then run: asvs verify --docs-path {output_dir} --level {level_choice}")

def main(args=None):
    parser = argparse.ArgumentParser(description="Initialize a new ASVS project")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parsed = parser.parse_args(args)
    
    if parsed.interactive:
        interactive_init()
    else:
        # Default behavior if run without args, or provide CLI flags in future
        print("Run with --interactive to start the wizard.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())