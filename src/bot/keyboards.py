from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Цель"),
         KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Добавить блюдо")],
        [KeyboardButton(text="AI рекомендация")],
    ],
    resize_keyboard=True,
)

admin_kb = user_kb

goal_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Задать цель")],
        [KeyboardButton(text="Обновить цель")],
        [KeyboardButton(text="Просмотреть текущую цель")],
        [KeyboardButton(text="Назад")],  # Возврат в главное меню
    ],
    resize_keyboard=True,
)

goal_update_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Обновить цель"),
               KeyboardButton(text="Главное меню")]],
    resize_keyboard=True,
)

goal_set_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Задать цель"),
               KeyboardButton(text="Главное меню")]],
    resize_keyboard=True,
)

statistics_set_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Статистика за месяц"),
               KeyboardButton(text="Главное меню")]],
    resize_keyboard=True,
)
