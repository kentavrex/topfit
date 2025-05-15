import asyncio
import logging
from io import BytesIO

import magic
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.keyboards import goal_set_kb, goal_update_kb, statistics_set_kb, unlike_dish_or_back_kb, user_kb
from bot.states import AddMealStates, SetNutritionGoalStates
from bot.validators import GoalValidator
from dependencies import container
from usecases import DishRecognitionUseCase, RecommendationUseCase, StatisticsUseCase, UsersUseCase
from usecases.errors import AudioToTextError, MaxRetryError, UserNutritionNotSetError
from usecases.schemas import ActivityType, GoalType, NutritionGoalSchema

router = Router()


@router.message(F.text.lower() == "главное меню")
async def main_menu(message: types.Message):
    await message.delete()
    await message.answer("Главное меню", reply_markup=user_kb)


@router.message(F.text.lower() == "добавить блюдо")
async def add_dish(message: types.Message, state: FSMContext):
    await message.answer("Отправьте текст, голосовое сообщение или фото блюда!")
    await state.set_state(AddMealStates.waiting_dish_obj)


@router.message(AddMealStates.waiting_dish_obj, F.text)
async def process_dish_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    statistics_uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    dish_recognition_uc: DishRecognitionUseCase = container.resolve(DishRecognitionUseCase)
    try:
        dish_data = await dish_recognition_uc.recognize_dish_from_text(dish_name=message.text)
        await send_dish_info(message, dish_data)
        await statistics_uc.update_statistics(user_id=user_id, dish_id=dish_data.id)
    except Exception as e:
        logging.error(f"Ошибка={e}")
        await message.answer("❌ Не удалось рассчитать калории. Попробуйте еще раз.")
    finally:
        await state.clear()


@router.message(AddMealStates.waiting_dish_obj, F.photo)
async def process_dish_image(message: types.Message, state: FSMContext):
    statistics_uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    dish_recognition_uc: DishRecognitionUseCase = container.resolve(DishRecognitionUseCase)

    # await message.answer("Загрузка изображений временно не доступна.")
    # await state.clear()

    processing_message = await message.answer("⏳Идет подсчет калорий..")
    user_id = message.from_user.id
    bot = message.bot

    try:
        file = await bot.get_file(message.photo[-1].file_id)
        file_bytes = await bot.download_file(file.file_path)
        file_bytes = file_bytes.read() if isinstance(file_bytes, BytesIO) else file_bytes

        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_bytes)
        logging.info(f"mime_type={mime_type}")
        dish_data = await dish_recognition_uc.recognize_dish_from_image(dish_bytes=file_bytes, mime_type=mime_type)

        await send_dish_info(message, dish_data)
        await processing_message.edit_text("✅ Подсчет завершен!")
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        await statistics_uc.update_statistics(user_id=user_id, dish_id=dish_data.id)
    except Exception as e:
        logging.error(f"Ошибка={e}")
        await processing_message.edit_text("❌ Не удалось распознать фото. Попробуйте еще раз.")
    finally:
        await state.clear()


@router.message(AddMealStates.waiting_dish_obj, F.voice)
async def process_dish_audio(message: types.Message, state: FSMContext):
    statistics_uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    dish_recognition_uc: DishRecognitionUseCase = container.resolve(DishRecognitionUseCase)

    processing_message = await message.answer("⏳Идет подсчет калорий..")
    user_id = message.from_user.id
    bot = message.bot

    try:
        file = await bot.get_file(message.voice.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        file_bytes = file_bytes_io.read()  # Приводим BytesIO к bytes

        try:
            dish_data = await dish_recognition_uc.recognize_dish_from_audio(file_bytes=file_bytes)
        except AudioToTextError:
            await processing_message.edit_text("❌ Не удалось распознать аудио. Попробуйте еще раз.")
            await asyncio.sleep(2)
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
            await state.clear()
            return

        await send_dish_info(message, dish_data)
        await processing_message.edit_text("✅ Подсчет завершен!")
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        await statistics_uc.update_statistics(user_id=user_id, dish_id=dish_data.id)
    except Exception as e:
        logging.error(f"Ошибка={e}")
        await processing_message.edit_text("❌ Не удалось рассчитать калории. Попробуйте еще раз.")
    finally:
        await state.clear()


async def send_dish_info(message: types.Message, dish_data):
    await message.answer(
        f"🍽 *Блюдо:* {dish_data.name}\n"
        f"🥩 *Белки:* {dish_data.protein:.1f} г\n"
        f"🧈 *Жиры:* {dish_data.fat:.1f} г\n"
        f"🍞 *Углеводы:* {dish_data.carbohydrates:.1f} г\n"
        f"🔥 *Калории:* {dish_data.calories:.1f} ккал\n",
        parse_mode="Markdown",
        reply_markup=unlike_dish_or_back_kb,
    )


@router.message(F.text.lower() == "блюдо не понравилось")
async def unlike_dish(message: types.Message):
    await message.delete()
    await message.answer(
        "Мы отметили, что блюдо вам не понравилось и оно не будет учитываться при генерации рекомендаций!",
        reply_markup=user_kb,
    )


@router.message(F.text.lower() == "статистика")
async def get_daily_statistics(message: types.Message):
    user_id = message.from_user.id
    uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    counted_statistics = await uc.get_daily_statistics(user_id=user_id)
    await message.answer(
        f"📅 **Статистика за сегодня**:\n"
        f"🥩 **Белки**: {counted_statistics.protein:.1f} г\n"
        f"🧈 **Жиры**: {counted_statistics.fat:.1f} г\n"
        f"🍞 **Углеводы**: {counted_statistics.carbohydrates:.1f} г\n"
        f"🔥 **Калории**: {counted_statistics.calories:.1f} ккал\n",
        parse_mode="Markdown",
        reply_markup=statistics_set_kb,
    )


@router.message(F.text.lower() == "статистика за месяц")
async def get_monthly_statistics(message: types.Message):
    processing_message = await message.answer(
        "⌛ **Подсчет статистики за последние 30 дней начался..**\n", parse_mode="Markdown"
    )
    user_id = message.from_user.id
    uc: StatisticsUseCase = container.resolve(StatisticsUseCase)
    counted_statistics = await uc.get_monthly_statistics(user_id=user_id)
    month_data = []
    for stat in counted_statistics:
        if stat.calories > 0:
            entry = (
                f"{stat.valid_from_dt.strftime('%d.%m')}: "
                f"{stat.calories:.1f}/"
                f"{stat.protein:.1f}/"
                f"{stat.fat:.1f}/"
                f"{stat.carbohydrates:.1f}"
            )
        else:
            entry = f"{stat.valid_from_dt.strftime('%d.%m')}: -"
        month_data.append(entry)

    text = "📅 **Статистика: калории/белки/жиры/углеводы**\n" + "\n".join(month_data)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
    await message.answer(text, parse_mode="Markdown", reply_markup=user_kb)


@router.message(F.text.lower() == "ai рекомендация")
async def generate_user_dish_recommendation(message: types.Message):
    processing_message = await message.answer(
        "🍽 **Рекомендуемое блюдо**\n"
        "Мы учитываем вашу дневную цель и статистику по КБЖУ, а также предпочтения, основанные на истории ваших блюд, "
        "чтобы предложить вам блюдо, которое вам точно понравится и будет вписываться в дневную норму.",
        parse_mode="Markdown",
    )
    user_id = message.from_user.id
    uc: RecommendationUseCase = container.resolve(RecommendationUseCase)
    try:
        recommendation = await uc.generate_recommendation(user_id=user_id)
    except MaxRetryError:
        await message.answer("Техническая ошибка. Попробуйте еще раз позднее.")
        return
    except UserNutritionNotSetError:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        await message.answer(
            "Персональная рекомендация блюда AI рассчитывается "
            "на основе вашей цели по КБЖУ.\n"
            "Вам необходимо задать **Цель** в панели Меню",
            parse_mode="Markdown",
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
        parse_mode="Markdown",
    )
    await message.answer(
        f"📝 **Рецепт на кол-во блюд - {recommendation.servings_count}**:\n{recommendation.receipt}\n\n"
        "Приятного аппетита! 😋",
        parse_mode="Markdown",
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
    try:
        height = GoalValidator.validate_height(message.text)
        await state.update_data(height=height)
        await message.answer("Вес (кг):")
        await state.set_state(SetNutritionGoalStates.waiting_weight)
    except ValueError as e:
        await message.answer(str(e))


@router.message(SetNutritionGoalStates.waiting_weight, F.text)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = GoalValidator.validate_weight(message.text)
        await state.update_data(weight=weight)
        await message.answer("Возраст:")
        await state.set_state(SetNutritionGoalStates.waiting_age)
    except ValueError as e:
        await message.answer(str(e))


@router.message(SetNutritionGoalStates.waiting_age, F.text)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = GoalValidator.validate_age(message.text)
        await state.update_data(age=age)
        await message.answer("Выберите пол (м/ж):")
        await state.set_state(SetNutritionGoalStates.waiting_gender)
    except ValueError as e:
        await message.answer(str(e))


@router.message(SetNutritionGoalStates.waiting_gender, F.text)
async def process_gender(message: types.Message, state: FSMContext):
    try:
        gender = GoalValidator.validate_gender(message.text)
        await state.update_data(gender=gender)
        await message.answer(f"Выберите уровень активности:\n{ActivityType.get_activity_options()}")
        await state.set_state(SetNutritionGoalStates.waiting_activity)
    except ValueError as e:
        await message.answer(str(e))


@router.message(SetNutritionGoalStates.waiting_activity, F.text)
async def process_activity(message: types.Message, state: FSMContext):
    try:
        activity_number = GoalValidator.validate_activity(message.text)
        await state.update_data(activity_number=activity_number)
        await message.answer(f"Выберите номер вашей цели:\n{GoalType.get_goal_options()}")
        await state.set_state(SetNutritionGoalStates.waiting_goal)
    except ValueError as e:
        await message.answer(str(e))


@router.message(SetNutritionGoalStates.waiting_goal, F.text)
async def process_goal(message: types.Message, state: FSMContext):
    try:
        goal_number = GoalValidator.validate_goal(message.text)
        user_id = message.from_user.id
        goal_data = await state.get_data()
        goal_data = NutritionGoalSchema(
            height=float(goal_data["height"]),
            weight=float(goal_data["weight"]),
            age=int(goal_data["age"]),
            is_male=goal_data["gender"],
            activity_type=ActivityType.from_number(goal_data["activity_number"]),
            nutrition_goal_type=GoalType.from_number(goal_number),
        )
        uc: UsersUseCase = container.resolve(UsersUseCase)
        await uc.set_nutrition_goal(user_id=user_id, goal_data=goal_data)
        await message.answer("Цель обновлена!", reply_markup=user_kb)
        await state.clear()
    except ValueError as e:
        await message.answer(str(e))


@router.message()
async def unknown_command(message: types.Message):
    await message.answer("❌ Неизвестная команда. Пожалуйста, проверьте ввод и попробуйте снова.")
