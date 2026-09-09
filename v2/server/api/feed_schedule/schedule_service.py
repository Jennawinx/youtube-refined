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

import json
from typing import Optional
from fastapi import Depends
from pydantic import BaseModel
from schema import ScheduleRules
from model import DAY_OF_WEEK, DAY_NAMES
from db import get_db


class RuleBlock(BaseModel):
    start_hour: int
    end_hour: int
    rule_name: str
    rule_ids: list[int]
    category_tags: list[str]
    min_energy: Optional[int] = None
    max_energy: Optional[int] = None
    min_educational: Optional[int] = None
    max_educational: Optional[int] = None


# class FeedSchedule(RootModel[dict[DAY_OF_WEEK, list[RuleBlock]]]):
#     """{ weekday -> [{ start_hour, end_hour, rule_name, category_tags, min_energy, max_energy, min_educational, max_educational }] }"""
#     pass

class FeedSchedule(BaseModel):
    """{ weekday -> [{ start_hour, end_hour, rule_name, category_tags, min_energy, max_energy, min_educational, max_educational }] }"""
    monday: list[RuleBlock]
    tuesday: list[RuleBlock]
    wednesday: list[RuleBlock]
    thursday: list[RuleBlock]
    friday: list[RuleBlock]
    saturday: list[RuleBlock]
    sunday: list[RuleBlock]


# type RuleSchedule = dict[DAY_OF_WEEK, list[TimeRange]]
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


def _schedule_merge_active_ranges(
    active_ranges: list[RuleBlock],
    start_hour: int,
    end_hour: int,
) -> RuleBlock:
    """Merge metadata for a time segment covered by one or more active ranges."""
    if len(active_ranges) == 1:
        src = active_ranges[0]
        return RuleBlock(
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

    # Overlap segment should keep the intersection of ranges.
    min_energy = _safe_max(*[r.min_energy for r in active_ranges])
    max_energy = _safe_min(*[r.max_energy for r in active_ranges])
    min_educational = _safe_max(*[r.min_educational for r in active_ranges])
    max_educational = _safe_min(*[r.max_educational for r in active_ranges])

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

    return RuleBlock(
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


def _schedule_resolve_overlaps(ranges: list[RuleBlock]) -> list[RuleBlock]:
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
    resolved: list[RuleBlock] = []

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

        resolved.append(
            _schedule_merge_active_ranges(active_ranges, start_hour, end_hour)
        )

    return resolved


def _schedule_compute(rules: list[ScheduleRules]) -> FeedSchedule:
    """
    Compute a weekly schedule from FeedRules.

    Returns a dictionary mapping day names to lists of TimeRange objects,
    with all overlaps resolved.

    Days are: monday, tuesday, wednesday, thursday, friday, saturday, sunday
    """

    schedule = {day: [] for day in DAY_NAMES}

    for day in DAY_NAMES:
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

            time_range = RuleBlock(
                start_hour=start_hour,
                end_hour=end_hour,
                rule_ids=[rule.id],
                rule_name=rule.name,
                category_tags=json.loads(rule.category_tags),
                min_energy=rule.min_energy,
                max_energy=rule.max_energy,
                min_educational=rule.min_educational,
                max_educational=rule.max_educational,
            )
            schedule[day].append(time_range)

        # Resolve overlaps for this day
        schedule[day] = _schedule_resolve_overlaps(schedule[day])

    return schedule


class FeedScheduleService:

    _ScheduleCache: FeedSchedule | None = None

    def __init__(self, db=Depends(get_db)):
        self._db = db

    def get_feed_schedule(self) -> FeedSchedule:
        """Get the weekly schedule from cache, computing it if not present."""
        if not FeedScheduleService._ScheduleCache:
            rules = (
                self._db.query(ScheduleRules)
                .order_by(ScheduleRules.start_time, ScheduleRules.name)
                .all()
            )
            schedule = _schedule_compute(list(rules))
            FeedScheduleService._ScheduleCache = schedule

        return FeedScheduleService._ScheduleCache

    def get_current_rule_block(
        self, day: DAY_OF_WEEK, hour: int
    ) -> Optional[RuleBlock]:
        """Get the active TimeRange for the given day and hour, if any."""
        schedule = self.get_feed_schedule()
        for time_range in schedule.get(day, []):
            if time_range.start_hour <= hour < time_range.end_hour:
                return time_range
        return None
