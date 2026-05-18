from typing import Optional

# Input parsing

def parse_rating(value: str, min:int = 1, max:int = 10) -> Optional[int]:
    """Parse a 1-10 rating GET param; returns None if missing/invalid."""
    try:
        v = int(value)
        return v if min <= v <= max else None
    except (ValueError, TypeError):
        return None

