import base64
import typing as t

from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

if t.TYPE_CHECKING:
    from src.app.web.app import Application


def setup_session(app: "Application"):
    fernet_key = app.config.session.key
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
