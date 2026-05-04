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

from datetime import time, timedelta
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


def resolve_overlaps(ranges: list[TimeRange]) -> list[TimeRange]:
    """
    Resolve overlapping time ranges using the split algorithm.

    Takes a list of potentially overlapping TimeRange objects and returns a
    non-overlapping list where overlaps are split according to the algorithm.
    """
    if not ranges:
        return []

    if len(ranges) == 1:
        return ranges

    # Sort by start time
    sorted_ranges = sorted(ranges, key=lambda r: r.start_hour)

    result = []
    current = sorted_ranges[0]

    for next_range in sorted_ranges[1:]:
        if not current.overlaps_with(next_range):
            result.append(current)
            current = next_range
        else:
            # Resolve overlap: split into X (current only), Y (both), Z (next only)
            differences_current = current.difference(next_range)
            intersection = current.intersection(next_range)
            differences_next = next_range.difference(current)

            result.extend(differences_current)
            if intersection:
                result.append(intersection)

            # Continue with remaining portions of next_range
            if differences_next:
                # Recursively resolve if there are more ranges
                current = next_range
            else:
                # next_range is completely consumed
                if sorted_ranges.index(next_range) + 1 < len(sorted_ranges):
                    current = sorted_ranges[sorted_ranges.index(next_range) + 1]

    result.append(current)
    return sorted(result, key=lambda r: r.start_hour)


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
