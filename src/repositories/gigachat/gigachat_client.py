import json
import logging
import re
import ssl
import time
from functools import wraps

import httpx
from typing import Self, BinaryIO

from usecases.errors import NotFoundError
from usecases.interfaces import AIClientInterface
from config import GigachatConfig
from usecases.schemas import NutritionData, DishRecommendation, DishData


def retry(retry_num: int = 3, retry_sleep_sec: int = 2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retry_num):
                try:
                    if attempt != 0:
                        kwargs['additional_message'] = ("Ответ должен быть в формате JSON и в формате ответа из примера. "
                                                        "Пожалуйста, отправь данные снова, но строго в формате JSON.")
                    return await func(*args, **kwargs)
                except json.JSONDecodeError as e:
                    logging.error(f"Ошибка в ответе от AI client (JSON Decode Error): {e}")
                except Exception as e:
                    logging.error(f"Ошибка в ответе от AI client: {e}")

                if attempt < retry_num - 1:
                    logging.error(f"Попытка {attempt + 1} не удалась.")
                    time.sleep(retry_sleep_sec)
                else:
                    logging.error(f"Не удалось выполнить {func.__name__} после {retry_num} попыток")
                    raise Exception(f'Превышено максимальное количество попыток для {func.__name__}')
            return None

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

    async def _send_request(self,
                            system_message: str,
                            user_message: str | None = None,
                            attachments: list[str] | None = None,
                            additional_message: str = '') -> str:
        """Отправляет запрос в GigaChat API для генерации ответа."""
        if not self._access_token:
            await self._update_access_token()

        system_message = f"{additional_message}\n {system_message}"
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        logging.info(f"system_message={system_message}\n user_message={user_message}")
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "system", "content": system_message}],
            "stream": False,
            "update_interval": 0,
        }
        if user_message:
            payload["messages"] += {"role": "user", "content": user_message}
        if attachments:
            payload["messages"] += {"role": "user", "attachments": attachments}
            payload["model"] = "GigaChat-Pro"
        else:
            payload["model"] = "GigaChat"

        async with httpx.AsyncClient(verify=self._ssl_context) as client:
            response = await client.post(url, headers=headers, content=json.dumps(payload))
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def _upload_gigachat_file(self, file_bytes: BinaryIO, mime_type: str) -> str | None:
        url = "https://gigachat.devices.sberbank.ru/api/v1/files"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }
        files = {
            "file": ("file.png", file_bytes, mime_type)
        }
        data = {"purpose": "general"}
        try:
            async with httpx.AsyncClient(verify=self._ssl_context) as client:
                response = await client.post(url, headers=headers, files=files, data=data)

            if response.status_code == 200:
                return response.json()['id']
            else:
                print(f"Ошибка: {response.status_code}, {response.text}")
                return None
        except httpx.RequestError as e:
            print(f"Ошибка при отправке запроса: {e}")
            return None

    @staticmethod
    async def _parse_json_response(message_response: str) -> dict:
        logging.debug(f"Received message response: {message_response}")
        match = re.search(r'```json\s*\n(.*?)\n\s*```', message_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logging.error(f"JSON decoding error: {e}")
                raise
        raise NotFoundError("Not found json in AI client response")

    @retry()
    async def recognize_meal_by_text(self, message: str, additional_message: str = '') -> DishData:
        system_message = (
        """
        Посчитай КБЖУ блюда.  
        Верни ответ строго в формате JSON, содержащий следующие поля:
        - "name" (str) - название 
        - "calories" (float) — калории  
        - "protein" (float) — белки  
        - "fat" (float) — жиры  
        - "carbohydrates" (float) — углеводы  
        Формат ответа:
        ```json
        {"name": "Ризотто с курицей, "protein": 25.3, "fat": 10.2, "carbohydrates": 150.2, "calories": 400.1}
        ```
        """
        )
        response = await self._send_request(system_message=system_message,
                                            user_message=message,
                                            additional_message=additional_message)
        response_parsed = await self._parse_json_response(response)
        return DishData(**response_parsed)

    @retry()
    async def get_dish_recommendation(self, message: str, additional_message: str = '') -> DishRecommendation:
        system_message = (
            """Тебе нужно предложить пользователю блюдо на основании следующих данных:
            1. Блюдо не должно сильно превышать норму (белки, жиры, углеводы, калории).  
            2. Список прошлых блюд пользователя с их КБЖУ — эта информация поможет понять вкусовые предпочтения 
            пользователя.
            Важно:
            - Блюдо не обязательно должно быть из прошлых блюд пользователя.
            - КБЖУ 1 порции блюда должно укладываться в дневную норму КБЖУ клиента - может быть меньше,
             главное не больше.
            - Рецепт может быть на несколько порций, в ответе КБЖУ возвращай для всех порций.

            Формат ответа: строго в формате JSON, содержащий:
            - "protein" (float) — белки во всех порциях
            - "fat" (float) — жиры во всех порциях
            - "carbohydrates" (float) — углеводы во всех порциях
            - "calories" (float) — калории во всех порциях
            - "name" (str) — название блюда
            - "receipt" (str) — рецепт (включая ингредиенты с граммировками и приготовлением)
            - "servings_count" (int) - кол-во порций, которые получаются в рецепте

            Пример ответа:
            ```json
            {
                "protein": 25.0,
                "fat": 10.0,
                "carbohydrates": 50.0,
                "calories": 400.0,
                "name": "Ризотто с цыпленком",
                "receipt": "Рецепт (включая ингредиенты с граммировками и приготовлением)"
                "servings_count": 5
            }
            ```
            """
        )
        response = await self._send_request(system_message=system_message,
                                            user_message=message,
                                            additional_message=additional_message)
        response_parsed = await self._parse_json_response(response)
        return DishRecommendation(**response_parsed)

    @retry()
    async def recognize_meal_by_image(
            self, dish_bytes: BinaryIO, mime_type: str, additional_message: str = ''
    ) -> DishData:
        file_id = await self._upload_gigachat_file(file_bytes=dish_bytes, mime_type=mime_type)
        if not file_id:
            logging.error("Ошибка загрузки файла")
            raise

        system_message = (
        """
        Посчитай КБЖУ блюда из приложенного файла.  
        Верни ответ строго в формате JSON, содержащий следующие поля:
        - "name" (str) - название 
        - "calories" (float) — калории  
        - "protein" (float) — белки  
        - "fat" (float) — жиры  
        - "carbohydrates" (float) — углеводы  
        Формат ответа:
        ```json
        {"name": "Ризотто с курицей, "protein": 25.3, "fat": 10.2, "carbohydrates": 150.2, "calories": 400.1}
        ```
        """
        )
        find_meal_text = "Что из еды представлено, просто перечисли."
        photo_recognize_text = await self._send_request(system_message=find_meal_text,
                                                        user_message=find_meal_text,
                                                        attachments=[file_id],
                                                        additional_message=additional_message)
        response = await self._send_request(system_message=system_message,
                                                        user_message=photo_recognize_text,
                                                        attachments=[file_id],
                                                        additional_message=additional_message)
        response_parsed = await self._parse_json_response(response)
        return DishData(**response_parsed)