"""Chapter content loader for kubepath."""

import glob
import re
from pathlib import Path
from typing import Any

import yaml


class ChapterNotFoundError(Exception):
    """Raised when a chapter file cannot be found."""

    pass


class ChapterValidationError(Exception):
    """Raised when chapter content fails validation."""

    pass


def get_content_dir() -> Path:
    """Get the content directory path."""
    # Content is now inside the package at kubepath/data/
    return Path(__file__).parent.parent / "data"


def load_chapter(chapter_number: int) -> dict[str, Any]:
    """Load a chapter by its number.

    Args:
        chapter_number: The chapter number to load (1, 2, etc.)

    Returns:
        Dictionary containing the chapter data with 'chapter' and 'concepts' keys.

    Raises:
        ChapterNotFoundError: If no chapter file found for the given number.
        ChapterValidationError: If chapter file is missing required fields.
        yaml.YAMLError: If YAML parsing fails.
    """
    content_dir = get_content_dir()
    chapters_dir = content_dir / "chapters"

    # Look for chapter file matching the pattern
    pattern = str(chapters_dir / f"{chapter_number:02d}-*.yaml")
    matching_files = glob.glob(pattern)

    if not matching_files:
        raise ChapterNotFoundError(
            f"Chapter {chapter_number} not found. "
            f"Expected file matching: {pattern}"
        )

    # Use the first matching file
    chapter_file = Path(matching_files[0])

    # Load and parse YAML
    with open(chapter_file, "r") as f:
        data = yaml.safe_load(f)

    # Validate required fields
    _validate_chapter(data, chapter_file)

    return data


def _validate_chapter(data: dict[str, Any], filepath: Path) -> None:
    """Validate chapter data has required fields.

    Args:
        data: The parsed YAML data.
        filepath: Path to the file (for error messages).

    Raises:
        ChapterValidationError: If validation fails.
    """
    if not isinstance(data, dict):
        raise ChapterValidationError(
            f"Chapter file {filepath} must contain a YAML dictionary"
        )

    if "chapter" not in data:
        raise ChapterValidationError(
            f"Chapter file {filepath} missing required 'chapter' field"
        )

    chapter_meta = data["chapter"]
    if not isinstance(chapter_meta, dict):
        raise ChapterValidationError(
            f"Chapter file {filepath}: 'chapter' must be a dictionary"
        )

    required_chapter_fields = ["number", "title"]
    for field in required_chapter_fields:
        if field not in chapter_meta:
            raise ChapterValidationError(
                f"Chapter file {filepath}: 'chapter' missing required field '{field}'"
            )

    if "concepts" not in data:
        raise ChapterValidationError(
            f"Chapter file {filepath} missing required 'concepts' field"
        )

    concepts = data["concepts"]
    if not isinstance(concepts, list) or len(concepts) == 0:
        raise ChapterValidationError(
            f"Chapter file {filepath}: 'concepts' must be a non-empty list"
        )

    for i, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: concept {i} must be a dictionary"
            )
        if "title" not in concept:
            raise ChapterValidationError(
                f"Chapter file {filepath}: concept {i} missing required 'title' field"
            )
        if "content" not in concept:
            raise ChapterValidationError(
                f"Chapter file {filepath}: concept {i} missing required 'content' field"
            )

    # Validate optional command_practice section
    if "command_practice" in data:
        _validate_command_practice(data["command_practice"], filepath)

    # Validate optional scenarios section
    if "scenarios" in data:
        _validate_scenarios(data["scenarios"], filepath)

    # Validate optional quiz section
    if "quiz" in data:
        _validate_quiz(data["quiz"], filepath)


def _validate_command_practice(practices: Any, filepath: Path) -> None:
    """Validate command_practice section.

    Args:
        practices: The command_practice data.
        filepath: Path to the file (for error messages).

    Raises:
        ChapterValidationError: If validation fails.
    """
    if not isinstance(practices, list):
        raise ChapterValidationError(
            f"Chapter file {filepath}: 'command_practice' must be a list"
        )

    required_fields = ["id", "title", "instructions", "command_hint", "validation", "points"]

    for i, practice in enumerate(practices):
        if not isinstance(practice, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: command_practice[{i}] must be a dictionary"
            )

        for field in required_fields:
            if field not in practice:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: command_practice[{i}] missing required field '{field}'"
                )

        # Validate validation sub-structure
        validation = practice["validation"]
        if not isinstance(validation, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: command_practice[{i}].validation must be a dictionary"
            )

        if "type" not in validation:
            raise ChapterValidationError(
                f"Chapter file {filepath}: command_practice[{i}].validation missing required field 'type'"
            )

        valid_types = ["command_output", "resource_exists", "resource_state", "resource_state_stable"]
        if validation["type"] not in valid_types:
            raise ChapterValidationError(
                f"Chapter file {filepath}: command_practice[{i}].validation.type must be one of {valid_types}"
            )


def _validate_scenarios(scenarios: Any, filepath: Path) -> None:
    """Validate scenarios section.

    Args:
        scenarios: The scenarios data.
        filepath: Path to the file (for error messages).

    Raises:
        ChapterValidationError: If validation fails.
    """
    if not isinstance(scenarios, list):
        raise ChapterValidationError(
            f"Chapter file {filepath}: 'scenarios' must be a list"
        )

    required_fields = ["id", "title", "description", "manifest", "hints", "solution_validation", "points"]

    for i, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: scenarios[{i}] must be a dictionary"
            )

        for field in required_fields:
            if field not in scenario:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: scenarios[{i}] missing required field '{field}'"
                )

        # Validate hints is a list
        if not isinstance(scenario["hints"], list) or len(scenario["hints"]) == 0:
            raise ChapterValidationError(
                f"Chapter file {filepath}: scenarios[{i}].hints must be a non-empty list"
            )

        # Validate solution_validation sub-structure
        validation = scenario["solution_validation"]
        if not isinstance(validation, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: scenarios[{i}].solution_validation must be a dictionary"
            )

        if "type" not in validation:
            raise ChapterValidationError(
                f"Chapter file {filepath}: scenarios[{i}].solution_validation missing required field 'type'"
            )


def _validate_quiz(quiz: Any, filepath: Path) -> None:
    """Validate quiz section.

    Args:
        quiz: The quiz data.
        filepath: Path to the file (for error messages).

    Raises:
        ChapterValidationError: If validation fails.
    """
    if not isinstance(quiz, dict):
        raise ChapterValidationError(
            f"Chapter file {filepath}: 'quiz' must be a dictionary"
        )

    if "questions" not in quiz:
        raise ChapterValidationError(
            f"Chapter file {filepath}: quiz missing required field 'questions'"
        )

    questions = quiz["questions"]
    if not isinstance(questions, list) or len(questions) == 0:
        raise ChapterValidationError(
            f"Chapter file {filepath}: quiz.questions must be a non-empty list"
        )

    valid_types = ["multiple_choice", "command_challenge", "fill_yaml", "true_false"]

    for i, question in enumerate(questions):
        if not isinstance(question, dict):
            raise ChapterValidationError(
                f"Chapter file {filepath}: quiz.questions[{i}] must be a dictionary"
            )

        required_fields = ["type", "question", "points"]
        for field in required_fields:
            if field not in question:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] missing required field '{field}'"
                )

        q_type = question["type"]
        if q_type not in valid_types:
            raise ChapterValidationError(
                f"Chapter file {filepath}: quiz.questions[{i}].type must be one of {valid_types}"
            )

        # Type-specific validation
        if q_type == "multiple_choice":
            if "options" not in question or not isinstance(question["options"], list):
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] (multiple_choice) must have 'options' list"
                )
            if "correct" not in question:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] (multiple_choice) must have 'correct' field"
                )

        elif q_type == "command_challenge":
            if "expected_contains" not in question:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] (command_challenge) must have 'expected_contains'"
                )

        elif q_type == "fill_yaml":
            if "yaml_template" not in question or "expected" not in question:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] (fill_yaml) must have 'yaml_template' and 'expected'"
                )

        elif q_type == "true_false":
            if "correct" not in question:
                raise ChapterValidationError(
                    f"Chapter file {filepath}: quiz.questions[{i}] (true_false) must have 'correct' field"
                )


def get_available_chapters() -> list[int]:
    """Scan content/chapters/ directory for available chapter files.

    Returns:
        Sorted list of chapter numbers found.
    """
    content_dir = get_content_dir()
    chapters_dir = content_dir / "chapters"

    if not chapters_dir.exists():
        return []

    chapters = []
    for file in chapters_dir.glob("*.yaml"):
        match = re.match(r"(\d+)-", file.name)
        if match:
            chapters.append(int(match.group(1)))

    return sorted(chapters)


def load_modules() -> list[dict[str, Any]]:
    """Load module definitions from content/modules.yaml.

    Returns:
        List of module dictionaries with keys:
        - id: Module number
        - name: Module name (CKAD domain)
        - ckad_weight: Percentage weight in CKAD exam
        - description: Module description
        - chapters: List of chapter numbers in this module
    """
    content_dir = get_content_dir()
    modules_file = content_dir / "modules.yaml"

    if not modules_file.exists():
        return []

    with open(modules_file, "r") as f:
        data = yaml.safe_load(f)

    return data.get("modules", [])


def get_chapter_titles() -> dict[int, str]:
    """Get titles for all available chapters.

    Returns:
        Dictionary mapping chapter number to title.
    """
    titles = {}
    for chapter_num in get_available_chapters():
        try:
            chapter_data = load_chapter(chapter_num)
            titles[chapter_num] = chapter_data["chapter"]["title"]
        except (ChapterNotFoundError, ChapterValidationError):
            titles[chapter_num] = f"Chapter {chapter_num}"
    return titles


def get_chapter_content_counts(chapter_number: int) -> dict[str, int]:
    """Get content item counts for a chapter.

    Args:
        chapter_number: The chapter number to get counts for.

    Returns:
        Dictionary with content counts:
        - concepts: Number of concept items
        - practices: Number of practice items
        - scenarios: Number of scenario items
        - quiz_questions: Number of quiz questions
    """
    try:
        chapter_data = load_chapter(chapter_number)
    except (ChapterNotFoundError, ChapterValidationError):
        return {
            "concepts": 0,
            "practices": 0,
            "scenarios": 0,
            "quiz_questions": 0,
        }

    concepts = chapter_data.get("concepts", [])
    practices = chapter_data.get("command_practice", [])
    scenarios = chapter_data.get("scenarios", [])
    quiz = chapter_data.get("quiz", {})
    quiz_questions = quiz.get("questions", [])

    return {
        "concepts": len(concepts),
        "practices": len(practices),
        "scenarios": len(scenarios),
        "quiz_questions": len(quiz_questions),
    }


# Cache for all chapter content counts
_chapter_content_cache: dict[int, dict[str, int]] | None = None


def get_all_chapter_content_counts() -> dict[int, dict[str, int]]:
    """Get content counts for all chapters (cached for performance).

    Returns:
        Dictionary mapping chapter number to content counts.
    """
    global _chapter_content_cache

    if _chapter_content_cache is not None:
        return _chapter_content_cache

    _chapter_content_cache = {}
    for chapter_num in get_available_chapters():
        _chapter_content_cache[chapter_num] = get_chapter_content_counts(chapter_num)

    return _chapter_content_cache
