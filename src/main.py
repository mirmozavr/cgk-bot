from aiohttp.web import run_app

from src.web.app import setup_app

if __name__ == "__main__":
    run_app(setup_app(dev_config=True))
