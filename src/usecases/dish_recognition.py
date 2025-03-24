import io
import logging
from typing import BinaryIO

import ffmpeg
import speech_recognition

from usecases.errors import AudioToTextError
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
            return await self._save_dish_to_db(dish_data=dish_nutrition_data)

    async def recognize_dish_from_image(self, dish_bytes: BinaryIO, mime_type: str) -> DishSchema:
        async with self._ai_client as ai_client:
            dish_nutrition_data = await ai_client.recognize_meal_by_image(dish_bytes=dish_bytes, mime_type=mime_type)
            return await self._save_dish_to_db(dish_data=dish_nutrition_data)

    async def recognize_dish_from_audio(self, file_bytes: bytes) -> DishSchema:
        text = await self._recognize_speech(file_bytes=file_bytes)
        if not text:
            logging.error("Не удалось распознать аудио")
            raise AudioToTextError

        async with self._ai_client as ai_client:
            dish_nutrition_data = await ai_client.recognize_meal_by_text_from_audio(message=text)
            return await self._save_dish_to_db(dish_data=dish_nutrition_data)

    @staticmethod
    async def _convert_ogg_to_wav(file_bytes: bytes) -> io.BytesIO:
        """Конвертирует OGG в WAV с помощью ffmpeg"""
        input_audio = io.BytesIO(file_bytes)  # Создаём BytesIO из bytes
        output_audio = io.BytesIO()

        process = (
            ffmpeg
            .input("pipe:0", format="ogg")
            .output("pipe:1", format="wav")
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )

        out, _ = process.communicate(input=input_audio.read())  # Передаём байты
        output_audio.write(out)
        output_audio.seek(0)

        return output_audio  # Возвращаем объект BytesIO

    async def _recognize_speech(self, file_bytes: bytes) -> str:
        """Распознаёт речь из аудиофайла"""
        recognizer = speech_recognition.Recognizer()

        # Конвертируем OGG в WAV
        wav_audio = await self._convert_ogg_to_wav(file_bytes)

        with speech_recognition.AudioFile(wav_audio) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            return text
        except speech_recognition.UnknownValueError:
            return ""
        except speech_recognition.RequestError:
            return ""
