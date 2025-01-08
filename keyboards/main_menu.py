from aiogram.types import BotCommand
from aiogram import Bot
from fluentogram import TranslatorHub, TranslatorRunner

from database.database_scratch import DATA


async def load_bot_command_menu(bot: Bot, *, translator_hub: TranslatorHub = None, i18n: TranslatorRunner = None):
    if translator_hub:
        _i18n = translator_hub.get_translator_by_locale(locale=DATA.get("language_code", "en"))
    else:
        _i18n = i18n

    if _i18n is None:
        raise TypeError(
            f"{load_bot_command_menu.__name__} function can only use TranslatorHub or TranslatorRunner object."
        )

    main_menu = [
        BotCommand(
            command="/start",
            description=_i18n.command.start()
        ),
        BotCommand(
            command="/help",
            description=_i18n.command.help()
        ),
        BotCommand(
            command="/add",
            description=_i18n.command.add()
        ),
        BotCommand(
            command="/adds",
            description=_i18n.command.adds()
        ),
        BotCommand(
            command="/as",
            description=_i18n.command.alias()
        ),
        BotCommand(
            command="/categories",
            description=_i18n.command.categories()
        ),
        BotCommand(
            command="/aliases",
            description=_i18n.command.aliases()
        ),
        BotCommand(
            command="/settings",
            description=_i18n.command.settings()
        )
    ]
    await bot.set_my_commands(main_menu)
