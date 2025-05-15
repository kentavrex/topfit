from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from usecases.schemas import DishSchema
from usecases.statistics import StatisticsUseCase


@pytest.mark.asyncio
async def test_get_daily_statistics_with_data():
    db_repo = AsyncMock()
    db_repo.__aenter__.return_value.get_user_dishes_history_by_period.return_value = [
        DishSchema(
            protein=Decimal("10"),
            fat=Decimal("5"),
            carbohydrates=Decimal("20"),
            calories=Decimal("200"),
            id=1,
            name="Лазанья",
        ),
        DishSchema(
            protein=Decimal("7"),
            fat=Decimal("3"),
            carbohydrates=Decimal("15"),
            calories=Decimal("150"),
            id=2,
            name="Овсянка",
        ),
    ]

    usecase = StatisticsUseCase(db_repository=db_repo)
    result = await usecase.get_daily_statistics(user_id=1)

    assert result.protein == Decimal("17")
    assert result.fat == Decimal("8")
    assert result.carbohydrates == Decimal("35")
    assert result.calories == Decimal("350")


@pytest.mark.asyncio
async def test_get_daily_statistics_empty():
    db_repo = AsyncMock()
    db_repo.__aenter__.return_value.get_user_dishes_history_by_period.return_value = []

    usecase = StatisticsUseCase(db_repository=db_repo)
    result = await usecase.get_daily_statistics(user_id=1)

    assert result.protein == Decimal("0")
    assert result.fat == Decimal("0")
    assert result.carbohydrates == Decimal("0")
    assert result.calories == Decimal("0")


@pytest.mark.asyncio
async def test_get_monthly_statistics_mixed_days():
    db_repo = AsyncMock()

    async def get_history(valid_from_dt, **_):
        if valid_from_dt.date().day % 2 == 0:
            return [
                DishSchema(
                    protein=Decimal("5"),
                    fat=Decimal("2"),
                    carbohydrates=Decimal("10"),
                    calories=Decimal("100"),
                    id=1,
                    name="Салат",
                )
            ]
        return []

    db_repo.__aenter__.return_value.get_user_dishes_history_by_period.side_effect = get_history

    usecase = StatisticsUseCase(db_repository=db_repo)
    stats = await usecase.get_monthly_statistics(user_id=1)

    assert len(stats) == 30
    for stat in stats:
        if stat.valid_from_dt.day % 2 == 0:
            assert stat.protein == Decimal("5")
            assert stat.fat == Decimal("2")
            assert stat.carbohydrates == Decimal("10")
            assert stat.calories == Decimal("100")
        else:
            assert stat.protein == Decimal("0")
            assert stat.fat == Decimal("0")
            assert stat.carbohydrates == Decimal("0")
            assert stat.calories == Decimal("0")


@pytest.mark.asyncio
async def test_get_monthly_statistics_all_empty():
    db_repo = AsyncMock()
    db_repo.__aenter__.return_value.get_user_dishes_history_by_period.return_value = []

    usecase = StatisticsUseCase(db_repository=db_repo)
    stats = await usecase.get_monthly_statistics(user_id=1)

    assert len(stats) == 30
    assert all(s.protein == Decimal("0") for s in stats)
    assert all(s.fat == Decimal("0") for s in stats)
    assert all(s.calories == Decimal("0") for s in stats)


@pytest.mark.asyncio
async def test_update_statistics_call():
    db_repo = AsyncMock()
    usecase = StatisticsUseCase(db_repository=db_repo)

    await usecase.update_statistics(user_id=123, dish_id=456)
    db_repo.__aenter__.return_value.add_statistics_obj.assert_awaited_once_with(user_id=123, dish_id=456)
