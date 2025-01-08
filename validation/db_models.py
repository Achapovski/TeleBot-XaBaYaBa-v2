from datetime import datetime
from decimal import Decimal
from email.policy import default
from typing import Union, Annotated

from database.enums import ExpensesEnum, LanguageCodesEnum, MonetaryCurrenciesEnum, TimeIntervalsEnum as Times
from custom_types.types import DefaultMoneyUnit

from pydantic import BaseModel, field_validator, ConfigDict, Field, constr, PlainSerializer, AliasChoices

from utils.date import DateConfig


def default_factory(default_value: str = str(DefaultMoneyUnit("0")), default_month: str | int = None) -> dict[int, str]:
    if not default_month:
        default_month = datetime.now().month
    return dict(((default_month, default_value),))


SerializedDecimal = Annotated[
    Decimal, PlainSerializer(lambda x: str(x), return_type=str)
]


class ConfigMixin:
    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, validate_default=True, extra="ignore"
    )


class MonetaryCurrenciesEnumConfig:
    def __init__(self, money_value: Decimal = DefaultMoneyUnit()):
        self.money_value = str(money_value)
        self.currencies_and_values = ((cur.value, money_value) for cur in MonetaryCurrenciesEnum)

    def to_dict(self):
        return dict(self.currencies_and_values)


class ValidUserModel(BaseModel, ConfigMixin):
    id: int
    username: Union[str, None] = None
    first_name: str
    last_name: Union[str, None] = None
    joined_date: Union[datetime | None] = None

    model_config = ConfigDict(strict=True, **ConfigMixin.model_config)


class ValidUserRelationshipModel(ValidUserModel, ConfigMixin):
    settings: "ValidSettingsModel"
    categories: list["ValidCategoryModel"]


class ValidSettingsModel(BaseModel, ConfigMixin):
    id: int
    settings_options: "ValidSettingsParams"


class ValidSettingsParams(BaseModel, ConfigMixin):
    language_code: LanguageCodesEnum = LanguageCodesEnum.ru
    monetary_currency: MonetaryCurrenciesEnum = MonetaryCurrenciesEnum.usd
    money_limits: dict[int, str] = Field(default_factory=default_factory)

    model_config = ConfigDict(use_enum_values=True, **ConfigMixin.model_config)


class ValidMonetaryModel(BaseModel, ConfigMixin):
    monetary_currencies: dict[str, SerializedDecimal] = MonetaryCurrenciesEnumConfig().to_dict()

    @field_validator("monetary_currencies")
    def checking_monetary_currencies_field(cls, value: dict[str, Decimal]):
        if value.__len__() != MonetaryCurrenciesEnum.__len__():
            raise ValueError(f"{cls.__name__} should be have length same {MonetaryCurrenciesEnum}")
        elif all([*map(lambda x: x in value.values(), MonetaryCurrenciesEnum)]):
            raise ValueError(f"'monetary_currencies' keys can only {MonetaryCurrenciesEnum.__name__} class attributes")
        return value


class ValidCategoryModel(BaseModel, ConfigMixin):
    title: constr(min_length=2, max_length=40)
    user_id: int
    day_expenses: Decimal = Field(default=DefaultMoneyUnit())
    week_expenses: Decimal = Field(default=DefaultMoneyUnit())
    month_expenses: Decimal = Field(default=DefaultMoneyUnit())
    quarter_expenses: Decimal = Field(default=DefaultMoneyUnit())
    half_year_expenses: Decimal = Field(default=DefaultMoneyUnit())
    year_expenses: Decimal = Field(default=DefaultMoneyUnit())
    date_config_string: str = Field(default=DateConfig().date_config)

    def __repr__(self):
        return (f"{self.__class__.__name__}(title = {self.title}, user = {self.user_id},"
                f" day_expenses = {self.day_expenses})")

    model_config = ConfigDict(defer_build=True)


class CategoryDTO(ValidCategoryModel):
    id: int
    created_date: datetime | None
    user_joined_date: datetime | None


class ValidCategoryRelationshipModel(ValidCategoryModel):
    user: ValidUserModel
    aliases_list: list["ValidAliasesModel"]


class ValidAliasesModel(BaseModel):
    title: str
    category_id: int
    user_id: int
