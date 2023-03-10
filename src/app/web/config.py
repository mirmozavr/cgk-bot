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
    db_name: str
    user: str
    password: str
    host: str = "localhost"
    port: int = 5432
    dialect: str = "postgresql+asyncpg"

    def get_db_url(self) -> str:
        """
        Form database url string for SQLAlchemy ORM engine
        :return: Database url
        """
        return f"{self.dialect}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None


def setup_config(app: "Application", config_path: str):
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
