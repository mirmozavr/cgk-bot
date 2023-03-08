import sys
from pathlib import Path

from aiohttp.web import run_app

path = str(Path(__file__).parent.parent)
if path not in sys.path:
    sys.path.append(path)


if __name__ == "__main__":
    from src.app.web.app import setup_app
    run_app(setup_app(dev_config=True))
