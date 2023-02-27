from sqlalchemy import select, insert

from src.app.admin.models import Admin, AdminModel
from src.app.store.base.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    async def get_by_email(self, email: str) -> Admin | None:
        stmt = select(AdminModel).where(AdminModel.email == email)
        async with self.app.database.session as session:
            result = await session.execute(stmt)
            data = result.fetchone()
            if data:
                data = data[0]
                return Admin(data.id, data.email, data.password)

    async def create_admin(self, email: str, password: str) -> Admin:
        ins = insert(AdminModel).values(email=email, password=password)
        async with self.app.database.session as session:
            await session.execute(ins)
            await session.commit()
        return await self.get_by_email(email)

