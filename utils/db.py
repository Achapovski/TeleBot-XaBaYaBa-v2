from logging import getLogger

from validation.config_models import DBConfig

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

logger = getLogger(__name__)


# Вынести в модуль БД "requests"
async def check_db_connection(session_maker: async_sessionmaker | sessionmaker) -> bool:
    async with session_maker() as session:
        try:
            await session.execute(text("SELECT VERSION()"))
            logger.info("DataBase is connected")
            return True
        # Реализовать реакцию бота на неправильное подключение к БД
        except ProgrammingError as error:
            logger.error(f"DataBase command error. {error}")
        except Exception as error:
            logger.error(f"DataBase connection error. {error}")


class DBConnection:
    def __init__(self, config: DBConfig):
        self.config = config

    async def create_async_sessionmaker(self):
        AsyncSessionMaker = async_sessionmaker(bind=await self.create_async_engine(), expire_on_commit=False)
        return AsyncSessionMaker

    async def create_async_engine(self):
        return create_async_engine(
            url=str(self.config.dsn),
            echo=self.config.is_echo
        )
