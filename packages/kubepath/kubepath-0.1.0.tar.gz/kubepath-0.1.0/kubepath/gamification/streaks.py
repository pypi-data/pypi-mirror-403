"""Streak tracking for kubepath gamification.

Tracks consecutive days of activity, similar to Duolingo.
"""

from datetime import date, timedelta
from typing import Any

# Streak milestones to celebrate
STREAK_MILESTONES = [7, 14, 30, 60, 90, 180, 365]


def update_streak(
    last_active_date: str | None,
    current_streak: int = 0,
    longest_streak: int = 0,
) -> dict[str, Any]:
    """Update streak based on activity.

    Args:
        last_active_date: ISO format date string of last activity, or None if first time
        current_streak: Current streak count
        longest_streak: Longest streak ever achieved

    Returns:
        Dict with updated streak info:
        - current: Updated current streak
        - longest: Updated longest streak
        - last_active_date: Today's date as ISO string
        - maintained: Whether streak was maintained (True) or reset (False)
        - milestone: Milestone reached (7, 14, 30, etc.) or None
    """
    today = date.today()
    today_str = today.isoformat()

    # First time user
    if last_active_date is None:
        return {
            "current": 1,
            "longest": max(1, longest_streak),
            "last_active_date": today_str,
            "maintained": True,
            "milestone": None,
        }

    last_date = date.fromisoformat(last_active_date)
    days_since = (today - last_date).days

    # Same day - no change to streak
    if days_since == 0:
        return {
            "current": current_streak,
            "longest": longest_streak,
            "last_active_date": today_str,
            "maintained": True,
            "milestone": None,
        }

    # Yesterday - streak continues!
    if days_since == 1:
        new_streak = current_streak + 1
        new_longest = max(new_streak, longest_streak)
        milestone = check_streak_milestone(new_streak)
        return {
            "current": new_streak,
            "longest": new_longest,
            "last_active_date": today_str,
            "maintained": True,
            "milestone": milestone,
        }

    # More than 1 day gap - streak resets
    return {
        "current": 1,
        "longest": longest_streak,
        "last_active_date": today_str,
        "maintained": False,
        "milestone": None,
    }


def check_streak_milestone(streak: int) -> int | None:
    """Check if the streak has hit a milestone.

    Args:
        streak: Current streak count

    Returns:
        Milestone number if hit (7, 14, 30, etc.), None otherwise
    """
    if streak in STREAK_MILESTONES:
        return streak
    return None


def format_streak_display(current: int, longest: int) -> str:
    """Format streak for terminal display.

    Args:
        current: Current streak
        longest: Longest streak

    Returns:
        Formatted string like "7-day streak" or "No streak"
    """
    if current <= 0:
        return "No streak"
    if current == 1:
        return "1-day streak"
    return f"{current}-day streak"
