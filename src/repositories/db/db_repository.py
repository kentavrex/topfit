import datetime
from typing import Self

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from usecases.interfaces import DBRepositoryInterface
from usecases.schemas import UserSchema, DishData, DishSchema, NutritionData, NutritionSchema
from .models import User, Statistics, Dish, RecommendationHistory, Nutrition


class DBRepository(DBRepositoryInterface):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_maker = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e
        finally:
            await self._session.close()

    async def create_user(self, user: UserSchema) -> None:
        self._session.add(User(**user.model_dump()))
        await self._session.flush()

    async def get_users(self) -> list[UserSchema]:
        return [
            UserSchema.model_validate(u)
            for u in (await self._session.scalars(select(User))).all()
        ]

    async def save_dish(self, dish_data: DishData) -> DishSchema:
        nutrition = Nutrition(**dish_data.model_dump(exclude={"name"}))
        self._session.add(nutrition)
        await self._session.flush()

        dish = Dish(name=dish_data.name, nutrition_id=nutrition.id)
        self._session.add(dish)
        await self._session.flush()

        return DishSchema(id=dish.id,
                          name=dish.name,
                          protein=dish.nutrition.protein,
                          fat=dish.nutrition.fat,
                          carbohydrates=dish.nutrition.carbohydrates,
                          calories=dish.nutrition.calories)

    async def add_statistics_obj(self, user_id: int, dish_id: int, like: bool = True) -> None:
        statistics_obj = Statistics(
            user_id=user_id,
            dish_id=dish_id,
            like=like,
        )
        self._session.add(statistics_obj)
        await self._session.flush()

    async def get_user_dishes_history_by_period(
            self, user_id: int, valid_from_dt: datetime.datetime, valid_to_dt: datetime.datetime
    ) -> list[DishSchema]:
        query = (
            select(Statistics)
            .filter(Statistics.user_id == user_id)
            .filter(Statistics.created_at >= valid_from_dt)
            .filter(Statistics.created_at <= valid_to_dt)
        ).options(
            joinedload(Statistics.dish).joinedload(Dish.nutrition)
        )
        statistics = await self._session.scalars(query)

        return [
            DishSchema(
                id=stat.dish.id,
                name=stat.dish.name,
                protein=stat.dish.nutrition.protein,
                fat=stat.dish.nutrition.fat,
                carbohydrates=stat.dish.nutrition.carbohydrates,
                calories=stat.dish.nutrition.calories
            )
            for stat in statistics
        ]

    async def get_user_dishes_history(self, user_id: int, limit: int = 50) -> list[str]:
        query = (
            select(Statistics)
            .filter(Statistics.user_id == user_id)
            .limit(limit)
            .options(joinedload(Statistics.dish))
        )

        statistics = await self._session.scalars(query)
        return [stat.dish.name for stat in statistics]

    async def save_user_recommendation(self, user_id: int, dish_id: int) -> None:
        user_recommendation = RecommendationHistory(user_id=user_id, dish_id=dish_id)
        self._session.add(user_recommendation)
        await self._session.flush()

    async def save_nutrition(self, nutrition_data: NutritionData) -> NutritionSchema:
        nutrition = Nutrition(**nutrition_data.model_dump())
        self._session.add(nutrition)
        await self._session.flush()
        return NutritionSchema.model_validate(nutrition)

    async def set_user_nutrition_goal(self, user_id: int, nutrition_goal_id: int) -> None:
        query = (
            update(User)
            .where(and_(User.telegram_id == user_id))
            .values({"nutrition_goal_id": nutrition_goal_id})
        )
        await self._session.execute(query)
        await self._session.flush()

    async def get_user_nutrition_goal(self, user_id: int) -> NutritionSchema | None:
        query = (
            select(User)
            .filter(User.telegram_id == user_id)
            .options(joinedload(User.nutrition_goal))
        )
        user = await self._session.scalar(query)
        if user and user.nutrition_goal:
            return NutritionSchema.model_validate(user.nutrition_goal)
        return None
