from aiogram.enums import ParseMode

from database.enums import ExpensesEnum, MonetaryCurrenciesEnum
from dialogs.dialogs_getters import (get_message_start_win, get_pre_settings_win,
                                     get_language_choice_win, get_currency_choice_win,
                                     get_default_money_value_win, lets_work, get_user_categories, get_category_alias,
                                     confirm_category_alias, get_category_list, get_category_period_buttons,
                                     get_settings_params)
from dialogs.dialog_factories import MoneyValueInputFactory, CategoryProcessingFactory, AliasProcessingFactory

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row, Radio, Back, Next, Column, Group

from dialogs.dialogs_states import InitStates, PreSettingsStates, WorkStates, UserCategoriesStates, SettingsStates
from dialogs.dialogs_handlers import (start_handler, pre_settings_handler,
                                      continue_with_default, continue_dialog,
                                      set_language_default, set_currency,
                                      lets_work_handler, set_alias_for_category, change_category_page, edit_date_period,
                                      edit_currency_type)
from keyboards.kbd_builder import KeyboardBuilder

starting_dialog = Dialog(
    Window(
        Format("{message}"),
        Button(
            text=Format("{button_start}"),
            on_click=start_handler,
            id="button_start"
        ),
        state=InitStates.start,
        getter=get_message_start_win
    ),
    Window(
        Format("{message}"),
        Row(Button(
            text=Format("{button_pre_settings}"),
            on_click=pre_settings_handler,
            id="button_back"
        ),
            Button(
                text=Format("{button_continue}"),
                on_click=continue_with_default,
                id="button_continue"
            )
        ),
        getter=get_pre_settings_win,
        state=InitStates.pre_settings,
    )
)

pre_settings_dialog = Dialog(
    Window(
        Format("{message}"),
        Radio(
            checked_text=Format("🔘{item[0]}"),
            unchecked_text=Format("⚪️{item[0]}"),
            id="radio_lang",
            item_id_getter=lambda x: x[1],
            items="languages",
        ),
        Row(
            Button(text=Format("{button_confirm}"),
                   id="confirm_button",
                   on_click=set_language_default
                   ),
        ),
        getter=get_language_choice_win,
        state=PreSettingsStates.language
    ),
    Window(
        Format("{message}"),
        Radio(
            checked_text=Format("🔘{item[0]}"),
            unchecked_text=Format("⚪️{item[0]}"),
            id="radio_curr",
            item_id_getter=lambda x: x[1],
            items="currency",
        ),
        Row(
            Button(
                text=Format("{button_confirm}"),
                id="confirm_button",
                on_click=set_currency
            ),
            Button(
                Format("{button_back}"),
                id="button_back",
                on_click=Back()
            )
        ),
        getter=get_currency_choice_win,
        state=PreSettingsStates.currency
    ),
    Window(
        Format(
            text="{message}",
            when="is_default",
        ),
        Format(
            text="{success_message}",
            when="is_selected"
        ),
        Row(
            Button(
                Format("{button_confirm}"),
                id="confirm",
                when="is_selected",
                on_click=lets_work_handler
            ),
            Button(
                Format("{button_back}"),
                id="back",
                when="is_selected",
                on_click=Back()
            )
        ),
        TextInput(
            id="text_input",
            on_error=MoneyValueInputFactory.money_value_input_error,
            on_success=MoneyValueInputFactory.money_value_input_success,
            type_factory=MoneyValueInputFactory.money_value_input_factory,
        ),
        getter=get_default_money_value_win,
        state=PreSettingsStates.money_limit,
        parse_mode=ParseMode.HTML,
    ),
)

working_dialog = Dialog(
    Window(
        Format("{message}"),
        TextInput(
            id="text_input",
            on_error=CategoryProcessingFactory.user_category_money_error,
            on_success=CategoryProcessingFactory.user_category_money_success,
            type_factory=CategoryProcessingFactory.user_category_money_factory,
        ),
        getter=lets_work,
        state=WorkStates.add_category,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        Format(
            text="{message}",
        ),
        Column(Radio(
            checked_text=Format("🔘\t\t{item[0]}"),
            unchecked_text=Format("⚪️\t\t{item[0]}"),
            id="radio_categories",
            item_id_getter=lambda x: x[1],
            items="categories",
        ),
            Button(
                Format("{button_confirm}"),
                id="alias_choice_button",
                on_click=Next(),
                when="show_button"
            ),
        ),
        getter=get_user_categories,
        state=WorkStates.choice_category_for_alias,
        parse_mode=ParseMode.HTML
    ),
    Window(
        Format("{message}"),
        TextInput(
            id="alias_input",
            on_error=AliasProcessingFactory.alias_choice_error,
            on_success=AliasProcessingFactory.alias_choice_success,
            type_factory=AliasProcessingFactory.alias_validate_factory,
        ),
        Button(
            text=Format("{button_back}"),
            id="button_back",
            on_click=Back()
        ),
        getter=get_category_alias,
        state=WorkStates.assign_alias_to_category,
    ),
    Window(
        Format("{message}"),
        Row(
            Button(
                Format("{button_confirm}"),
                id="confirm_button",
                on_click=set_alias_for_category
            ),
            Button(
                text=Format("{button_back}"),
                id="button_back",
                on_click=Back()
            ),
        ),
        getter=confirm_category_alias,
        state=WorkStates.confirm_alias_choice,
        parse_mode=ParseMode.HTML,
    )
)
categories_dialog = Dialog(
    Window(
        Format("{message}"),
        Row(
            Button(
                Format("{button_back}"),
                on_click=change_category_page,
                id="button_back",
                when="show_pagination"
            ),
            Button(
                Format("{button_calendar}"),
                on_click=change_category_page,
                id="button_calendar",
            ),
            Button(
                Format("{button_info}"),
                id="button_info",
                when="show_pagination"
            ),
            Button(
                Format("{button_currencies}"),
                on_click=change_category_page,
                id="button_currencies",
            ),
            Button(
                Format("{button_next}"),
                on_click=change_category_page,
                id="button_next",
                when="show_pagination"
            ),
        ),
        KeyboardBuilder.from_enum(ExpensesEnum, handler=edit_date_period, width=3,
                                  enum_value=False, when="show_periods", postfix="_button")
        # Group(
        #     Button(
        #         Format("{day_button}"),
        #         id=ExpensesEnum.day.name,
        #         on_click=edit_date_period
        #     ),
        #     Button(
        #         Format("{week_button}"),
        #         id=ExpensesEnum.week.name,
        #         on_click=edit_date_period
        #     ),
        #     Button(
        #         Format("{month_button}"),
        #         id=ExpensesEnum.month.name,
        #         on_click=edit_date_period
        #     ),
        #     Button(
        #         Format("{quarter_button}"),
        #         id=ExpensesEnum.quarter.name,
        #         on_click=edit_date_period
        #     ),
        #     Button(
        #         Format("{half_year_button}"),
        #         id=ExpensesEnum.half_year.name,
        #         on_click=edit_date_period
        #     ),
        #     Button(
        #         Format("{year_button}"),
        #         id=ExpensesEnum.year.name,
        #         on_click=edit_date_period
        #     ),
        #     width=3,
        #     when="show_periods"
        # ),
        ,
        KeyboardBuilder.from_enum(MonetaryCurrenciesEnum, edit_currency_type, when="show_currencies"),
        # Group(
        #     Button(
        #         Format("{byn}"),
        #         id=MonetaryCurrenciesEnum.byn.value,
        #         on_click=edit_currency_type
        #     ),
        #     Button(
        #         Format("{usd}"),
        #         id=MonetaryCurrenciesEnum.usd.value,
        #         on_click=edit_currency_type
        #     ),
        #     Button(
        #         Format("{rub}"),
        #         id=MonetaryCurrenciesEnum.rub.value,
        #         on_click=edit_currency_type
        #     ),
        #     Button(
        #         Format("{eur}"),
        #         id=MonetaryCurrenciesEnum.eur.value,
        #         on_click=edit_currency_type
        #     ),
        #     width=4,
        #     when="show_currencies",
        # ),
        getter=(get_category_list, get_category_period_buttons),
        state=UserCategoriesStates.get_categories,
        parse_mode=ParseMode.HTML,
    ),
)

settings_dialog = Dialog(
    Window(
        Format("{message}"),
        Button(Const("text"), id="button", on_click=Back()),
        getter=get_settings_params,
        state=SettingsStates.select_param,
        parse_mode=ParseMode.HTML,
    ),
)
