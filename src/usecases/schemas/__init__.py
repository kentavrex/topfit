import datetime
from enum import Enum

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    class Config:
        from_attributes = True


class GoalType(Enum):
    LOSE_WEIGHT = "Сброс веса"
    SUPPORT_FORM = "Поддержка формы"
    GAIN_WEIGHT = "Набор массы"

    @classmethod
    def get_goal_options(cls):
        return "\n".join(f"{index + 1} - {goal.value}" for index, goal in enumerate(cls))

    @classmethod
    def from_number(cls, number: int):
        return list(cls)[number - 1]


class UserSchema(CustomBaseModel):
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    nutrition_goal_id: int | None = None


class NutritionGoalSchema(CustomBaseModel):
    height: float
    weight: float
    age: int
    is_male: bool
    nutrition_goal_type: GoalType

    def __str__(self):
        return (f"Height: {self.height}, Weight: {self.weight}, Age: {self.age},"
                f" IsMail: {self.is_male} Goal: {self.nutrition_goal_type.value}")


class NutritionData(CustomBaseModel):
    protein: float = 0.0
    fat: float = 0.0
    carbohydrates: float = 0.0
    calories: float = 0.0


class NutritionSchema(NutritionData):
    id: int


class DishData(NutritionData):
    name: str


class DishSchema(DishData):
    id: int


class DishRecommendation(DishData):
    receipt: str
    servings_count: int


class CountedStatisticsSchema(CustomBaseModel):
    user_id: int
    protein: float
    fat: float
    carbohydrates: float
    calories: float
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
