from datetime import datetime, timedelta

from config import settings
from usecases.interfaces import DBRepositoryInterface
from usecases.schemas import CountedStatisticsSchema, DishSchema


class StatisticsUseCase:
    def __init__(self, db_repository: DBRepositoryInterface):
        self._db = db_repository

    async def get_daily_statistics(self, user_id: int) -> CountedStatisticsSchema:
        today = datetime.now(settings.moscow_tz).date()
        async with self._db as db:
            dishes_history: [DishSchema] = await db.get_user_dishes_history_by_period(
                user_id=user_id,
                date_from=today,
                date_to=today
            )
        return CountedStatisticsSchema(
            user_id=user_id,
            date_from=today,
            date_to=today,
            protein=sum(stat.protein for stat in dishes_history),
            fat=sum(stat.fat for stat in dishes_history),
            carbohydrates=sum(stat.carbohydrates for stat in dishes_history),
            calories=sum(stat.calories for stat in dishes_history),
        )

    async def get_monthly_statistics(self, user_id: int) -> list[CountedStatisticsSchema]:
        today = datetime.now(settings.moscow_tz).date()
        start_date = today - timedelta(days=29)  # включая сегодня — итого 30 дней

        statistics = []
        async with self._db as db:
            for offset in range(30):
                current_date = start_date + timedelta(days=offset)
                dishes: [DishSchema] = await db.get_user_dishes_history_by_period(
                    user_id=user_id,
                    date_from=current_date,
                    date_to=current_date
                )
                if not dishes:
                    statistics.append(CountedStatisticsSchema(user_id=user_id,
                                                              date_from=current_date,
                                                              date_to=current_date))
                    continue

                statistics.append(CountedStatisticsSchema(
                    user_id=user_id,
                    date_from=current_date,
                    date_to=current_date,
                    protein=sum(d.protein for d in dishes),
                    fat=sum(d.fat for d in dishes),
                    carbohydrates=sum(d.carbohydrates for d in dishes),
                    calories=sum(d.calories for d in dishes),
                ))

        return statistics

    async def update_statistics(self, user_id: int, dish_id: int) -> None:
        async with self._db as db:
            await db.add_statistics_obj(user_id=user_id, dish_id=dish_id)
