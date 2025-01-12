from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from aiogram_dialog.manager.manager import StartMode, DialogManager
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker

from dialogs.dialog_factories import CategoryProcessingFactory
from dialogs.dialogs_states import InitStates, WorkStates, UserCategoriesStates, SettingsStates
from fluentogram import TranslatorRunner

from services.user_message_handler import category_parse

from database.requests import CategoryDBRequests, SettingsDBRequests
from custom_filters.filters import CategoriesStateFilter

router = Router()


@router.message(CommandStart())
async def start_bot_process(message: Message, dialog_manager: DialogManager, state: FSMContext, bot: Bot,
                            db_session: async_sessionmaker, i18n: TranslatorRunner, **kwargs):
    data = {"db_session": db_session, "i18n": i18n}
    await dialog_manager.start(state=InitStates.start, mode=StartMode.RESET_STACK, data=data)


@router.message(Command("add"))
async def add_category_process(message: Message, dialog_manager: DialogManager, db_session: async_sessionmaker,
                               i18n: TranslatorRunner, bot: Bot, **kwargs):
    command = message.text.split()[0]
    category, money_value = category_parse(message, command)

    await CategoryDBRequests.add_category(session_maker=db_session, user_id=message.from_user.id,
                                          category_name=category, money_value=money_value)


@router.message(Command("as"))
async def add_alias_process(message: Message, dialog_manager: DialogManager,
                            db_session: async_sessionmaker, i18n: TranslatorRunner):
    await dialog_manager.start(WorkStates.choice_category_for_alias)


@router.message(Command("categories"))
async def get_categories_process(message: Message, dialog_manager: DialogManager,
                                 db_session: async_sessionmaker, i18n: TranslatorRunner):
    await dialog_manager.start(UserCategoriesStates.get_categories)


@router.message(Command("aliases"))
async def get_aliases_process(message: Message, dialog_manager: DialogManager, db_session: async_sessionmaker,
                              i18n: TranslatorRunner):
    pass


@router.message(Command("settings"))
async def change_bot_settings_process(message: Message, dialog_manager: DialogManager, db_session: async_sessionmaker,
                                      i18n: TranslatorRunner):
    user_settings = await SettingsDBRequests.get_params(db_session, message.from_user.id)
    data = {"user_settings": user_settings, "i18n": i18n, "is_settings": False,
            "money_value": tuple(user_settings.money_limits.values())[-1],
            "language_code": user_settings.language_code,
            "currency_type": user_settings.monetary_currency,
            "db_session": db_session}
    await dialog_manager.start(SettingsStates.select_param, data=data)


# Возможно заглушка, пересмотреть варианты возврата пользователя обратно - в рабочий диалог
# Вынести то, что есть в фабрике для определения категорий в отдельный класс, а в фабрике уже вызывать
# лишь определнные методы, таким образом будет адекватная возможность вызова методов класса и в этом обработчике
@router.message(CategoriesStateFilter())
async def return_to_working_dialog_process(message: Message, dialog_manager: DialogManager,
                                           db_session: async_sessionmaker, i18n: TranslatorRunner):
    if dialog_manager.current_context().state is UserCategoriesStates.get_categories:
        try:
            CategoryProcessingFactory.user_category_money_factory(message.text)
        except ValueError as err:
            print(err)
        else:
            await CategoryProcessingFactory.user_category_money_success(message=message, dialog_manager=dialog_manager,
                                                                        widget=None, db_session=db_session)
        await dialog_manager.done()
