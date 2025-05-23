from abc import ABC, abstractmethod
from typing import BinaryIO, Self

from usecases.schemas import DishData, DishRecommendation


class AIClientInterface(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def _send_request(
        self, system_message: str, user_message: str, attachments: list[str] | None = None, additional_message: str = ""
    ) -> str: ...

    @abstractmethod
    async def recognize_meal_by_text(self, message: str, additional_message: str = "") -> DishData: ...

    @abstractmethod
    async def recognize_meal_by_text_from_audio(self, message: str, additional_message: str = "") -> DishData: ...

    @abstractmethod
    async def recognize_meal_by_image(
        self, dish_bytes: BinaryIO, mime_type: str, additional_message: str = ""
    ) -> DishData: ...

    @abstractmethod
    async def get_dish_recommendation(self, message: str, additional_message: str = "") -> DishRecommendation: ...
