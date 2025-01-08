import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs

from database.models import Base
from dialogs.dialogs import settings_dialog, starting_dialog, working_dialog, categories_dialog, pre_settings_dialog

from handlers.user_handlers import router
from keyboards.main_menu import load_bot_command_menu
from fluentogram import TranslatorHub

from utils.i18n import create_translator_hub

from middlewares.db import DBSessionMiddleware, TrackAllUsersMiddleware
from middlewares.sheduler import DateIntervalMiddleware
from middlewares.i18n import TranslatorRunnerMiddleware

from config_data.yaml_config import get_config
from validation.config_models import DBConfig, BotConfig
from utils.db import check_db_connection, DBConnection

from sqlalchemy.ext.asyncio import async_sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore


async def main():
    # Вынести логирование в отдельный модуль.
    logger = logging.getLogger(name=__name__)
    logging.basicConfig(
        format="[%(asctime)s]:[%(levelname)s] - %(filename)s: \t%(message)s",
        level=logging.INFO
    )

    bot_config = get_config(BotConfig, "bot")
    db_config = get_config(DBConfig, "db")

    bot: Bot = Bot(token=str(bot_config.token.get_secret_value()))
    dp: Dispatcher = Dispatcher()

    # Проверка подключения к базе данных, определение создателя сессий
    db: DBConnection = DBConnection(db_config)
    db_session: async_sessionmaker = await db.create_async_sessionmaker()

    # Инициализация и запуск расписания задач
    # job_stores = {"default": RedisJobStore()}
    scheduler: AsyncIOScheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.start()

    await check_db_connection(session_maker=db_session)

    # Создание сессии БД и моделей таблиц
    async with (await db.create_async_engine()).connect() as session:
        await session.run_sync(Base.metadata.create_all)
        await session.commit()

    translator_hub: TranslatorHub = create_translator_hub()

    dp.include_router(router)
    dp.include_routers(starting_dialog, settings_dialog, working_dialog, categories_dialog, pre_settings_dialog)
    setup_dialogs(dp)
    dp.update.outer_middleware(DBSessionMiddleware(db_session))
    dp.message.outer_middleware(TrackAllUsersMiddleware())
    dp.update.middleware(DateIntervalMiddleware(scheduler))
    dp.update.middleware(TranslatorRunnerMiddleware())

    await load_bot_command_menu(bot=bot, translator_hub=translator_hub)
    logger.info("Bot is running.")
    await dp.start_polling(bot, _translator_hub=translator_hub, test_data="Test Data")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot was stopped.")
