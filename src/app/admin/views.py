from hashlib import sha256

from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session

from src.app.admin.schemes import AdminSchema
from src.app.web.app import View
from src.app.web.mixins import AuthRequiredMixin
from src.app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = self.data
        email, password = data["email"], data["password"]
        existing_admin = await self.store.admins.get_by_email(email)

        if existing_admin is None:
            raise HTTPForbidden(reason="no user with email")
        if existing_admin.password != sha256(password.encode()).hexdigest():
            raise HTTPForbidden(reason="invalid password")

        raw_admin = AdminSchema().dump(existing_admin)

        session = await new_session(self.request)
        session["admin"] = raw_admin

        return json_response(raw_admin)


class AdminCurrentView(AuthRequiredMixin, View):
    @response_schema(AdminSchema)
    async def get(self):
        return json_response(data=AdminSchema().dump(self.request.admin))
