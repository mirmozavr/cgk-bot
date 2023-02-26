import typing as t
from dataclasses import dataclass
from pathlib import Path

import ruamel.yaml as yaml
if t.TYPE_CHECKING:
    from src.app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    database: str
    user: str
    password: str
    host: str = "localhost"
    port: int = 5432


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None


def setup_config(app: "Application", dev: bool):
    env_path = Path(__file__).parent.parent.parent
    if dev:
        config_path = env_path.joinpath("./env/dev.env.yaml")
    else:
        config_path = env_path.joinpath("./env/prod.env.yaml")
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
    )
