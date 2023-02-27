from aiohttp.abc import StreamResponse
from aiohttp.web_exceptions import HTTPForbidden


class AuthRequiredMixin:
    async def _iter(self) -> StreamResponse:
        if not self.request.admin:
            raise HTTPForbidden
        
        return await super()._iter()
