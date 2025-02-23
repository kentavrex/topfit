import datetime

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.config import settings


class Base(DeclarativeBase): ...


class DailyIntake(Base):
    __tablename__ = "daily_intakes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    date: Mapped[datetime.date] = mapped_column()
    protein: Mapped[float] = mapped_column(default=0.0)  # Белки
    fat: Mapped[float] = mapped_column(default=0.0)  # Жиры
    carbohydrates: Mapped[float] = mapped_column(default=0.0)  # Углеводы
    calories: Mapped[float] = mapped_column(default=0.0)  # Калории

    user: Mapped["User"] = relationship(back_populates="daily_intakes")

    def __repr__(self) -> str:
        return f"<DailyIntake user_id={self.user_id} date={self.date} calories={self.calories}>"


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    protein: Mapped[float]
    fat: Mapped[float]
    carbohydrates: Mapped[float]
    calories: Mapped[float]
    image_url: Mapped[str | None]  # Для хранения изображения из s3

    def __repr__(self) -> str:
        return f"<Dish name={self.name} calories={self.calories}>"


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now(settings.moscow_tz))

    user: Mapped["User"] = relationship(back_populates="recommendation_history")
    dish: Mapped["Dish"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<RecommendationHistory user_id={self.user_id} "
            f"dish_name={self.dish.name}"
            f" recommended_at={self.created_at}>"
        )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"))
    like: Mapped[bool]  # Оценка блюда (нравится/не нравится)

    user: Mapped["User"] = relationship(back_populates="preferences")
    dish: Mapped["Dish"] = relationship()

    def __repr__(self) -> str:
        return f"<UserPreference user_id={self.user_id} dish_name={self.dish.name} like={self.like}>"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None]

    daily_intakes: Mapped[list["DailyIntake"]] = relationship(back_populates="user")
    recommendations: Mapped[list["RecommendationHistory"]] = relationship(back_populates="user")
    preferences: Mapped[list["UserPreference"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User_id={self.telegram_id} username={self.username}>"
