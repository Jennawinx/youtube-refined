from typing import Optional

from feed.services.schedule import WeekDay

# Input parsing

def parse_rating(value: str, min:int = 1, max:int = 10) -> Optional[int]:
    """Parse a 1-10 rating GET param; returns None if missing/invalid."""
    try:
        v = int(value)
        return v if min <= v <= max else None
    except (ValueError, TypeError):
        return None


def parse_week_day(value: str) -> Optional[WeekDay]:
    """Parse full weekday name; returns WeekDay enum or None if invalid."""
    days = {
        "monday": WeekDay.MONDAY,
        "tuesday": WeekDay.TUESDAY,
        "wednesday": WeekDay.WEDNESDAY,
        "thursday": WeekDay.THURSDAY,
        "friday": WeekDay.FRIDAY,
        "saturday": WeekDay.SATURDAY,
        "sunday": WeekDay.SUNDAY,
    }
    if value is None:
        return None
    
    day = value.strip().lower()
    return days.get(day, None)


def parse_hour(value: str) -> Optional[int]:
    """Parse hour value in the inclusive range 0..24."""
    try:
        hour = int(value)
        return hour if 0 <= hour <= 24 else None
    except (ValueError, TypeError):
        return None

