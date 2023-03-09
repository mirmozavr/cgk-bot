import asyncio
import json
import typing as t
from typing import Optional, List

from aiohttp.client import ClientSession
from sqlalchemy import select

from src.app.bot.models import GameModel, PlayerModel
from src.app.store.base.base_accessor import BaseAccessor
from src.app.store.tg_api.dataclasses import Message, Update, Chat, User, CallbackQuery
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
        asyncio.create_task(self.poller.start())

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
            "timeout": 60,
            "allowed_updates": json.dumps(["message", "callback_query"]),
        }
        get_updates_url = f"{self.base_url}/getUpdates"
        async with self.session.get(get_updates_url, params=params) as response:
            data = await response.json()
            for raw_update in data["result"]:
                # process only group messages
                if ("message" in raw_update) and (
                        raw_update["message"]["chat"]["type"] not in ("supergroup", "group")
                        or not raw_update["message"].get("text")
                ):
                    self.offset = raw_update["update_id"] + 1
                    continue
                update = self.dict_to_dc(raw_update)

                await self.app.store.bot_manager.handle_update(update)

                # Increment offset by 1 to mark updates as accepted
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
            "team_up": "Gather the team",
            "start_game": "Start game",
            "end_game": "End game",
            "group_stats": "Group game stats",
            "player_stats": "Personal game stats",
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
        if "message" in raw_data:
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
                        username=raw_data["message"]["from"].get("username"),
                    ),
                ),
            )
        if "callback_query" in raw_data:
            return Update(
                update_id=raw_data["update_id"],
                callback_query=CallbackQuery(
                    id=raw_data["callback_query"]["id"],
                    data=raw_data["callback_query"].get("data"),
                    user=User(
                        id=raw_data["callback_query"]["from"]["id"],
                        is_bot=raw_data["callback_query"]["from"]["is_bot"],
                        first_name=raw_data["callback_query"]["from"]["first_name"],
                        username=raw_data["callback_query"]["from"].get("username"),
                    ),
                    message=Message(
                        message_id=raw_data["callback_query"]["message"]["message_id"],
                        text=raw_data["callback_query"]["message"].get("text"),
                        date=raw_data["callback_query"]["message"].get("date"),
                        user=User(
                            id=raw_data["callback_query"]["message"]["from"]["id"],
                            is_bot=raw_data["callback_query"]["message"]["from"]["is_bot"],
                            first_name=raw_data["callback_query"]["message"]["from"]["first_name"],
                            username=raw_data["callback_query"]["message"]["from"].get("username"),
                        ),
                        chat=Chat(
                            id=raw_data["callback_query"]["message"]["chat"]["id"],
                            type=raw_data["callback_query"]["message"]["chat"]["type"],
                            title=raw_data["callback_query"]["message"]["chat"]["title"],
                        )
                    ),
                )
            )

    async def send_message(self, chat_id: int, text: str) -> None:
        """
        Send text message to chat
        :param chat_id: Chat ID
        :param text: Text to send to chat
        :return:
        """
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": text,
        }
        resp = await self.session.get(url, params=params)
        return (await resp.json())["result"]["date"]

    async def reply_to_message(self, message: Message, text: str) -> None:
        """
        Reply to text message
        :param message: Message object
        :param text: Text to send to chat
        :return:
        """
        params = {
            "chat_id": message.chat.id,
            "text": text,
            "reply_to_message_id": message.message_id,
        }
        snd_msg_url = f"{self.base_url}/sendMessage"
        await self.session.get(snd_msg_url, params=params)

    async def send_inline_button(self, message: Message, data: str) -> None:
        """
        Send inline button to message chat
        :param message: Message object
        :param data: Data in button
        :return:
        """
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": message.chat.id,
            "text": "Press the button to join THE TEAM",
            "reply_markup": json.dumps(
                {
                    "inline_keyboard": [[{"text": "Join the team",
                                          "callback_data": data}]],
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                }
            ),
        }
        await self.session.get(url, params=params)

    async def send_choose_responder_buttons(self, game: GameModel, text: str) -> int:
        """
        Send reply buttons with team player names for cap to choose responder
        :param game: GameModel object
        :param text: Message text
        :return: Integer, representing timestamp
        """
        url = f"{self.base_url}/sendMessage"
        capitan = await self.get_player_by_id(game.cap_id)
        params = {
            "chat_id": game.id,
            "text": f"{capitan.first_name} {text}",
            "entities": json.dumps(
              [{
                  "type": "text_mention",
                  "offset": 0,
                  "length": len(capitan.first_name) - 1,
                  "user": {
                      "id": game.cap_id
                  }
              }]
            ),
            "reply_markup": json.dumps(
                {
                    "keyboard": [[{"text": f"{player.first_name}"}
                                  for player in await self.get_team_players_models(game)]],
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                    "selective": True
                }
            ),
        }
        resp = await self.session.get(url, params=params)
        return (await resp.json())["result"]["date"]

    async def remove_buttons(self, game: GameModel, text: str) -> int:
        """
        Remove reply buttons
        :param game: GameModel object
        :param text: Message text
        :return: Integer, representing timestamp
        """
        url = f"{self.base_url}/sendMessage"
        params = {
            "chat_id": game.id,
            "text": text,
            "reply_markup": json.dumps({"remove_keyboard": True}),
        }
        resp = await self.session.get(url, params=params)
        return (await resp.json())["result"]["date"]

    async def answer_cq(self, cq: CallbackQuery, text: str):
        """
        Answer to callback query
        :param cq: CallbackQuery object
        :param text: Message text
        :return:
        """
        url = f"{self.base_url}/answerCallbackQuery"
        params = {
            "callback_query_id": cq.id,
            "text": text,
            "show_alert": "false",
        }
        await self.session.get(url, params=params)

    async def get_game_by_message(self, message: Message) -> Optional[GameModel]:
        """
        Get game from db and return Game dataclass object
        :param message: Message dataclass object
        :return: GameModel object
        """
        stmt = (
            select(GameModel)
            .where(GameModel.id == message.chat.id)
        )
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            return result.one_or_none()

    async def create_game_by_message(self, message: Message) -> GameModel:
        """
        Create game object at db by received message
        :param message: Message dataclass object
        :return: GameModel object
        """
        game_model = GameModel(
            id=message.chat.id,
            update_time=message.date,
        )
        async with self.app.database.session.begin() as session:
            session.add(game_model)
            return game_model

    async def create_player_by_message(self, message: Message) -> PlayerModel:
        """
        Add new player to database by message
        :param message: Message object
        :return: Newly created PlayerModel
        """
        player_model = PlayerModel(
            id=message.user.id,
            username=message.user.username if message.user.username else None,
            first_name=message.user.first_name,
        )
        async with self.app.database.session.begin() as session:
            session.add(player_model)
            return player_model

    async def get_player_by_name(self, game: GameModel, name: str) -> Optional[PlayerModel]:
        """
        Get PlayerModel by name. Useful when captain is selecting responder with
        reply buttons
        :param game: GameModel object
        :param name: Player name
        :return: PlayerModel object
        """
        stmt = (
            select(PlayerModel)
            .where(
                (PlayerModel.first_name == name)
                & (PlayerModel.id.in_(map(int, game.team_to_list())))
            )
        )
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            return result.one_or_none()

    async def get_player_by_id(self, player_id: int) -> Optional[PlayerModel]:
        """
        Get PlayerModel by id
        :param player_id: ID of the player
        :return: PlayerModel
        """
        stmt = (
            select(PlayerModel)
            .where(PlayerModel.id == int(player_id))
        )
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            return result.one_or_none()

    async def get_team_players_models(self, game: GameModel) -> list[PlayerModel]:
        """
        Get a sequence of PlayerModels representing playing team.
        Useful when sending reply buttons to capitan
        :param game: GameModel object
        :return: List of PlayerModel objects for team members
        """
        stmt = (
            select(PlayerModel)
            .where(PlayerModel.id.in_(map(int, game.team_to_list())))
        )
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            return result.all()
