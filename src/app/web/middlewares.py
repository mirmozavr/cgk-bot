import json
import typing

from aiohttp.web_exceptions import HTTPException, HTTPUnprocessableEntity
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from sqlalchemy.exc import IntegrityError

from src.app.admin.models import Admin
from src.app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from src.app.web.app import Application, Request


@middleware
async def auth_middleware(request: "Request", handler: callable):
    session = await get_session(request)
    if session.new:
        request.admin = None
    else:
        try:
            request.admin = Admin.from_session(session)
        except KeyError as e:
            http_status = 401
            return error_json_response(
                http_status=http_status,
                status=HTTP_ERROR_CODES[http_status],
                message=str(e),
            )
    return await handler(request)


HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
        return response
    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data=json.loads(e.text),
        )
    except HTTPException as e:
        return error_json_response(
            http_status=e.status,
            status=HTTP_ERROR_CODES.get(e.status),
            message=e.reason,
            data=e.text,
        )
    except IntegrityError as e:
        http_status = 404 if e.orig.pgcode == "23503" else 409
        return error_json_response(
            http_status=http_status,
            status=HTTP_ERROR_CODES[http_status],
            message=str(e)
        )
    except Exception as e:
        return error_json_response(
            http_status=500,
            status=HTTP_ERROR_CODES[500],
            message=str(e),
        )


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(auth_middleware)
    app.middlewares.append(session_middleware(EncryptedCookieStorage(app.config.session.key)))
    app.middlewares.append(validation_middleware)
