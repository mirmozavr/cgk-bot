import typing as t

from src.app.admin.views import AdminCurrentView, AdminLoginView

if t.TYPE_CHECKING:
    from src.app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
