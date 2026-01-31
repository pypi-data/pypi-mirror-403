import shutil
import os
import sys
from pathlib import Path

def init_project():
    target_dir = Path.cwd()
    template_dir = Path(__file__).parent / "templates" / "project"

    if not template_dir.exists():
        print("❌ Radium template not found")
        sys.exit(1)

    for item in template_dir.iterdir():
        dest = target_dir / item.name

        if dest.exists():
            print(f"⚠️ Skipping {item.name} (already exists)")
            continue

        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    print("✅ Radium project initialized!")

def main():
    if len(sys.argv) < 2:
        print("Usage: radium init")
        return

    if sys.argv[1] == "init":
        init_project()
    else:
        print("Unknown command")