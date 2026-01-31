"""
Вспомогательные утилиты для decorators: работа со временем и парсинг данных записи.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Union


def format_seconds_to_human(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}с"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")

    return " ".join(parts) if parts else "0м"


def parse_time_string(time_str: Union[str, int]) -> int:
    if isinstance(time_str, int):
        return time_str

    time_str = time_str.strip().lower()
    if time_str.isdigit():
        return int(time_str)

    total_seconds = 0
    pattern = r"(\d+)\s*(h|m|s)"
    matches = re.findall(pattern, time_str)
    if not matches:
        raise ValueError(f"Неверный формат времени: '{time_str}'. Используйте формат '1h 30m 45s'")

    for value, unit in matches:
        value = int(value)
        if unit == "h":
            total_seconds += value * 3600
        elif unit == "m":
            total_seconds += value * 60
        elif unit == "s":
            total_seconds += value

    if total_seconds <= 0:
        raise ValueError(f"Время должно быть больше 0: '{time_str}'")

    return total_seconds


def parse_supabase_datetime(datetime_str: str) -> datetime:
    if not datetime_str:
        raise ValueError("Пустая строка даты и времени")

    datetime_str = datetime_str.strip()

    try:
        if datetime_str.endswith("Z"):
            datetime_str = datetime_str[:-1] + "+00:00"
            return datetime.fromisoformat(datetime_str)

        if "+" in datetime_str or datetime_str.count("-") > 2:
            return datetime.fromisoformat(datetime_str)

        if "T" in datetime_str:
            return datetime.fromisoformat(datetime_str + "+00:00")

        return datetime.fromisoformat(datetime_str + "T00:00:00+00:00")
    except ValueError as e:
        raise ValueError(f"Неверный формат даты и времени: '{datetime_str}'. Ошибка: {e}")


def format_datetime_for_supabase(dt: datetime) -> str:
    if not isinstance(dt, datetime):
        raise ValueError("Ожидается объект datetime")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat()


def get_time_difference_seconds(dt1: datetime, dt2: datetime) -> int:
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)

    return int((dt2 - dt1).total_seconds())


def is_datetime_recent(dt: datetime, max_age_seconds: int = 3600) -> bool:
    if not isinstance(dt, datetime):
        raise ValueError("Ожидается объект datetime")

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    age_seconds = (now - dt).total_seconds()
    return age_seconds <= max_age_seconds


def parse_appointment_data(data_str: str) -> Dict[str, Any]:
    if not data_str or not isinstance(data_str, str):
        return {}

    result = {}
    try:
        pattern = r"([^:]+):\s*([^,]+?)(?=,\s*[^:]+:|$)"
        matches = re.findall(pattern, data_str.strip())

        for key, value in matches:
            clean_key = key.strip()
            clean_value = value.strip()
            if clean_value.endswith(","):
                clean_value = clean_value[:-1].strip()
            result[clean_key] = clean_value

        if "дата" in result and "время" in result:
            try:
                appointment_datetime = datetime.strptime(f"{result['дата']} {result['время']}", "%Y-%m-%d %H:%M")
                result["datetime"] = appointment_datetime
                result["datetime_str"] = appointment_datetime.strftime("%Y-%m-%d %H:%M")
                now = datetime.now()
                result["is_past"] = appointment_datetime < now
            except ValueError as e:
                result["datetime_error"] = str(e)
        return result
    except Exception as e:
        return {"error": str(e), "raw_data": data_str}


def format_appointment_data(appointment_data: Dict[str, Any]) -> str:
    if not appointment_data or not isinstance(appointment_data, dict):
        return ""

    exclude_fields = {
        "datetime",
        "datetime_str",
        "is_past",
        "datetime_error",
        "error",
        "raw_data",
    }

    parts = []
    for key, value in appointment_data.items():
        if key not in exclude_fields and value is not None:
            parts.append(f"{key}: {value}")

    return ", ".join(parts)


def validate_appointment_data(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    result = {"valid": True, "errors": [], "warnings": []}

    required_fields = ["имя", "телефон", "процедура", "мастер", "дата", "время"]
    for field in required_fields:
        if field not in appointment_data or not appointment_data[field]:
            result["errors"].append(f"Отсутствует обязательное поле: {field}")
            result["valid"] = False

    if "телефон" in appointment_data:
        phone = appointment_data["телефон"]
        if not re.match(r"^\+?[1-9]\d{10,14}$", phone.replace(" ", "").replace("-", "")):
            result["warnings"].append(f"Неверный формат телефона: {phone}")

    if "дата" in appointment_data:
        try:
            datetime.strptime(appointment_data["дата"], "%Y-%m-%d")
        except ValueError:
            result["errors"].append(f"Неверный формат даты: {appointment_data['дата']}")
            result["valid"] = False

    if "время" in appointment_data:
        try:
            datetime.strptime(appointment_data["время"], "%H:%M")
        except ValueError:
            result["errors"].append(f"Неверный формат времени: {appointment_data['время']}")
            result["valid"] = False

    if "is_past" in appointment_data and appointment_data["is_past"]:
        result["warnings"].append("Запись назначена на прошедшую дату")

    return result
