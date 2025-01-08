from aiogram.types import Message
from fluentogram import TranslatorRunner

from decimal import Decimal
from database.enums import MonetaryCurrenciesEnum


# NotImplemented
async def send_exceeded_limit_message(message: Message, i18n: TranslatorRunner, total_money_value: Decimal,
                                      money_value: Decimal, money_currency: MonetaryCurrenciesEnum):

    notify_message = i18n.notify.limit_exceeded(total_money_value=total_money_value, money_value=money_value,
                                                money_currency=money_currency)
    await message.answer(notify_message)
