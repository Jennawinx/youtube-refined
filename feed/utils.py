from typing import Optional

from feed.services.schedule import WeekDay

# Input parsing

def parse_rating(value: Optional[str], min:int = 1, max:int = 10) -> Optional[int]:
    """Parse a 1-10 rating GET param; returns None if missing/invalid."""
    if value is None or value.strip() == "":
        return None
    try:
        v = int(value.strip())
        return v if min <= v <= max else None
    except (ValueError, TypeError):
        return None


def parse_week_day(value: Optional[str]) -> Optional[WeekDay]:
    """Parse full weekday name; returns WeekDay enum or None if invalid."""
    if value is None or value.strip() == "":
        return None
    
    days = {
        "monday": WeekDay.MONDAY,
        "tuesday": WeekDay.TUESDAY,
        "wednesday": WeekDay.WEDNESDAY,
        "thursday": WeekDay.THURSDAY,
        "friday": WeekDay.FRIDAY,
        "saturday": WeekDay.SATURDAY,
        "sunday": WeekDay.SUNDAY,
    }

    day = value.strip().lower()
    return days.get(day, None)


def parse_comma_list(value: Optional[str]) -> list[str]:
    """Parse a comma-separated list; returns empty list if missing/invalid."""
    if not value or not value.strip():
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def parse_hour(value: Optional[str]) -> Optional[int]:
    """Parse hour value in the inclusive range 0..24."""
    if value is None or value.strip() == "":
        return None
    
    try:
        hour = int(value.strip())
        return hour if 0 <= hour <= 24 else None
    except (ValueError, TypeError):
        return None


# Filters

def filter_exists(l: list) -> list:
    """Filter out None values from a list."""
    return [x for x in l if x is not None]


def find_max(l: list) -> Optional[int]:
    """Find max value in a list, ignoring None; returns None if no valid values."""
    filtered = filter_exists(l)
    return max(filtered) if len(filtered) > 0 else None


def find_min(l: list) -> Optional[int]:
    """Find min value in a list, ignoring None; returns None if no valid values."""
    filtered = filter_exists(l)
    return min(filtered) if len(filtered) > 0 else None
