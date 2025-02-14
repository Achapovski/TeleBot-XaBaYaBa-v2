from datetime import datetime

from aiogram import Bot
from aiogram.types import User
from aiogram_dialog.manager.manager import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import ManagedRadio

from fluentogram import TranslatorRunner, TranslatorHub
from sqlalchemy.ext.asyncio import async_sessionmaker

from custom_types.types import DefaultMoneyUnit
from database.enums import ExpensesEnum, MonetaryCurrenciesEnum, TimeIntervalsEnum, SettingsParamsEnum
from database.requests import UserDBRequests, SettingsDBRequests
from keyboards.main_menu import load_bot_command_menu
from services.categories_handler import compute_money_value_with_timestamps, compute_expected_costs
from services.check_actually_currencies import get_valid_expenses
from validation.db_models import ValidCategoryModel, ValidSettingsParams, CategoryDTO


async def get_message_start_win(dialog_manager: DialogManager, event_from_user: User,
                                i18n: TranslatorRunner, bot: Bot, msgs_to_del: list, **kwargs):
    if len(msgs_to_del) > 2:
        await bot.delete_messages(chat_id=event_from_user.id, message_ids=msgs_to_del[:-1])

    username = event_from_user.username if event_from_user.username else event_from_user.first_name
    message = i18n.get("message-start", username=username)
    button_start = i18n.get("button-start")

    # Обновляет меню команд бота при выводе первого диалогового окна.
    await load_bot_command_menu(bot=bot, i18n=i18n)
    return {"message": message, "button_start": button_start}


async def get_pre_settings_win(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    message = i18n.get("message-pre_settings")
    button_pre_settings = i18n.get("button-pre_settings")
    button_continue = i18n.get("button-continue")
    return {"message": message, "button_pre_settings": button_pre_settings, "button_continue": button_continue}


async def get_language_choice_win(dialog_manager: DialogManager, i18n: TranslatorRunner, event_from_user: User,
                                  _translator_hub: TranslatorHub, bot: Bot, **kwargs):
    settings: ValidSettingsParams = dialog_manager.start_data.get("user_settings")
    dialog_manager.dialog_data.setdefault("language_code", settings.language_code)
    radio: ManagedRadio = dialog_manager.find("radio_lang")
    all_locales_buttons = sorted([(loc.locale, loc.locale) for loc in i18n.translators], key=lambda x: x[0])

    if not radio.get_checked():
        for locale in all_locales_buttons:
            if dialog_manager.dialog_data.get("language_code") == locale[0]:
                await radio.set_checked(locale[0])
                break

    dialog_manager.dialog_data["language_code"] = radio.get_checked()
    i18n: TranslatorRunner = _translator_hub.get_translator_by_locale(locale=radio.get_checked())
    message = i18n.pre_setting_choice.language()
    button_back = i18n.button.back()
    button_confirm = i18n.button.confirm()

    # Обновляет меню команд бота в реальном времени, при смене локали.
    await load_bot_command_menu(bot=bot, i18n=i18n)

    return {"message": message, "languages": all_locales_buttons,
            "button_back": button_back, "button_confirm": button_confirm}


async def get_currency_choice_win(dialog_manager: DialogManager, _translator_hub: TranslatorHub, **kwargs):
    settings: ValidSettingsParams = dialog_manager.start_data.get("user_settings")
    radio: ManagedRadio = dialog_manager.find("radio_curr")
    language_code = dialog_manager.dialog_data.get("language_code")
    i18n = _translator_hub.get_translator_by_locale(locale=language_code)

    all_currency_types = [
        (i18n.get("currency-{curr}".format(curr=curr.value)), curr) for curr in MonetaryCurrenciesEnum
    ]
    if not radio.get_checked():
        await radio.set_checked(settings.monetary_currency)

    dialog_manager.dialog_data["currency_type"] = radio.get_checked()

    message = i18n.pre_setting_choice.currency()
    button_back = i18n.button.back()
    button_confirm = i18n.button.confirm()

    return {"message": message, "currency": all_currency_types,
            "button_back": button_back, "button_confirm": button_confirm}


async def get_default_money_value_win(dialog_manager: DialogManager, _translator_hub: TranslatorHub, **kwargs):
    settings: ValidSettingsParams = dialog_manager.start_data.get("user_settings")
    dialog_manager.dialog_data.setdefault("money_value", settings.money_limits.get(datetime.now().month))
    currency_type = dialog_manager.dialog_data.get("currency_type", dialog_manager.start_data.get("currency_type"))
    money_value = dialog_manager.dialog_data.get("money_value", dialog_manager.start_data.get("money_value"))
    language_code = dialog_manager.dialog_data.get("language_code", dialog_manager.start_data.get("language_code"))
    i18n = _translator_hub.get_translator_by_locale(locale=language_code)

    is_default = (False, True)[money_value is None]
    if money_value is None or money_value is DefaultMoneyUnit('0').__str__():
        success_message = i18n.message.money_unlimited_select()
    else:
        success_message = i18n.message.confirm_money_value(money_value=money_value, currency=currency_type)

    message = i18n.message.money_value()
    if money_value is None:
        message += "\n" + i18n.message.money_unlimited()
    button_confirm = i18n.button.confirm()
    button_back = i18n.button.back()

    return {"message": message, "is_default": is_default, "is_selected": not is_default,
            "success_message": success_message, "button_confirm": button_confirm, "button_back": button_back}


async def lets_work(dialog_manager: DialogManager, _translator_hub: TranslatorHub, bot: Bot, event_from_user: User,
                    db_session: async_sessionmaker, i18n: TranslatorRunner, msgs_to_del: list, **kwargs):
    if len(msgs_to_del) > 2:
        await bot.delete_messages(chat_id=event_from_user.id, message_ids=msgs_to_del[:-1])

    # Определяем два варианта определения языковой модели: Через настройку пользователя (один контекст) через мидлварь
    if dialog_manager.start_data:
        language_code = dialog_manager.start_data.get("language_code")
        i18n = _translator_hub.get_translator_by_locale(locale=language_code)

    message = i18n.message.lets_work()

    # Добавляем db_session в контекст рабочего диалога, чтобы воспользоваться сессией в фабриках диалогов
    dialog_manager.dialog_data["db_session"] = db_session
    dialog_manager.dialog_data.update({"db_session": db_session, "message_to_del": msgs_to_del})
    return {"message": message}


async def get_user_categories(dialog_manager: DialogManager, i18n: TranslatorRunner, db_session: async_sessionmaker,
                              event_from_user: User, msgs_to_del: list, bot: Bot, **kwargs):
    print(msgs_to_del)
    if len(msgs_to_del) > 2:
        await bot.delete_messages(chat_id=event_from_user.id, message_ids=msgs_to_del[:-1])

    radio: ManagedRadio = dialog_manager.find("radio_categories")
    categories: list[ValidCategoryModel] = await UserDBRequests.get_categories(session_maker=db_session,
                                                                               user_id=event_from_user.id)
    dialog_manager.current_context().dialog_data["categories"] = categories

    show_button = (False, True)[bool(radio.get_checked())]

    if not (category := radio.get_checked()):
        message = i18n.message.categories_list()
    else:
        message = i18n.message.categories_choice(category=category)

    button_confirm = i18n.button.confirm()
    categories: list[tuple[str, str]] = [(category.title, category.title) for category in categories]

    return {"message": message, "button_confirm": button_confirm,
            "categories": categories, "show_button": show_button}


async def get_category_alias(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    message = i18n.message.categories_alias()
    button_back = i18n.button.back()

    return {"message": message, "button_back": button_back}


async def confirm_category_alias(dialog_manager: DialogManager, i18n: TranslatorRunner,
                                 db_session: async_sessionmaker, **kwargs):
    dialog_manager.dialog_data["db_session"] = db_session
    category = dialog_manager.find("radio_categories").get_checked()
    alias: ManagedTextInput = dialog_manager.find("alias_input")
    message = i18n.message.categories_alias_confirm(category=category, alias=alias.get_value())
    button_back, button_confirm = [i18n.get(f"button-{button}") for button in ("back", "confirm")]

    return {"message": message, "button_back": button_back, "button_confirm": button_confirm}


async def get_category_list(dialog_manager: DialogManager, i18n: TranslatorRunner, db_session: async_sessionmaker,
                            event_from_user: User, bot: Bot, msgs_to_del: list, **kwargs):
    if len(msgs_to_del) > 2:
        await bot.delete_messages(chat_id=event_from_user.id, message_ids=msgs_to_del[:-1])
    dialog_data = dialog_manager.current_context().dialog_data
    categories: list[ValidCategoryModel] = await UserDBRequests.get_categories(session_maker=db_session,
                                                                               user_id=event_from_user.id)
    settings: ValidSettingsParams = await SettingsDBRequests.get_params(session_maker=db_session,
                                                                        user_id=event_from_user.id)
    dialog_data.setdefault("default_currency", str(settings.monetary_currency))

    page = dialog_data.get("page", 0)
    show_periods = dialog_data.setdefault("button_calendar", False)
    show_currencies = dialog_data.setdefault("button_currencies", False)
    current_period = dialog_data.setdefault("current_period", ExpensesEnum.month.value)
    monetary_currency = dialog_data.setdefault("current_currency", str(settings.monetary_currency))
    dialog_data["categories"] = categories
    categories = dialog_data.get("actually_categories", categories)

    category_enum = [[]]
    for idx, category in enumerate(categories, 1):
        menu_point = i18n.message.categories_menu_point(number=idx, category=category.title,
                                                        amount=str(DefaultMoneyUnit(getattr(category, current_period))),
                                                        currency=monetary_currency)
        category_enum[-1].append(menu_point)
        if idx % 4 == 0 and categories.__len__() > idx:
            category_enum.append([])

    page_num = category_enum.__len__()
    dialog_manager.current_context().dialog_data["page_num"] = page_num
    expected_costs = compute_expected_costs(current_period, settings.money_limits)
    _expected_costs = (await get_valid_expenses(expected_costs, str(settings.monetary_currency)))[monetary_currency]
    money_limit_value = compute_money_value_with_timestamps(categories, current_period)
    _money_limit_value = (await get_valid_expenses(money_limit_value, monetary_currency))[monetary_currency]
    money_limit_text = i18n.message.money_indicator(total_money_value=_money_limit_value,
                                                    expected_costs=_expected_costs,
                                                    money_currency=monetary_currency)

    text = f"{money_limit_text}\n" + "\n".join(category_enum[page])

    show_pagination = (False, True)[page_num > 1]

    button_next_text = i18n.button.pagination_next()
    button_back_text = i18n.button.pagination_back()
    button_info_text = f"{page + 1}/{page_num} ✏️"
    button_currencies_text = i18n.button.currency()
    button_calendar_text = i18n.button.period()
    button_editor = i18n.button.editor()

    currencies = {key.name: key.value for key in MonetaryCurrenciesEnum}

    return {"message": text, "button_next": button_next_text, "button_info": button_info_text,
            "button_back": button_back_text, "button_calendar": button_calendar_text,
            "button_currencies": button_currencies_text, "show_pagination": show_pagination,
            "show_periods": show_periods, "show_currencies": show_currencies, "button_editor": button_editor,
            "hide_pagination": not show_pagination, **currencies}


async def get_category_editor(dialog_manager: DialogManager, i18n: TranslatorRunner, db_session: async_sessionmaker,
                              event_from_user: User, **kwargs):
    message = i18n.message.settings_delete()
    categories: list[CategoryDTO] = dialog_manager.dialog_data.get("categories")
    category_buttons = ((category.id, category.title) for category in categories)
    button_confirm = i18n.button.confirm()
    return {"message": message, "categories": tuple(category_buttons), "button_confirm": button_confirm}


async def get_category_period_buttons(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    time_periods = {
        f"{period.name}_button": i18n.get(f"button-{period.value}") for period in TimeIntervalsEnum
    }
    return time_periods


async def get_setting_language(dialog_manager: DialogManager, i18n: TranslatorRunner,
                               db_session: async_sessionmaker, **kwargs):
    message = i18n.pre_setting_choice.language()
    button_confirm = i18n.buttom.confirm()
    return {"message": message, "button_confirm": button_confirm}


async def get_setting_money_limit(dialog_manager: DialogManager, _translator_hub: TranslatorHub, **kwargs):
    i18n = _translator_hub.get_translator_by_locale(dialog_manager.dialog_data.get("language_code"))
    user_settings: ValidSettingsParams = dialog_manager.start_data.get("user_settings")
    current_money_value = dialog_manager.dialog_data.get("money_value", dialog_manager.start_data.get("money_value"))
    message = i18n.message.confirm_money_value(money_value=current_money_value,
                                               currency=user_settings.monetary_currency)
    button_confirm = i18n.button.confirm()
    return {"message": message, "button_confirm": button_confirm}


async def get_setting_money_currency(dialog_manager: DialogManager, i18n: TranslatorRunner,
                                     db_session: async_sessionmaker, **kwargs):
    message = i18n.message.pre_settings_choice.currency()
    button_confirm = i18n.button.confirm()
    return {"message": message, "button_confirm": button_confirm}


async def get_settings_params(dialog_manager: DialogManager, db_session: async_sessionmaker, event_from_user: User,
                              _translator_hub: TranslatorHub, bot: Bot, msgs_to_del: list, **kwargs):
    if len(msgs_to_del) > 2:
        await bot.delete_messages(chat_id=event_from_user.id, message_ids=msgs_to_del[:-1])

    dialog_manager.dialog_data["user_settings"] = await SettingsDBRequests.get_params(db_session, event_from_user.id)

    standard_language_code = dialog_manager.start_data.get("language_code")
    new_language_code = dialog_manager.dialog_data.get("language_code", standard_language_code)
    i18n = _translator_hub.get_translator_by_locale(new_language_code)

    message = i18n.message.settings_menu()
    confirm_button = i18n.button.confirm()

    data = {element.name: i18n.get(f"setting-{element.value}") for element in SettingsParamsEnum}
    return {"message": message, "confirm_button": confirm_button, **data}
