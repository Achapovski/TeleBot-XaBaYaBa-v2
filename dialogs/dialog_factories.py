from decimal import Decimal
from logging import getLogger

from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from sqlalchemy.ext.asyncio import async_sessionmaker

from custom_types.types import DefaultMoneyUnit
from database.enums import ExpensesEnum
from database.models import User, Alias, Category
from database.requests import UserDBRequests, CategoryDBRequests, AliasDBRequests
from services.fuzzy_comparison import find_most_similar_options
from services.user_message_handler import define_money_unit, define_category_unit

logger = getLogger(__name__)


class MoneyValueInputFactory:
    @staticmethod
    def money_value_input_factory(text: str):
        if define_money_unit(text) >= 0:
            return text
        raise ValueError

    @staticmethod
    async def money_value_input_success(message: Message, widget: ManagedTextInput,
                                        dialog_manager: DialogManager, *args, **kwargs):
        money_value = define_money_unit(message.text)
        dialog_manager.current_context().dialog_data["money_value"] = money_value.__str__()
        # if dialog_manager.start_data.get("is_settings"):
        #     await dialog_manager.done()

    @staticmethod
    async def money_value_input_error(message: Message, widget: ManagedTextInput,
                                      dialog_manager: DialogManager, *args, **kwargs):
        i18n = dialog_manager.dialog_data.get("i18n")
        if i18n:
            await message.answer(i18n.error.money_value_choose())
        else:
            await message.answer("Bad command, try again.")


class CategoryProcessingFactory:
    # Возможно не самая лучшая идея - из-за возникновения race condition (Необходимо протестировать)
    __category = None
    __category_id = None
    __money_value = None

    @classmethod
    def user_category_money_factory(cls, text: str, **kwargs):
        try:
            cls.__category = define_category_unit(message=text).lower()
            cls.__money_value = define_money_unit(message=text)
        except (ValueError, TypeError):
            raise ValueError

    @staticmethod
    async def user_category_money_error(message: Message, widget: ManagedTextInput,
                                        dialog_manager: DialogManager, *args, **kwargs):
        logger.error("Invalid category name")

    @classmethod
    async def user_category_money_success(cls, message: Message, widget: ManagedTextInput | None,
                                          dialog_manager: DialogManager, *args, **kwargs):

        db_session = dialog_manager.dialog_data.get("db_session") \
            if not kwargs.get("db_session") \
            else kwargs.get("db_session")

        alias = await AliasDBRequests.get_alias(session_maker=db_session, user_id=message.from_user.id,
                                                alias_name=cls.__category)

        if alias:
            cat = await CategoryDBRequests.get_category(session_maker=db_session, category_id=alias.category_id)
            cat_data = cat.model_dump(include={expenses.value for expenses in ExpensesEnum})
            await CategoryDBRequests.update_category(session_maker=db_session, category_id=alias.category_id,
                                                     money_value=cls.__money_value, data=cat_data)
        else:
            await CategoryDBRequests.add_category(session_maker=db_session, category_name=cls.__category,
                                                  money_value=cls.__money_value, user_id=message.from_user.id)


class AliasProcessingFactory:
    @staticmethod
    def alias_validate_factory(text: str):
        if not text.isalpha():
            raise ValueError
        return text

    @staticmethod
    async def alias_choice_error(message: Message, widget: ManagedTextInput,
                                 dialog_manager: DialogManager, *args, **kwargs):
        pass

    @staticmethod
    async def alias_choice_success(message: Message, widget: ManagedTextInput,
                                   dialog_manager: DialogManager, *args, **kwargs):
        dialog_manager.dialog_data["alias"] = message.text
        await dialog_manager.next()
        return message.text
