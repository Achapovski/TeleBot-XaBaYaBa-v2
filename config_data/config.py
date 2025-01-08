from environs import Env
from dataclasses import dataclass


@dataclass
class Bot:
    token: str


@dataclass
class Config:
    bot: Bot


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path=path)
    return Config(
        bot=Bot(
            token=env("BOT_TOKEN")
        )
    )



