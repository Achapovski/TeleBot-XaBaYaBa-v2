from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from fluentogram import TranslatorHub, TranslatorRunner
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.database_scratch import DATA
from database.requests import SettingsDBRequests
from validation.db_models import ValidSettingsModel, ValidSettingsParams


class TranslatorRunnerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")

        if not user:
            return await handler(event, data)

        language_code = user.language_code
        hub: TranslatorHub = data.get("_translator_hub")
        db_session: async_sessionmaker = data.get("db_session")

        if event.model_dump().get("message") is not None:
            user_id = event.model_dump()["message"]["chat"]["id"]
        elif event.model_dump().get("callback_query") is not None:
            user_id = event.model_dump()["callback_query"]["from_user"]["id"]
        else:
            user_id = None

        settings: ValidSettingsParams = await SettingsDBRequests.get_params(session_maker=db_session, user_id=user_id)

        if settings.language_code:
            data["i18n"] = hub.get_translator_by_locale(locale=str(settings.language_code))
        else:
            data["i18n"] = hub.get_translator_by_locale(locale=language_code)

        return await handler(event, data)
