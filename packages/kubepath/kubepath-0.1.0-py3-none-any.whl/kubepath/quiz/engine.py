"""Quiz engine for kubepath."""

from dataclasses import dataclass, field
from typing import Any, Optional

from kubepath.utils.progress import (
    get_error_bank_questions,
    save_to_error_bank,
    remove_from_error_bank,
)


@dataclass
class QuizResult:
    """Result of checking an answer."""

    question_index: int
    correct: bool
    points_earned: int
    max_points: int
    user_answer: str
    explanation: str


class QuizEngine:
    """Engine for running interactive quizzes.

    Handles:
    - Question management with error bank mixing
    - Answer validation for 4 question types
    - AI hints (without revealing answers)
    - Score tracking
    - Progress persistence

    Example:
        engine = QuizEngine(chapter=1, quiz_data=quiz_data)
        engine.prepare_questions(error_bank_percent=20)

        while not engine.is_complete():
            question = engine.get_current_question()
            # Display question...
            result = engine.check_answer(user_input)
            if result.correct:
                engine.advance()
    """

    def __init__(
        self,
        chapter: int,
        quiz_data: dict[str, Any],
        gemini_client: Optional[Any] = None,
    ):
        """Initialize the quiz engine.

        Args:
            chapter: Chapter number for this quiz.
            quiz_data: Quiz dictionary from chapter YAML.
            gemini_client: Optional GeminiClient for AI hints.
        """
        self.chapter = chapter
        self.original_questions = quiz_data.get("questions", [])
        self.questions: list[dict[str, Any]] = []
        self.passing_score = quiz_data.get("passing_score", 70)
        self.gemini = gemini_client

        self.current_index = 0
        self.answers: dict[int, dict[str, Any]] = {}
        self.total_points = 0
        self.max_points = 0
        self.hints_used = 0
        self.ai_hint_penalty = 2

        # Track which questions came from error bank
        self._error_bank_indices: set[int] = set()

    def prepare_questions(self, error_bank_percent: int = 20) -> None:
        """Prepare questions by mixing in error bank questions.

        Args:
            error_bank_percent: Percentage of questions to take from error bank.
        """
        # Start with original questions
        self.questions = list(self.original_questions)

        # Calculate how many error bank questions to include
        total = len(self.questions)
        error_count = max(1, int(total * error_bank_percent / 100)) if total > 0 else 0

        # Get error bank questions (excluding current chapter to avoid duplicates)
        error_questions = get_error_bank_questions(
            count=error_count,
            exclude_chapter=self.chapter,
        )

        if error_questions:
            import random

            # Replace random questions with error bank questions
            indices_to_replace = random.sample(
                range(total),
                min(len(error_questions), total),
            )

            for i, idx in enumerate(indices_to_replace):
                if i < len(error_questions):
                    # Mark as from error bank
                    error_q = error_questions[i].copy()
                    error_q["_from_error_bank"] = True
                    self.questions[idx] = error_q
                    self._error_bank_indices.add(idx)

        # Calculate max points
        self.max_points = sum(q.get("points", 0) for q in self.questions)

    def get_current_question(self) -> Optional[dict[str, Any]]:
        """Get the current question.

        Returns:
            Current question dict, or None if quiz is complete.
        """
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    def check_answer(self, answer: str) -> QuizResult:
        """Check if the answer is correct.

        Does NOT advance to next question - call advance() after correct answer.

        Args:
            answer: User's answer (A/B/C/D, command, or text value).

        Returns:
            QuizResult with correctness, points, and explanation.
        """
        question = self.get_current_question()
        if not question:
            return QuizResult(
                question_index=self.current_index,
                correct=False,
                points_earned=0,
                max_points=0,
                user_answer=answer,
                explanation="No question available.",
            )

        q_type = question.get("type", "multiple_choice")
        points = question.get("points", 0)
        explanation = question.get("explanation", "")

        correct = self._validate_answer(question, answer)

        if correct:
            # Award points (only on first correct answer)
            if self.current_index not in self.answers:
                self.total_points += points

            self.answers[self.current_index] = {
                "answer": answer,
                "correct": True,
                "points": points,
            }

            # Remove from error bank if it was there and user got it right
            question_text = question.get("question", "")
            remove_from_error_bank(question_text)

        return QuizResult(
            question_index=self.current_index,
            correct=correct,
            points_earned=points if correct else 0,
            max_points=points,
            user_answer=answer,
            explanation=explanation if correct else "",
        )

    def _validate_answer(self, question: dict[str, Any], answer: str) -> bool:
        """Validate answer based on question type.

        Args:
            question: Question dictionary.
            answer: User's answer.

        Returns:
            True if answer is correct.
        """
        q_type = question.get("type", "multiple_choice")
        answer = answer.strip()

        if q_type == "multiple_choice":
            return self._validate_multiple_choice(question, answer)
        elif q_type == "true_false":
            return self._validate_true_false(question, answer)
        elif q_type == "command_challenge":
            return self._validate_command_challenge(question, answer)
        elif q_type == "fill_yaml":
            return self._validate_fill_yaml(question, answer)

        return False

    def _validate_multiple_choice(self, question: dict[str, Any], answer: str) -> bool:
        """Validate multiple choice answer.

        Args:
            question: Question with 'correct' index (0-based).
            answer: User answer (A, B, C, or D).

        Returns:
            True if answer matches correct index.
        """
        answer = answer.upper()
        if answer not in ("A", "B", "C", "D"):
            return False

        # Convert letter to index (A=0, B=1, C=2, D=3)
        answer_index = ord(answer) - ord("A")
        correct_index = question.get("correct", -1)

        return answer_index == correct_index

    def _validate_true_false(self, question: dict[str, Any], answer: str) -> bool:
        """Validate true/false answer.

        Args:
            question: Question with 'correct' boolean.
            answer: User answer (A=True, B=False, or true/false).

        Returns:
            True if answer matches.
        """
        answer = answer.upper().strip()

        # Support both A/B and true/false
        if answer in ("A", "TRUE", "T", "YES", "Y"):
            user_answer = True
        elif answer in ("B", "FALSE", "F", "NO", "N"):
            user_answer = False
        else:
            return False

        return user_answer == question.get("correct", False)

    def _validate_command_challenge(self, question: dict[str, Any], answer: str) -> bool:
        """Validate command challenge answer.

        Args:
            question: Question with 'expected_contains' and optional 'alternatives'.
            answer: User's command.

        Returns:
            True if answer contains expected text or matches an alternative.
        """
        answer = answer.lower().strip()

        # Check main expected
        expected = question.get("expected_contains", "").lower()
        if expected and expected in answer:
            return True

        # Check alternatives
        # Only check if the alternative is contained in the user's answer
        # (allowing extra flags/arguments), NOT the reverse (which would
        # accept incomplete commands like "kubectl cluster" for "kubectl cluster-info")
        alternatives = question.get("alternatives", [])
        for alt in alternatives:
            if alt.lower() in answer:
                return True

        return False

    def _validate_fill_yaml(self, question: dict[str, Any], answer: str) -> bool:
        """Validate fill-in-the-blank YAML answer.

        Args:
            question: Question with 'expected' value.
            answer: User's answer.

        Returns:
            True if answer matches expected (case-insensitive).
        """
        expected = question.get("expected", "").strip().lower()
        return answer.strip().lower() == expected

    def skip_question(self) -> None:
        """Skip the current question.

        Awards 0 points and adds question to error bank.
        """
        question = self.get_current_question()
        if not question:
            return

        # Record as skipped
        self.answers[self.current_index] = {
            "answer": "skipped",
            "correct": False,
            "points": 0,
        }

        # Add to error bank (unless it came from error bank)
        if self.current_index not in self._error_bank_indices:
            save_to_error_bank(
                chapter=self.chapter,
                question_data=question,
                user_answer="skipped",
            )

        # Move to next question
        self.current_index += 1

    def advance(self) -> None:
        """Advance to the next question."""
        self.current_index += 1

    def get_ai_hint(self, question: Optional[dict[str, Any]] = None) -> Optional[str]:
        """Get an AI-generated hint for the current question.

        Costs ai_hint_penalty points (only deducted on success).

        Args:
            question: Optional question to get hint for (uses current if not provided).

        Returns:
            Hint text, or None if AI unavailable.
        """
        if not self.gemini:
            return None

        if question is None:
            question = self.get_current_question()

        if not question:
            return None

        # Build context for the AI
        q_type = question.get("type", "multiple_choice")
        q_text = question.get("question", "")

        context = f"Question type: {q_type}\nQuestion: {q_text}"

        if q_type == "multiple_choice":
            options = question.get("options", [])
            context += "\n\nOptions:"
            for i, opt in enumerate(options):
                context += f"\n  [{chr(65 + i)}] {opt}"

        elif q_type == "true_false":
            context += "\n\nOptions: [A] True  [B] False"

        elif q_type == "command_challenge":
            hint = question.get("hint", "")
            if hint:
                context += f"\n\nQuestion hint: {hint}"

        elif q_type == "fill_yaml":
            template = question.get("yaml_template", "")
            if template:
                context += f"\n\nYAML template:\n{template}"

        # Use the GeminiClient's answer_question method which handles
        # configuration and rate limits properly
        hint_text = self.gemini.answer_question(
            context_title="Quiz Question",
            context_content=context,
            learner_question="Give me a hint to guide me toward the answer without revealing it directly. Keep it to 2-3 sentences.",
            section_type="quiz",
        )

        if hint_text:
            # Only deduct points and count hint if we got a successful response
            self.total_points = max(0, self.total_points - self.ai_hint_penalty)
            self.hints_used += 1
            return hint_text[:400]

        return None

    def is_complete(self) -> bool:
        """Check if quiz is complete.

        Returns:
            True if all questions have been answered.
        """
        return self.current_index >= len(self.questions)

    def get_summary(self) -> dict[str, Any]:
        """Get quiz summary statistics.

        Returns:
            Dictionary with score, max_score, correct count, passed status, etc.
        """
        correct_count = sum(1 for a in self.answers.values() if a.get("correct", False))
        percentage = int((self.total_points / self.max_points) * 100) if self.max_points > 0 else 0
        passed = percentage >= self.passing_score

        return {
            "score": self.total_points,
            "max_score": self.max_points,
            "correct": correct_count,
            "total": len(self.questions),
            "percentage": percentage,
            "passed": passed,
            "hints_used": self.hints_used,
            "hint_penalty_total": self.hints_used * self.ai_hint_penalty,
            "error_bank_questions": len(self._error_bank_indices),
        }

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore quiz state from saved progress.

        Args:
            state: Saved state dictionary with current_index, answers, etc.
        """
        self.current_index = state.get("current_index", 0)
        self.answers = state.get("answers", {})
        self.total_points = state.get("total_points", 0)
        self.hints_used = state.get("hints_used", 0)

    def get_state_for_persistence(self) -> dict[str, Any]:
        """Get current state for saving to progress file.

        Returns:
            State dictionary suitable for JSON serialization.
        """
        return {
            "current_index": self.current_index,
            "answers": self.answers,
            "total_points": self.total_points,
            "hints_used": self.hints_used,
        }

    def record_wrong_answer(self, answer: str) -> None:
        """Record a wrong answer and add question to error bank.

        Called when user gets a question wrong (not when they retry successfully).

        Args:
            answer: The wrong answer the user gave.
        """
        question = self.get_current_question()
        if not question:
            return

        # Add to error bank (unless it came from error bank)
        if self.current_index not in self._error_bank_indices:
            save_to_error_bank(
                chapter=self.chapter,
                question_data=question,
                user_answer=answer,
            )
