"""CLI application for kubepath."""

import typer

from kubepath.console import get_console, print_banner, clear_screen
from kubepath.content import (
    load_chapter,
    get_available_chapters,
    load_modules,
    get_chapter_titles,
    get_chapter_content_counts,
    get_all_chapter_content_counts,
    ChapterNotFoundError,
    ChapterValidationError,
    render_concept,
    render_chapter_header,
    render_navigation_help,
    render_progress_bar,
    render_command_practice,
    render_practice_navigation_help,
    render_validation_result,
    render_main_menu,
    render_continue_prompt,
    render_env_check,
    render_section_transition,
    render_chapter_complete,
    render_next_chapter_prompt,
    render_command_output,
    render_hint,
    render_command_prompt,
    render_scenario,
    render_scenario_deployed,
    render_scenario_hint,
    render_scenario_navigation_help,
    render_scenario_result,
    render_quiz_header,
    render_quiz_question,
    render_quiz_result,
    render_quiz_summary,
    render_quiz_navigation_help,
    render_course_progress,
    render_chapter_progress,
    # Gamification
    render_player_status,
    render_level_up_celebration,
    render_streak_milestone,
    # Hands-on mode
    render_hands_on_choice,
    render_hands_on_skip_message,
    render_hands_on_toggle_menu,
)
from kubepath.utils import (
    get_current_concept,
    save_progress,
    clear_progress,
    get_active_session,
    set_active_session,
    clear_active_session,
    get_chapter_section,
    mark_section_completed,
    save_scenario_state,
    load_scenario_state,
    clear_scenario_state,
    save_quiz_state,
    load_quiz_state,
    clear_quiz_state,
    get_course_progress,
    get_chapter_progress,
    estimate_course_time_remaining,
    estimate_chapter_time_remaining,
    # Gamification
    get_gamification_status,
    update_gamification_data,
    record_activity,
    # Auto-update
    check_and_update,
    should_check_for_updates,
)
from kubepath.k8s import (
    detect_os,
    check_kubectl_installed,
    detect_k8s_environment,
    show_setup_guide,
    show_kubectl_install,
    show_minikube_required_warning,
    validate_from_spec,
    execute_command,
    validate_output,
)
from kubepath.scenarios import create_scenario_engine
from kubepath.quiz import QuizEngine
from kubepath.config import (
    get_config_status,
    set_gemini_api_key,
    clear_gemini_api_key,
    is_gemini_configured,
    get_hands_on_mode,
    set_hands_on_mode,
    is_hands_on_configured,
)
from kubepath.ai import GeminiClient, GEMINI_AVAILABLE


def has_yaml_content(manifest: str) -> bool:
    """Check if manifest has actual YAML content (not just comments).

    Args:
        manifest: YAML manifest string.

    Returns:
        True if manifest has real content to deploy.
    """
    if not manifest:
        return False
    # Filter out empty lines and comments
    lines = [line.strip() for line in manifest.split("\n")]
    content_lines = [line for line in lines if line and not line.startswith("#")]
    return len(content_lines) > 0


def get_next_chapter(current: int) -> int | None:
    """Get the next chapter number after current."""
    chapters = get_available_chapters()
    try:
        idx = chapters.index(current)
        if idx < len(chapters) - 1:
            return chapters[idx + 1]
    except ValueError:
        pass
    return None


def get_previous_chapter(current: int) -> int | None:
    """Get the previous chapter number before current."""
    chapters = get_available_chapters()
    try:
        idx = chapters.index(current)
        if idx > 0:
            return chapters[idx - 1]
    except ValueError:
        pass
    return None


def get_chapter_titles() -> dict[int, str]:
    """Get a map of chapter numbers to titles."""
    titles = {}
    for num in get_available_chapters():
        try:
            chapter_data = load_chapter(num)
            titles[num] = chapter_data["chapter"]["title"]
        except (ChapterNotFoundError, ChapterValidationError):
            titles[num] = f"Chapter {num}"
    return titles


app = typer.Typer(
    name="kubepath",
    help="Interactive CLI application for learning Kubernetes",
    add_completion=False,
    invoke_without_command=True,
)


def get_user_input() -> str:
    """Get single character input from user."""
    try:
        user_input = input("> ").strip().lower()
        return user_input[0] if user_input else ""
    except (EOFError, KeyboardInterrupt):
        return "q"


def get_command_input() -> str:
    """Get command input from user with $ prompt."""
    try:
        return input("$ ").strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _handle_share_prompt(level: int, level_name: str, console) -> None:
    """Handle social sharing prompt after level-up celebration.

    Args:
        level: Level number reached.
        level_name: Name of the level.
        console: Rich console instance.
    """
    from kubepath.gamification.sharing import (
        open_twitter_share,
        open_linkedin_share,
        open_instagram_share,
    )

    while True:
        user_input = get_user_input()
        if user_input == "x":
            if open_twitter_share(level_name, level):
                console.print("[success]Opening X (Twitter)...[/success]")
            else:
                console.print("[error]Could not open browser[/error]")
            break
        elif user_input == "l":
            if open_linkedin_share(level_name, level):
                console.print("[success]Opening LinkedIn...[/success]")
            else:
                console.print("[error]Could not open browser[/error]")
            break
        elif user_input == "i":
            if open_instagram_share(level_name, level):
                console.print("[success]Message copied! Opening Instagram...[/success]")
            else:
                console.print("[warning]Opening Instagram (clipboard may not have copied)[/warning]")
            break
        elif user_input == "" or user_input == "\n":
            # Enter pressed, continue without sharing
            break


def _handle_streak_share_prompt(streak_days: int, console) -> None:
    """Handle social sharing prompt after streak milestone celebration.

    Args:
        streak_days: Number of days in the streak.
        console: Rich console instance.
    """
    from kubepath.gamification.sharing import (
        open_twitter_streak_share,
        open_linkedin_streak_share,
        open_instagram_streak_share,
    )

    while True:
        user_input = get_user_input()
        if user_input == "x":
            if open_twitter_streak_share(streak_days):
                console.print("[success]Opening X (Twitter)...[/success]")
            else:
                console.print("[error]Could not open browser[/error]")
            break
        elif user_input == "l":
            if open_linkedin_streak_share(streak_days):
                console.print("[success]Opening LinkedIn...[/success]")
            else:
                console.print("[error]Could not open browser[/error]")
            break
        elif user_input == "i":
            if open_instagram_streak_share(streak_days):
                console.print("[success]Message copied! Opening Instagram...[/success]")
            else:
                console.print("[warning]Opening Instagram (clipboard may not have copied)[/warning]")
            break
        elif user_input == "" or user_input == "\n":
            # Enter pressed, continue without sharing
            break


def _perform_silent_update() -> None:
    """Perform silent update check and display brief message if updated."""
    console = get_console()

    try:
        result = check_and_update()

        if result.updated:
            console.print(
                f"[success]Updated to v{result.remote_version}[/success]",
                highlight=False,
            )
        elif result.update_available and not result.updated:
            # Update available but failed
            console.print(
                f"[warning]Update available (v{result.remote_version}) "
                f"but failed: {result.error}[/warning]",
                highlight=False,
            )
        # If no update or check failed, remain silent

    except Exception:
        # Silently ignore any unexpected errors during update
        # The app should still work even if update check fails
        pass


def show_main_menu() -> tuple[str, int | None]:
    """Display main menu and get user selection.

    Returns:
        Tuple of (action, chapter_num):
        - ("start", chapter) - Start a chapter
        - ("continue", chapter) - Continue active session
        - ("browse", None) - Browse chapters
        - ("doctor", None) - Check environment
        - ("quit", None) - Exit
    """
    console = get_console()

    while True:
        clear_screen()
        print_banner()

        chapters = get_available_chapters()
        session = get_active_session()
        chapter_titles = get_chapter_titles()

        # Show course progress bar
        total_chapters = len(chapters)
        if total_chapters > 0:
            course_progress = get_course_progress(total_chapters)
            all_content = get_all_chapter_content_counts()
            time_remaining = estimate_course_time_remaining(all_content)
            render_course_progress(
                course_progress["completed_chapters"],
                course_progress["total_chapters"],
                time_remaining,
                console,
            )
            console.print()

        # Show player gamification status
        gamification = get_gamification_status()
        render_player_status(
            total_score=gamification["total_score"],
            level=gamification["current_level"],
            level_name=gamification["level_name"],
            progress_to_next=gamification["progress_to_next"],
            streak_current=gamification["streak"].get("current", 0),
            streak_longest=gamification["streak"].get("longest", 0),
            console=console,
        )
        console.print()

        # Get hands-on mode status
        hands_on_mode = get_hands_on_mode()

        render_main_menu(chapters, session, chapter_titles, hands_on_mode, console)
        console.print()

        user_input = get_user_input()

        if user_input == "c" and session:
            return ("continue", session["chapter"])
        elif user_input == "s" and chapters:
            return ("start", chapters[0])
        elif user_input == "b":
            return ("browse", None)
        elif user_input == "h":
            return ("configure_hands_on", None)
        elif user_input == "e":
            return ("doctor", None)
        elif user_input == "a":
            return ("configure_ai", None)
        elif user_input == "r":
            return ("reset", None)
        elif user_input == "q":
            return ("quit", None)
        # Invalid input - redraw menu


def prompt_continue_session(session: dict) -> bool:
    """Prompt user to continue active session.

    Returns:
        True if user wants to continue, False for menu.
    """
    console = get_console()
    clear_screen()
    print_banner()

    chapter_titles = get_chapter_titles()
    title = chapter_titles.get(session["chapter"], f"Chapter {session['chapter']}")

    render_continue_prompt(session["chapter"], session["section"], title, console)
    console.print()

    user_input = get_user_input()
    return user_input == "y"


def check_k8s_environment_interactive() -> bool:
    """Check K8s environment with inline retry option.

    Returns:
        True if environment is ready, False if user chose to skip.
    """
    console = get_console()

    while True:
        clear_screen()
        print_banner()

        os_info = detect_os()
        kubectl_installed = check_kubectl_installed()
        cluster_env = detect_k8s_environment() if kubectl_installed else None

        render_env_check(os_info, kubectl_installed, cluster_env, console)

        # Check if all good
        if kubectl_installed and cluster_env and cluster_env.is_running:
            # Check if it's minikube
            if cluster_env.provider == "minikube":
                console.print()
                console.print("[success]Environment ready![/success]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
                return True
            else:
                # Non-minikube provider detected - warn the user
                show_minikube_required_warning(cluster_env.provider)
                console.print()
                console.print("[hint]\\[Enter] Continue anyway  \\[m] Setup minikube  \\[s] Skip[/hint]")

                try:
                    choice = input("> ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    return False

                if choice == "s":
                    return False
                elif choice == "m":
                    # Show minikube setup instructions
                    clear_screen()
                    print_banner()
                    show_setup_guide(os_info)
                    console.print("[hint]Press Enter to retry after starting minikube...[/hint]")
                    input()
                    continue
                else:
                    # Continue with non-minikube cluster
                    console.print()
                    console.print("[warning]Proceeding with non-minikube cluster.[/warning]")
                    input("\nPress Enter to continue...")
                    return True

        # Show install instructions
        console.print()
        if not kubectl_installed:
            show_kubectl_install(os_info)
        elif not cluster_env or not cluster_env.is_running:
            if cluster_env:
                # Cluster configured but not running
                if cluster_env.provider == "minikube":
                    console.print("[hint]Start your minikube cluster:[/hint]")
                    console.print("  [success]$ minikube start[/success]")
                else:
                    # Non-minikube cluster not running - show minikube setup guide
                    console.print(f"[hint]Your {cluster_env.provider} cluster is not running.[/hint]")
                    console.print()
                    show_setup_guide(os_info)
            else:
                show_setup_guide(os_info)

        console.print()
        console.print("[hint]\\[Enter] Retry  \\[s] Skip practice[/hint]")

        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        if choice == "s":
            return False
        # Otherwise retry


def interactive_concepts(
    chapter_num: int,
    concepts: list[dict],
    chapter_meta: dict,
    start_from_last: bool = False,
) -> str:
    """Run interactive concept navigation.

    Args:
        chapter_num: The chapter number.
        concepts: List of concept dictionaries.
        chapter_meta: Chapter metadata dictionary.
        start_from_last: If True, start from the last concept.

    Returns:
        - "completed": User completed all concepts
        - "quit": User quit
        - "previous": User wants to go to previous chapter
    """
    console = get_console()
    total = len(concepts)

    # Load saved progress or start from last if requested
    if start_from_last:
        current_index = total - 1
    else:
        current_index = get_current_concept(chapter_num)

    # Ensure index is valid
    if current_index >= total:
        current_index = 0

    # Set active session
    set_active_session(chapter_num, "concepts")

    # Get content counts for time estimation
    content_counts = get_chapter_content_counts(chapter_num)

    while True:
        # Clear screen for clean display
        clear_screen()
        print_banner()
        render_chapter_header(chapter_meta, console)

        # Show chapter progress bar
        chapter_progress = get_chapter_progress(chapter_num)
        time_remaining = estimate_chapter_time_remaining(
            chapter_num, content_counts, chapter_progress["current_section"]
        )
        render_chapter_progress(
            chapter_progress["current_section"],
            time_remaining,
            console,
        )

        # Render current concept (1-based for display)
        render_concept(concepts[current_index], current_index + 1, total, console)

        # Render progress bar
        render_progress_bar(current_index + 1, total, console)

        # Render navigation help
        render_navigation_help(current_index + 1, total, console)

        # Get user input
        user_input = get_user_input()

        if user_input == "n":
            if current_index < total - 1:
                current_index += 1
                save_progress(chapter_num, current_index)
            else:
                # Completed all concepts
                return "completed"

        elif user_input == "c":
            # Continue to practice (from last concept)
            if current_index == total - 1:
                return "completed"

        elif user_input == "p":
            if current_index > 0:
                current_index -= 1
                save_progress(chapter_num, current_index)
            else:
                # At first concept - offer to go to previous chapter
                prev_chapter = get_previous_chapter(chapter_num)
                if prev_chapter:
                    return "previous"

        elif user_input == "q":
            save_progress(chapter_num, current_index)
            return "quit"

        elif user_input == "r":
            # Reset progress (hidden command)
            current_index = 0
            save_progress(chapter_num, current_index)

        elif user_input == "?":
            # Ask AI a question about the current concept
            if not GEMINI_AVAILABLE:
                console.print()
                console.print("[warning]AI requires google-generativeai package.[/warning]")
                console.print("[hint]Install with: pip install google-generativeai[/hint]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
                continue

            if not is_gemini_configured():
                if not prompt_gemini_setup():
                    continue

            console.print()
            console.print("[info]Ask your question about this concept:[/info]")
            question = input("> ").strip()
            if not question:
                continue

            console.print()
            console.print("[hint]Thinking...[/hint]")

            client = GeminiClient()
            concept = concepts[current_index]
            answer = client.answer_question(
                context_title=concept.get("title", ""),
                context_content=concept.get("content", ""),
                learner_question=question,
                section_type="concept",
            )

            console.print()
            if answer:
                console.print("[info]🤖 AI Answer:[/info]")
                console.print()
                console.print(f"   {answer}")
            else:
                console.print("[warning]Could not get an answer. Please try again.[/warning]")

            console.print()
            console.print("[hint]Press Enter to continue...[/hint]")
            input()


def get_practice_hint(practice: dict, result) -> str:
    """Get a hint for failed practice validation.

    Args:
        practice: The practice dictionary.
        result: The validation result.

    Returns:
        A hint string to help the user.
    """
    # Check for explicit hint in practice definition
    if "hint" in practice:
        return practice["hint"]

    # Generate basic hints based on validation result
    validation = practice.get("validation", {})
    expected = validation.get("expected_contains", "")
    output = result.output.lower() if result.output else ""

    if "connection refused" in output:
        return "Your Kubernetes cluster may not be running. Try starting it first."

    if "not found" in output and "command" in output:
        return "The command was not found. Make sure kubectl is installed correctly."

    if "unable to connect" in output:
        return "Cannot connect to the cluster. Make sure your cluster is running."

    if expected:
        return f"The output should contain '{expected}'. Check that you ran the correct command."

    # Placeholder for future LLM-based hints
    # TODO: Integrate Gemini API for intelligent hints
    return "Check the command and try again."


def interactive_practice(
    chapter_num: int,
    practices: list[dict],
    chapter_meta: dict,
) -> str:
    """Run interactive command practice.

    Users type actual kubectl commands, which are executed against the cluster.

    Args:
        chapter_num: The chapter number.
        practices: List of practice dictionaries.
        chapter_meta: Chapter metadata dictionary.

    Returns:
        - "completed": User completed all practices
        - "quit": User quit
    """
    console = get_console()
    total = len(practices)
    current_index = 0
    completed = set()
    total_points = 0
    command_history = []  # Track all commands for AI context

    # Set active session
    set_active_session(chapter_num, "practice")

    # Get content counts for time estimation
    content_counts = get_chapter_content_counts(chapter_num)

    while True:
        clear_screen()
        print_banner()
        render_chapter_header(chapter_meta, console)

        # Show chapter progress bar
        chapter_progress = get_chapter_progress(chapter_num)
        time_remaining = estimate_chapter_time_remaining(
            chapter_num, content_counts, chapter_progress["current_section"]
        )
        render_chapter_progress(
            chapter_progress["current_section"],
            time_remaining,
            console,
        )

        console.print("[info]Command Practice[/info]\n")

        practice = practices[current_index]
        render_command_practice(practice, current_index + 1, total, console)

        # Show completion status
        console.print()
        status_parts = []
        if current_index in completed:
            status_parts.append("[success]✓ Completed[/success]")
        status_parts.append(f"[hint]{len(completed)}/{total} done[/hint]")
        if total_points > 0:
            status_parts.append(f"[points]{total_points} pts[/points]")
        console.print("  ".join(status_parts))

        # Show command prompt instead of navigation help
        hint = practice.get("command_hint", "")
        render_command_prompt(hint, console)

        # Get command input from user
        user_command = get_command_input()

        # Handle special inputs
        if user_command.lower() in ("q", "quit", "exit"):
            console.print(f"\n[info]Progress: {len(completed)}/{total} practices completed.[/info]")
            return "quit"

        if user_command.lower() in ("s", "skip", "n", "next"):
            if current_index < total - 1:
                current_index += 1
            else:
                # Last practice - allow completing section even with skips
                if len(completed) < total:
                    console.print(f"\n[hint]Skipping remaining practice(s). No points awarded for skipped items.[/hint]")
                    input("\nPress Enter...")
                return "completed"
            continue

        if user_command.lower() in ("p", "prev", "previous"):
            if current_index > 0:
                current_index -= 1
            continue

        if not user_command:
            continue  # Empty input, redraw

        if user_command == "?":
            # Ask AI a question about the current practice
            if not GEMINI_AVAILABLE:
                console.print()
                console.print("[warning]AI requires google-generativeai package.[/warning]")
                console.print("[hint]Install with: pip install google-generativeai[/hint]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
                continue

            if not is_gemini_configured():
                if not prompt_gemini_setup():
                    continue

            console.print()
            console.print("[info]Ask your question about this practice:[/info]")
            question = input("> ").strip()
            if not question:
                continue

            console.print()
            console.print("[hint]Thinking...[/hint]")

            # Build context including command history
            context = practice.get("instructions", "")

            # Include the command hint so AI knows what command is being taught
            cmd_hint = practice.get("command_hint", "")
            if cmd_hint:
                context += f"\n\nCommand being taught: {cmd_hint}"

            if command_history:
                context += "\n\nCommand history (most recent last):"
                # Show last 5 commands to keep context manageable
                for entry in command_history[-5:]:
                    status = "✓" if entry["success"] else "✗"
                    context += f"\n{status} $ {entry['command']}"
                    if entry["output"]:
                        context += f"\n   Output: {entry['output'][:200]}"

            client = GeminiClient()
            answer = client.answer_question(
                context_title=practice.get("title", ""),
                context_content=context,
                learner_question=question,
                section_type="practice",
            )

            console.print()
            if answer:
                console.print("[info]🤖 AI Answer:[/info]")
                console.print()
                console.print(f"   {answer}")
            else:
                console.print("[warning]Could not get an answer. Please try again.[/warning]")

            console.print()
            console.print("[hint]Press Enter to continue...[/hint]")
            input()
            continue

        # Already completed - just show message
        if current_index in completed:
            console.print("\n[hint]Already completed! Type 's' or 'n' to continue.[/hint]")
            input("Press Enter...")
            continue

        # Execute the user's command
        result = execute_command(user_command)
        command_history.append({
            "command": user_command,
            "output": result.output[:300] if result.output else "",
            "success": result.success,
        })

        # Display command output
        console.print()
        render_command_output(result.output, console)

        # Validate the output
        validation_spec = practice.get("validation", {})
        expected_contains = validation_spec.get("expected_contains", "")

        if result.success and validate_output(result.output, expected_contains):
            # Success!
            points = practice.get("points", 0)
            console.print()
            console.print("[success]✓ Correct! Output matches expected criteria.[/success]")
            if points > 0:
                console.print(f"[points]+{points} points earned![/points]")

            completed.add(current_index)
            total_points += points

            if current_index < total - 1:
                console.print("\n[hint]Press Enter to continue...[/hint]")
                input()
                current_index += 1
            elif len(completed) == total:
                console.print("\n[success]All practices completed![/success]")
                console.print(f"[points]Total: {total_points} points[/points]")

                # Update gamification
                if total_points > 0:
                    gamification_result = update_gamification_data(total_points)
                    if gamification_result.get("level_up"):
                        input("\nPress Enter to continue...")
                        clear_screen()
                        print_banner()
                        level_up = gamification_result["level_up"]
                        render_level_up_celebration(
                            level_up["level"],
                            level_up["name"],
                            level_up["total_score"],
                            console,
                        )
                        _handle_share_prompt(level_up["level"], level_up["name"], console)

                input("\nPress Enter to continue...")
                return "completed"
            else:
                input("\nPress Enter...")
        else:
            # Failed - show error and hint
            console.print()
            if not result.success:
                console.print(f"[error]✗ {result.message}[/error]")
            elif expected_contains:
                console.print(f"[error]✗ Output doesn't contain '{expected_contains}'[/error]")
            else:
                console.print("[error]✗ Command output doesn't match expected criteria.[/error]")

            # Show hint
            hint_text = get_practice_hint(practice, result)
            render_hint(hint_text, console)

            console.print()
            console.print("[hint]Press Enter to try again...[/hint]")
            input()


def prompt_gemini_setup() -> bool:
    """Prompt user to set up Gemini API key.

    Returns:
        True if key was configured successfully.
    """
    console = get_console()

    console.print()
    console.print("[info]🤖 AI Assistant Setup[/info]")
    console.print()
    console.print("[success]✓ 100% FREE - No credit card required![/success]")
    console.print("[hint]kubepath uses only the free tier of Google's Gemini API.[/hint]")
    console.print()
    console.print("[info]How to get your free API key (takes ~1 minute):[/info]")
    console.print()
    console.print("  1. Go to: [link]https://aistudio.google.com/app/apikey[/link]")
    console.print("  2. Sign in with your Google account")
    console.print("  3. Click 'Create API Key' → Select any project")
    console.print("  4. Copy the generated key")
    console.print()
    console.print("[info]Free quota (more than enough for learning!):[/info]")
    console.print("  • 50-250 requests per day")
    console.print("  • 15 requests per minute")
    console.print("  • No billing or payment setup needed")
    console.print()
    console.print("[hint]Paste your API key here (or 'q' to skip):[/hint]")

    try:
        api_key = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return False

    if api_key.lower() == "q" or not api_key:
        console.print("[hint]Skipped. You can set up later with 'kubepath config --set-key'[/hint]")
        return False

    # Validate the key
    console.print()
    console.print("[hint]Validating API key...[/hint]")

    client = GeminiClient(api_key=api_key)
    success, message = client.validate_api_key()

    if success:
        set_gemini_api_key(api_key)
        console.print("[success]✓ API key saved successfully![/success]")
        console.print("[hint]AI hints are now available during scenarios.[/hint]")
        input("\nPress Enter to continue...")
        return True
    else:
        console.print(f"[error]✗ {message}[/error]")
        console.print("[hint]Please check your API key and try again.[/hint]")
        input("\nPress Enter to continue...")
        return False


def interactive_scenarios(
    chapter_num: int,
    scenarios: list[dict],
    chapter_meta: dict,
) -> str:
    """Run interactive debugging scenarios.

    Users investigate and fix broken K8s deployments.

    Args:
        chapter_num: The chapter number.
        scenarios: List of scenario dictionaries.
        chapter_meta: Chapter metadata dictionary.

    Returns:
        - "completed": All scenarios completed or skipped
        - "quit": User quit
    """
    console = get_console()
    total = len(scenarios)
    current_index = 0
    completed = set()
    total_points = 0

    # Load saved state if resuming
    saved_state = load_scenario_state(chapter_num)
    resumed_scenario_state = None
    if saved_state:
        current_index = saved_state.get("current_index", 0)
        completed = set(saved_state.get("completed", []))
        total_points = saved_state.get("total_points", 0)
        resumed_scenario_state = saved_state.get("current_scenario")

    # Create scenario engine
    engine = create_scenario_engine(enable_ai=True)

    # Set active session
    set_active_session(chapter_num, "scenarios")

    # Get content counts for time estimation
    content_counts = get_chapter_content_counts(chapter_num)

    while current_index < total:
        clear_screen()
        print_banner()
        render_chapter_header(chapter_meta, console)

        # Show chapter progress bar
        chapter_progress = get_chapter_progress(chapter_num)
        time_remaining = estimate_chapter_time_remaining(
            chapter_num, content_counts, chapter_progress["current_section"]
        )
        render_chapter_progress(
            chapter_progress["current_section"],
            time_remaining,
            console,
        )

        console.print("[info]Debugging Scenarios[/info]\n")

        scenario = scenarios[current_index]

        # Check if already completed
        if current_index in completed:
            render_scenario(scenario, current_index + 1, total, console)
            console.print("\n[success]✓ Already completed[/success]")
            console.print()
            console.print("[hint]\\[n]ext  \\[q]uit[/hint]")
            nav = get_user_input()
            if nav == "n":
                current_index += 1
            elif nav == "q":
                engine.cleanup()
                return "quit"
            continue

        # Start scenario - show description
        render_scenario(scenario, current_index + 1, total, console)

        # Check if there's a manifest to deploy (not just comments)
        manifest = scenario.get("manifest", "")
        if has_yaml_content(manifest):
            console.print()
            console.print("[warning]Deploying broken resources to your cluster...[/warning]")

            deploy_result = engine.start_scenario(scenario)

            if not deploy_result.success:
                console.print(f"[error]Deployment failed: {deploy_result.message}[/error]")
                console.print("[hint]Press Enter to skip this scenario...[/hint]")
                input()
                current_index += 1
                continue

            render_scenario_deployed(scenario, console)
        else:
            # No manifest - start without deployment
            engine.start_scenario(scenario)

        # Restore state if resuming this scenario
        if resumed_scenario_state:
            engine.restore_hint_state(
                resumed_scenario_state.get("hints_used", 0),
                resumed_scenario_state.get("ai_hints_used", 0),
            )
            engine.restore_command_history(
                resumed_scenario_state.get("command_history", [])
            )
            console.print("[info]Resuming scenario - your previous progress is restored.[/info]")
            resumed_scenario_state = None  # Only restore once

        # Main scenario loop
        while True:
            # Show navigation
            hints_used = engine.current_context.hint_manager.hints_used if engine.current_context else 0
            total_hints = len(scenario.get("hints", []))

            console.print()
            render_scenario_navigation_help(
                current_index + 1, total, hints_used, total_hints, console
            )

            # Check if AI is available and show option
            if GEMINI_AVAILABLE and is_gemini_configured():
                console.print("[info]\\[a][/info]i hint")

            # Show command prompt
            console.print()
            console.print("[hint]Enter kubectl command to investigate, or use navigation keys:[/hint]")
            user_input = get_command_input()

            # Handle navigation keys
            if user_input.lower() in ("q", "quit"):
                # Save state before quitting
                save_scenario_state(
                    chapter=chapter_num,
                    current_index=current_index,
                    completed=completed,
                    total_points=total_points,
                    hints_used=engine.current_context.hint_manager.hints_used if engine.current_context else 0,
                    ai_hints_used=engine.current_context.hint_manager.ai_hints_used if engine.current_context else 0,
                    command_history=engine.get_command_history_for_persistence(),
                )
                engine.cleanup()
                return "quit"

            if user_input.lower() in ("s", "skip"):
                engine.skip_scenario()
                # Save state after skipping (no current_scenario)
                save_scenario_state(
                    chapter=chapter_num,
                    current_index=current_index + 1,  # Move to next
                    completed=completed,
                    total_points=total_points,
                )
                current_index += 1
                break

            if user_input.lower() in ("v", "verify"):
                result = engine.validate_solution()
                if result.success:
                    # Success!
                    points = engine.calculate_score()
                    render_scenario_result(
                        success=True,
                        message="You fixed it!",
                        points=scenario.get("points", 0),
                        hints_used=hints_used,
                        hint_penalty=scenario.get("hint_penalty", 5),
                        console=console,
                    )
                    completed.add(current_index)
                    total_points += points
                    engine.cleanup()

                    # Save state after completing scenario (no current_scenario)
                    save_scenario_state(
                        chapter=chapter_num,
                        current_index=current_index + 1,  # Move to next
                        completed=completed,
                        total_points=total_points,
                    )

                    console.print("\n[hint]Press Enter to continue...[/hint]")
                    input()
                    current_index += 1
                    break
                else:
                    render_scenario_result(
                        success=False,
                        message=result.message or "Not fixed yet. Keep investigating!",
                        console=console,
                    )
                continue

            if user_input.lower() in ("h", "hint"):
                hint = engine.get_hint()
                if hint:
                    render_scenario_hint(
                        hint["text"],
                        hint["number"],
                        hint["total"],
                        hint["penalty"],
                        console,
                    )
                    # Save state after using hint
                    save_scenario_state(
                        chapter=chapter_num,
                        current_index=current_index,
                        completed=completed,
                        total_points=total_points,
                        hints_used=engine.current_context.hint_manager.hints_used if engine.current_context else 0,
                        ai_hints_used=engine.current_context.hint_manager.ai_hints_used if engine.current_context else 0,
                        command_history=engine.get_command_history_for_persistence(),
                    )
                else:
                    console.print("[warning]No more hints available![/warning]")
                continue

            if user_input.lower() in ("a", "ai"):
                # AI hint
                if not GEMINI_AVAILABLE:
                    console.print("[warning]AI hints require google-generativeai package.[/warning]")
                    console.print("[hint]Install: pip install google-generativeai[/hint]")
                    continue

                if not is_gemini_configured():
                    # Prompt for API key setup
                    prompt_gemini_setup()
                    continue

                console.print("[hint]Getting AI hint...[/hint]")
                ai_hint = engine.get_ai_hint()
                if ai_hint:
                    console.print()
                    console.print(f"[info]🤖 AI Hint:[/info] {ai_hint.hint_text}")
                    if ai_hint.suggested_commands:
                        console.print()
                        console.print("[hint]Try these commands:[/hint]")
                        for cmd in ai_hint.suggested_commands[:3]:
                            console.print(f"  [success]$ {cmd}[/success]")
                    # Save state after using AI hint
                    save_scenario_state(
                        chapter=chapter_num,
                        current_index=current_index,
                        completed=completed,
                        total_points=total_points,
                        hints_used=engine.current_context.hint_manager.hints_used if engine.current_context else 0,
                        ai_hints_used=engine.current_context.hint_manager.ai_hints_used if engine.current_context else 0,
                        command_history=engine.get_command_history_for_persistence(),
                    )
                else:
                    console.print("[warning]Could not get AI hint. Try again later.[/warning]")
                continue

            # Execute as kubectl command
            if user_input:
                result = engine.execute_learner_command(user_input)
                render_command_output(result.output, console)
                if not result.success:
                    console.print(f"[error]{result.message}[/error]")

                # Save state after each command
                save_scenario_state(
                    chapter=chapter_num,
                    current_index=current_index,
                    completed=completed,
                    total_points=total_points,
                    hints_used=engine.current_context.hint_manager.hints_used if engine.current_context else 0,
                    ai_hints_used=engine.current_context.hint_manager.ai_hints_used if engine.current_context else 0,
                    command_history=engine.get_command_history_for_persistence(),
                )

    # All scenarios done
    mark_section_completed(chapter_num, "scenarios")
    clear_scenario_state(chapter_num)  # Clean up saved scenario state

    console.print()
    console.print(f"[success]All scenarios completed![/success]")
    if total_points > 0:
        console.print(f"[points]Total: {total_points} points[/points]")

        # Update gamification
        gamification_result = update_gamification_data(total_points)
        if gamification_result.get("level_up"):
            input("\nPress Enter to continue...")
            clear_screen()
            print_banner()
            level_up = gamification_result["level_up"]
            render_level_up_celebration(
                level_up["level"],
                level_up["name"],
                level_up["total_score"],
                console,
            )
            _handle_share_prompt(level_up["level"], level_up["name"], console)

    input("\nPress Enter to continue...")

    return "completed"


def interactive_quiz(
    chapter_num: int,
    quiz_data: dict,
    chapter_meta: dict,
) -> str:
    """Run interactive quiz with unlimited retries and AI help.

    Args:
        chapter_num: The chapter number.
        quiz_data: Quiz dictionary from chapter YAML.
        chapter_meta: Chapter metadata dictionary.

    Returns:
        - "completed": User completed the quiz
        - "quit": User quit
    """
    console = get_console()

    # Create quiz engine
    gemini = GeminiClient() if GEMINI_AVAILABLE and is_gemini_configured() else None
    engine = QuizEngine(chapter_num, quiz_data, gemini_client=gemini)

    # Load saved state if resuming
    saved_state = load_quiz_state(chapter_num)
    if saved_state:
        engine.restore_state(saved_state)
        console.print("[info]Resuming quiz from where you left off.[/info]")
        input("\nPress Enter to continue...")

    # Prepare questions (80% current + 20% error bank)
    engine.prepare_questions(error_bank_percent=20)

    # Set active session
    set_active_session(chapter_num, "quiz")

    # Get content counts for time estimation
    content_counts = get_chapter_content_counts(chapter_num)

    # Quiz header
    total_questions = len(engine.questions)
    passing_score = engine.passing_score

    while not engine.is_complete():
        clear_screen()
        print_banner()
        render_chapter_header(chapter_meta, console)

        # Show chapter progress bar
        chapter_progress = get_chapter_progress(chapter_num)
        time_remaining = estimate_chapter_time_remaining(
            chapter_num, content_counts, chapter_progress["current_section"]
        )
        render_chapter_progress(
            chapter_progress["current_section"],
            time_remaining,
            console,
        )

        # Show quiz header
        render_quiz_header(passing_score, total_questions, console)

        # Get current question
        question = engine.get_current_question()
        if not question:
            break

        # Render question
        render_quiz_question(
            question,
            engine.current_index + 1,
            total_questions,
            console,
        )

        # Show status
        console.print()
        status_parts = [
            f"[hint]Score: {engine.total_points} pts[/hint]",
        ]
        if engine.hints_used > 0:
            status_parts.append(f"[warning]AI Hints: {engine.hints_used} (-{engine.hints_used * engine.ai_hint_penalty} pts)[/warning]")
        console.print("  ".join(status_parts))

        # Navigation help
        render_quiz_navigation_help(console)

        # Get input
        q_type = question.get("type", "multiple_choice")
        if q_type in ("multiple_choice", "true_false"):
            console.print("[info]Enter your answer (A, B, C, D):[/info]")
        elif q_type == "command_challenge":
            console.print("[info]Enter your command:[/info]")
        elif q_type == "fill_yaml":
            console.print("[info]Enter the value to fill in:[/info]")

        answer = input("> ").strip()

        # Handle special inputs
        if answer.lower() in ("q", "quit", "exit"):
            # Save state before quitting
            state = engine.get_state_for_persistence()
            save_quiz_state(
                chapter_num,
                state["current_index"],
                state["answers"],
                state["total_points"],
                state["hints_used"],
            )
            console.print(f"\n[info]Quiz progress saved. Resume anytime.[/info]")
            return "quit"

        if answer.lower() in ("s", "skip"):
            # Skip question - 0 points, add to error bank
            engine.skip_question()
            console.print("\n[hint]Question skipped (0 points). Added to review list.[/hint]")
            input("\nPress Enter to continue...")
            continue

        if answer == "?":
            # AI hint
            if not GEMINI_AVAILABLE:
                console.print()
                console.print("[warning]AI hints require google-generativeai package.[/warning]")
                console.print("[hint]Install: pip install google-generativeai[/hint]")
                input("\nPress Enter to continue...")
                continue

            if not is_gemini_configured():
                if not prompt_gemini_setup():
                    continue
                # Recreate gemini client after setup
                engine.gemini = GeminiClient()

            console.print()
            console.print("[hint]Getting AI hint...[/hint]")
            hint = engine.get_ai_hint(question)
            if hint:
                console.print()
                console.print(f"[info]🤖 AI Hint (-{engine.ai_hint_penalty} pts):[/info]")
                console.print()
                console.print(f"   {hint}")
            else:
                console.print("[warning]Could not get AI hint. Try again later.[/warning]")

            input("\nPress Enter to continue...")
            continue

        if not answer:
            continue  # Empty input, redraw

        # Check answer
        result = engine.check_answer(answer)
        console.print()
        render_quiz_result(
            result.correct,
            result.explanation,
            result.points_earned,
            console,
        )

        if not result.correct:
            # Wrong answer - can retry unlimited times
            # Record wrong answer to error bank (first wrong attempt only)
            if engine.current_index not in engine.answers:
                engine.record_wrong_answer(answer)

            console.print()
            console.print("[hint]Try again, press \\[?] for AI hint, or \\[s] to skip[/hint]")
            input("\nPress Enter to try again...")
        else:
            # Correct - move to next question
            input("\nPress Enter to continue...")
            engine.advance()

        # Save progress after each action
        state = engine.get_state_for_persistence()
        save_quiz_state(
            chapter_num,
            state["current_index"],
            state["answers"],
            state["total_points"],
            state["hints_used"],
        )

    # Quiz complete
    clear_screen()
    print_banner()
    render_chapter_header(chapter_meta, console)

    summary = engine.get_summary()
    render_quiz_summary(
        score=summary["score"],
        max_score=summary["max_score"],
        correct_count=summary["correct"],
        total_questions=summary["total"],
        passed=summary["passed"],
        passing_score=passing_score,
        console=console,
    )

    # Show additional stats
    console.print()
    if summary["hints_used"] > 0:
        console.print(f"[hint]AI Hints used: {summary['hints_used']} (-{summary['hint_penalty_total']} pts)[/hint]")
    if summary["error_bank_questions"] > 0:
        console.print(f"[hint]Review questions included: {summary['error_bank_questions']}[/hint]")

    # Update gamification
    if summary["score"] > 0:
        gamification_result = update_gamification_data(summary["score"])
        if gamification_result.get("level_up"):
            input("\nPress Enter to continue...")
            clear_screen()
            print_banner()
            level_up = gamification_result["level_up"]
            render_level_up_celebration(
                level_up["level"],
                level_up["name"],
                level_up["total_score"],
                console,
            )
            _handle_share_prompt(level_up["level"], level_up["name"], console)

    # Clear quiz state
    clear_quiz_state(chapter_num)

    input("\nPress Enter to continue...")
    return "completed"


def run_chapter(chapter_num: int, start_section: str | None = None):
    """Run full chapter flow: concepts → practice → scenarios → quiz.

    Args:
        chapter_num: Chapter number to run.
        start_section: Where to start ("concepts" or "practice").
    """
    console = get_console()

    try:
        chapter_data = load_chapter(chapter_num)
    except ChapterNotFoundError as e:
        clear_screen()
        print_banner()
        console.print(f"[error]Error: {e}[/error]")
        input("\nPress Enter...")
        return
    except ChapterValidationError as e:
        clear_screen()
        print_banner()
        console.print(f"[error]Invalid chapter: {e}[/error]")
        input("\nPress Enter...")
        return

    # Determine starting section - check active session first
    if not start_section:
        # Check active session (tracks where user actually is, e.g., mid-quiz)
        session = get_active_session()
        if session and session.get("chapter") == chapter_num:
            start_section = session.get("section")
        else:
            start_section = get_chapter_section(chapter_num)
    section = start_section
    start_from_last = False
    chapter_meta = chapter_data["chapter"]
    env_check_passed = False  # Track if environment check has already passed

    while True:
        if section == "concepts":
            result = interactive_concepts(
                chapter_num=chapter_num,
                concepts=chapter_data["concepts"],
                chapter_meta=chapter_meta,
                start_from_last=start_from_last,
            )

            if result == "quit":
                return
            elif result == "previous":
                prev_chapter = get_previous_chapter(chapter_num)
                if prev_chapter:
                    chapter_num = prev_chapter
                    chapter_data = load_chapter(chapter_num)
                    chapter_meta = chapter_data["chapter"]
                    start_from_last = True
                    section = "concepts"
                    continue
            elif result == "completed":
                # Transition to practice - first check environment
                clear_screen()
                print_banner()
                render_section_transition("concepts", "practice", chapter_meta, console)
                console.print()

                # Check K8s environment before proceeding to practice
                practices = chapter_data.get("command_practice", [])
                if practices:
                    # Only check environment if there are practices
                    if not check_k8s_environment_interactive():
                        # User chose to skip practice - go to scenarios (which will route to quiz if skipped)
                        section = "scenarios"
                        continue
                    env_check_passed = True  # Mark that env check passed

                # Mark concepts completed ONLY after user commits to proceeding
                mark_section_completed(chapter_num, "concepts")
                section = "practice"

        elif section == "practice":
            practices = chapter_data.get("command_practice", [])

            if not practices:
                # No practice, go to scenarios
                section = "scenarios"
                continue

            # Check if hands-on mode is disabled
            if not get_hands_on_mode():
                render_hands_on_skip_message("practice", console)
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
                mark_section_completed(chapter_num, "practice")
                section = "scenarios"
                continue

            # Check K8s environment (for direct `practice` command, skip if already checked)
            if not env_check_passed:
                if not check_k8s_environment_interactive():
                    # User skipped practice - go to scenarios
                    section = "scenarios"
                    continue
                env_check_passed = True

            result = interactive_practice(
                chapter_num=chapter_num,
                practices=practices,
                chapter_meta=chapter_meta,
            )

            if result == "quit":
                return
            elif result == "completed":
                mark_section_completed(chapter_num, "practice")
                section = "scenarios"

        elif section == "scenarios":
            scenarios = chapter_data.get("scenarios", [])

            if not scenarios:
                # No scenarios, go to quiz
                section = "quiz"
                continue

            # Check if hands-on mode is disabled
            if not get_hands_on_mode():
                clear_screen()
                print_banner()
                render_hands_on_skip_message("scenarios", console)
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
                mark_section_completed(chapter_num, "scenarios")
                section = "quiz"
                continue

            # Transition to scenarios
            clear_screen()
            print_banner()
            render_section_transition("practice", "scenarios", chapter_meta, console)
            console.print()

            # Check K8s environment before scenarios
            if not check_k8s_environment_interactive():
                # User skipped scenarios - go to quiz
                section = "quiz"
                continue

            result = interactive_scenarios(
                chapter_num=chapter_num,
                scenarios=scenarios,
                chapter_meta=chapter_meta,
            )

            if result == "quit":
                return
            elif result == "completed":
                mark_section_completed(chapter_num, "scenarios")
                section = "quiz"

        elif section == "quiz":
            quiz_data = chapter_data.get("quiz", {})

            if not quiz_data or not quiz_data.get("questions"):
                # No quiz, go directly to completed
                mark_section_completed(chapter_num, "quiz")
                section = "completed"
                continue

            # Transition to quiz
            clear_screen()
            print_banner()
            render_section_transition("scenarios", "quiz", chapter_meta, console)
            console.print()
            console.print("[hint]Press Enter to start the quiz...[/hint]")
            input()

            result = interactive_quiz(
                chapter_num=chapter_num,
                quiz_data=quiz_data,
                chapter_meta=chapter_meta,
            )

            if result == "quit":
                return
            elif result == "completed":
                mark_section_completed(chapter_num, "quiz")
                section = "completed"

        elif section == "completed":
            # Show chapter completion
            clear_screen()
            print_banner()
            render_chapter_complete(chapter_meta, console=console)

            # Check for next chapter
            next_chapter = get_next_chapter(chapter_num)
            if next_chapter:
                try:
                    next_data = load_chapter(next_chapter)
                    next_title = next_data["chapter"]["title"]
                except (ChapterNotFoundError, ChapterValidationError):
                    next_title = f"Chapter {next_chapter}"

                render_next_chapter_prompt(next_chapter, next_title, console)
                console.print()

                user_input = get_user_input()

                if user_input == "n":
                    chapter_num = next_chapter
                    chapter_data = load_chapter(chapter_num)
                    chapter_meta = chapter_data["chapter"]
                    section = "concepts"
                    start_from_last = False
                    clear_active_session()
                    continue
                elif user_input == "m":
                    clear_active_session()
                    return  # Return to menu
                else:
                    clear_active_session()
                    return  # Quit
            else:
                # All chapters complete
                console.print()
                console.print("[success]🎉 Congratulations![/success]")
                console.print("[success]You've completed all available chapters![/success]")
                console.print()
                console.print("[hint]Press Enter to return to menu...[/hint]")
                input()
                clear_active_session()
                return


def interactive_reset():
    """Interactive reset progress flow."""
    console = get_console()

    clear_screen()
    print_banner()

    chapters = get_available_chapters()
    chapter_titles = get_chapter_titles()

    console.print()
    console.print("[chapter]Reset Progress[/chapter]")
    console.print()

    # Build options
    console.print("  [info]\\[a][/info] Reset ALL progress (start fresh)")
    for ch in chapters:
        title = chapter_titles.get(ch, f"Chapter {ch}")
        console.print(f"  [info]\\[{ch}][/info] Reset Chapter {ch}: {title}")
    console.print("  [info]\\[q][/info] Cancel")
    console.print()

    user_input = get_user_input()

    if user_input == "q":
        return

    if user_input == "a":
        # Confirm reset all
        console.print()
        console.print("[warning]This will reset ALL course progress.[/warning]")
        console.print("[hint]Type 'yes' to confirm, or press Enter to cancel:[/hint]")
        confirm = input("> ").strip().lower()
        if confirm == "yes":
            clear_progress(None)
            console.print()
            console.print("[success]All course progress has been reset.[/success]")
            console.print()
            console.print("[hint]Press Enter to continue...[/hint]")
            input()
        else:
            console.print("[info]Reset cancelled.[/info]")
            console.print()
            console.print("[hint]Press Enter to continue...[/hint]")
            input()
        return

    # Try to parse as chapter number
    try:
        chapter_num = int(user_input)
        if chapter_num in chapters:
            title = chapter_titles.get(chapter_num, f"Chapter {chapter_num}")
            console.print()
            console.print(f"[warning]This will reset progress for Chapter {chapter_num}: {title}[/warning]")
            console.print("[hint]Type 'yes' to confirm, or press Enter to cancel:[/hint]")
            confirm = input("> ").strip().lower()
            if confirm == "yes":
                clear_progress(chapter_num)
                console.print()
                console.print(f"[success]Progress reset for Chapter {chapter_num}.[/success]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
            else:
                console.print("[info]Reset cancelled.[/info]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
    except ValueError:
        pass  # Invalid input, just return to menu


def interactive_configure_ai():
    """Interactive AI configuration flow."""
    console = get_console()

    clear_screen()
    print_banner()

    console.print()
    console.print("[chapter]Configure AI Assistant[/chapter]")
    console.print()

    # Show current status
    if is_gemini_configured():
        console.print("[success]Status: AI is configured ✓[/success]")
        console.print()
        console.print("  [info]\\[c][/info] Change API key")
        console.print("  [info]\\[r][/info] Remove API key")
        console.print("  [info]\\[q][/info] Back to menu")
    else:
        console.print("[warning]Status: AI is not configured[/warning]")
        console.print()
        console.print("  [info]\\[s][/info] Set up API key")
        console.print("  [info]\\[q][/info] Back to menu")

    console.print()
    user_input = get_user_input()

    if user_input == "q":
        return

    if is_gemini_configured():
        if user_input == "c":
            # Change API key
            console.print()
            prompt_gemini_setup()
        elif user_input == "r":
            # Remove API key
            console.print()
            console.print("[warning]This will remove your saved API key.[/warning]")
            console.print("[hint]Type 'yes' to confirm, or press Enter to cancel:[/hint]")
            confirm = input("> ").strip().lower()
            if confirm == "yes":
                clear_gemini_api_key()
                console.print()
                console.print("[success]API key removed.[/success]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
            else:
                console.print("[info]Cancelled.[/info]")
                console.print()
                console.print("[hint]Press Enter to continue...[/hint]")
                input()
    else:
        if user_input == "s":
            # Set up API key
            console.print()
            prompt_gemini_setup()


def interactive_configure_hands_on():
    """Interactive hands-on mode configuration flow."""
    console = get_console()

    clear_screen()
    print_banner()

    console.print()
    console.print("[chapter]Configure Hands-On Mode[/chapter]")
    console.print()

    current_mode = get_hands_on_mode()
    render_hands_on_toggle_menu(current_mode, console)

    console.print()
    user_input = get_user_input()

    if user_input == "t":
        # Toggle hands-on mode
        new_mode = not current_mode
        set_hands_on_mode(new_mode)

        console.print()
        if new_mode:
            console.print("[success]Hands-On Mode ENABLED![/success]")
            console.print("[dim]You'll now be able to practice kubectl commands.[/dim]")
            console.print("[dim]Make sure you have Docker, kubectl, and minikube set up.[/dim]")
        else:
            console.print("[warning]Hands-On Mode DISABLED[/warning]")
            console.print("[dim]You'll learn theory and take quizzes only.[/dim]")
            console.print("[dim]Practice and Scenario sections will be skipped.[/dim]")

        console.print()
        console.print("[hint]Press Enter to continue...[/hint]")
        input()
    # 'b' or any other key returns to menu


def prompt_hands_on_mode_choice():
    """First-run prompt for hands-on mode selection.

    Shows welcome screen asking user to choose between Full Experience
    (requires K8s setup) or Theory Only mode.
    """
    console = get_console()

    clear_screen()
    print_banner()

    render_hands_on_choice(console)

    console.print()
    console.print("[hint]Enter your choice [1/2]:[/hint]")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            # Default to theory mode if interrupted
            set_hands_on_mode(False)
            return

        if user_input == "1":
            set_hands_on_mode(True)
            console.print()
            console.print("[success]Full Experience mode enabled![/success]")
            console.print("[dim]Make sure you have Docker, kubectl, and minikube set up.[/dim]")
            console.print("[dim]You can check your setup from the main menu [e].[/dim]")
            break
        elif user_input == "2":
            set_hands_on_mode(False)
            console.print()
            console.print("[info]Theory Only mode enabled.[/info]")
            console.print("[dim]You can enable hands-on mode later from the main menu [h].[/dim]")
            break
        else:
            console.print("[warning]Please enter 1 or 2[/warning]")

    console.print()
    console.print("[hint]Press Enter to continue...[/hint]")
    input()


def browse_chapters():
    """Browse and select chapters grouped by CKAD modules."""
    console = get_console()

    while True:
        clear_screen()
        print_banner()

        chapters = get_available_chapters()
        modules = load_modules()
        chapter_titles = get_chapter_titles()

        if not chapters:
            console.print("[warning]No chapters found.[/warning]")
            input("\nPress Enter...")
            return

        console.print("[info]Browse Chapters by CKAD Module[/info]\n")

        # Group chapters by module
        for module in modules:
            module_name = module.get("name", "Unknown")
            ckad_weight = module.get("ckad_weight", 0)
            module_chapters = module.get("chapters", [])

            # Calculate module completion
            completed_count = 0
            for ch_num in module_chapters:
                if ch_num in chapters:
                    section = get_chapter_section(ch_num)
                    if section == "completed":
                        completed_count += 1

            total_in_module = len([c for c in module_chapters if c in chapters])

            # Module header with CKAD percentage
            if ckad_weight > 0:
                console.print(f"[chapter]{module_name}[/chapter] [hint]({ckad_weight}% of CKAD)[/hint]")
            else:
                console.print(f"[chapter]{module_name}[/chapter] [hint](Foundation)[/hint]")

            if total_in_module > 0:
                console.print(f"  [hint]{completed_count}/{total_in_module} completed[/hint]")

            # List chapters in this module
            for ch_num in module_chapters:
                if ch_num not in chapters:
                    continue

                title = chapter_titles.get(ch_num, f"Chapter {ch_num}")
                section = get_chapter_section(ch_num)

                # Progress indicator
                if section == "completed":
                    status = "[success]✓[/success]"
                elif section in ("practice", "scenarios"):
                    status = "[hint]→[/hint]"
                elif get_current_concept(ch_num) > 0:
                    status = "[hint]○[/hint]"
                else:
                    status = " "

                console.print(f"    {status} [info]\\[{ch_num}][/info] {title}")

            console.print()

        console.print("[hint]Enter chapter number (or 'q' to go back):[/hint]")

        try:
            user_input = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if user_input == "q" or user_input == "":
            return

        try:
            selected = int(user_input)
            if selected in chapters:
                run_chapter(selected)
                return
            console.print(f"[warning]Chapter {selected} not found.[/warning]")
            input("Press Enter...")
        except ValueError:
            console.print("[warning]Enter a valid chapter number.[/warning]")
            input("Press Enter...")


def run_doctor():
    """Run environment check."""
    console = get_console()
    clear_screen()
    print_banner()

    console.print("[info]Environment Check[/info]\n")

    os_info = detect_os()
    os_display = os_info.name.capitalize()
    if os_info.is_wsl:
        os_display = "Linux (WSL)"
    console.print(f"  [success]OS:[/success] {os_info.system} ({os_display})")

    if check_kubectl_installed():
        console.print("  [success]kubectl:[/success] Installed")
    else:
        console.print("  [warning]kubectl:[/warning] Not found")
        show_kubectl_install(os_info)
        input("\nPress Enter...")
        return

    env = detect_k8s_environment()
    if env:
        console.print(f"  [success]Context:[/success] {env.context}")
        console.print(f"  [success]Provider:[/success] {env.provider}")

        # Check if it's minikube
        if env.provider != "minikube":
            console.print(f"  [warning]Recommended:[/warning] minikube")

        if env.is_running:
            console.print("  [success]Cluster:[/success] Running")
            if env.provider == "minikube":
                console.print("\n[success]Your environment is ready for kubepath![/success]")
            else:
                console.print("\n[warning]kubepath is designed for minikube.[/warning]")
                console.print("[hint]Consider switching to minikube for the best experience.[/hint]")
        else:
            console.print("  [warning]Cluster:[/warning] Not responding")
            if env.provider == "minikube":
                console.print("\n[hint]Try: minikube start[/hint]")
            else:
                console.print("\n[hint]Consider using minikube instead.[/hint]")
                console.print("[hint]Install: https://minikube.sigs.k8s.io/docs/start/[/hint]")
    else:
        console.print("  [warning]Context:[/warning] Not configured")
        show_setup_guide(os_info)

    input("\nPress Enter...")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Interactive CLI for learning Kubernetes.

    Run without arguments to see the main menu.
    """
    if ctx.invoked_subcommand is not None:
        return  # Subcommand specified, let it run

    # Auto-update check (silent, non-blocking)
    if should_check_for_updates():
        _perform_silent_update()

    # First-run: prompt for hands-on mode choice
    if not is_hands_on_configured():
        prompt_hands_on_mode_choice()

    # Record activity for streak tracking
    console = get_console()
    streak_milestone = record_activity()
    if streak_milestone:
        clear_screen()
        print_banner()
        render_streak_milestone(streak_milestone["milestone"], console)
        _handle_streak_share_prompt(streak_milestone["milestone"], console)

    # Check for active session
    session = get_active_session()
    if session:
        if prompt_continue_session(session):
            run_chapter(session["chapter"], session["section"])
            # After returning, show menu
            while True:
                action, chapter = show_main_menu()
                if action == "quit":
                    return
                elif action in ("start", "continue"):
                    run_chapter(chapter)
                elif action == "browse":
                    browse_chapters()
                elif action == "configure_hands_on":
                    interactive_configure_hands_on()
                elif action == "doctor":
                    run_doctor()
                elif action == "configure_ai":
                    interactive_configure_ai()
                elif action == "reset":
                    interactive_reset()
            return

    # No active session - show main menu
    while True:
        action, chapter = show_main_menu()
        if action == "quit":
            return
        elif action in ("start", "continue"):
            run_chapter(chapter)
        elif action == "browse":
            browse_chapters()
        elif action == "configure_hands_on":
            interactive_configure_hands_on()
        elif action == "doctor":
            run_doctor()
        elif action == "configure_ai":
            interactive_configure_ai()
        elif action == "reset":
            interactive_reset()


# Keep existing commands for power users
@app.command()
def start(
    chapter: int = typer.Argument(..., help="Chapter number to start"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset progress"),
):
    """Start learning a specific chapter (power user command)."""
    if reset:
        clear_progress(chapter)
        run_chapter(chapter, "concepts")  # Explicit fresh start
    else:
        # Resume from saved progress if available
        run_chapter(chapter)  # Let run_chapter determine section from active session


@app.command()
def practice(
    chapter: int = typer.Argument(..., help="Chapter number for practice"),
):
    """Jump directly to command practice (power user command)."""
    run_chapter(chapter, "practice")


@app.command(name="list")
def list_chapters():
    """Browse available chapters (alias for browse)."""
    browse_chapters()


@app.command()
def reset(
    chapter: int = typer.Argument(None, help="Chapter number to reset (omit for all)"),
    all_chapters: bool = typer.Option(False, "--all", "-a", help="Reset all chapters"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Reset progress for a chapter or the entire course."""
    console = get_console()

    # Determine what to reset
    if all_chapters or chapter is None:
        # Reset everything
        if not yes:
            console.print("[warning]This will reset ALL course progress.[/warning]")
            confirm = input("Are you sure? (y/N): ").strip().lower()
            if confirm != "y":
                console.print("[info]Reset cancelled.[/info]")
                return

        clear_progress(None)
        console.print("[success]All course progress has been reset.[/success]")
    else:
        # Reset specific chapter
        if not yes:
            console.print(f"[warning]This will reset progress for chapter {chapter}.[/warning]")
            confirm = input("Are you sure? (y/N): ").strip().lower()
            if confirm != "y":
                console.print("[info]Reset cancelled.[/info]")
                return

        clear_progress(chapter)
        console.print(f"[success]Progress reset for chapter {chapter}.[/success]")


@app.command()
def doctor():
    """Check environment and diagnose K8s setup issues."""
    run_doctor()


@app.command()
def config(
    set_key: bool = typer.Option(False, "--set-key", help="Set Gemini API key"),
    clear_key: bool = typer.Option(False, "--clear-key", help="Clear Gemini API key"),
):
    """Manage kubepath configuration (Gemini API key)."""
    console = get_console()
    clear_screen()
    print_banner()

    if set_key:
        prompt_gemini_setup()
        return

    if clear_key:
        clear_gemini_api_key()
        console.print("[success]Gemini API key cleared.[/success]")
        return

    # Show current config status
    console.print("[info]Configuration Status[/info]\n")

    status = get_config_status()

    console.print(f"  [hint]Config file:[/hint] {status['config_file']}")
    console.print(f"  [hint]Config exists:[/hint] {'Yes' if status['config_exists'] else 'No'}")
    console.print()

    if status["gemini_configured"]:
        source = status["gemini_key_source"]
        if source == "config_file":
            source_display = "config file"
        else:
            source_display = f"environment variable ({source})"
        console.print(f"  [success]Gemini API:[/success] Configured (from {source_display})")
        console.print(f"  [hint]Model:[/hint] {status['gemini_model']}")
    else:
        console.print("  [warning]Gemini API:[/warning] Not configured")
        console.print()
        console.print("[hint]To enable AI debugging hints, run:[/hint]")
        console.print("  [success]kubepath config --set-key[/success]")

    console.print()
    input("Press Enter to continue...")


@app.command()
def scenarios(
    chapter: int = typer.Argument(..., help="Chapter number for scenarios"),
):
    """Jump directly to debugging scenarios (power user command)."""
    run_chapter(chapter, "scenarios")


if __name__ == "__main__":
    app()
