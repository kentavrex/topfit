from unittest.mock import AsyncMock

import pytest
from decimal import Decimal
from usecases.statistics import StatisticsUseCase
from usecases.schemas import DishSchema

@pytest.mark.asyncio
async def test_get_daily_statistics(mocker):
    db_repo = AsyncMock()
    db_repo.__aenter__.return_value.get_user_dishes_history_by_period.return_value = [
        DishSchema(protein=Decimal("10"), fat=Decimal("5"), carbohydrates=Decimal("20"), calories=Decimal("200"), id=1, name="Лазанья")
    ]
    usecase = StatisticsUseCase(db_repository=db_repo)
    result = await usecase.get_daily_statistics(user_id=1)

    assert result.protein == Decimal("10")
    assert result.fat == Decimal("5")
    assert result.calories == Decimal("200")
