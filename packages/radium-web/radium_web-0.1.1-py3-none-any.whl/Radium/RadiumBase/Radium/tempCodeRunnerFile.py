from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "App"

paths = []


def scan(folder: Path, route: str):
    has_subfolder = False

    for item in folder.iterdir():
        if item.is_dir():
            has_subfolder = True
            new_route = f"{route}/{item.name}"
            paths.append(new_route)
            scan(item, new_route)

    if not has_subfolder:
        paths.append(route)


for folder in APP_DIR.iterdir():
    if folder.is_dir() and folder.name.startswith("@"):
        base_route = "/" + folder.name.replace("@", "")
        scan(folder, base_route)


print(paths)
