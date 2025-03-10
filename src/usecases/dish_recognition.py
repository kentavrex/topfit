import json

from usecases.interfaces import DBRepositoryInterface, AIClientInterface
from usecases.schemas import DishData, DishSchema


class DishRecognitionUseCase:
    def __init__(self, ai_client: AIClientInterface, db_repository: DBRepositoryInterface):
        self._ai_client = ai_client
        self._db = db_repository

    async def _save_dish_to_db(self, dish_data: DishData) -> DishSchema:
        async with self._db as db:
            return await db.save_dish(dish_data)

    async def recognize_dish_from_text(self, dish_name: str) -> DishSchema:
        async with self._ai_client as ai_client:
            dish_nutrition_data = await ai_client.recognize_meal_by_text(message=dish_name)
            return await self._save_dish_to_db(dish_data=DishData(name=dish_name, **dish_nutrition_data.model_dump()))

    async def recognize_dish_from_image(self, image_url: str) -> DishSchema:
        # Логика распознавания блюда по изображению через нейросеть
        pass

    async def recognize_dish_from_audio(self, audio_file: str) -> DishSchema:
        # Логика распознавания блюда по аудио
        pass
