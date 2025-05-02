import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import current_moscow_date


class Base(DeclarativeBase): ...


class Nutrition(Base):
    __tablename__ = "nutrition"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    protein: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    fat: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    carbohydrates: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    calories: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)

    def __repr__(self) -> str:
        return (f"<Nutrition protein={self.protein} fat={self.fat} "
                f"carbohydrates={self.carbohydrates} calories={self.calories}>")


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nutrition_id: Mapped[int] = mapped_column(ForeignKey("nutrition.id"))

    nutrition: Mapped["Nutrition"] = relationship()

    def __repr__(self) -> str:
        return f"<Dish name={self.name} calories={self.nutrition.calories}>"


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), default=current_moscow_date)

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
    date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), default=current_moscow_date)
    like: Mapped[bool]  = mapped_column(default=True) # Оценка блюда (нравится/не нравится)

    user: Mapped["User"] = relationship(back_populates="statistics")
    dish: Mapped["Dish"] = relationship()

    def __repr__(self) -> str:
        return f"<Statistics user_id={self.user_id} date={self.date} add dish_id={self.dish_id}>"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(100))
    nutrition_goal_id: Mapped[int | None] = mapped_column(ForeignKey("nutrition.id"))

    statistics: Mapped[list["Statistics"]] = relationship(back_populates="user")
    recommendation_history: Mapped[list["RecommendationHistory"]] = relationship(back_populates="user")
    nutrition_goal: Mapped["Nutrition"] = relationship()

    def __repr__(self) -> str:
        return f"<User_id={self.telegram_id} username={self.username}>"
