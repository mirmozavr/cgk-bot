import json
import typing as t
from pprint import pprint
from typing import Optional, List

from aiohttp.client import ClientSession

from src.app.store.base.base_accessor import BaseAccessor
from src.app.store.tg_api.dataclasses import Message, Update, Chat, User
from src.app.store.tg_api.poller import Poller

if t.TYPE_CHECKING:
    from src.app.web.app import Application


class TgApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.base_url = f"https://api.telegram.org/bot{self.app.config.bot.token}"
        self.poller: Optional[Poller] = None
        self.offset: Optional[int] = None
        self.commands: Optional[List[str]] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession()
        self.poller = Poller(self.app.store)
        await self.set_initial_commands()
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        await self.poller.stop()
        self.session = None
        self.poller = None
        self.offset = None

    async def poll(self) -> None:
        """
        Run a poll and handle incoming updates
        :return:
        """
        params = {
            "offset": self.offset or "",
            "timeout": 5,
            "allowed_updates": ["message"],
        }
        get_updates_url = f"{self.base_url}/getUpdates"
        async with self.session.get(get_updates_url, params=params) as response:
            data = await response.json()
            pprint(data)
            for raw_update in data["result"]:
                # process only group messages
                if (
                        raw_update.get("my_chat_member")
                        or raw_update["message"]["chat"]["type"] != "group"
                        or not raw_update["message"].get("text")
                ):
                    self.offset = raw_update["update_id"] + 1
                    continue
                update = self.dict_to_dc(raw_update)

                # todo: handle updates here

                self.offset = update.update_id + 1

    async def set_initial_commands(self) -> None:
        """
        Set initial commands for all group chats
        :return:
        """
        set_commands_url = f"{self.base_url}/setMyCommands"
        commands = {
            "about": "Info",
            "rules": "Game rules",
            "start_game": "Start game",
            "end_game": "End game",
        }
        params = {
            "commands": json.dumps(
                [{"command": k, "description": v} for k, v in commands.items()]
            ),
            "type": "all_group_chats",
        }
        await self.session.get(set_commands_url, params=params)

    async def delete_commands(self, chat_id: int) -> None:
        """
        Delete commands for group chat
        :param chat_id: ID of a group chat to delete commands for
        :return:
        """
        del_commands_url = f"{self.base_url}/deleteMyCommands"
        params = {
            "type": "chat",
            "chat_id": chat_id,
        }
        await self.session.get(del_commands_url, params=params)

    @staticmethod
    def dict_to_dc(raw_data: dict) -> Update:
        """
        Process dict to Update dataclass for further use. Only works with
        messages from Group chats
        :param raw_data: Dict object received from getUpdates
        :return: Message class object with nested Chat, User, Message dataclasses
        """
        return Update(
            update_id=raw_data["update_id"],
            message=Message(
                message_id=raw_data["message"]["message_id"],
                date=raw_data["message"]["date"],
                text=raw_data["message"]["text"],
                chat=Chat(
                    id=raw_data["message"]["chat"]["id"],
                    type=raw_data["message"]["chat"]["type"],
                    title=raw_data["message"]["chat"]["title"],
                ),
                user=User(
                    id=raw_data["message"]["from"]["id"],
                    is_bot=raw_data["message"]["from"]["is_bot"],
                    first_name=raw_data["message"]["from"]["first_name"],
                    username=raw_data["message"]["from"]["username"],
                    language_code=raw_data["message"]["from"]["language_code"],
                ),
            ),
        )

    # async def send_message(self, message: Message) -> None:
    #     params = {
    #         "user_id": message.user_id,
    #         "random_id": int.from_bytes(os.urandom(4), byteorder="big"),
    #         "message": f"I GOT YOUR MESSAGE\n{message.text}",
    #         "access_token": self.app.config.bot.token,
    #         "v": "5.131",
    #     }
    #     msg_url = "https://api.vk.com/method/messages.send"
    #     await self.session.get(msg_url, params=params)
