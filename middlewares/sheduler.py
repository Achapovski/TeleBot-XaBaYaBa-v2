from datetime import datetime
from random import randint
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg.pgproto.pgproto import timedelta
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.requests import CategoryDBRequests


class DateIntervalMiddleware(BaseMiddleware):
    def __init__(self, scheduler):
        self.scheduler: AsyncIOScheduler = scheduler
        self.cache = TTLCache(maxsize=10000, ttl=60 * 60 * 24)

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ):
        db_session = data.get("db_session")

        if event.model_dump().get("message") is not None:
            user_id = event.model_dump()["message"]["chat"]["id"]
        elif event.model_dump().get("callback_query") is not None:
            user_id = event.model_dump()["callback_query"]["from_user"]["id"]
        else:
            user_id = None

        if user_id and not self.cache.get(user_id):
            # обновляем данные в случае, если пользователя нет в кэше (Не заходил в бота более суток)
            await self.send_scheduled_message(user_id=user_id, db_session=db_session, pop=False)
            current_time = datetime.now()
            seconds_to_new_day = (datetime(year=current_time.year, month=current_time.month, day=current_time.day) +
                                  timedelta(days=1, seconds=randint(20, 21)) - current_time).seconds

            self.scheduler.add_job(func=self.send_scheduled_message, trigger="date",
                                   kwargs={"user_id": user_id, "db_session": db_session},
                                   run_date=datetime.now() + timedelta(seconds=seconds_to_new_day),
                                   misfire_grace_time=3600 * 3)
            self.cache[user_id] = True
        return await handler(event, data)

    async def send_scheduled_message(self, user_id: int, db_session: async_sessionmaker, pop: bool = True):
        await CategoryDBRequests.update_date_config_string(session_maker=db_session, user_id=user_id)
        if pop:
            self.cache.pop(user_id)
