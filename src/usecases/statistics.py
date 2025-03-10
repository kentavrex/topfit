from datetime import datetime

from config import settings
from usecases.interfaces import DBRepositoryInterface
from usecases.schemas import CountedStatisticsSchema, DishSchema


class StatisticsUseCase:
    def __init__(self, db_repository: DBRepositoryInterface):
        self._db = db_repository

    async def get_statistics(self,
                             user_id: int,
                             date_from: datetime.date = settings.today,
                             date_to: datetime.date = settings.today) -> CountedStatisticsSchema:
        async with self._db as db:
            dishes_history: [DishSchema] = await db.get_user_dishes_history_by_period(user_id=user_id,
                                                                                      date_from=date_from,
                                                                                      date_to=date_to)
        return CountedStatisticsSchema(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            protein=sum(stat.protein for stat in dishes_history),
            fat=sum(stat.fat for stat in dishes_history),
            carbohydrates=sum(stat.carbohydrates for stat in dishes_history),
            calories=sum(stat.calories for stat in dishes_history),
        )


    async def update_statistics(self, user_id: int, dish_id: int) -> None:
        async with self._db as db:
            await db.add_statistics_obj(user_id=user_id, dish_id=dish_id)
