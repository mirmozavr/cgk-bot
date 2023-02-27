import typing as t

from src.app.store.database import Database

if t.TYPE_CHECKING:
    from src.app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from src.app.store.admin.accessor import AdminAccessor
        # from src.app.store.bot.manager import BotManager
        # from src.app.store.quiz.accessor import QuizAccessor
        # from src.app.store.vk_api.accessor import VkApiAccessor

        self.admins = AdminAccessor(app)
        # self.quizzes = QuizAccessor(app)
        # self.vk_api = VkApiAccessor(app)
        # self.bots_manager = BotManager(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
