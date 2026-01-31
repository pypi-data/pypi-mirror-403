from pathlib import Path
import importlib.util

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"

routes = {}  # route -> page function


def load_page(file_path: Path):
    module_name = "_page_" + "_".join(file_path.parts)

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "page"):
        raise RuntimeError(f"'page()' not found in {file_path}")

    return module.page


def scan(folder: Path, route: str):
    subfolders = [
        d for d in folder.iterdir()
        if d.is_dir() and "__" not in d.name
    ]

    # leaf → load page.py
    if not subfolders:
        page_file = folder / "page.py"
        if not page_file.exists():
            raise FileNotFoundError(f"page.py missing in {folder}")

        routes[route] = load_page(page_file)
        return

    for sub in subfolders:
        scan(sub, f"{route}/{sub.name}")


for folder in APP_DIR.iterdir():
    if folder.is_dir() and folder.name.startswith("@"):
        base_route = "/" + folder.name.replace("@", "")
        scan(folder, base_route)


