import asyncio
from asyncio import Task
from typing import Optional

from src.app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    async def start(self):
        self.poll_task = asyncio.create_task(self.poll())
        self.is_running = True
        await self.poll_task

    async def stop(self):
        self.is_running = False
        await self.store.tg_api.session.close()

    async def poll(self):
        while self.is_running:
            await self.store.tg_api.poll()
