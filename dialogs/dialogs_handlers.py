from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, ManagedRadio
from aiogram_dialog.manager.manager import DialogManager
from fluentogram import TranslatorRunner

from database.enums import ExpensesEnum, MonetaryCurrenciesEnum, SettingsParamsEnum
from database.requests import AliasDBRequests, SettingsDBRequests
from dialogs.dialogs_states import PreSettingsStates, WorkStates, SettingsStates
from services.check_actually_currencies import get_valid_expenses
from validation.db_models import CategoryDTO, ValidCategoryModel


async def start_handler(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def pre_settings_handler(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.start_data
    user_settings = await SettingsDBRequests.get_params(session_maker=data.get("db_session"),
                                                        user_id=callback.from_user.id)
    data.update({"user_settings": user_settings})
    await dialog_manager.start(PreSettingsStates.language, data=data)


async def continue_with_default(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()
    await dialog_manager.start(WorkStates.add_category)


async def set_language_default(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    i18n: TranslatorRunner = dialog_manager.start_data.get("i18n")
    radio: ManagedRadio = dialog_manager.find("radio_lang")

    language_code = radio.get_checked()
    full_language_code = i18n.get("language-full_language_code_{code}".format(code=language_code))
    message = i18n.get("select-language", language=full_language_code)

    await callback.answer(message)
    if dialog_manager.start_data.get("is_settings"):
        return await dialog_manager.done()
    await dialog_manager.next()


async def set_currency(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    i18n = dialog_manager.start_data.get("i18n")

    currency_type = dialog_manager.dialog_data.get("currency_type", MonetaryCurrenciesEnum.byn.value)
    message = i18n.get("select-currency", currency=currency_type.upper())

    await callback.answer(message)
    await dialog_manager.next()


async def lets_work_handler(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    # Вызов коммит обновления параметров пользователя в БД
    db_session = dialog_manager.start_data.get("db_session")
    money_value = dialog_manager.dialog_data.get("money_value")
    language_code = dialog_manager.dialog_data.get("language_code")
    currency_type = dialog_manager.dialog_data.get("currency_type")

    await SettingsDBRequests.update_params(session_maker=db_session, user_id=callback.from_user.id,
                                           money_limits=money_value, language_code=language_code,
                                           monetary_currency=currency_type)

    await dialog_manager.done()
    await dialog_manager.start(WorkStates.add_category, data={"language_code": language_code})


async def set_alias_for_category(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    db_session = dialog_manager.dialog_data.get("db_session")
    cats: list[CategoryDTO] = dialog_manager.dialog_data.get("categories")
    alias = dialog_manager.dialog_data.get("alias")
    if (category_name := dialog_manager.find("radio_categories").get_checked()) and alias:
        category_id = [cat for cat in cats if category_name == cat.title][0].id
        await AliasDBRequests.add_alias(session_maker=db_session, alias=alias,
                                        category_id=category_id, user_id=callback.from_user.id)

    await dialog_manager.switch_to(WorkStates.add_category)


async def change_category_page(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    page = dialog_manager.current_context().dialog_data.get("page", 0)
    page_num = dialog_manager.current_context().dialog_data.get("page_num", 0)

    dialog_data = dialog_manager.current_context().dialog_data

    match button.widget_id:
        case "button_back" if page > 0:
            dialog_data["page"] = page - 1
        case "button_next" if page < page_num - 1:
            dialog_data["page"] = page + 1
        case "button_currencies":
            dialog_data["button_currencies"] = not dialog_data.get("button_currencies", False)
        case "button_calendar":
            dialog_data["button_calendar"] = not dialog_data.get("button_calendar", False)


async def edit_date_period(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.current_context().dialog_data["current_period"] = getattr(ExpensesEnum, button.widget_id).value
    await callback.answer()


async def edit_currency_type(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    selected_currency = button.widget_id
    default_currency = dialog_manager.dialog_data.get("default_currency")
    default_currency: MonetaryCurrenciesEnum = getattr(MonetaryCurrenciesEnum, f"{default_currency}")
    categories: list[ValidCategoryModel] = dialog_manager.dialog_data.get("categories")

    actually_categories = []
    dictionary = {}

    for cat in categories:
        for period in ExpensesEnum:
            current_value = getattr(cat, f"{period.value}")
            valid_expenses = await get_valid_expenses(current_value, default_currency.value)
            dictionary[period.value] = valid_expenses[selected_currency]

        cat = cat.model_dump(exclude={key.value for key in ExpensesEnum})
        actually_categories.append(ValidCategoryModel(**cat, **dictionary))

    dialog_manager.current_context().dialog_data["actually_categories"] = actually_categories
    dialog_manager.current_context().dialog_data["current_currency"] = selected_currency
    await callback.answer()


async def edit_settings_param(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    db_session = dialog_manager.dialog_data.get("db_session")
    user_settings = await SettingsDBRequests.get_params(db_session, callback.from_user.id)

    dialog_manager.dialog_data.setdefault("language_code", user_settings.language_code)
    dialog_manager.dialog_data.setdefault("currency_type", user_settings.monetary_currency)
    dialog_manager.dialog_data.setdefault("money_value", tuple(user_settings.money_limits.values())[-1])

    match button.widget_id:
        case SettingsParamsEnum.language.value:
            await dialog_manager.switch_to(SettingsStates.language)
        case SettingsParamsEnum.money_limit.value:
            await dialog_manager.switch_to(SettingsStates.money_limit)
        case SettingsParamsEnum.default_currency.name:
            await dialog_manager.switch_to(SettingsStates.currency)
    await callback.answer(button.widget_id)


async def edit_language_param(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    language_code: ManagedRadio = dialog_manager.find("radio_lang")
    if selected_language := language_code.get_checked():
        dialog_manager.dialog_data["language_code"] = selected_language
    await dialog_manager.switch_to(SettingsStates.select_param)


async def edit_money_limit_param(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(SettingsStates.select_param)


async def edit_currency_param(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    monetary_currency: ManagedRadio = dialog_manager.find("radio_curr")
    if selected_currency := monetary_currency.get_checked():
        dialog_manager.dialog_data["currency_type"] = selected_currency
    await dialog_manager.switch_to(SettingsStates.select_param)
