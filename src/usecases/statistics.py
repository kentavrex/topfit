import logging
from datetime import datetime, time, timedelta
from decimal import Decimal

from config import settings
from usecases.interfaces import DBRepositoryInterface
from usecases.schemas import CountedStatisticsSchema, DishSchema


class StatisticsUseCase:
    def __init__(self, db_repository: DBRepositoryInterface):
        self._db = db_repository

    async def get_daily_statistics(self, user_id: int) -> CountedStatisticsSchema:
        now = datetime.now(settings.moscow_tz)
        today_start = datetime.combine(now.date(), time.min).replace(tzinfo=settings.moscow_tz)
        today_end = datetime.combine(now.date(), time.max).replace(tzinfo=settings.moscow_tz)
        logging.info(f"{today_start=}")
        logging.info(f"{today_end=}")
        async with self._db as db:
            dishes_history: [DishSchema] = await db.get_user_dishes_history_by_period(
                user_id=user_id,
                valid_from_dt=today_start,
                valid_to_dt=today_end,
            )
        return CountedStatisticsSchema(
            user_id=user_id,
            valid_from_dt=today_start,
            valid_to_dt=today_end,
            protein=sum((stat.protein for stat in dishes_history), start=Decimal("0")),
            fat=sum((stat.fat for stat in dishes_history), start=Decimal("0")),
            carbohydrates=sum((stat.carbohydrates for stat in dishes_history), start=Decimal("0")),
            calories=sum((stat.calories for stat in dishes_history), start=Decimal("0")),
        )

    async def get_monthly_statistics(self, user_id: int) -> list[CountedStatisticsSchema]:
        today = datetime.now(settings.moscow_tz).date()
        start_date = today - timedelta(days=29)  # включая сегодня — итого 30 дней

        statistics = []
        async with self._db as db:
            for offset in range(30):
                now = start_date + timedelta(days=offset)
                current_date_start = datetime.combine(now, time.min).replace(tzinfo=settings.moscow_tz)
                current_date_end = datetime.combine(now, time.max).replace(tzinfo=settings.moscow_tz)

                dishes: [DishSchema] = await db.get_user_dishes_history_by_period(
                    user_id=user_id,
                    valid_from_dt=current_date_start,
                    valid_to_dt=current_date_end,
                )
                if not dishes:
                    statistics.append(
                        CountedStatisticsSchema(
                            user_id=user_id, valid_from_dt=current_date_start, valid_to_dt=current_date_end
                        )
                    )
                    continue

                statistics.append(
                    CountedStatisticsSchema(
                        user_id=user_id,
                        valid_from_dt=current_date_start,
                        valid_to_dt=current_date_end,
                        protein=sum((d.protein for d in dishes), start=Decimal("0")),
                        fat=sum((d.fat for d in dishes), start=Decimal("0")),
                        carbohydrates=sum((d.carbohydrates for d in dishes), start=Decimal("0")),
                        calories=sum((d.calories for d in dishes), start=Decimal("0")),
                    )
                )

        return statistics

    async def update_statistics(self, user_id: int, dish_id: int) -> None:
        async with self._db as db:
            await db.add_statistics_obj(user_id=user_id, dish_id=dish_id)
