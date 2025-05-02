import datetime
from abc import ABC, abstractmethod
from typing import Self

from usecases.schemas import (
    UserSchema,
    DishData,
    DishSchema,
    NutritionData,
    NutritionSchema,
)


class DBRepositoryInterface(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def create_user(self, user: UserSchema) -> None: ...

    @abstractmethod
    async def get_users(self) -> list[UserSchema]: ...

    @abstractmethod
    async def save_dish(self, dish_data: DishData) -> DishSchema: ...

    @abstractmethod
    async def add_statistics_obj(self, user_id: int, dish_id: int, like: bool = True) -> None: ...

    @abstractmethod
    async def get_user_dishes_history_by_period(
            self, user_id: int, valid_from_dt: datetime.datetime, valid_to_dt: datetime.datetime
    ) -> list[DishSchema]: ...

    @abstractmethod
    async def get_user_dishes_history(self, user_id: int, limit: int = 50) -> list[str]: ...

    @abstractmethod
    async def save_user_recommendation(self, user_id: int, dish_id: int) -> None: ...

    @abstractmethod
    async def save_nutrition(self, nutrition_data: NutritionData) -> NutritionSchema: ...

    @abstractmethod
    async def set_user_nutrition_goal(self, user_id: int, nutrition_goal_id: int) -> None: ...

    @abstractmethod
    async def get_user_nutrition_goal(self, user_id: int) -> NutritionSchema | None: ...
