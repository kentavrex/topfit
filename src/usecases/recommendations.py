import datetime
from decimal import Decimal

from config import settings
from usecases.errors import UserNutritionNotSetError
from usecases.interfaces import DBRepositoryInterface, AIClientInterface
from usecases.schemas import DishData, DishRecommendation, NutritionSchema, DishSchema, CountedStatisticsSchema


class RecommendationUseCase:
    def __init__(self, ai_client: AIClientInterface, db_repository: DBRepositoryInterface):
        self._ai_client = ai_client
        self._db = db_repository

    async def _get_dish_recommendation_message_text(self, user_id: int) -> str:
        async with self._db as db:
            user_nutrition_goal: NutritionSchema = await db.get_user_nutrition_goal(user_id=user_id)
        if not user_nutrition_goal:
            raise UserNutritionNotSetError

        async with self._db as db:
            user_dishes_history: list[str] = await db.get_user_dishes_history(user_id=user_id, limit=50)
            dishes_history: [DishSchema] = await db.get_user_dishes_history_by_period(
                user_id=user_id,
                date_from=datetime.datetime.now(tz=settings.moscow_tz).date(),
                date_to=datetime.datetime.now(tz=settings.moscow_tz).date()
            )
        dish_nutrition_goal_text = CountedStatisticsSchema(
            user_id=user_id,
            protein=max(user_nutrition_goal.protein - sum(stat.protein for stat in dishes_history), Decimal(2)),
            fat=max(user_nutrition_goal.fat - sum(stat.fat for stat in dishes_history), Decimal(0)),
            carbohydrates=max(user_nutrition_goal.carbohydrates - sum(stat.carbohydrates for stat in dishes_history),
                              Decimal(10)),
            calories=max(user_nutrition_goal.calories - sum(stat.calories for stat in dishes_history), Decimal(300)),
        )
        if user_dishes_history:
            return (f"Примерный (не точный) желаемый кбжу: {dish_nutrition_goal_text}. "
                    f"История прошлых блюд: {", ".join(user_dishes_history)}")
        return (f"Примерный (не точный) желаемый кбжу: {dish_nutrition_goal_text}. "
                f"Истории прошлых блюд нет, просто порекомендуй что-нибудь вкусное.")

    async def generate_recommendation(self, user_id: int) -> DishRecommendation:
        dish_recommendation_text = await self._get_dish_recommendation_message_text(user_id=user_id)
        async with self._ai_client as ai_client:
            dish_recommendation = await ai_client.get_dish_recommendation(message=dish_recommendation_text)

        async with self._db as db:
            saved_dish = await db.save_dish(DishData(**dish_recommendation.model_dump()))
            await db.save_user_recommendation(user_id=user_id, dish_id=saved_dish.id)
        return dish_recommendation
