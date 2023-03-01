from dataclasses import dataclass


@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    username: str = None
    language_code: str = None


@dataclass
class Chat:
    id: int
    type: str
    first_name: str = None
    username: str = None
    title: str = None


@dataclass
class Message:
    message_id: int
    text: str = None
    date: int = None
    user: User = None
    chat: Chat = None


@dataclass
class Update:
    update_id: int
    message: "Message"
