"""Content renderer for kubepath using Rich."""

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from kubepath.console import get_console


def render_concepts(concepts: list[dict[str, Any]], console: Console | None = None) -> None:
    """Render a list of concepts to the console.

    Args:
        concepts: List of concept dictionaries with 'title', 'content', and optional 'key_points'.
        console: Optional Rich console to use. If None, uses the global console.
    """
    if console is None:
        console = get_console()

    for i, concept in enumerate(concepts):
        render_concept(concept, i + 1, len(concepts), console)
        console.print()  # Add spacing between concepts


def render_concept(
    concept: dict[str, Any],
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render a single concept to the console.

    Args:
        concept: Concept dictionary with 'title', 'content', and optional 'key_points'.
        index: The concept number (1-based).
        total: Total number of concepts.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    title = concept.get("title", "Untitled")
    content = concept.get("content", "")
    key_points = concept.get("key_points", [])

    # Create the panel title with progress indicator
    panel_title = f"[chapter]{index}/{total}[/chapter] {title}"

    # Render content as markdown
    md_content = Markdown(content)

    # Create panel with content
    panel = Panel(
        md_content,
        title=panel_title,
        title_align="left",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    # Render key points if present
    if key_points:
        render_key_points(key_points, console)


def render_key_points(key_points: list[str], console: Console | None = None) -> None:
    """Render key points as a bullet list.

    Args:
        key_points: List of key point strings.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print("[success]Key Points:[/success]")
    for point in key_points:
        console.print(f"  [success]•[/success] {point}")


def render_chapter_header(
    chapter: dict[str, Any],
    console: Console | None = None,
) -> None:
    """Render the chapter header.

    Args:
        chapter: Chapter metadata dictionary with 'number', 'title', 'description'.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    number = chapter.get("number", "?")
    title = chapter.get("title", "Untitled")
    description = chapter.get("description", "")

    console.print()
    console.print(f"[chapter]Chapter {number}: {title}[/chapter]")
    if description:
        console.print(f"[hint]{description}[/hint]")
    console.print()


def render_progress_bar(
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render a progress bar showing concept completion.

    Args:
        index: Current concept index (1-based).
        total: Total number of concepts.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    percentage = int((index / total) * 100)

    # Create progress bar with styling
    progress_bar = ProgressBar(
        total=total,
        completed=index,
        width=16,
        complete_style="cyan",
        finished_style="bold green",
    )

    # Use Table.grid for inline layout
    table = Table.grid(padding=(0, 1))
    table.add_column()  # Label
    table.add_column()  # Progress bar
    table.add_column()  # Status text

    table.add_row(
        Text("Progress:", style="cyan"),
        progress_bar,
        Text(f"{index}/{total} ({percentage}%)", style="dim italic"),
    )

    console.print()
    console.print(table)


def render_navigation_help(
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render navigation help for interactive mode.

    Args:
        index: Current concept index (1-based).
        total: Total number of concepts.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()

    # Build navigation options
    # Use backslash to escape brackets: \[ becomes literal [
    nav_parts = []
    if index > 1:
        nav_parts.append("[info]\\[p][/info]rev")
    if index < total:
        nav_parts.append("[info]\\[n][/info]ext")
    else:
        # Last concept - show continue to practice
        nav_parts.append("[info]\\[c][/info]ontinue")
    nav_parts.append("[info]\\[?][/info] Ask AI")
    nav_parts.append("[info]\\[q][/info]uit")

    nav_text = "  ".join(nav_parts)
    console.print(nav_text)


def render_command_practice(
    practice: dict[str, Any],
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render a single command practice item.

    Args:
        practice: Practice dictionary with 'title', 'instructions', 'command_hint'.
        index: The practice number (1-based).
        total: Total number of practices.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    title = practice.get("title", "Untitled Practice")
    instructions = practice.get("instructions", "")
    command_hint = practice.get("command_hint", "")
    points = practice.get("points", 0)

    # Create panel title with progress indicator
    panel_title = f"[chapter]{index}/{total}[/chapter] {title}"
    if points > 0:
        panel_title += f"  [points]+{points} pts[/points]"

    # Build content
    content_parts = []

    # Instructions as markdown
    if instructions:
        content_parts.append(Markdown(instructions.strip()))

    # Create panel
    panel = Panel(
        "\n".join(str(p) for p in content_parts) if len(content_parts) > 1 else content_parts[0] if content_parts else "",
        title=panel_title,
        title_align="left",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)

    # Show command hint
    if command_hint:
        console.print()
        console.print("[hint]Command to run:[/hint]")
        console.print(f"  [success]{command_hint}[/success]")


def render_practice_navigation_help(
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render navigation help for practice mode.

    Args:
        index: Current practice index (1-based).
        total: Total number of practices.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print("[hint]Run the command above, then:[/hint]")

    # Build navigation options
    nav_parts = []
    if index > 1:
        nav_parts.append("[info]\\[p][/info]rev")
    nav_parts.append("[info]\\[c][/info]heck")
    nav_parts.append("[info]\\[s][/info]kip")
    nav_parts.append("[info]\\[q][/info]uit")

    nav_text = "  ".join(nav_parts)
    console.print(nav_text)


def render_validation_result(
    success: bool,
    message: str,
    points: int = 0,
    console: Console | None = None,
) -> None:
    """Render the result of a command validation.

    Args:
        success: Whether the validation passed.
        message: Message describing the result.
        points: Points earned (only shown if success).
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    if success:
        console.print(f"[success]✓ {message}[/success]")
        if points > 0:
            console.print(f"[points]+{points} points earned![/points]")
    else:
        console.print(f"[error]✗ {message}[/error]")
        console.print("[hint]Try again, press \\[?] for AI hint, or \\[s] to skip[/hint]")


def render_main_menu(
    chapters: list[int],
    active_session: dict | None,
    chapter_titles: dict[int, str],
    hands_on_mode: bool = True,
    console: Console | None = None,
) -> None:
    """Render the main menu.

    Args:
        chapters: List of available chapter numbers.
        active_session: Active session dict or None.
        chapter_titles: Map of chapter number to title.
        hands_on_mode: Whether hands-on mode is enabled.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()

    # Build menu options
    options = []

    if active_session:
        ch = active_session["chapter"]
        section = active_session["section"]
        title = chapter_titles.get(ch, f"Chapter {ch}")
        section_label = "Concepts" if section == "concepts" else "Practice"
        options.append(f"[info]\\[c][/info] Continue {title} → {section_label}")

    if chapters:
        first_chapter = chapters[0]
        first_title = chapter_titles.get(first_chapter, f"Chapter {first_chapter}")
        options.append(f"[info]\\[s][/info] Start Learning ({first_title})")

    options.append("[info]\\[b][/info] Browse Chapters")

    # Hands-on mode toggle with status
    if hands_on_mode:
        hands_on_status = "[success]ON[/success]"
        hands_on_desc = "[dim]kubectl practice enabled[/dim]"
    else:
        hands_on_status = "[warning]OFF[/warning]"
        hands_on_desc = "[dim]theory only mode[/dim]"
    options.append(f"[info]\\[h][/info] Hands-On Mode: {hands_on_status} {hands_on_desc}")

    options.append("[info]\\[e][/info] Configure K8s Environment")
    options.append("[info]\\[a][/info] Configure AI")
    options.append("[info]\\[r][/info] Reset Progress")
    options.append("[info]\\[q][/info] Quit")

    # Render in a panel
    menu_content = "\n".join(f"  {opt}" for opt in options)

    panel = Panel(
        menu_content,
        title="[chapter]Main Menu[/chapter]",
        title_align="left",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def render_continue_prompt(
    chapter: int,
    section: str,
    chapter_title: str,
    console: Console | None = None,
) -> None:
    """Render the continue session prompt.

    Args:
        chapter: Chapter number.
        section: Current section.
        chapter_title: Chapter title.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    section_labels = {
        "concepts": "Concepts",
        "practice": "Command Practice",
        "scenarios": "Debugging Scenarios",
        "quiz": "Quiz",
    }
    section_label = section_labels.get(section, section.capitalize())

    console.print()
    console.print(f"[info]You have an active session:[/info]")
    console.print(f"  Chapter {chapter}: {chapter_title}")
    console.print(f"  Section: {section_label}")
    console.print()
    console.print("[hint]Continue where you left off?[/hint]")
    console.print("  [info]\\[y][/info] Yes, continue")
    console.print("  [info]\\[n][/info] No, show menu")


def render_env_check(
    os_info: Any,
    kubectl_installed: bool,
    cluster_env: Any | None,
    console: Console | None = None,
) -> None:
    """Render environment check results.

    Args:
        os_info: OSInfo object with system details.
        kubectl_installed: Whether kubectl is installed.
        cluster_env: K8sEnvironment object or None.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print("[info]Environment Check[/info]")
    console.print()

    # OS check - always passes
    os_display = os_info.name.capitalize()
    if os_info.is_wsl:
        os_display = "Linux (WSL)"
    console.print(f"  [success]✓[/success] OS: {os_info.system} ({os_display})")

    # kubectl check
    if kubectl_installed:
        console.print("  [success]✓[/success] kubectl: Installed")
    else:
        console.print("  [error]✗[/error] kubectl: Not found")
        return

    # Cluster check
    if cluster_env and cluster_env.is_running:
        console.print(f"  [success]✓[/success] Cluster: {cluster_env.provider} running")
    elif cluster_env:
        console.print(f"  [warning]✗[/warning] Cluster: {cluster_env.provider} not responding")
    else:
        console.print("  [warning]✗[/warning] Cluster: No context configured")


def render_section_transition(
    from_section: str,
    to_section: str,
    chapter_meta: dict,
    console: Console | None = None,
) -> None:
    """Render transition between sections.

    Args:
        from_section: Section just completed.
        to_section: Section about to start.
        chapter_meta: Chapter metadata.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()

    if from_section == "concepts" and to_section == "practice":
        console.print("[success]✓ Concepts Complete![/success]")
        console.print()
        console.print("[info]Ready for Command Practice[/info]")
        console.print("[hint]You'll now practice real kubectl commands.[/hint]")
    elif from_section == "practice" and to_section == "scenarios":
        console.print("[success]✓ Practice Complete![/success]")
        console.print()
        console.print("[info]Ready for Debugging Scenarios![/info]")
        console.print("[hint]You'll deploy broken K8s resources and fix them.[/hint]")
    elif from_section == "practice":
        console.print("[success]✓ Practice Complete![/success]")
    elif from_section == "scenarios":
        console.print("[success]✓ Scenarios Complete![/success]")


def render_chapter_complete(
    chapter_meta: dict,
    total_points: int = 0,
    console: Console | None = None,
) -> None:
    """Render chapter completion screen.

    Args:
        chapter_meta: Chapter metadata.
        total_points: Total points earned.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    number = chapter_meta.get("number", "?")
    title = chapter_meta.get("title", "Untitled")

    console.print()
    console.print("[success]🎉 Chapter Complete![/success]")
    console.print(f"[chapter]Chapter {number}: {title}[/chapter]")

    if total_points > 0:
        console.print(f"[points]+{total_points} points earned![/points]")


def render_next_chapter_prompt(
    next_chapter: int,
    next_title: str,
    console: Console | None = None,
) -> None:
    """Render prompt for starting next chapter.

    Args:
        next_chapter: Next chapter number.
        next_title: Next chapter title.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print(f"[info]Next: Chapter {next_chapter} - {next_title}[/info]")
    console.print()
    console.print("  [info]\\[n][/info] Start next chapter")
    console.print("  [info]\\[m][/info] Return to menu")
    console.print("  [info]\\[q][/info] Quit")


def render_command_output(
    output: str,
    console: Console | None = None,
) -> None:
    """Render command output in a styled panel.

    Args:
        output: The command output to display.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    # Truncate very long output
    max_lines = 20
    lines = output.strip().split("\n")
    if len(lines) > max_lines:
        display_output = "\n".join(lines[:max_lines])
        display_output += f"\n... ({len(lines) - max_lines} more lines)"
    else:
        display_output = output.strip()

    if not display_output:
        display_output = "(no output)"

    panel = Panel(
        display_output,
        title="[info]Command Output[/info]",
        title_align="left",
        border_style="dim",
        padding=(0, 1),
    )
    console.print(panel)


def render_hint(
    hint_text: str,
    console: Console | None = None,
) -> None:
    """Render a hint for failed validation.

    Args:
        hint_text: The hint message to display.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print(f"[hint]💡 Hint: {hint_text}[/hint]")


def render_command_prompt(
    hint: str,
    console: Console | None = None,
) -> None:
    """Render the command input prompt with hint.

    Args:
        hint: The command hint to show.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    if hint:
        console.print(f"[hint]Hint: {hint}[/hint]")
        console.print()
    console.print("[info]Enter your command (or 's' to skip, '?' to ask AI, 'q' to quit):[/info]")


# =============================================================================
# Scenario Rendering Functions
# =============================================================================


def render_scenario(
    scenario: dict[str, Any],
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render a debugging scenario challenge.

    Args:
        scenario: Scenario dictionary with 'title', 'description', 'points'.
        index: The scenario number (1-based).
        total: Total number of scenarios.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    title = scenario.get("title", "Untitled Scenario")
    description = scenario.get("description", "")
    points = scenario.get("points", 0)

    # Create panel title with progress and points
    panel_title = f"[chapter]{index}/{total}[/chapter] 🔧 {title}"
    if points > 0:
        panel_title += f"  [points]+{points} pts[/points]"

    # Render description as markdown
    content = Markdown(description.strip()) if description else ""

    panel = Panel(
        content,
        title=panel_title,
        title_align="left",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)


def render_scenario_deployed(
    scenario: dict[str, Any],
    console: Console | None = None,
) -> None:
    """Render message that scenario has been deployed.

    Args:
        scenario: Scenario dictionary.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print("[warning]⚠️  A broken deployment has been applied to your cluster.[/warning]")
    console.print("[hint]Use kubectl to diagnose and fix the issue.[/hint]")


def render_scenario_hint(
    hint: str,
    hint_number: int,
    total_hints: int,
    penalty: int = 0,
    console: Console | None = None,
) -> None:
    """Render a scenario hint.

    Args:
        hint: The hint text.
        hint_number: Which hint this is (1-based).
        total_hints: Total number of hints available.
        penalty: Points deducted for using this hint.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print(f"[hint]💡 Hint {hint_number}/{total_hints}:[/hint]")
    console.print(f"   {hint}")
    if penalty > 0:
        console.print(f"   [warning](-{penalty} points)[/warning]")


def render_scenario_navigation_help(
    index: int,
    total: int,
    hints_used: int,
    total_hints: int,
    console: Console | None = None,
) -> None:
    """Render navigation help for scenario mode.

    Args:
        index: Current scenario index (1-based).
        total: Total number of scenarios.
        hints_used: Number of hints already used.
        total_hints: Total hints available.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()

    # Build navigation options
    nav_parts = []
    nav_parts.append("[info]\\[v][/info]erify solution")

    if hints_used < total_hints:
        nav_parts.append(f"[info]\\[h][/info]int ({hints_used}/{total_hints})")

    nav_parts.append("[info]\\[s][/info]kip")
    nav_parts.append("[info]\\[q][/info]uit")

    nav_text = "  ".join(nav_parts)
    console.print(nav_text)


def render_scenario_result(
    success: bool,
    message: str,
    points: int = 0,
    hints_used: int = 0,
    hint_penalty: int = 0,
    console: Console | None = None,
) -> None:
    """Render the result of a scenario validation.

    Args:
        success: Whether the scenario was solved.
        message: Result message.
        points: Base points for the scenario.
        hints_used: Number of hints used.
        hint_penalty: Points lost per hint.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    if success:
        console.print(f"[success]✓ {message}[/success]")
        final_points = max(0, points - (hints_used * hint_penalty))
        if final_points > 0:
            if hints_used > 0:
                console.print(
                    f"[points]+{final_points} points earned! "
                    f"(base {points} - {hints_used * hint_penalty} hint penalty)[/points]"
                )
            else:
                console.print(f"[points]+{final_points} points earned![/points]")
    else:
        console.print(f"[error]✗ {message}[/error]")
        console.print("[hint]Keep trying! Use 'h' for a hint if you're stuck.[/hint]")


# =============================================================================
# Quiz Rendering Functions
# =============================================================================


def render_quiz_header(
    passing_score: int = 70,
    total_questions: int = 0,
    console: Console | None = None,
) -> None:
    """Render the quiz header.

    Args:
        passing_score: Percentage required to pass.
        total_questions: Total number of questions.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print("[info]📝 Quiz Time![/info]")
    console.print(f"[hint]Answer {total_questions} questions. Passing score: {passing_score}%[/hint]")
    console.print()


def render_quiz_question(
    question: dict[str, Any],
    index: int,
    total: int,
    console: Console | None = None,
) -> None:
    """Render a quiz question.

    Args:
        question: Question dictionary with 'type', 'question', 'options', etc.
        index: Question number (1-based).
        total: Total number of questions.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    q_type = question.get("type", "multiple_choice")
    q_text = question.get("question", "")
    points = question.get("points", 0)

    # Question header
    panel_title = f"[chapter]Question {index}/{total}[/chapter]"
    if points > 0:
        panel_title += f"  [points]+{points} pts[/points]"

    # Build question content based on type
    if q_type == "multiple_choice":
        options = question.get("options", [])
        content_parts = [q_text, ""]
        for i, opt in enumerate(options):
            content_parts.append(f"  [{chr(65 + i)}] {opt}")
        content = "\n".join(content_parts)

    elif q_type == "true_false":
        content = f"{q_text}\n\n  [A] True\n  [B] False"

    elif q_type == "command_challenge":
        hint = question.get("hint", "")
        content = q_text
        if hint:
            content += f"\n\n[hint]Hint: {hint}[/hint]"

    elif q_type == "fill_yaml":
        template = question.get("yaml_template", "")
        content = f"{q_text}\n\n```yaml\n{template}\n```"

    else:
        content = q_text

    panel = Panel(
        Markdown(content) if q_type in ["command_challenge", "fill_yaml"] else content,
        title=panel_title,
        title_align="left",
        border_style="magenta",
        padding=(1, 2),
    )
    console.print(panel)


def render_quiz_input_prompt(
    question_type: str,
    console: Console | None = None,
) -> None:
    """Render the quiz answer input prompt.

    Args:
        question_type: Type of question.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    if question_type == "multiple_choice":
        console.print("[info]Enter your answer (A, B, C, D):[/info]")
    elif question_type == "true_false":
        console.print("[info]Enter your answer (A=True, B=False):[/info]")
    elif question_type == "command_challenge":
        console.print("[info]Enter your command:[/info]")
    elif question_type == "fill_yaml":
        console.print("[info]Enter the value to fill in the blank:[/info]")
    else:
        console.print("[info]Enter your answer:[/info]")


def render_quiz_result(
    correct: bool,
    explanation: str = "",
    points: int = 0,
    console: Console | None = None,
) -> None:
    """Render the result of a quiz answer.

    Args:
        correct: Whether the answer was correct.
        explanation: Explanation of the correct answer.
        points: Points earned if correct.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    if correct:
        console.print("[success]✓ Correct![/success]")
        if points > 0:
            console.print(f"[points]+{points} points![/points]")
    else:
        console.print("[error]✗ Incorrect[/error]")

    if explanation:
        console.print()
        console.print(f"[hint]📖 {explanation}[/hint]")


def render_quiz_summary(
    score: int,
    max_score: int,
    correct_count: int,
    total_questions: int,
    passed: bool,
    passing_score: int = 70,
    console: Console | None = None,
) -> None:
    """Render the quiz completion summary.

    Args:
        score: Points earned.
        max_score: Maximum possible points.
        correct_count: Number of correct answers.
        total_questions: Total number of questions.
        passed: Whether the quiz was passed.
        passing_score: Required percentage to pass.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    percentage = int((score / max_score) * 100) if max_score > 0 else 0

    console.print()

    if passed:
        console.print("[success]🎉 Quiz Passed![/success]")
    else:
        console.print("[warning]📚 Quiz Not Passed[/warning]")
        console.print(f"[hint]You need {passing_score}% to pass. Review and try again![/hint]")

    console.print()
    console.print(f"Score: [points]{score}/{max_score} points ({percentage}%)[/points]")
    console.print(f"Correct: {correct_count}/{total_questions} questions")


def render_quiz_navigation_help(
    console: Console | None = None,
) -> None:
    """Render navigation help during quiz.

    Args:
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()
    console.print("[hint]Press Enter to continue, or 'q' to quit[/hint]")


# =============================================================================
# Progress Bar Rendering Functions
# =============================================================================


def format_time_remaining(minutes: int) -> str:
    """Format minutes as human-readable time estimate.

    Args:
        minutes: Number of minutes.

    Returns:
        Formatted string like "~5 min", "~1.5 hours", "~3 hours".
    """
    if minutes <= 0:
        return "Complete"
    elif minutes < 60:
        return f"~{minutes} min"
    elif minutes < 120:
        hours = minutes / 60
        return f"~{hours:.1f} hours"
    else:
        hours = round(minutes / 60)
        return f"~{hours} hours"


def render_course_progress(
    completed_chapters: int,
    total_chapters: int,
    time_remaining_minutes: int,
    console: Console | None = None,
) -> None:
    """Render course-level progress bar with time estimate.

    Args:
        completed_chapters: Number of completed chapters.
        total_chapters: Total chapters in course.
        time_remaining_minutes: Estimated minutes to complete course.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    percentage = int((completed_chapters / total_chapters) * 100) if total_chapters > 0 else 0

    # Create progress bar
    progress_bar = ProgressBar(
        total=total_chapters,
        completed=completed_chapters,
        width=20,
        complete_style="cyan",
        finished_style="bold green",
    )

    # Format time
    time_str = format_time_remaining(time_remaining_minutes)

    # Use Table.grid for inline layout
    table = Table.grid(padding=(0, 1))
    table.add_column()  # Label
    table.add_column()  # Progress bar
    table.add_column()  # Status text

    table.add_row(
        Text("Course Progress:", style="cyan"),
        progress_bar,
        Text(f"{percentage}% ({completed_chapters}/{total_chapters} chapters)", style="dim"),
    )

    console.print(table)

    if time_remaining_minutes > 0:
        console.print(f"[hint]Estimated time remaining: {time_str}[/hint]")


def render_chapter_progress(
    current_section: str,
    time_remaining_minutes: int,
    console: Console | None = None,
) -> None:
    """Render chapter-level progress bar with time estimate.

    Args:
        current_section: Current section name (concepts, practice, scenarios, quiz, completed).
        time_remaining_minutes: Estimated minutes to complete chapter.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    # Map sections to completion level (0-4)
    section_order = ["concepts", "practice", "scenarios", "quiz", "completed"]
    try:
        completed = section_order.index(current_section)
    except ValueError:
        completed = 0

    total = 4  # Total sections

    percentage = int((completed / total) * 100)

    # Create progress bar
    progress_bar = ProgressBar(
        total=total,
        completed=completed,
        width=16,
        complete_style="green",
        finished_style="bold green",
    )

    # Format time
    time_str = format_time_remaining(time_remaining_minutes)

    # Get current section display name
    section_display = {
        "concepts": "Concepts",
        "practice": "Practice",
        "scenarios": "Scenarios",
        "quiz": "Quiz",
        "completed": "Complete",
    }.get(current_section, current_section.capitalize())

    # Use Table.grid for inline layout
    table = Table.grid(padding=(0, 1))
    table.add_column()  # Label
    table.add_column()  # Progress bar
    table.add_column()  # Status text

    table.add_row(
        Text("Chapter:", style="green"),
        progress_bar,
        Text(f"{percentage}% ({section_display})", style="dim"),
    )

    console.print(table)

    if time_remaining_minutes > 0 and current_section != "completed":
        console.print(f"[hint]Estimated: {time_str}[/hint]")


# ==================== Gamification Renderers ====================


def render_player_status(
    total_score: int,
    level: int,
    level_name: str,
    progress_to_next: tuple[int, int],
    streak_current: int,
    streak_longest: int,
    console: Console | None = None,
) -> None:
    """Render player gamification status panel with emojis.

    Shows level, score, progress to next level, and streak.

    Args:
        total_score: Total accumulated score.
        level: Current level number (1-12).
        level_name: Current level name.
        progress_to_next: Tuple of (points_earned_towards_next, points_needed).
        streak_current: Current streak in days.
        streak_longest: Longest streak ever.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    current_towards, needed_for_next = progress_to_next

    # Build level and streak line with emojis
    level_text = f"⭐ Level {level}: {level_name}"

    # Format streak with fire emoji
    if streak_current > 0:
        streak_text = f"🔥 {streak_current}-day streak"
    else:
        streak_text = "No streak"

    # Score line with emoji
    score_text = f"💰 Score: {total_score:,} pts"

    # Progress bar to next level
    if needed_for_next > 0:
        progress_bar = ProgressBar(
            total=needed_for_next,
            completed=current_towards,
            width=20,
            complete_style="yellow",
            finished_style="bold yellow",
        )
        progress_text = f"{current_towards}/{needed_for_next} to Level {level + 1}"
    else:
        # Max level reached
        progress_bar = ProgressBar(
            total=1,
            completed=1,
            width=20,
            complete_style="bold magenta",
            finished_style="bold magenta",
        )
        progress_text = "🏆 MAX LEVEL"

    # Build the content
    content = Table.grid(padding=(0, 2))
    content.add_column()
    content.add_column(justify="right")

    # Row 1: Level and Streak
    content.add_row(
        Text(level_text, style="bold yellow"),
        Text(streak_text, style="cyan"),
    )

    # Row 2: Score
    content.add_row(
        Text(score_text, style="dim"),
        Text(""),
    )

    # Row 3: Progress bar
    progress_table = Table.grid(padding=(0, 1))
    progress_table.add_column()
    progress_table.add_column()
    progress_table.add_row(progress_bar, Text(progress_text, style="dim"))

    content.add_row(progress_table, Text(""))

    panel = Panel(
        content,
        border_style="yellow",
        padding=(0, 1),
    )
    console.print(panel)


def render_level_up_celebration(
    new_level: int,
    level_name: str,
    total_score: int,
    console: Console | None = None,
) -> None:
    """Render level-up celebration screen with ASCII art and social sharing.

    Args:
        new_level: New level number reached.
        level_name: New level name.
        total_score: Current total score.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    from kubepath.gamification.ascii_art import LEVEL_UP_ART
    from kubepath.gamification.sharing import GITHUB_URL, HASHTAGS

    # Build the celebration content
    content = Text()

    # Header with emojis
    content.append("\n     🎉🎉🎉   LEVEL UP!   🎉🎉🎉\n", style="bold yellow")

    # ASCII Art
    content.append(LEVEL_UP_ART, style="yellow")

    # Level achievement with emojis
    content.append(f"\n     🏆 You are now a {level_name}! 🏆\n", style="bold cyan")
    content.append(f"                ⭐ Level {new_level} ⭐\n", style="yellow")

    # Separator
    content.append("\n  ─────────────────────────────────────────────────\n\n", style="dim")

    # Share prompt
    content.append("  📢 Share your achievement with friends!\n\n", style="")

    # Share message preview
    share_preview = (
        f'  "🚀 I just reached {level_name} (Level {new_level}) on Kubepath!\n'
        f'   Kubepath teaches Kubernetes interactively in your terminal.\n'
        f'   Try it: {GITHUB_URL}\n'
        f'   {HASHTAGS}"\n\n'
    )
    content.append(share_preview, style="italic dim")

    # Share options with emojis
    content.append("  [x] 🐦 Share on X (Twitter)\n", style="cyan")
    content.append("  [l] 💼 Share on LinkedIn\n", style="cyan")
    content.append("  [i] 📸 Share on Instagram (copies to clipboard)\n", style="cyan")
    content.append("  [Enter] Continue\n", style="dim")

    panel = Panel(
        content,
        title="[bold yellow]🎉 Congratulations! 🎉[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)


def render_streak_milestone(
    streak_days: int,
    console: Console | None = None,
) -> None:
    """Render streak milestone celebration with ASCII art and social sharing.

    Args:
        streak_days: Number of days in the streak (7, 14, 30, etc.).
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    from kubepath.gamification.ascii_art import STREAK_ART
    from kubepath.gamification.sharing import GITHUB_URL, STREAK_HASHTAGS

    content = Text()

    # Header with emojis
    content.append("\n     🔥🔥🔥   STREAK MILESTONE!   🔥🔥🔥\n", style="bold cyan")

    # ASCII Art
    content.append(STREAK_ART, style="cyan")

    # Streak achievement with emojis
    content.append(f"\n              🔥 {streak_days}-DAY STREAK! 🔥\n", style="bold yellow")

    # Motivational message
    content.append(f"\n  Amazing dedication! You've been learning for {streak_days} days straight!\n", style="")
    content.append("        Keep it up - consistency is the key to mastery!\n", style="dim")

    # Separator
    content.append("\n  ─────────────────────────────────────────────────\n\n", style="dim")

    # Share prompt
    content.append("  📢 Share your streak with friends!\n\n", style="")

    # Share message preview
    share_preview = (
        f'  "🔥 I\'m on a {streak_days}-day learning streak on Kubepath!\n'
        f'   Kubepath teaches Kubernetes interactively in your terminal.\n'
        f'   Join me: {GITHUB_URL}\n'
        f'   {STREAK_HASHTAGS}"\n\n'
    )
    content.append(share_preview, style="italic dim")

    # Share options with emojis
    content.append("  [x] 🐦 Share on X (Twitter)\n", style="cyan")
    content.append("  [l] 💼 Share on LinkedIn\n", style="cyan")
    content.append("  [i] 📸 Share on Instagram (copies to clipboard)\n", style="cyan")
    content.append("  [Enter] Continue\n", style="dim")

    panel = Panel(
        content,
        title="[bold cyan]🔥 Streak Milestone! 🔥[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def render_score_gained(
    points: int,
    new_total: int,
    console: Console | None = None,
) -> None:
    """Render points earned notification.

    Args:
        points: Points earned.
        new_total: New total score.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print(f"[points]+{points} points![/points] Total: {new_total:,} pts")


# ==================== Hands-On Mode Renderers ====================


def render_hands_on_choice(
    console: Console | None = None,
) -> None:
    """Render first-run prompt asking user to choose hands-on or theory-only mode.

    Args:
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    content = Text()

    content.append("How would you like to learn?\n\n", style="")

    # Option 1: Full Experience
    content.append("  [1] Full Experience ", style="bold cyan")
    content.append("(Recommended)\n", style="dim")
    content.append("      Learn concepts + hands-on practice with real kubectl\n", style="")
    content.append("      Requires: Docker, kubectl, minikube\n\n", style="dim")

    # Option 2: Theory Only
    content.append("  [2] Theory Only\n", style="bold cyan")
    content.append("      Learn concepts and take quizzes\n", style="")
    content.append("      No Kubernetes setup needed\n", style="")
    content.append("      You can enable hands-on mode later from the main menu\n", style="dim")

    panel = Panel(
        content,
        title="[bold cyan]Welcome to Kubepath![/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def render_hands_on_status(
    enabled: bool,
    console: Console | None = None,
) -> None:
    """Render current hands-on mode status for main menu.

    Args:
        enabled: Whether hands-on mode is enabled.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    if enabled:
        status = "[success]ON[/success]"
        description = "Practice kubectl commands on a real cluster"
    else:
        status = "[warning]OFF[/warning]"
        description = "Theory mode - enable to practice kubectl"

    console.print(f"[info]\\[h][/info] Hands-On Mode: {status}")
    console.print(f"      [dim]{description}[/dim]")


def render_hands_on_skip_message(
    section: str,
    console: Console | None = None,
) -> None:
    """Render message when skipping practice/scenarios in theory mode.

    Args:
        section: The section being skipped ("practice" or "scenarios").
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    section_display = "Practice" if section == "practice" else "Scenarios"

    console.print()
    console.print(f"[dim]Skipping {section_display} (Theory mode)[/dim]")
    console.print("[dim]Enable hands-on mode from main menu [h] to practice kubectl commands[/dim]")
    console.print()


def render_hands_on_toggle_menu(
    current_mode: bool,
    console: Console | None = None,
) -> None:
    """Render the hands-on mode toggle menu.

    Args:
        current_mode: Current hands-on mode setting.
        console: Optional Rich console to use.
    """
    if console is None:
        console = get_console()

    console.print()

    if current_mode:
        console.print("Hands-On Mode is currently: [success]ENABLED[/success]")
        console.print("[dim]Practice and Scenarios will require kubectl/minikube[/dim]")
    else:
        console.print("Hands-On Mode is currently: [warning]DISABLED[/warning]")
        console.print("[dim]Practice and Scenarios will be skipped[/dim]")

    console.print()
    console.print("[info]What would you like to do?[/info]")
    console.print("  [info]\\[t][/info] Toggle hands-on mode")
    console.print("  [info]\\[b][/info] Back to main menu")
