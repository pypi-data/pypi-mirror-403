"""Spaced Repetition System algorithm for Sensei.

Implements an SM-2 inspired algorithm for scheduling review tasks.
"""

from datetime import datetime, timedelta
from typing import Any

from sensei.models import SRSMetadata


def get_initial_srs_metadata() -> dict[str, Any]:
    """Get initial SRS metadata for a new task."""
    return SRSMetadata().model_dump()


def calculate_next_interval(
    metadata: dict[str, Any],
    passed: bool,
    score: float | None = None,
) -> tuple[dict[str, Any], datetime]:
    """
    Calculate the next review interval based on assessment results.

    Args:
        metadata: Current SRS metadata (interval_days, ease_factor, repetition_count)
        passed: Whether the assessment was passed
        score: Optional numeric score (0-10 scale)

    Returns:
        Tuple of (updated_metadata, next_due_date)
    """
    srs = SRSMetadata(**metadata)

    if passed:
        srs.repetition_count += 1
        if srs.repetition_count == 1:
            srs.interval_days = 1
        elif srs.repetition_count == 2:
            srs.interval_days = 3
        else:
            srs.interval_days = round(srs.interval_days * srs.ease_factor)
    else:
        srs.repetition_count = 0
        srs.interval_days = 1
        srs.ease_factor = max(1.3, srs.ease_factor - 0.2)

    # Score-based adjustment
    if score is not None:
        if score >= 8:
            srs.ease_factor = min(2.5, srs.ease_factor + 0.1)
        elif score < 5:
            srs.ease_factor = max(1.3, srs.ease_factor - 0.1)

    next_due = datetime.now() + timedelta(days=srs.interval_days)

    return srs.model_dump(), next_due


def calculate_due_date_from_days(days: int) -> datetime:
    """Calculate a due date N days from now."""
    return datetime.now() + timedelta(days=days)
