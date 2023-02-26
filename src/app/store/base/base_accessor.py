import typing as t

if t.TYPE_CHECKING:
    from src.app.web.app import Application


class BaseAccessor:
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        app.on_startup.append(self.connect)
        app.on_cleanup.append(self.disconnect)

    async def connect(self, app: "Application"):
        raise NotImplementedError

    async def disconnect(self, app: "Application"):
        raise NotImplementedError
