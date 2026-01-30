"""Gamification module for kubepath.

Provides level system, streak tracking, and social sharing features.
"""

from kubepath.gamification.levels import (
    LEVELS,
    get_level_for_score,
    get_next_level,
    get_progress_to_next_level,
    check_level_up,
)
from kubepath.gamification.streaks import (
    update_streak,
    check_streak_milestone,
    STREAK_MILESTONES,
)
from kubepath.gamification.sharing import (
    get_share_message,
    get_streak_share_message,
    copy_to_clipboard,
    open_twitter_share,
    open_linkedin_share,
    open_instagram_share,
    open_twitter_streak_share,
    open_linkedin_streak_share,
    open_instagram_streak_share,
)
from kubepath.gamification.ascii_art import (
    LEVEL_UP_ART,
    STREAK_ART,
    TROPHY_ART,
)

__all__ = [
    "LEVELS",
    "get_level_for_score",
    "get_next_level",
    "get_progress_to_next_level",
    "check_level_up",
    "update_streak",
    "check_streak_milestone",
    "STREAK_MILESTONES",
    "get_share_message",
    "get_streak_share_message",
    "copy_to_clipboard",
    "open_twitter_share",
    "open_linkedin_share",
    "open_instagram_share",
    "open_twitter_streak_share",
    "open_linkedin_streak_share",
    "open_instagram_streak_share",
    "LEVEL_UP_ART",
    "STREAK_ART",
    "TROPHY_ART",
]
