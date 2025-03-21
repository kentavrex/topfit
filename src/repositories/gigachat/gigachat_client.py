import json
import logging
import re
import ssl
import time
from functools import wraps

import httpx
from typing import Self

from usecases.errors import NotFoundError
from usecases.interfaces import AIClientInterface
from config import GigachatConfig
from usecases.schemas import NutritionData, DishRecommendation


def retry(retry_num: int = 3, retry_sleep_sec: int = 1):
    def decorator(func):
        """decorator"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """wrapper"""
            for attempt in range(retry_num):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    logging.error("Ошибка в ответе от AI client")
                    time.sleep(retry_sleep_sec)
                logging.error("Trying attempt %s of %s.", attempt + 1, retry_num)
            logging.error("func %s retry failed", func)
            raise Exception('Exceed max retry num: {} failed'.format(retry_num))
        return wrapper
    return decorator


class GigachatClient(AIClientInterface):
    def __init__(self, config: GigachatConfig) -> None:
        self._config = config
        self._access_token: str | None = None

        # Создание SSL-контекста для отключения проверки сертификатов
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE

    async def __aenter__(self) -> Self:
        await self._update_access_token()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    async def _update_access_token(self) -> None:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            'RqUID': 'b5cd3af6-8c96-457e-b807-641226b0040e',
            "Authorization": f"Basic {self._config.GIGACHAT_API_KEY}",
        }
        payload = {"scope": "GIGACHAT_API_PERS"}
        async with httpx.AsyncClient(verify=self._ssl_context) as client:
            response = await client.post(url, headers=headers, data=payload)

        response.raise_for_status()

        self._access_token = response.json()["access_token"]

    async def _send_request(self, system_message: str, user_message: str) -> str:
        """Отправляет запрос в GigaChat API для генерации ответа."""
        if not self._access_token:
            await self._update_access_token()

        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        payload = json.dumps({
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "update_interval": 0
        })
        async with httpx.AsyncClient(verify=self._ssl_context) as client:
            response = await client.post(url, headers=headers, content=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    async def _parse_json_response(message_response: str) -> dict:
        match = re.search(r'```json\s*\n(.*?)\n\s*```', message_response, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise NotFoundError("Not found json in AI client response")

    @retry()
    async def recognize_meal_by_text(self, message: str) -> NutritionData:
        system_message = (
        """
        Посчитай КБЖУ блюда.  
        Верни ответ строго в формате JSON, содержащий следующие поля:  
        - "calories" (float) — калории  
        - "protein" (float) — белки  
        - "fat" (float) — жиры  
        - "carbohydrates" (float) — углеводы  
        Формат ответа:
        ```json
        {"protein": 12.3, "fat": 1200.2, "carbohydrates": 21.2, "calories": 23.1}
        ```
        """
        )
        response = await self._send_request(system_message=system_message, user_message=message)
        response_parsed = await self._parse_json_response(response)
        return NutritionData(**response_parsed)

    @retry()
    async def get_dish_recommendation(self, message: str) -> DishRecommendation:
        system_message = (
            """Тебе нужно предложить пользователю блюдо на основании следующих данных:  
            1. Примерное (не точное) количество КБЖУ, к которому должно соответствовать блюдо.  
            2. Список прошлых блюд пользователя с их КБЖУ — эта информация поможет понять вкусовые 
            предпочтения пользователя.
            Важно:  
            - Блюдо не обязательно должно быть из прошлых блюд пользователя.  
            - Основная цель — чтобы предложенное блюдо примерно соответствовало заданному КБЖУ.  
            - В ответе должен быть указан сам рецепт (ингредиенты с граммировками).  
            Формат ответа: строго в формате JSON, содержащий:  
            - "protein" (float) — белки  
            - "fat" (float) — жиры  
            - "carbohydrates" (float) — углеводы  
            - "calories" (float) — калории  
            - "name" (str) — название блюда  
            - "receipt" (str) — рецепт приготовления  
            Пример ответа:
            ```json
            {"protein": 25.0, "fat": 10.0, "carbohydrates": 50.0, "calories": 400.0,
             "name": "Название блюда", "receipt": "Рецепт блюда}
            ```
            """
        )
        response = await self._send_request(system_message=system_message, user_message=message)
        response_parsed = await self._parse_json_response(response)
        return DishRecommendation(**response_parsed)
