from aiogram.fsm.state import State, StatesGroup


class AddMealStates(StatesGroup):
    waiting_dish_obj = State()


class SetNutritionGoalStates(StatesGroup):
    waiting_height = State()
    waiting_weight = State()
    waiting_age = State()
    waiting_goal = State()
    waiting_activity = State()
    waiting_gender = State()
