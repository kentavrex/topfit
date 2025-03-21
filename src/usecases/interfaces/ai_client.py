from abc import ABC, abstractmethod
from typing import Self

from usecases.schemas import DishRecommendation, NutritionData


class AIClientInterface(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def _send_request(self, system_message: str, user_message: str) -> str: ...

    @abstractmethod
    async def recognize_meal_by_text(self, message: str) -> NutritionData: ...

    @abstractmethod
    async def get_dish_recommendation(self, message: str) -> DishRecommendation: ...
