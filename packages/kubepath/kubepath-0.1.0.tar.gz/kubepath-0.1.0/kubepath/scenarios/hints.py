"""Progressive hint system with point penalties."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HintResult:
    """Result of requesting a hint."""

    hint_text: str
    hint_number: int  # 1-based
    total_hints: int
    penalty_applied: int
    has_more_hints: bool


@dataclass
class HintManager:
    """Manages progressive hints for a scenario.

    Tracks which hints have been used and calculates point penalties.

    Example:
        manager = HintManager(
            hints=["Check pod status", "Look at the image name", "Fix the typo"],
            hint_penalty=5,
        )
        hint = manager.get_next_hint()  # Returns first hint, applies 5 point penalty
        score = manager.calculate_final_score(25)  # 25 - 5 = 20
    """

    hints: List[str]
    hint_penalty: int = 5
    ai_hint_penalty: int = 2  # AI hints cost less (encourages learning)
    _hints_used: int = 0
    _ai_hints_used: int = 0

    @property
    def hints_used(self) -> int:
        """Number of static hints used so far."""
        return self._hints_used

    @property
    def ai_hints_used(self) -> int:
        """Number of AI hints used so far."""
        return self._ai_hints_used

    @property
    def hints_remaining(self) -> int:
        """Number of static hints still available."""
        return len(self.hints) - self._hints_used

    @property
    def total_penalty(self) -> int:
        """Total penalty accumulated from all hints used."""
        static_penalty = self._hints_used * self.hint_penalty
        ai_penalty = self._ai_hints_used * self.ai_hint_penalty
        return static_penalty + ai_penalty

    @property
    def static_hint_penalty(self) -> int:
        """Penalty from static hints only."""
        return self._hints_used * self.hint_penalty

    def get_next_hint(self) -> Optional[HintResult]:
        """Get the next hint and apply penalty.

        Returns:
            HintResult with hint text and penalty info, or None if no more hints.
        """
        if self._hints_used >= len(self.hints):
            return None

        hint_text = self.hints[self._hints_used]
        self._hints_used += 1

        return HintResult(
            hint_text=hint_text,
            hint_number=self._hints_used,
            total_hints=len(self.hints),
            penalty_applied=self.hint_penalty,
            has_more_hints=self._hints_used < len(self.hints),
        )

    def peek_next_hint(self) -> Optional[str]:
        """Preview next hint without using it.

        Returns:
            The next hint text, or None if no more hints.
        """
        if self._hints_used >= len(self.hints):
            return None
        return self.hints[self._hints_used]

    def record_ai_hint(self) -> int:
        """Record that an AI hint was used.

        Returns:
            The penalty applied for the AI hint.
        """
        self._ai_hints_used += 1
        return self.ai_hint_penalty

    def calculate_final_score(self, base_points: int) -> int:
        """Calculate final score after hint penalties.

        Args:
            base_points: Maximum points for the scenario.

        Returns:
            Final score (minimum 0).
        """
        return max(0, base_points - self.total_penalty)

    def reset(self) -> None:
        """Reset hint usage (for retrying scenario)."""
        self._hints_used = 0
        self._ai_hints_used = 0

    def get_summary(self) -> dict:
        """Get summary of hint usage.

        Returns:
            Dictionary with hint usage statistics.
        """
        return {
            "static_hints_used": self._hints_used,
            "static_hints_total": len(self.hints),
            "ai_hints_used": self._ai_hints_used,
            "total_penalty": self.total_penalty,
        }
