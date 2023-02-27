from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec

from src.app.admin.models import Admin
from src.app.store import setup_store, Store
from src.app.store.database import Database
from src.app.web.config import setup_config, Config
from src.app.web.middlewares import setup_middlewares
from src.app.web.routes import setup_routes
from src.app.web.session import setup_session


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    database: Optional[Database] = None


class Request(AiohttpRequest):
    admin: Optional[Admin] = None

    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self):
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()

apispec_params = {
    "title": "Vk Quiz Bot",
    "url": "/docs/json",
    "swagger_path": "/docs"}


def setup_app(*, dev_config: bool):
    setup_config(app, dev_config)
    setup_aiohttp_apispec(app, **apispec_params)
    setup_session(app)
    setup_middlewares(app)
    setup_routes(app)
    setup_store(app)
    return app
