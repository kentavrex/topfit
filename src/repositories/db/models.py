import datetime

import pytz
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import settings


class Base(DeclarativeBase): ...


class Nutrition(Base):
    __tablename__ = "nutrition"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    protein: Mapped[float]
    fat: Mapped[float]
    carbohydrates: Mapped[float]
    calories: Mapped[float]

    def __repr__(self) -> str:
        return (f"<Nutrition protein={self.protein} fat={self.fat} "
                f"carbohydrates={self.carbohydrates} calories={self.calories}>")


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    nutrition_id: Mapped[int] = mapped_column(ForeignKey("nutrition.id"))

    nutrition: Mapped["Nutrition"] = relationship()

    def __repr__(self) -> str:
        return f"<Dish name={self.name} calories={self.nutrition.calories}>"


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(settings.moscow_tz).replace(tzinfo=None))

    user: Mapped["User"] = relationship(back_populates="recommendation_history")
    dish: Mapped["Dish"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<RecommendationHistory user_id={self.user_id} "
            f"dish_name={self.dish.name}"
            f" recommended_at={self.created_at}>"
        )


class Statistics(Base):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    date: Mapped[datetime.date] =  mapped_column(default=datetime.datetime.now(settings.moscow_tz).date())
    like: Mapped[bool]  = mapped_column(default=True) # Оценка блюда (нравится/не нравится)

    user: Mapped["User"] = relationship(back_populates="statistics")
    dish: Mapped["Dish"] = relationship()

    def __repr__(self) -> str:
        return f"<Statistics user_id={self.user_id} date={self.date} add dish_id={self.dish_id}>"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None]
    nutrition_goal_id: Mapped[int | None] = mapped_column(ForeignKey("nutrition.id"))

    statistics: Mapped[list["Statistics"]] = relationship(back_populates="user")
    recommendation_history: Mapped[list["RecommendationHistory"]] = relationship(back_populates="user")
    nutrition_goal: Mapped["Nutrition"] = relationship()

    def __repr__(self) -> str:
        return f"<User_id={self.telegram_id} username={self.username}>"
