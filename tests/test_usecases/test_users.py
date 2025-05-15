from unittest.mock import AsyncMock

import pytest

from usecases.schemas import ActivityType, GoalType, NutritionGoalSchema
from usecases.users import UsersUseCase


@pytest.mark.asyncio
async def test_set_nutrition_goal(mocker):
    db_repo = AsyncMock()
    ai_client = AsyncMock()

    db_repo.__aenter__.return_value.save_nutrition.return_value = mocker.Mock(id=42)
    db_repo.__aenter__.return_value.set_user_nutrition_goal.return_value = None

    usecase = UsersUseCase(ai_client=ai_client, db_repository=db_repo)
    await usecase.set_nutrition_goal(
        user_id=1,
        goal_data=NutritionGoalSchema(
            weight=70,
            height=175,
            age=25,
            is_male=True,
            activity_type=ActivityType.MAXIMUM,
            nutrition_goal_type=GoalType.SUPPORT_FORM,
        ),
    )

    db_repo.__aenter__.return_value.set_user_nutrition_goal.assert_called_once()
