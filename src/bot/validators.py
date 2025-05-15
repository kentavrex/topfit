from usecases.schemas import GoalType, ActivityType


class GoalValidator:
    @classmethod
    def validate_height(cls, value: str) -> float:
        try:
            height = float(value)
            if 50 <= height <= 250:
                return height
            raise ValueError
        except ValueError:
            raise ValueError("Рост должен быть числом от 50 до 250 см.") from None

    @classmethod
    def validate_weight(cls, value: str) -> float:
        try:
            weight = float(value)
            if 20 <= weight <= 300:
                return weight
            raise ValueError
        except ValueError:
            raise ValueError("Вес должен быть числом от 20 до 300 кг.") from None

    @classmethod
    def validate_age(cls, value: str) -> int:
        try:
            age = int(value)
            if 10 <= age <= 120:
                return age
            raise ValueError
        except ValueError:
            raise ValueError("Возраст должен быть числом от 10 до 120 лет.") from None

    @classmethod
    def validate_gender(cls, value: str) -> bool:
        if value.strip().lower() in ["м", "ж"]:
            return value.lower() == "м"
        raise ValueError("Введите 'м' (мужской) или 'ж' (женский).")

    @classmethod
    def validate_activity(cls, value: str) -> int:
        try:
            activity_number = int(value)
            if activity_number in [i + 1 for i, _ in enumerate(ActivityType)]:
                return activity_number
            raise ValueError
        except ValueError:
            raise ValueError("Введите корректный номер уровня активности.") from None


    @classmethod
    def validate_goal(cls, value: str) -> int:
        try:
            goal_number = int(value)
            if goal_number in [i + 1 for i, _ in enumerate(GoalType)]:
                return goal_number
            raise ValueError
        except ValueError:
            raise ValueError("Введите корректный номер цели.") from None
