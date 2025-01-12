from aiogram.fsm.state import State, StatesGroup


class InitStates(StatesGroup):
    start = State()
    pre_settings = State()


class SettingsStates(StatesGroup):
    select_param = State()
    language = State()
    money_limit = State()
    currency = State()
    confirm_params = State


class PreSettingsStates(StatesGroup):
    language = State()
    currency = State()
    money_limit = State()
    categories = State()


class WorkStates(StatesGroup):
    add_category = State()
    choice_category_for_alias = State()
    assign_alias_to_category = State()
    confirm_alias_choice = State()


class UserCategoriesStates(StatesGroup):
    get_categories = State()
