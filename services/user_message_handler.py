from collections.abc import Generator
from aiogram.types import Message

from custom_types.types import DefaultMoneyUnit
from exceptions.custom_errors import IncorrectAmountException, IncorrectCategoryException, ParseException, \
    IncorrectMessageText
from re import search, DOTALL
from decimal import Decimal


def category_parse(message: Message, bot_command: str = None) -> tuple[str, Decimal | None]:
    try:
        category = define_category_unit(message.text)
        money_value = define_money_unit(message.text)
        return category, money_value
    except ParseException:
        raise "Parse Error"


def define_money_unit(message: str) -> Decimal | None:
    _money_pattern = r"\D*\b(?P<amount>[0-9]+[.,]?[0-9]{0,2}).*"
    _money_value = search(_money_pattern, message, DOTALL)

    try:
        result = DefaultMoneyUnit(_money_value.groupdict().get("amount").replace(",", "."))
        return result
    except (TypeError, AttributeError):
        return None


def define_category_unit(message: str, bot_command: str = "") -> str:
    _letters_group = f'([a-zA-Z]+|[а-яА-Я]+)'
    _start_group = "start"
    _end_group = "end"
    _prefix = ("", bot_command + r"\s")[bool(bot_command)]
    _category_pattern = rf"{bot_command}((?P<{_start_group}>\b{_letters_group}\b)|.+(?P<{_end_group}>\b{_letters_group}))"
    _category_type = search(_category_pattern, message, DOTALL)

    if bot_command and not bot_command.startswith("/"):
        raise IncorrectMessageText(f"Argument '{bot_command}' should be start with '/'")

    if not _category_type:
        raise IncorrectCategoryException()
    try:
        result: Generator[str | None] = (cat for cat in _category_type.groupdict().values() if cat is not None)
        return next(result)
    except TypeError:
        raise ParseException()
