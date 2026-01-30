from pathlib import Path

from starlette.staticfiles import StaticFiles

def get_studio_static_files() -> StaticFiles:
    frontend_dist_path = Path(__file__).parent.parent / "frontend" / "static"
    return StaticFiles(directory=str(frontend_dist_path), html=True)

studio_static_files = get_studio_static_files()
