from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select, and_, column, Result, case
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from custom_types.types import DefaultMoneyUnit
from database.enums import ExpensesEnum, MonetaryCurrenciesEnum, TimeIntervalsEnum
from database.models import Category, User as UserModel, Base, Alias, Settings
from utils.date import DateConfig
from validation.db_models import (ValidUserModel, ValidSettingsModel, ValidSettingsParams,
                                  ValidCategoryModel, default_factory, ValidAliasesModel, CategoryDTO)
from aiogram.types import User

logger = getLogger(__name__)


class SettingsDBRequests:
    model = Settings

    @classmethod
    async def add_params(cls, session_maker: async_sessionmaker, user: User) -> None:
        async with (session_maker as session):
            stmt = insert(cls.model).values(
                ValidSettingsModel(id=user.id, settings_options=ValidSettingsParams()).model_dump()
            )
            on_conflict = stmt.on_conflict_do_nothing()

            await session.execute(on_conflict)
            await session.commit()

    @classmethod
    async def update_params(cls, session_maker: async_sessionmaker, user_id: int, **kwargs) -> None:
        if money_limit := kwargs.get("money_limits"):
            month = datetime.now().month
            req = await cls.get_params(session_maker=session_maker, user_id=user_id)
            kwargs["money_limits"] = req.money_limits
            kwargs["money_limits"].update(default_factory(money_limit, default_month=month))

        async with session_maker as session:
            stmt = update(cls.model).values(settings_options=ValidSettingsParams(**kwargs).model_dump()).where(
                user_id == cls.model.id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_params(cls, session_maker: async_sessionmaker, user_id: int, *columns: str) -> ValidSettingsParams:
        columns = (column(col) for col in columns) if columns else (cls.model,)

        async with session_maker as session:
            stmt = select(*columns).select_from(cls.model).where(user_id == cls.model.id)
            result: Result = await session.execute(stmt)

        return ValidSettingsModel.model_validate(result.scalars().first(), from_attributes=True).settings_options


class UserDBRequests:
    model = UserModel

    @classmethod
    async def add_user(cls, session_maker: async_sessionmaker, user: User):
        async with session_maker as session:
            user_params: dict[str, Any] = ValidUserModel(**dict(user)).model_dump(exclude={"joined_date"})

            stmt = insert(cls.model).values(user_params)
            on_conflict = stmt.on_conflict_do_update(index_elements=["id"], set_=user_params)

            await session.execute(on_conflict)
            await session.commit()

        await SettingsDBRequests.add_params(session_maker=session_maker, user=user)

    @classmethod
    async def get_user(cls, session_maker: async_sessionmaker, user_id: int):
        async with session_maker as session:
            stmt = select(cls.model).select_from(cls.model).where(user_id == cls.model.id)
            result = await session.execute(stmt)
            user = result.scalars().first()
        return user

    @classmethod
    async def update_user(cls, session_maker: async_sessionmaker, user_id: int, **kwargs):
        async with session_maker as session:
            stmt = update(cls.model).values(ValidUserModel(id=user_id, **kwargs).model_dump())
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_categories(cls, session_maker: async_sessionmaker,
                             user_id: int, limit: int = None) -> list[CategoryDTO]:
        async with session_maker as session:
            stmt = select(cls.model).select_from(cls.model).where(user_id == cls.model.id).options(
                selectinload(cls.model.categories))
            result = await session.execute(stmt)
            user = result.scalars().first().categories
        return [CategoryDTO.model_validate(row, from_attributes=True) for row in user][slice(limit)]


class CategoryDBRequests:
    model = Category

    @classmethod
    async def add_category(cls, session_maker: async_sessionmaker, user_id: int,
                           category_name: str, money_value: Decimal | int | float | str = DefaultMoneyUnit()) -> None:
        values = {key.value: money_value for key in ExpensesEnum}
        params = ValidCategoryModel(title=category_name.lower(), user_id=user_id, **values).model_dump()

        async with session_maker as session:
            stmt = insert(cls.model).values(**params)
            on_conflict = stmt.on_conflict_do_update(index_elements=["title", "user_id"],
                                                     set_=await cls._generate_params_on_conflict(
                                                         session_maker=session_maker, category_name=category_name,
                                                         user_id=user_id, old_params=params))
            await session.execute(on_conflict)
            await session.commit()

    @classmethod
    async def get_category(cls, session_maker: async_sessionmaker, user_id: int = None,
                           category_name: str = None, category_id: int = None) -> ValidCategoryModel:

        async with session_maker as session:
            if category_id:
                stmt = select(cls.model).select_from(cls.model).where(category_id == cls.model.id)
            else:
                stmt = select(cls.model).select_from(cls.model).where(
                    and_(user_id == cls.model.user_id, category_name == cls.model.title))

            result = await session.execute(stmt)

        if category := result.scalars().first():
            return ValidCategoryModel.model_validate(category, from_attributes=True)

    @classmethod
    async def update_category(cls, session_maker: async_sessionmaker, category_id: int,
                              data: dict, money_value: Decimal | int | float | str):
        cat = (await cls.get_category(session_maker=session_maker, category_id=category_id)).model_dump()
        values = {key: cat[key] + money_value for key in data}

        async with session_maker as session:
            stmt = update(cls.model).values(**values).where(category_id == cls.model.id)
            await session.execute(stmt)
            await session.commit()
        return

    @classmethod
    async def update_date_config_string(cls, session_maker: async_sessionmaker, category_id: int = None,
                                        user_id: int = None):
        data_date_config = []

        if not category_id and user_id:
            cats = await UserDBRequests.get_categories(session_maker=session_maker, user_id=user_id)
            data_date_config += [(cat.id, cat.date_config_string) for cat in cats]
        elif not user_id and category_id:
            cat = await cls.get_category(session_maker=session_maker, category_id=category_id)
            data_date_config += [(category_id, cat.date_config_string)]

        time_intervals = defaultdict(list)
        for cat_id, element in data_date_config:
            time_intervals[cat_id] += DateConfig().compare_date_configs(DateConfig(element))

        await cls._update_category_date_configs(session_maker=session_maker, category_ids=time_intervals)

    @classmethod
    async def _update_category_date_configs(cls, session_maker: async_sessionmaker, category_ids: dict[str, list[int]]):
        async with session_maker as session:
            stmt = update(cls.model).where(cls.model.id.in_(category_ids)).values(
                **(await cls._generate_expenses_values_for_date_config(category_ids))
            )
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def _generate_expenses_values_for_date_config(cls, categories_to_update: dict[str, list[int]]):
        # Выбирается любой список временных интервалов, т.к. обновление параметров происходит в любом случае раз
        # в день и ДО обновление значений пользователем
        intervals = tuple(categories_to_update.values())[0]
        values = {}

        for interval in intervals:
            values[getattr(ExpensesEnum, f"{interval}").value] = DefaultMoneyUnit()

        values["date_config_string"] = DateConfig().date_config
        return values

    @classmethod
    async def _generate_params_on_conflict(cls, session_maker: async_sessionmaker, user_id: int,
                                           category_name: str, old_params: dict) -> dict:
        cat = await cls.get_category(session_maker=session_maker, user_id=user_id, category_name=category_name.lower())

        if not cat:
            return old_params
        clean_cat_params = cat.model_dump(exclude={"date_config_string", "user_id", "title"})
        return {key: old_params.get(key, 0) + value for key, value in clean_cat_params.items()}


class AliasDBRequests:
    model = Alias

    @classmethod
    async def get_alias(cls, session_maker: async_sessionmaker, user_id: int,
                        alias_name: str = None) -> ValidAliasesModel | None:
        options = [user_id == cls.model.user_id]
        if alias_name:
            options += [alias_name == cls.model.title]

        async with session_maker as session:
            stmt = select(cls.model).select_from(cls.model).where(
                and_(*options)
            ).options(selectinload(cls.model.category_name))
            result = await session.execute(stmt)

            if not (obj := result.scalars().first()):
                return
            return ValidAliasesModel.model_validate(obj, from_attributes=True)
            # return [ValidAliasesModel.model_validate(row, from_attributes=True) for row in obj]

    @classmethod
    async def add_alias(cls, session_maker: async_sessionmaker, alias: str, category_id: int, user_id: int):
        async with session_maker as session:
            stmt = insert(Alias).values(**ValidAliasesModel(
                title=alias.lower(), category_id=category_id, user_id=user_id).model_dump())
            do_nothing_on_conflict = stmt.on_conflict_do_nothing()

            await session.execute(do_nothing_on_conflict)
            await session.commit()
