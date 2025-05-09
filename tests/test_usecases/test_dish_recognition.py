from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from usecases.dish_recognition import DishRecognitionUseCase
from usecases.schemas import DishData, DishSchema


@pytest.mark.asyncio
async def test_recognize_dish_from_text():
    ai_client = AsyncMock()
    db_repo = AsyncMock()

    dish_data = DishData(
        name="авокадо тост", calories=Decimal(500), protein=Decimal(20), fat=Decimal(15), carbohydrates=Decimal(60)
    )
    ai_client.__aenter__.return_value.recognize_meal_by_text.return_value = dish_data
    db_repo.__aenter__.return_value.save_dish.return_value = DishSchema(id=1, **dish_data.model_dump())

    usecase = DishRecognitionUseCase(ai_client=ai_client, db_repository=db_repo)
    result = await usecase.recognize_dish_from_text(dish_name="авокадо тост")

    assert result.name == "авокадо тост"
    assert result.calories == 500
