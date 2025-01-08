from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, SmallInteger, DateTime, func, DECIMAL
from sqlalchemy import JSON, select, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped

from custom_types.types import DefaultMoneyUnit
from database.utils import get_current_date_config
from validation.db_models import MonetaryCurrenciesEnumConfig


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__}: {"".join(cols)} >"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=False, unique=True)
    username = Column(String(64))
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64))
    joined_date = Column(DateTime, server_default=func.now(), nullable=False)
    settings: Mapped["Settings"] = relationship(back_populates="user")
    categories: Mapped[list["Category"]] = relationship(back_populates="user")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    settings_options = Column(JSON, nullable=False)
    user: Mapped["User"] = relationship(back_populates="settings")


class Category(Base):
    __tablename__ = "categories"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, unique=True)
    title = Column(String(40), unique=False, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    day_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    week_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    month_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    quarter_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    half_year_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    year_expenses = Column(DECIMAL, nullable=False, default=DefaultMoneyUnit())
    date_config_string = Column(String, nullable=False, server_default=get_current_date_config())
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    user_joined_date = Column(DateTime, nullable=True,
                              default=select(User.joined_date).select_from(User).where(user_id == User.id).limit(1))
    user: Mapped["User"] = relationship(back_populates="categories")
    aliases_list: Mapped[list["Alias"]] = relationship(back_populates="category_name")

    __table_args__ = (UniqueConstraint("title", "user_id", name="title_user_id_field"), )
    repr_cols = (id, title, day_expenses)


class Alias(Base):
    __tablename__ = "aliases"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True, unique=True)
    title = Column(String(20), nullable=False, unique=False)
    category_id = Column(SmallInteger, ForeignKey("categories.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_name: Mapped["Category"] = relationship(back_populates="aliases_list")
