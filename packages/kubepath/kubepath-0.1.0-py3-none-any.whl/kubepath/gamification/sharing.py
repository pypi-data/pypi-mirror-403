"""Social sharing for kubepath achievements.

Enables sharing on X (Twitter), LinkedIn, and Instagram.
"""

import subprocess
import sys
import urllib.parse
import webbrowser

GITHUB_URL = "https://github.com/nithin-nk/kubepath"
HASHTAGS = "#Kubepath #Kubernetes #K8s #DevOps #Learning #CKAD"
STREAK_HASHTAGS = "#Kubepath #Kubernetes #K8s #DevOps #LearningStreak #CKAD"


def get_share_message(level_name: str, level_num: int) -> str:
    """Generate share message for a level-up achievement.

    Args:
        level_name: Name of the level reached
        level_num: Level number (1-12)

    Returns:
        Pre-formatted share message with hashtags
    """
    return (
        f"🚀 I just reached {level_name} (Level {level_num}) on Kubepath! "
        f"Kubepath teaches Kubernetes interactively in your terminal. "
        f"Try it: {GITHUB_URL} "
        f"{HASHTAGS}"
    )


def get_streak_share_message(streak_days: int) -> str:
    """Generate share message for a streak milestone.

    Args:
        streak_days: Number of days in the streak

    Returns:
        Pre-formatted share message with hashtags
    """
    return (
        f"🔥 I'm on a {streak_days}-day learning streak on Kubepath! "
        f"Kubepath teaches Kubernetes interactively in your terminal. "
        f"Join me: {GITHUB_URL} "
        f"{STREAK_HASHTAGS}"
    )


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard (cross-platform).

    Args:
        text: Text to copy

    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == "darwin":
            # macOS
            subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
            )
            return True
        elif sys.platform == "linux":
            # Linux with xclip
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
            )
            return True
        elif sys.platform == "win32":
            # Windows with clip
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16"),
                check=True,
            )
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


def open_twitter_share(level_name: str, level_num: int) -> bool:
    """Open X (Twitter) with pre-filled tweet for level-up.

    Args:
        level_name: Name of the level reached
        level_num: Level number

    Returns:
        True if browser opened successfully
    """
    message = get_share_message(level_name, level_num)
    encoded = urllib.parse.quote(message)
    url = f"https://twitter.com/intent/tweet?text={encoded}"
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_linkedin_share(level_name: str, level_num: int) -> bool:
    """Open LinkedIn share page for level-up.

    Args:
        level_name: Name of the level reached (unused, kept for consistency)
        level_num: Level number (unused, kept for consistency)

    Returns:
        True if browser opened successfully
    """
    encoded_url = urllib.parse.quote(GITHUB_URL)
    url = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_instagram_share(level_name: str, level_num: int) -> bool:
    """Copy message to clipboard and open Instagram for level-up.

    Instagram doesn't have a direct share API, so we copy the message
    to clipboard and open Instagram for the user to paste.

    Args:
        level_name: Name of the level reached
        level_num: Level number

    Returns:
        True if clipboard copy and browser open succeeded
    """
    message = get_share_message(level_name, level_num)
    copied = copy_to_clipboard(message)
    try:
        webbrowser.open("https://instagram.com")
        return copied
    except Exception:
        return False


# ==================== Streak Sharing Functions ====================


def open_twitter_streak_share(streak_days: int) -> bool:
    """Open X (Twitter) with pre-filled tweet for streak milestone.

    Args:
        streak_days: Number of days in the streak

    Returns:
        True if browser opened successfully
    """
    message = get_streak_share_message(streak_days)
    encoded = urllib.parse.quote(message)
    url = f"https://twitter.com/intent/tweet?text={encoded}"
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_linkedin_streak_share(streak_days: int) -> bool:
    """Open LinkedIn share page for streak milestone.

    Args:
        streak_days: Number of days in the streak (unused, kept for consistency)

    Returns:
        True if browser opened successfully
    """
    encoded_url = urllib.parse.quote(GITHUB_URL)
    url = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_instagram_streak_share(streak_days: int) -> bool:
    """Copy streak message to clipboard and open Instagram.

    Instagram doesn't have a direct share API, so we copy the message
    to clipboard and open Instagram for the user to paste.

    Args:
        streak_days: Number of days in the streak

    Returns:
        True if clipboard copy and browser open succeeded
    """
    message = get_streak_share_message(streak_days)
    copied = copy_to_clipboard(message)
    try:
        webbrowser.open("https://instagram.com")
        return copied
    except Exception:
        return False
