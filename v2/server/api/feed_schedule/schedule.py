"""
Service for computing weekly schedule data from FeedRules.

Handles time block overlap resolution using the following algorithm:
When two time blocks A and B overlap, they are split into 3 blocks:
  - X: A ∩ B^c (time only in A, not in B)
  - Y: A ∩ B (time in both A and B)
  - Z: A^c ∩ B (time only in B, not in A)

For each split block:
  - X gets A's tags, energy range, educational range
  - Y gets union of both tags, intersection of energy ranges, intersection of educational ranges
  - Z gets B's tags, energy range, educational range

This ensures every time slot has all applicable rules represented, with overlaps
showing the intersection of constraints.
"""

from datetime import time
from typing import Optional
from schema import ScheduleRules
from model import DAY_OF_WEEK

type RuleSchedule = dict[DAY_OF_WEEK, list[TimeRange]]
"""{ weekday -> [{ start_hour, end_hour, rule_name, category_tags, min_energy, max_energy, min_educational, max_educational }] }"""


def _filter_none[T](values: list[T | None] = None) -> list[T]:
    if not values:
        return [] 
    else:
        return [v for v in values if v is not None]
    
def _safe_max[T: int | float](*values: list[T | None]) -> T | None:
    _values = _filter_none(values)
    if len(_values) > 0:
        return max(_values)
    else:
        return None

def _safe_min[T: int | float](*values: list[T | None]) -> T | None:
    _values = _filter_none(values)
    if len(_values) > 0:
        return min(_values)
    else:
        return None


# TODO: Refactor logic.....
class TimeRange:
    """Represents a time range with associated rule metadata."""

    def __init__(
        self,
        start_hour: int,
        end_hour: int,
        rule_ids: list[int],
        rule_name: str,
        category_tags: list[str],
        min_energy: Optional[int],
        max_energy: Optional[int],
        min_educational: Optional[int],
        max_educational: Optional[int],
    ):
        self.start_hour = start_hour  # 0-23
        self.end_hour = end_hour  # 0-23 (exclusive, so 1-24 in terms of actual hour)
        self.rule_ids = rule_ids
        self.rule_name = rule_name
        self.category_tags = category_tags
        self.min_energy = min_energy
        self.max_energy = max_energy
        self.min_educational = min_educational
        self.max_educational = max_educational
        self.hours = end_hour - start_hour  # Duration in hours

    def time_str(self) -> str:
        """Return human-readable time range like '9:00 AM - 10:00 AM'."""
        start = time(hour=self.start_hour)
        end = time(hour=self.end_hour % 24)
        return f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"

    def overlaps_with(self, other: TimeRange) -> bool:
        """Check if this range overlaps with another."""
        return self.start_hour < other.end_hour and other.start_hour < self.end_hour

    def intersection(self, other: TimeRange) -> Optional[TimeRange]:
        """Return the overlapping portion, or None if no overlap."""

        if not self.overlaps_with(other):
            return None

        return TimeRange(
            start_hour      =_safe_max(self.start_hour, other.start_hour),
            end_hour        =_safe_min(self.end_hour, other.end_hour),
            rule_ids        =[*self.rule_ids, *other.rule_ids],
            rule_name       =f"{self.rule_name} & {other.rule_name}",
            category_tags   =list(set(self.category_tags + other.category_tags)),
            min_energy      =_safe_max(self.min_energy, other.min_energy),
            max_energy      =_safe_min(self.max_energy, other.max_energy),
            min_educational =_safe_max(self.min_educational, other.min_educational),
            max_educational =_safe_min(self.max_educational, other.max_educational),
        )

    def difference(self, other: TimeRange) -> list[TimeRange]:
        """Return the portions of this range that don't overlap with other."""
        if not self.overlaps_with(other):
            return [self]

        result = []
        # Part before the overlap
        if self.start_hour < other.start_hour:
            result.append(
                TimeRange(
                    start_hour=self.start_hour,
                    end_hour=min(self.end_hour, other.start_hour),
                    rule_ids=self.rule_ids,
                    rule_name=self.rule_name,
                    category_tags=self.category_tags,
                    min_energy=self.min_energy,
                    max_energy=self.max_energy,
                    min_educational=self.min_educational,
                    max_educational=self.max_educational,
                )
            )

        # Part after the overlap
        if self.end_hour > other.end_hour:
            result.append(
                TimeRange(
                    start_hour=max(self.start_hour, other.end_hour),
                    end_hour=self.end_hour,
                    rule_ids=self.rule_ids,
                    rule_name=self.rule_name,
                    category_tags=self.category_tags,
                    min_energy=self.min_energy,
                    max_energy=self.max_energy,
                    min_educational=self.min_educational,
                    max_educational=self.max_educational,
                )
            )

        return result


def _merge_active_ranges(
    active_ranges: list[TimeRange],
    start_hour: int,
    end_hour: int,
) -> TimeRange:
    """Merge metadata for a time segment covered by one or more active ranges."""
    if len(active_ranges) == 1:
        src = active_ranges[0]
        return TimeRange(
            start_hour=start_hour,
            end_hour=end_hour,
            rule_ids=src.rule_ids,
            rule_name=src.rule_name,
            category_tags=list(src.category_tags),
            min_energy=src.min_energy,
            max_energy=src.max_energy,
            min_educational=src.min_educational,
            max_educational=src.max_educational,
        )

    rule_ids: list[int] = []
    rule_names: list[str] = []
    category_tags: list[str] = []
    for r in active_ranges:
        if r.rule_name not in rule_names:
            rule_names.append(r.rule_name)
            rule_ids.extend(r.rule_ids)
        for tag in r.category_tags:
            if tag not in category_tags:
                category_tags.append(tag)

    min_energies = [r.min_energy for r in active_ranges]
    max_energies = [r.max_energy for r in active_ranges]
    min_educationals = [r.min_educational for r in active_ranges]
    max_educationals = [r.max_educational for r in active_ranges]

    # Overlap segment should keep the intersection of ranges.
    min_energy = _safe_max(min_energies)
    max_energy = _safe_min(max_energies)
    min_educational = _safe_max(min_educationals)
    max_educational = _safe_min(max_educationals)

    if min_energy is not None and max_energy is not None and min_energy > max_energy:
        min_energy = None
        max_energy = None
        
    if (
        min_educational is not None
        and max_educational is not None
        and min_educational > max_educational
    ):
        min_educational = None
        max_educational = None

    return TimeRange(
        start_hour=start_hour,
        end_hour=end_hour,
        rule_ids=rule_ids,
        rule_name=" & ".join(rule_names),
        category_tags=category_tags,
        min_energy=min_energy,
        max_energy=max_energy,
        min_educational=min_educational,
        max_educational=max_educational,
    )


def resolve_overlaps(ranges: list[TimeRange]) -> list[TimeRange]:
    """
    Resolve overlapping ranges by splitting across unique boundaries.

    This guarantees X/Y/Z style segments are emitted:
    - X = A - B
    - Y = A ∩ B
    - Z = B - A
    """
    if not ranges:
        return []

    boundaries = sorted({p for r in ranges for p in (r.start_hour, r.end_hour)})
    resolved: list[TimeRange] = []

    for idx in range(len(boundaries) - 1):
        start_hour = boundaries[idx]
        end_hour = boundaries[idx + 1]
        if start_hour == end_hour:
            continue

        active_ranges = [
            r for r in ranges if r.start_hour < end_hour and start_hour < r.end_hour
        ]
        if not active_ranges:
            continue

        resolved.append(_merge_active_ranges(active_ranges, start_hour, end_hour))

    return resolved


def compute_feed_schedule(rules: list[ScheduleRules]) -> RuleSchedule:
    """
    Compute a weekly schedule from FeedRules.

    Returns a dictionary mapping day names to lists of TimeRange objects,
    with all overlaps resolved.

    Days are: monday, tuesday, wednesday, thursday, friday, saturday, sunday
    """
    day_names = [
        DAY_OF_WEEK.MON,
        DAY_OF_WEEK.TUE,
        DAY_OF_WEEK.WED,
        DAY_OF_WEEK.THU,
        DAY_OF_WEEK.FRI,
        DAY_OF_WEEK.SAT,
        DAY_OF_WEEK.SUN,
    ]
    schedule = {day: [] for day in day_names}

    for day in day_names:
        # Find all rules active on this day
        day_rules = [r for r in rules if getattr(r, day)]

        for rule in day_rules:
            # Convert time to hour (rounded down for fractional hours)
            start_hour = rule.start_time.hour
            # For end_time, if it's midnight (0:00), it means end of day (hour 24)
            end_hour = rule.end_time.hour if rule.end_time.hour != 0 else 24

            # If end_time is before start_time, assume it wraps to next day
            if end_hour <= start_hour and rule.end_time.hour != 0:
                # Don't include this; it's invalid or wraps days
                continue

            time_range = TimeRange(
                start_hour=start_hour,
                end_hour=end_hour,
                rule_ids=[rule.id],
                rule_name=rule.name,
                category_tags=rule.category_tags or [],
                min_energy=rule.min_energy,
                max_energy=rule.max_energy,
                min_educational=rule.min_educational,
                max_educational=rule.max_educational,
            )
            schedule[day].append(time_range)

        # Resolve overlaps for this day
        schedule[day] = resolve_overlaps(schedule[day])

    return schedule


class FeedSchedule:

    _ScheduleCache: RuleSchedule | None = None

    def __init__(self, db):
        self._db = db

    def get_feed_schedule(self) -> RuleSchedule:
        """Get the weekly schedule from cache, computing it if not present."""
        if not FeedSchedule._ScheduleCache:
            rules = (
                self._db.query(ScheduleRules)
                .order_by(ScheduleRules.start_time, ScheduleRules.name)
                .all()
            )
            schedule = compute_feed_schedule(list(rules))
            FeedSchedule._ScheduleCache = schedule

        return FeedSchedule._ScheduleCache

    def get_current_rule_block(
        self, day: DAY_OF_WEEK, hour: int
    ) -> Optional[TimeRange]:
        """Get the active TimeRange for the given day and hour, if any."""
        schedule = self.get_feed_schedule()
        for time_range in schedule.get(day, []):
            if time_range.start_hour <= hour < time_range.end_hour:
                return time_range
        return None
