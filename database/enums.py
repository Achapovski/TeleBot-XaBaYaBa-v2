from enum import Enum


class TimeField:
    def __init__(self, readable_name: str, db_name: str):
        self.readable_name = readable_name
        self.db_name = db_name


class BaseFormatter(Enum):
    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return self.__str__()


class LanguageCodesEnum(BaseFormatter):
    ru = "ru"
    en = "en"


class MonetaryCurrenciesEnum(BaseFormatter):
    byn = "byn"
    usd = "usd"
    rub = "rub"
    eur = "eur"


class ExpensesEnum(BaseFormatter):
    day = "day_expenses"
    week = "week_expenses"
    month = "month_expenses"
    quarter = "quarter_expenses"
    half_year = "half_year_expenses"
    year = "year_expenses"


class TimeIntervalsEnum(BaseFormatter):
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    half_year = "half_year"
    year = "year"


class SettingsParamsEnum(BaseFormatter):
    pass
