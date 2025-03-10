from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Текущая цель"),
         KeyboardButton(text="Обновить цель"),
         KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Добавить блюдо")],
        [KeyboardButton(text="AI рекомендация")],
    ],
    resize_keyboard=True,
)

admin_kb = user_kb
