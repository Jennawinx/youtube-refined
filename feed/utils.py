from typing import Optional

# Input parsing

def parse_rating(value: str, min:int = 1, max:int = 10) -> Optional[int]:
    """Parse a 1-10 rating GET param; returns None if missing/invalid."""
    try:
        v = int(value)
        return v if min <= v <= max else None
    except (ValueError, TypeError):
        return None


def parse_day(value: str) -> Optional[str]:
    """Parse full weekday name; returns lowercase name or None if invalid."""
    days = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }
    if value is None:
        return None
    
    day = value.strip().lower()
    return day if day in days else None


def parse_hour(value: str) -> Optional[int]:
    """Parse hour value in the inclusive range 0..24."""
    try:
        hour = int(value)
        return hour if 0 <= hour <= 24 else None
    except (ValueError, TypeError):
        return None

