import shutil
import sys
from pathlib import Path
from importlib.resources import files

def init_project(name):
    target = Path.cwd() / name

    if target.exists():
        print(f"❌ {name} already exists")
        sys.exit(1)

    # Locate RadiumBase inside installed package (wheel-safe)
    base_template = files("Radium") / "RadiumBase"

    if not base_template.exists():
        raise RuntimeError(
            "RadiumBase missing from package. Packaging error."
        )

    # Copy EVERYTHING exactly
    shutil.copytree(base_template, target)

    print("✅ Project created successfully")
    print(f"➡️  cd {name}")
    print("➡️  python main.py")

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "init":
        print("Usage: radium init <project_name>")
        return

    init_project(sys.argv[2])
