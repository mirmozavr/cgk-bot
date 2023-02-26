from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from src.web.config import setup_config
from src.web.session import setup_session
class Application(AiohttpApplication):
    ...


app = Application()


def setup_app(*, dev_config: bool):
    setup_config(app, dev_config)
    setup_session(app)
    return app
