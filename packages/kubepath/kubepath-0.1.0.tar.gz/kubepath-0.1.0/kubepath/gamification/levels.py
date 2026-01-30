"""Level system for kubepath gamification.

Defines 12 Kubernetes-themed levels based on total score.
"""

from typing import Any

# Level definitions: 12 levels from beginner to master
LEVELS: list[dict[str, Any]] = [
    {"level": 1, "name": "Pod Seedling", "min_score": 0},
    {"level": 2, "name": "Container Cadet", "min_score": 100},
    {"level": 3, "name": "Namespace Navigator", "min_score": 300},
    {"level": 4, "name": "Deployment Apprentice", "min_score": 600},
    {"level": 5, "name": "Service Scout", "min_score": 1000},
    {"level": 6, "name": "ConfigMap Crafter", "min_score": 1500},
    {"level": 7, "name": "Secret Keeper", "min_score": 2100},
    {"level": 8, "name": "Volume Voyager", "min_score": 2800},
    {"level": 9, "name": "Cluster Captain", "min_score": 3600},
    {"level": 10, "name": "Helm Hero", "min_score": 4500},
    {"level": 11, "name": "CKAD Champion", "min_score": 5500},
    {"level": 12, "name": "Kubernetes Kurator", "min_score": 6600},
]

MAX_LEVEL = 12


def get_level_for_score(score: int) -> dict[str, Any]:
    """Get the level info for a given score.

    Args:
        score: Total score across all chapters

    Returns:
        Level dict with 'level', 'name', and 'min_score' keys
    """
    current_level = LEVELS[0]
    for level in LEVELS:
        if score >= level["min_score"]:
            current_level = level
        else:
            break
    return current_level


def get_next_level(current_level: int) -> dict[str, Any] | None:
    """Get the next level info, or None if at max level.

    Args:
        current_level: Current level number (1-12)

    Returns:
        Next level dict or None if at max level
    """
    if current_level >= MAX_LEVEL:
        return None
    return LEVELS[current_level]  # 0-indexed, so level N -> index N is next


def get_progress_to_next_level(score: int) -> tuple[int, int]:
    """Calculate progress towards the next level.

    Args:
        score: Total score

    Returns:
        Tuple of (points_earned_towards_next, points_needed_for_next)
        Returns (0, 0) if at max level
    """
    current = get_level_for_score(score)
    next_level = get_next_level(current["level"])

    if next_level is None:
        return (0, 0)

    current_min = current["min_score"]
    next_min = next_level["min_score"]

    points_earned = score - current_min
    points_needed = next_min - current_min

    return (points_earned, points_needed)


def check_level_up(old_score: int, new_score: int) -> dict[str, Any] | None:
    """Check if adding points caused a level up.

    Args:
        old_score: Score before adding points
        new_score: Score after adding points

    Returns:
        New level dict if leveled up, None otherwise
    """
    old_level = get_level_for_score(old_score)
    new_level = get_level_for_score(new_score)

    if new_level["level"] > old_level["level"]:
        return new_level
    return None
