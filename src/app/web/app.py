from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
)

from src.app.store.database import Database
from src.app.web.config import setup_config, Config
from src.app.web.session import setup_session


class Application(AiohttpApplication):
    config: Optional[Config] = None
    # store: Optional[Store] = None
    database: Optional[Database] = None


app = Application()


def setup_app(*, dev_config: bool):
    setup_config(app, dev_config)
    setup_session(app)
    return app
