import json

from usecases.errors import UserNutritionNotSetError
from usecases.interfaces import DBRepositoryInterface, AIClientInterface
from usecases.schemas import UserSchema, NutritionGoalSchema, GoalType, NutritionSchema


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

    async def set_nutrition_goal(self, user_id: int, height: float, weight: float, goal_number: int) -> None:
        user_message = NutritionGoalSchema(height=height,
                                           weight=weight,
                                           nutrition_goal_type=GoalType.from_number(goal_number))
        async with self._ai_client as ai_client:
            nutrition = await ai_client.get_nutrition_recommendation(message=str(user_message))
        async with self._db as db:
            saved_nutrition = await db.save_nutrition(nutrition)
            await db.set_user_nutrition_goal(user_id=user_id, nutrition_goal_id=saved_nutrition.id)

    async def get_nutrition_goal(self, user_id: int) -> NutritionSchema | None:
        async with self._db as db:
            nutrition = await db.get_user_nutrition_goal(user_id)
        if not nutrition:
            raise UserNutritionNotSetError
        return nutrition
