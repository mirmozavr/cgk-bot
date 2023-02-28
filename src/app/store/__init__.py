import typing as t

from src.app.store.database import Database

if t.TYPE_CHECKING:
    from src.app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from src.app.store.admin.accessor import AdminAccessor
        # from src.app.store.quiz.accessor import QuizAccessor # Resolve merge conflict
        from src.app.bot.manager import BotManager
        from src.app.store.tg_api.accessor import TgApiAccessor

        self.admins = AdminAccessor(app)
        self.bot_manager = BotManager(app)
        # self.quiz = QuizAccessor(app) # Resolve merge conflict
        self.tg_api = TgApiAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
