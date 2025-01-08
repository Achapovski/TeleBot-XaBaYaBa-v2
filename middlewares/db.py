from datetime import datetime
from decimal import Decimal
from typing import Any, Awaitable, Callable, Dict, cast

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from sqlalchemy.ext.asyncio import async_sessionmaker

from database.requests import UserDBRequests

from cachetools import TTLCache
from exceptions.custom_errors import IncorrectUserException


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker):
        self.db_session = session_maker

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ):
        if isinstance(self.db_session, async_sessionmaker):
            async with self.db_session(expire_on_commit=True) as session:
                data["db_session"] = session
                return await handler(event, data)


class TrackAllUsersMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache = TTLCache(
            maxsize=1000,
            # ttl=60 * 60 * 3,
            ttl=5
        )

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ):
        event = cast(Message, event)

        if event.from_user.id not in self.cache:
            db_session: async_sessionmaker = data["db_session"]

            try:
                await UserDBRequests.add_user(session_maker=db_session, user=event.from_user)
            except IncorrectUserException:
                return
            self.cache[event.from_user.id] = None

        return await handler(event, data)
