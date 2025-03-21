from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards import goal_update_kb, goal_set_kb, user_kb
from bot.states import AddMealStates, SetNutritionGoalStates
from dependencies import container
from usecases import UsersUseCase, DishRecognitionUseCase, RecommendationUseCase, StatisticsUseCase
from usecases.errors import UserNutritionNotSetError
from usecases.schemas import GoalType, NutritionGoalSchema

router = Router()


@router.message(F.text.lower() == "главное меню")
async def add_dish(message: types.Message):
    await message.answer("К главному меню", reply_markup=user_kb)


@router.message(F.text.lower() == "добавить блюдо")
async def add_dish(message: types.Message, state: FSMContext):
    await message.answer("Отправьте текст/(аудио/фото) блюда")
    await state.set_state(AddMealStates.waiting_dish_obj)


@router.message(AddMealStates.waiting_dish_obj, F.text)
async def process_dish_obj(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    uc: DishRecognitionUseCase = container.resolve(DishRecognitionUseCase)
    dish_data = await uc.recognize_dish_from_text(dish_name=message.text)
    await message.answer(
        f"🍽 *Блюдо:* {dish_data.name}\n"
        f"🥩 *Белки:* {dish_data.protein:.1f} г\n"
        f"🧈 *Жиры:* {dish_data.fat:.1f} г\n"
        f"🍞 *Углеводы:* {dish_data.carbohydrates:.1f} г"
        f"🔥 *Калории:* {dish_data.calories:.1f} ккал\n",
        parse_mode="Markdown",
    )
    # TODO: В будущем добавить возможность корректировки данных

    uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    await uc.update_statistics(user_id=user_id, dish_id=dish_data.id)
    await message.answer(f"Статистика обновлена!")

    await state.clear()


@router.message(F.text.lower() == "статистика")
async def get_daily_statistics(message: types.Message):
    user_id = message.from_user.id
    uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    counted_statistics = await uc.get_statistics(user_id=user_id)
    await message.answer(
        f"📅 **Статистика за сегодня**:\n"
        f"🥩 **Белки**: {counted_statistics.protein:.1f} г\n"
        f"🧈 **Жиры**: {counted_statistics.fat:.1f} г\n"
        f"🍞 **Углеводы**: {counted_statistics.carbohydrates:.1f} г\n"
        f"🔥 **Калории**: {counted_statistics.calories:.1f} ккал\n",
        parse_mode="Markdown",
    )

@router.message(F.text.lower() == "ai рекомендация")
async def generate_user_dish_recommendation(message: types.Message):
    await message.answer(
        f"🍽 **Рекомендуемое блюдо**\n"
        f"Мы учитываем вашу дневную цель и статистику по КБЖУ, а также предпочтения, основанные на истории ваших блюд, "
        "чтобы предложить вам блюдо, которое вам точно понравится и будет вписываться в дневную норму.",
        parse_mode="Markdown"
    )
    user_id = message.from_user.id
    uc: RecommendationUseCase = container.resolve(RecommendationUseCase)
    try:
        recommendation = await uc.generate_recommendation(user_id=user_id)
    except UserNutritionNotSetError:
        await message.answer(
        "Персональная рекомендация блюда AI рассчитывается "
             "на основе ваших добавленных ранее блюд, а также на основе "
             "вашей дневной цели и статистики по КБЖУ.\n"
             "Вам необходимо задать **Цель** в панели Меню",
             parse_mode="Markdown"
        )
        return
    servings_count = recommendation.servings_count
    await message.answer(
        f"**Блюдо**: {recommendation.name}\n\n"
        f"**Состав**:\n"
        f"• Белки: {(recommendation.protein / servings_count):.1f} г\n"
        f"• Жиры: {(recommendation.fat / servings_count):.1f} г\n"
        f"• Углеводы: {(recommendation.carbohydrates / servings_count):.1f} г\n"
        f"• Калории: {(recommendation.calories / servings_count):.1f} ккал\n",
        parse_mode="Markdown"
    )
    await message.answer(
        f"📝 **Рецепт на кол-во блюд: {recommendation.servings_count}**:\n{recommendation.receipt}\n\n"
        "Приятного аппетита! 😋",
        parse_mode="Markdown"
    )


@router.message(F.text.lower() == "цель")
async def handle_goal(message: types.Message):
    user_id = message.from_user.id
    uc: UsersUseCase = container.resolve(UsersUseCase)

    try:
        nutrition = await uc.get_nutrition_goal(user_id=user_id)
        await message.answer(
            f"📅 **Ваша дневная цель КБЖУ**:\n"
            f"🥩 **Белки**: {nutrition.protein:.1f} г\n"
            f"🧈 **Жиры**: {nutrition.fat:.1f} г\n"
            f"🍞 **Углеводы**: {nutrition.carbohydrates:.1f} г\n"
            f"🔥 **Калории**: {nutrition.calories:.1f} ккал\n",
            parse_mode="Markdown",
            reply_markup=goal_update_kb,
        )
    except UserNutritionNotSetError:
        await message.answer(
            "У вас ещё нет заданной цели. Задайте её сейчас, чтобы получать рекомендации.",
            reply_markup=goal_set_kb,
        )


@router.message(F.text.lower() == "обновить цель")
async def update_nutrition_goal(message: types.Message, state: FSMContext):
    await set_nutrition_goal(message=message, state=state)


@router.message(F.text.lower() == "задать цель")
async def set_nutrition_goal(message: types.Message, state: FSMContext):
    await message.answer("Рост (см):")
    await state.set_state(SetNutritionGoalStates.waiting_height)


@router.message(SetNutritionGoalStates.waiting_height, F.text)
async def process_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Вес (кг):")
    await state.set_state(SetNutritionGoalStates.waiting_weight)


@router.message(SetNutritionGoalStates.waiting_weight, F.text)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer(f"Возраст:")
    await state.set_state(SetNutritionGoalStates.waiting_age)


@router.message(SetNutritionGoalStates.waiting_age, F.text)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer(f"Выберите пол (м/ж):")
    await state.set_state(SetNutritionGoalStates.waiting_goal)


@router.message(SetNutritionGoalStates.waiting_goal, F.text)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer(f"Выберите номер вашей цели:\n{GoalType.get_goal_options()}")
    await state.set_state(SetNutritionGoalStates.waiting_gender)

@router.message(SetNutritionGoalStates.waiting_gender, F.text)
async def process_goal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    goal_data = await state.get_data()
    uc: UsersUseCase = container.resolve(UsersUseCase)
    goal_data = NutritionGoalSchema(height=float(goal_data["height"]),
                                    weight=float(goal_data["weight"]),
                                    age=int(goal_data["age"]),
                                    is_male=True if goal_data["gender"] == "м" else False,
                                    nutrition_goal_type=GoalType.from_number(int(message.text.lower())))
    await uc.set_nutrition_goal(user_id=user_id, goal_data=goal_data)
    await message.answer(f"Цель обновлена!", reply_markup=user_kb)
    await state.clear()
