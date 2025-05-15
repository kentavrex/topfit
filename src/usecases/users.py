from decimal import Decimal

from usecases.errors import UserNutritionNotSetError
from usecases.interfaces import AIClientInterface, DBRepositoryInterface
from usecases.schemas import ActivityType, GoalType, NutritionData, NutritionGoalSchema, NutritionSchema, UserSchema


class UsersUseCase:
    def __init__(self, ai_client: AIClientInterface, db_repository: DBRepositoryInterface):
        self._ai_client = ai_client
        self._db = db_repository

    async def save_user(self, user: UserSchema) -> None:
        async with self._db as db:
            await db.create_user(user)

    async def get_users(self) -> list[UserSchema]:
        async with self._db as db:
            return await db.get_users()

    async def _update_user(self, user: UserSchema) -> None:
        async with self._db as db:
            await db.create_user(user)

    async def set_nutrition_goal(self, user_id: int, goal_data: NutritionGoalSchema) -> None:
        nutrition = self.__calculate_nutrition_goal(goal_data=goal_data)
        async with self._db as db:
            saved_nutrition = await db.save_nutrition(nutrition)
            await db.set_user_nutrition_goal(user_id=user_id, nutrition_goal_id=saved_nutrition.id)

    async def get_nutrition_goal(self, user_id: int) -> NutritionSchema | None:
        async with self._db as db:
            nutrition = await db.get_user_nutrition_goal(user_id)
        if not nutrition:
            raise UserNutritionNotSetError
        return nutrition

    @staticmethod
    def __calculate_bmr(goal_data: NutritionGoalSchema) -> float:
        """Рассчитываем BMR по формуле Миффлина-Сан Жеора"""
        bmr = 10 * goal_data.weight + 6.25 * goal_data.height - 5 * goal_data.age
        return bmr + 5 if goal_data.is_male else bmr - 161

    @staticmethod
    def __calculate_daily_calories(bmr: float, goal_data: NutritionGoalSchema) -> float:
        """Рассчитываем дневную норму калорий на основе цели"""
        base = bmr
        match goal_data.activity_type:
            case ActivityType.MINIMUM:
                base *= 1.2
            case ActivityType.AVERAGE:
                base *= 1.55
            case ActivityType.MAXIMUM:
                base *= 1.7
            case _:
                raise ValueError("Некорректное значение activity_number")

        match goal_data.nutrition_goal_type:
            case GoalType.LOSE_WEIGHT:
                return base * 0.85  # Снижение на 15%
            case GoalType.SUPPORT_FORM:
                return base  # Поддержка формы
            case GoalType.GAIN_WEIGHT:
                return base * 1.15  # Увеличение на 15%
            case _:
                raise ValueError("Некорректное значение goal_number")

    @staticmethod
    def __calculate_macros(daily_calories: float) -> NutritionData:
        """Распределяем КБЖУ (30% белков, 30% жиров, 40% углеводов)"""
        protein = (daily_calories * 0.3) / 4  # Белки: 4 ккал на грамм
        fat = (daily_calories * 0.3) / 9  # Жиры: 9 ккал на грамм
        carbs = (daily_calories * 0.4) / 4  # Углеводы: 4 ккал на грамм

        return NutritionData(
            calories=round(Decimal(daily_calories), 1),
            protein=round(Decimal(protein), 1),
            fat=round(Decimal(fat), 1),
            carbohydrates=round(Decimal(carbs), 1),
        )

    def __calculate_nutrition_goal(self, goal_data: NutritionGoalSchema) -> NutritionData:
        """Основная функция для расчёта КБЖУ"""
        bmr = self.__calculate_bmr(goal_data)
        daily_calories = self.__calculate_daily_calories(bmr=bmr, goal_data=goal_data)
        return self.__calculate_macros(daily_calories)
