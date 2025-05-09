from typing import Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from config import settings
from dependencies import container
from usecases import UsersUseCase
from usecases.schemas import UserSchema


class SaveUserMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: TelegramObject, data: dict):
        user: User = data["event_from_user"]
        users_uc: UsersUseCase = container.resolve(UsersUseCase)

        if user.id in {u.telegram_id for u in await users_uc.get_users()}:
            return await handler(event, data)

        user_to_save = UserSchema(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        await users_uc.save_user(user_to_save)
        await event.bot.send_message(user_to_save.telegram_id, text=self._get_new_user_intro_message())

        if user.id != settings.ADMIN_ID:
            await event.bot.send_message(settings.ADMIN_ID, text=self._get_new_user_message(user_to_save))

        return await handler(event, data)

    @staticmethod
    def _get_new_user_message(user: UserSchema) -> str:
        return (
            f"Новый пользователь бота:\n"
            f"ID: {user.telegram_id}\n"
            f"Имя: {user.first_name} {user.last_name or ""}"
            f"\n\n{"" + user.username or ""}"
        )

    @staticmethod
    def _get_new_user_intro_message() -> str:
        return (
            "Что умеет бот TopFit:\n"
            "- 🎯Поможет определиться с целью по вашей дневной норме КБЖУ (Цель)\n"
            "- 🧮Посчитает за вас калории блюда по тексту, фото или голосовому сообщению (Добавить блюдо)\n"
            "- 🔥Будет отслеживать за вас статистику добавленных блюд за день (Статистика)\n"
            "- 🍽Порекомендует блюдо на основе ваших предпочтений и дневной КБЖУ из цели (AI рекомендация)\n"
        )
