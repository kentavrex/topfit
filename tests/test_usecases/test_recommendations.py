import pytest
from unittest.mock import AsyncMock, MagicMock

from usecases import RecommendationUseCase
from usecases.errors import UserNutritionNotSetError
from usecases.schemas import NutritionSchema, DishRecommendation, DishSchema
from decimal import Decimal


@pytest.mark.asyncio
async def test_generate_recommendation_success():
    # Подготовка mock-ов
    mock_db = MagicMock()
    mock_db.__aenter__.return_value = mock_db
    mock_db.get_user_nutrition_goal = AsyncMock(return_value=NutritionSchema(
        protein=Decimal(100),
        fat=Decimal(70),
        carbohydrates=Decimal(250),
        calories=Decimal(2000),
        id=1,
    ))
    mock_db.get_user_dishes_history = AsyncMock(return_value=["борщ", "гречка"])
    mock_db.get_user_dishes_history_by_period = AsyncMock(return_value=[
        DishSchema(protein=Decimal(20), fat=Decimal(30), carbohydrates=Decimal(100), calories=Decimal(800),
                   name="4 сыра пицца", id=1),
    ])
    mock_db.save_dish = AsyncMock(return_value=MagicMock(id=1))
    mock_db.save_user_recommendation = AsyncMock()

    mock_ai = MagicMock()
    mock_ai.__aenter__.return_value = mock_ai
    mock_ai.get_dish_recommendation = AsyncMock(return_value=DishRecommendation(
        name="Куриная грудка",
        protein=Decimal(40),
        fat=Decimal(10),
        carbohydrates=Decimal(60),
        calories=Decimal(600),
        receipt="Рецепт блюда",
        servings_count=5,
    ))

    # Создание usecase
    use_case = RecommendationUseCase(ai_client=mock_ai, db_repository=mock_db)

    # Вызов
    result = await use_case.generate_recommendation(user_id=123)

    # Проверки
    assert result.name == "Куриная грудка"
    mock_db.get_user_nutrition_goal.assert_called_once_with(user_id=123)
    mock_db.get_user_dishes_history.assert_called_once_with(user_id=123, limit=50)
    mock_ai.get_dish_recommendation.assert_awaited()


@pytest.mark.asyncio
async def test_generate_recommendation_nutrition_not_set():
    mock_db = MagicMock()
    mock_db.__aenter__.return_value = mock_db
    mock_db.get_user_nutrition_goal = AsyncMock(return_value=None)

    mock_ai = MagicMock()
    mock_ai.__aenter__.return_value = mock_ai

    use_case = RecommendationUseCase(ai_client=mock_ai, db_repository=mock_db)

    with pytest.raises(UserNutritionNotSetError):
        await use_case.generate_recommendation(user_id=123)
