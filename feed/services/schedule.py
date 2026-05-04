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

from feed.models import FeedRule


class TimeRange:
    """Represents a time range with associated rule metadata."""

    def __init__(
        self,
        start_hour: int,
        end_hour: int,
        rule_name: str,
        category_tags: list[str],
        min_energy: Optional[int],
        max_energy: Optional[int],
        min_educational: Optional[int],
        max_educational: Optional[int],
    ):
        self.start_hour = start_hour  # 0-23
        self.end_hour = end_hour  # 0-23 (exclusive, so 1-24 in terms of actual hour)
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

    def overlaps_with(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another."""
        return self.start_hour < other.end_hour and other.start_hour < self.end_hour

    def intersection(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Return the overlapping portion, or None if no overlap."""
        if not self.overlaps_with(other):
            return None

        start = max(self.start_hour, other.start_hour)
        end = min(self.end_hour, other.end_hour)

        # Combine tags from both rules
        combined_tags = list(set(self.category_tags + other.category_tags))

        # Intersection of energy ranges
        min_energy = (
            max(self.min_energy, other.min_energy)
            if self.min_energy and other.min_energy
            else self.min_energy or other.min_energy
        )
        max_energy = (
            min(self.max_energy, other.max_energy)
            if self.max_energy and other.max_energy
            else self.max_energy or other.max_energy
        )

        # Intersection of educational ranges
        min_educational = (
            max(self.min_educational, other.min_educational)
            if self.min_educational and other.min_educational
            else self.min_educational or other.min_educational
        )
        max_educational = (
            min(self.max_educational, other.max_educational)
            if self.max_educational and other.max_educational
            else self.max_educational or other.max_educational
        )

        return TimeRange(
            start_hour=start,
            end_hour=end,
            rule_name=f"{self.rule_name} & {other.rule_name}",
            category_tags=combined_tags,
            min_energy=min_energy,
            max_energy=max_energy,
            min_educational=min_educational,
            max_educational=max_educational,
        )

    def difference(self, other: "TimeRange") -> list["TimeRange"]:
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
            rule_name=src.rule_name,
            category_tags=list(src.category_tags),
            min_energy=src.min_energy,
            max_energy=src.max_energy,
            min_educational=src.min_educational,
            max_educational=src.max_educational,
        )

    rule_names: list[str] = []
    category_tags: list[str] = []
    for r in active_ranges:
        if r.rule_name not in rule_names:
            rule_names.append(r.rule_name)
        for tag in r.category_tags:
            if tag not in category_tags:
                category_tags.append(tag)

    min_energies = [r.min_energy for r in active_ranges if r.min_energy is not None]
    max_energies = [r.max_energy for r in active_ranges if r.max_energy is not None]
    min_educationals = [
        r.min_educational for r in active_ranges if r.min_educational is not None
    ]
    max_educationals = [
        r.max_educational for r in active_ranges if r.max_educational is not None
    ]

    # Overlap segment should keep the intersection of ranges.
    min_energy = max(min_energies) if min_energies else None
    max_energy = min(max_energies) if max_energies else None
    min_educational = max(min_educationals) if min_educationals else None
    max_educational = min(max_educationals) if max_educationals else None

    if (
        min_energy is not None
        and max_energy is not None
        and min_energy > max_energy
    ):
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
            r
            for r in ranges
            if r.start_hour < end_hour and start_hour < r.end_hour
        ]
        if not active_ranges:
            continue

        resolved.append(_merge_active_ranges(active_ranges, start_hour, end_hour))

    return resolved


def compute_weekly_schedule(rules: list[FeedRule]) -> dict[str, list[TimeRange]]:
    """
    Compute a weekly schedule from FeedRules.

    Returns a dictionary mapping day names to lists of TimeRange objects,
    with all overlaps resolved.

    Days are: monday, tuesday, wednesday, thursday, friday, saturday, sunday
    """
    day_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
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
