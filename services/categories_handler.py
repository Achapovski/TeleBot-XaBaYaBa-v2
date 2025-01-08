from decimal import Decimal

from custom_types.types import DefaultMoneyUnit
from database.enums import TimeIntervalsEnum, MonetaryCurrenciesEnum, ExpensesEnum
from validation.db_models import ValidCategoryModel


def compute_money_value_with_timestamps(categories: list[ValidCategoryModel], time_interval: str) -> DefaultMoneyUnit:
    total_expenses = 0
    for category in categories:
        total_expenses += getattr(category, time_interval)
    return DefaultMoneyUnit(total_expenses)


def compute_expected_costs(time_interval: str, money_limits: dict[str | int, str]) -> DefaultMoneyUnit:
    match time_interval:
        case ExpensesEnum.quarter.value:
            index = 3
        case ExpensesEnum.half_year.value:
            index = 6
        case ExpensesEnum.year.value:
            index = 12
        case _:
            index = 1
        
    result = sum([*map(lambda x: Decimal(x), [*money_limits.values()][slice(index)])])
    return DefaultMoneyUnit(result)
