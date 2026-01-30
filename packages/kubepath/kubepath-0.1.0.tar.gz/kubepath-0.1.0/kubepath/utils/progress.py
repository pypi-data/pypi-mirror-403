"""Progress tracking for kubepath."""

import json
from pathlib import Path
from typing import Any


def get_progress_dir() -> Path:
    """Get the kubepath data directory (~/.kubepath)."""
    return Path.home() / ".kubepath"


def get_progress_file() -> Path:
    """Get the progress file path."""
    return get_progress_dir() / "progress.json"


def load_progress() -> dict[str, Any]:
    """Load progress data from file.

    Returns:
        Progress dictionary with structure:
        {
            "active_chapter": 1,
            "active_section": "concepts",
            "chapters": {
                "1": {
                    "current_concept": 0,
                    "section": "concepts",
                    "concepts_completed": false,
                    "practice_completed": false
                },
                ...
            }
        }
    """
    progress_file = get_progress_file()

    if not progress_file.exists():
        return {"chapters": {}}

    try:
        with open(progress_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"chapters": {}}


def save_progress(chapter: int, concept_index: int) -> None:
    """Save progress for a chapter.

    Args:
        chapter: Chapter number.
        concept_index: Current concept index (0-based).
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()

    if "chapters" not in progress:
        progress["chapters"] = {}

    chapter_key = str(chapter)
    if chapter_key not in progress["chapters"]:
        progress["chapters"][chapter_key] = {}

    progress["chapters"][chapter_key]["current_concept"] = concept_index

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def get_current_concept(chapter: int) -> int:
    """Get the current concept index for a chapter.

    Args:
        chapter: Chapter number.

    Returns:
        Current concept index (0-based), or 0 if no progress saved.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return 0

    if chapter_key not in progress["chapters"]:
        return 0

    return progress["chapters"][chapter_key].get("current_concept", 0)


def clear_progress(chapter: int | None = None) -> None:
    """Clear progress for a chapter or all chapters.

    Args:
        chapter: Chapter number to clear, or None to clear all.
    """
    progress_file = get_progress_file()

    if not progress_file.exists():
        return

    if chapter is None:
        # Clear all progress
        progress_file.unlink()
        return

    # Clear specific chapter
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" in progress and chapter_key in progress["chapters"]:
        del progress["chapters"][chapter_key]

    # Also clear active session if it matches
    if progress.get("active_chapter") == chapter:
        progress.pop("active_chapter", None)
        progress.pop("active_section", None)

    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def get_active_session() -> dict[str, Any] | None:
    """Get the current active learning session.

    Returns:
        Dictionary with {"chapter": int, "section": str} or None if no active session.
        Section is one of: "concepts", "practice"
    """
    progress = load_progress()

    active_chapter = progress.get("active_chapter")
    active_section = progress.get("active_section")

    if active_chapter is None:
        return None

    return {
        "chapter": active_chapter,
        "section": active_section or "concepts",
    }


def set_active_session(chapter: int, section: str) -> None:
    """Set the current active learning session.

    Args:
        chapter: Chapter number.
        section: Current section ("concepts" or "practice").
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    progress["active_chapter"] = chapter
    progress["active_section"] = section

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def clear_active_session() -> None:
    """Clear the active session (user quit to menu)."""
    progress = load_progress()
    progress.pop("active_chapter", None)
    progress.pop("active_section", None)

    progress_file = get_progress_file()
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def get_chapter_section(chapter: int) -> str:
    """Get the current section for a chapter.

    Args:
        chapter: Chapter number.

    Returns:
        Section name: "concepts", "practice", "scenarios", or "completed".
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return "concepts"

    chapter_data = progress["chapters"].get(chapter_key, {})
    return chapter_data.get("section", "concepts")


def mark_section_completed(chapter: int, section: str) -> None:
    """Mark a section as completed and advance to next section.

    Args:
        chapter: Chapter number.
        section: Section that was completed ("concepts", "practice", or "scenarios").
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        progress["chapters"] = {}

    if chapter_key not in progress["chapters"]:
        progress["chapters"][chapter_key] = {}

    if section == "concepts":
        progress["chapters"][chapter_key]["concepts_completed"] = True
        progress["chapters"][chapter_key]["section"] = "practice"
        progress["active_section"] = "practice"
    elif section == "practice":
        progress["chapters"][chapter_key]["practice_completed"] = True
        progress["chapters"][chapter_key]["section"] = "scenarios"
        progress["active_section"] = "scenarios"
    elif section == "scenarios":
        progress["chapters"][chapter_key]["scenarios_completed"] = True
        progress["chapters"][chapter_key]["section"] = "quiz"
        progress["active_section"] = "quiz"
    elif section == "quiz":
        progress["chapters"][chapter_key]["quiz_completed"] = True
        progress["chapters"][chapter_key]["section"] = "completed"
        # Clear active session since chapter is done
        progress.pop("active_chapter", None)
        progress.pop("active_section", None)

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def is_section_completed(chapter: int, section: str) -> bool:
    """Check if a section has been completed.

    Args:
        chapter: Chapter number.
        section: Section to check ("concepts", "practice", or "scenarios").

    Returns:
        True if the section is completed.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return False

    chapter_data = progress["chapters"].get(chapter_key, {})

    if section == "concepts":
        return chapter_data.get("concepts_completed", False)
    elif section == "practice":
        return chapter_data.get("practice_completed", False)
    elif section == "scenarios":
        return chapter_data.get("scenarios_completed", False)
    elif section == "quiz":
        return chapter_data.get("quiz_completed", False)

    return False


def save_scenario_state(
    chapter: int,
    current_index: int,
    completed: set[int],
    total_points: int,
    hints_used: int = 0,
    ai_hints_used: int = 0,
    command_history: list[dict] | None = None,
) -> None:
    """Save scenario progress for a chapter.

    Args:
        chapter: Chapter number.
        current_index: Current scenario index (0-based).
        completed: Set of completed scenario indices.
        total_points: Points accumulated in scenarios section.
        hints_used: Number of static hints used in current scenario.
        ai_hints_used: Number of AI hints used in current scenario.
        command_history: List of command dicts for current scenario.
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        progress["chapters"] = {}

    if chapter_key not in progress["chapters"]:
        progress["chapters"][chapter_key] = {}

    progress["chapters"][chapter_key]["scenario_state"] = {
        "current_index": current_index,
        "completed": list(completed),
        "total_points": total_points,
        "current_scenario": {
            "hints_used": hints_used,
            "ai_hints_used": ai_hints_used,
            "command_history": command_history or [],
        },
    }

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def load_scenario_state(chapter: int) -> dict[str, Any] | None:
    """Load saved scenario state for a chapter.

    Args:
        chapter: Chapter number.

    Returns:
        Dictionary with scenario state:
        - current_index: int
        - completed: list[int]
        - total_points: int
        - current_scenario: dict with hints_used, ai_hints_used, command_history
        Or None if no saved state.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return None

    chapter_data = progress["chapters"].get(chapter_key, {})
    return chapter_data.get("scenario_state")


def clear_scenario_state(chapter: int) -> None:
    """Clear scenario state when section is completed.

    Args:
        chapter: Chapter number.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return

    if chapter_key not in progress["chapters"]:
        return

    if "scenario_state" in progress["chapters"][chapter_key]:
        del progress["chapters"][chapter_key]["scenario_state"]

        progress_file = get_progress_file()
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)


# Quiz state and error bank functions


def save_quiz_state(
    chapter: int,
    current_index: int,
    answers: dict[int, dict],
    total_points: int,
    hints_used: int = 0,
) -> None:
    """Save quiz progress for a chapter.

    Args:
        chapter: Chapter number.
        current_index: Current question index (0-based).
        answers: Dict mapping question index to answer details.
        total_points: Points accumulated so far.
        hints_used: Number of AI hints used.
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        progress["chapters"] = {}

    if chapter_key not in progress["chapters"]:
        progress["chapters"][chapter_key] = {}

    # Convert int keys to strings for JSON serialization
    answers_serializable = {str(k): v for k, v in answers.items()}

    progress["chapters"][chapter_key]["quiz_state"] = {
        "current_index": current_index,
        "answers": answers_serializable,
        "total_points": total_points,
        "hints_used": hints_used,
    }

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def load_quiz_state(chapter: int) -> dict[str, Any] | None:
    """Load saved quiz state for a chapter.

    Args:
        chapter: Chapter number.

    Returns:
        Dictionary with quiz state:
        - current_index: int
        - answers: dict mapping question index to answer details
        - total_points: int
        - hints_used: int
        Or None if no saved state.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return None

    chapter_data = progress["chapters"].get(chapter_key, {})
    state = chapter_data.get("quiz_state")

    if state:
        # Convert string keys back to int
        state["answers"] = {int(k): v for k, v in state.get("answers", {}).items()}

    return state


def clear_quiz_state(chapter: int) -> None:
    """Clear quiz state when section is completed.

    Args:
        chapter: Chapter number.
    """
    progress = load_progress()
    chapter_key = str(chapter)

    if "chapters" not in progress:
        return

    if chapter_key not in progress["chapters"]:
        return

    if "quiz_state" in progress["chapters"][chapter_key]:
        del progress["chapters"][chapter_key]["quiz_state"]

        progress_file = get_progress_file()
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)


def save_to_error_bank(
    chapter: int,
    question_data: dict[str, Any],
    user_answer: str,
) -> None:
    """Save a question to the error bank (user got it wrong or skipped).

    Args:
        chapter: Source chapter number.
        question_data: Full question dictionary from chapter YAML.
        user_answer: The answer the user gave (or "skipped").
    """
    from datetime import datetime

    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()

    if "error_bank" not in progress:
        progress["error_bank"] = []

    # Check if this exact question already exists (avoid duplicates)
    question_text = question_data.get("question", "")
    for existing in progress["error_bank"]:
        if existing.get("question_data", {}).get("question") == question_text:
            # Update existing entry
            existing["user_answer"] = user_answer
            existing["added_at"] = datetime.now().isoformat()
            existing["attempt_count"] = existing.get("attempt_count", 1) + 1
            progress_file = get_progress_file()
            with open(progress_file, "w") as f:
                json.dump(progress, f, indent=2)
            return

    # Add new entry
    progress["error_bank"].append({
        "question_data": question_data,
        "source_chapter": chapter,
        "user_answer": user_answer,
        "added_at": datetime.now().isoformat(),
        "attempt_count": 1,
    })

    # Limit error bank size to 100 questions (remove oldest)
    if len(progress["error_bank"]) > 100:
        progress["error_bank"] = progress["error_bank"][-100:]

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def load_error_bank() -> list[dict[str, Any]]:
    """Load all errors from the error bank.

    Returns:
        List of error entries with question_data, source_chapter, user_answer, etc.
    """
    progress = load_progress()
    return progress.get("error_bank", [])


def get_error_bank_questions(
    count: int,
    exclude_chapter: int | None = None,
) -> list[dict[str, Any]]:
    """Get random questions from error bank for 20% mix.

    Args:
        count: Number of questions to retrieve.
        exclude_chapter: Optional chapter to exclude (current chapter).

    Returns:
        List of question_data dictionaries from error bank.
    """
    import random

    error_bank = load_error_bank()

    # Filter out questions from excluded chapter if specified
    if exclude_chapter is not None:
        error_bank = [
            e for e in error_bank
            if e.get("source_chapter") != exclude_chapter
        ]

    if not error_bank:
        return []

    # Randomly select up to count questions
    selected = random.sample(error_bank, min(count, len(error_bank)))

    # Return just the question_data for mixing into quiz
    return [e["question_data"] for e in selected]


def remove_from_error_bank(question_text: str) -> None:
    """Remove a question from error bank when user answers correctly.

    Args:
        question_text: The question text to remove.
    """
    progress = load_progress()

    if "error_bank" not in progress:
        return

    # Filter out the question
    progress["error_bank"] = [
        e for e in progress["error_bank"]
        if e.get("question_data", {}).get("question") != question_text
    ]

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


# Time estimation constants (minutes per item)
TIME_PER_CONCEPT = 3
TIME_PER_PRACTICE = 4
TIME_PER_SCENARIO = 12
TIME_PER_QUIZ_QUESTION = 1.5

# Section completion weights for chapter progress
SECTION_WEIGHTS = {
    "concepts": 0.20,
    "practice": 0.25,
    "scenarios": 0.35,
    "quiz": 0.20,
}


def get_course_progress(total_chapters: int) -> dict[str, Any]:
    """Calculate overall course progress.

    Args:
        total_chapters: Total number of chapters in the course.

    Returns:
        Dictionary with:
        - completed_chapters: Number of fully completed chapters
        - total_chapters: Total chapters in course
        - percentage: Completion percentage (0-100)
        - current_chapter: Current active chapter or None
        - current_section: Current active section or None
    """
    progress = load_progress()

    completed_chapters = 0
    chapters_data = progress.get("chapters", {})

    for chapter_key, chapter_data in chapters_data.items():
        if chapter_data.get("section") == "completed":
            completed_chapters += 1

    percentage = int((completed_chapters / total_chapters) * 100) if total_chapters > 0 else 0

    return {
        "completed_chapters": completed_chapters,
        "total_chapters": total_chapters,
        "percentage": percentage,
        "current_chapter": progress.get("active_chapter"),
        "current_section": progress.get("active_section"),
    }


def get_chapter_progress(chapter: int) -> dict[str, Any]:
    """Calculate progress within a specific chapter.

    Args:
        chapter: Chapter number.

    Returns:
        Dictionary with:
        - completed_sections: Number of completed sections (0-4)
        - total_sections: Always 4
        - current_section: Current section name
        - percentage: Weighted completion percentage
    """
    progress = load_progress()
    chapter_key = str(chapter)
    chapter_data = progress.get("chapters", {}).get(chapter_key, {})

    current_section = chapter_data.get("section", "concepts")

    # Count completed sections
    completed_sections = 0
    percentage = 0.0

    if chapter_data.get("concepts_completed", False):
        completed_sections += 1
        percentage += SECTION_WEIGHTS["concepts"]

    if chapter_data.get("practice_completed", False):
        completed_sections += 1
        percentage += SECTION_WEIGHTS["practice"]

    if chapter_data.get("scenarios_completed", False):
        completed_sections += 1
        percentage += SECTION_WEIGHTS["scenarios"]

    if chapter_data.get("quiz_completed", False):
        completed_sections += 1
        percentage += SECTION_WEIGHTS["quiz"]

    return {
        "completed_sections": completed_sections,
        "total_sections": 4,
        "current_section": current_section,
        "percentage": int(percentage * 100),
    }


def estimate_chapter_time(content_counts: dict[str, int]) -> int:
    """Estimate total minutes to complete a chapter.

    Args:
        content_counts: Dict with concepts, practices, scenarios, quiz_questions counts.

    Returns:
        Estimated minutes to complete the chapter.
    """
    concepts = content_counts.get("concepts", 0)
    practices = content_counts.get("practices", 0)
    scenarios = content_counts.get("scenarios", 0)
    quiz_questions = content_counts.get("quiz_questions", 0)

    total_minutes = (
        concepts * TIME_PER_CONCEPT +
        practices * TIME_PER_PRACTICE +
        scenarios * TIME_PER_SCENARIO +
        quiz_questions * TIME_PER_QUIZ_QUESTION
    )

    return int(total_minutes)


def estimate_course_time_remaining(
    chapters_content: dict[int, dict[str, int]],
) -> int:
    """Estimate minutes remaining to complete the entire course.

    Args:
        chapters_content: Dict mapping chapter number to content counts.

    Returns:
        Estimated minutes remaining.
    """
    progress = load_progress()
    chapters_data = progress.get("chapters", {})

    total_remaining = 0

    for chapter_num, content_counts in chapters_content.items():
        chapter_key = str(chapter_num)
        chapter_data = chapters_data.get(chapter_key, {})

        # If chapter is completed, skip it
        if chapter_data.get("section") == "completed":
            continue

        # Calculate time for remaining sections
        chapter_time = estimate_chapter_time_remaining(
            chapter_num,
            content_counts,
            chapter_data.get("section", "concepts"),
        )
        total_remaining += chapter_time

    return total_remaining


def estimate_chapter_time_remaining(
    chapter: int,
    content_counts: dict[str, int],
    current_section: str | None = None,
) -> int:
    """Estimate minutes remaining for a chapter.

    Args:
        chapter: Chapter number.
        content_counts: Content counts for this chapter.
        current_section: Current section (if None, loads from progress).

    Returns:
        Estimated minutes remaining.
    """
    if current_section is None:
        progress = load_progress()
        chapter_key = str(chapter)
        chapter_data = progress.get("chapters", {}).get(chapter_key, {})
        current_section = chapter_data.get("section", "concepts")

    concepts = content_counts.get("concepts", 0)
    practices = content_counts.get("practices", 0)
    scenarios = content_counts.get("scenarios", 0)
    quiz_questions = content_counts.get("quiz_questions", 0)

    remaining = 0

    # Add time for each remaining section
    sections_order = ["concepts", "practice", "scenarios", "quiz", "completed"]

    try:
        current_index = sections_order.index(current_section)
    except ValueError:
        current_index = 0

    # Add partial time for current section (estimate 50% remaining)
    if current_section == "concepts":
        remaining += int(concepts * TIME_PER_CONCEPT * 0.5)
    elif current_section == "practice":
        remaining += int(practices * TIME_PER_PRACTICE * 0.5)
    elif current_section == "scenarios":
        remaining += int(scenarios * TIME_PER_SCENARIO * 0.5)
    elif current_section == "quiz":
        remaining += int(quiz_questions * TIME_PER_QUIZ_QUESTION * 0.5)

    # Add full time for sections after current
    if current_index < sections_order.index("practice"):
        remaining += int(practices * TIME_PER_PRACTICE)
    if current_index < sections_order.index("scenarios"):
        remaining += int(scenarios * TIME_PER_SCENARIO)
    if current_index < sections_order.index("quiz"):
        remaining += int(quiz_questions * TIME_PER_QUIZ_QUESTION)

    return remaining


# ==================== Gamification Functions ====================


def _get_gamification_data() -> dict[str, Any]:
    """Get gamification data from progress, initializing if needed.

    Returns:
        Gamification dict with total_score, current_level, level_name, streak.
    """
    from kubepath.gamification.levels import get_level_for_score

    progress = load_progress()

    if "gamification" not in progress:
        # Initialize with defaults
        level_info = get_level_for_score(0)
        progress["gamification"] = {
            "total_score": 0,
            "current_level": level_info["level"],
            "level_name": level_info["name"],
            "streak": {
                "current": 0,
                "longest": 0,
                "last_active_date": None,
            },
        }

    return progress["gamification"]


def _save_gamification_data(gamification: dict[str, Any]) -> None:
    """Save gamification data to progress file.

    Args:
        gamification: Gamification dict to save.
    """
    progress_dir = get_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()
    progress["gamification"] = gamification

    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def get_total_score() -> int:
    """Get total score across all chapters.

    Returns:
        Total accumulated score.
    """
    gamification = _get_gamification_data()
    return gamification.get("total_score", 0)


def get_gamification_status() -> dict[str, Any]:
    """Get current gamification status for display.

    Returns:
        Dictionary with:
        - total_score: int
        - current_level: int (1-12)
        - level_name: str
        - progress_to_next: tuple (current, needed)
        - streak: dict with current, longest, last_active_date
    """
    from kubepath.gamification.levels import get_progress_to_next_level

    gamification = _get_gamification_data()
    total_score = gamification.get("total_score", 0)

    return {
        "total_score": total_score,
        "current_level": gamification.get("current_level", 1),
        "level_name": gamification.get("level_name", "Pod Seedling"),
        "progress_to_next": get_progress_to_next_level(total_score),
        "streak": gamification.get("streak", {
            "current": 0,
            "longest": 0,
            "last_active_date": None,
        }),
    }


def add_points_to_total(points: int) -> dict[str, Any] | None:
    """Add points to total score and check for level up.

    Args:
        points: Points to add.

    Returns:
        Level-up info dict if level changed (with level, name, total_score),
        None otherwise.
    """
    from kubepath.gamification.levels import check_level_up, get_level_for_score

    if points <= 0:
        return None

    gamification = _get_gamification_data()
    old_score = gamification.get("total_score", 0)
    new_score = old_score + points

    gamification["total_score"] = new_score

    # Check for level up
    level_up = check_level_up(old_score, new_score)
    if level_up:
        gamification["current_level"] = level_up["level"]
        gamification["level_name"] = level_up["name"]

    _save_gamification_data(gamification)

    if level_up:
        return {
            "level": level_up["level"],
            "name": level_up["name"],
            "total_score": new_score,
        }
    return None


def record_activity() -> dict[str, Any] | None:
    """Record user activity and update streak.

    Call this when the app starts or user completes an activity.

    Returns:
        Streak milestone info if a milestone was reached (with milestone, current, longest),
        None otherwise.
    """
    from kubepath.gamification.streaks import update_streak

    gamification = _get_gamification_data()
    streak_data = gamification.get("streak", {})

    result = update_streak(
        last_active_date=streak_data.get("last_active_date"),
        current_streak=streak_data.get("current", 0),
        longest_streak=streak_data.get("longest", 0),
    )

    gamification["streak"] = {
        "current": result["current"],
        "longest": result["longest"],
        "last_active_date": result["last_active_date"],
    }

    _save_gamification_data(gamification)

    if result.get("milestone"):
        return {
            "milestone": result["milestone"],
            "current": result["current"],
            "longest": result["longest"],
        }
    return None


def update_gamification_data(points_earned: int) -> dict[str, Any]:
    """Update gamification state after earning points.

    This is the main function to call after completing sections.
    It updates total score, checks for level up, and updates streak.

    Args:
        points_earned: Points earned from the completed section.

    Returns:
        Dictionary with:
        - level_up: Level info if leveled up, None otherwise
        - streak_milestone: Milestone info if reached, None otherwise
        - total_score: New total score
        - current_level: Current level number
        - level_name: Current level name
    """
    level_up = add_points_to_total(points_earned)
    streak_milestone = record_activity()

    status = get_gamification_status()

    return {
        "level_up": level_up,
        "streak_milestone": streak_milestone,
        "total_score": status["total_score"],
        "current_level": status["current_level"],
        "level_name": status["level_name"],
    }
