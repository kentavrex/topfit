def validate_height(value: str) -> float:
    try:
        height = float(value)
        if 50 <= height <= 250:
            return height
        raise ValueError
    except ValueError:
        raise ValueError("Рост должен быть числом от 50 до 250 см.")

def validate_weight(value: str) -> float:
    try:
        weight = float(value)
        if 20 <= weight <= 300:
            return weight
        raise ValueError
    except ValueError:
        raise ValueError("Вес должен быть числом от 20 до 300 кг.")

def validate_age(value: str) -> int:
    try:
        age = int(value)
        if 10 <= age <= 120:
            return age
        raise ValueError
    except ValueError:
        raise ValueError("Возраст должен быть числом от 10 до 120 лет.")

def validate_gender(value: str) -> bool:
    if value.lower() in ["м", "ж"]:
        return value.lower() == "м"
    raise ValueError("Введите 'м' (мужской) или 'ж' (женский).")

def validate_goal(value: str) -> int:
    try:
        goal_number = int(value)
        if goal_number in [1, 2, 3]:  # Заменить на реальные ID целей
            return goal_number
        raise ValueError
    except ValueError:
        raise ValueError("Введите корректный номер цели.")
