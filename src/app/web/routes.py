from aiohttp.web_app import Application


def setup_routes(app: Application):
    from src.app.admin.routes import setup_routes as admin_setup_routes

    admin_setup_routes(app)
