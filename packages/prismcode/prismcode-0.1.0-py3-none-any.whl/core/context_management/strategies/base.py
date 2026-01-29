"""
Base interface for consolidation strategies.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ground_truth import HistoryManager, Entry
    from ..tokens import TokenCounter


@dataclass
class ConsolidationResult:
    """Result of a consolidation operation."""

    # Did consolidation happen?
    consolidated: bool

    # How many entries were replaced?
    entries_replaced: int = 0

    # Token counts
    tokens_before: int = 0
    tokens_after: int = 0

    # The gist that was created (if any)
    gist_text: Optional[str] = None

    # Entry IDs that were consolidated
    consolidated_ids: List[str] = field(default_factory=list)

    @property
    def tokens_saved(self) -> int:
        return self.tokens_before - self.tokens_after

    @property
    def compression_ratio(self) -> float:
        if self.tokens_after == 0:
            return 0.0
        return self.tokens_before / self.tokens_after


class ConsolidationStrategy(ABC):
    """
    Base class for memory consolidation strategies.

    A strategy determines:
    1. WHEN to consolidate (should_consolidate)
    2. WHAT to consolidate (which entries to compress)
    3. HOW to consolidate (the gist prompt and process)

    Subclasses implement the specific logic.
    """

    def __init__(
        self,
        budget: int,
        threshold: float = 0.7,
        gist_fn: Optional[Callable[[str], str]] = None,
    ):
        """
        Args:
            budget: Maximum token budget for working history
            threshold: Trigger consolidation when usage exceeds this (0.0-1.0)
            gist_fn: Function that takes text and returns a gist/summary.
                    If None, must be provided when calling consolidate().
        """
        self.budget = budget
        self.threshold = threshold
        self.gist_fn = gist_fn

    @abstractmethod
    def should_consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
    ) -> bool:
        """
        Check if consolidation should happen.

        Args:
            history: The history manager
            counter: Token counter for measuring usage

        Returns:
            True if consolidation should run
        """
        ...

    @abstractmethod
    async def consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        gist_fn: Optional[Callable[[str], str]] = None,
    ) -> ConsolidationResult:
        """
        Run consolidation on the history.

        Args:
            history: The history manager (will be modified in place)
            counter: Token counter
            gist_fn: Function to generate gist. Overrides self.gist_fn if provided.

        Returns:
            ConsolidationResult with details of what was done
        """
        ...

    def get_usage(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
    ) -> tuple[int, float]:
        """
        Get current token usage.

        Returns:
            (token_count, usage_ratio)
        """
        from ..query import HistoryQuery

        query = HistoryQuery(history.working.entries, counter)
        tokens = query.total_tokens()
        ratio = tokens / self.budget if self.budget > 0 else 0.0

        return tokens, ratio
