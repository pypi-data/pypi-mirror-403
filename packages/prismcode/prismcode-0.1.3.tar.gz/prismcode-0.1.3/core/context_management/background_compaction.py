"""
Background Compaction System

Proactively compacts history in a background thread before hitting limits.
The agent continues working while compaction happens asynchronously.

Key features:
- Triggers at configurable threshold (default 70% of budget)
- Runs in background thread, doesn't block agent
- Atomic swap of compacted history when ready
- Thread-safe with proper locking
"""
import threading
import time
import logging
from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .ground_truth import HistoryManager, WorkingHistory, Entry
    from .tokens import TokenCounter

logger = logging.getLogger(__name__)


@dataclass
class CompactionStatus:
    """Status of the background compaction."""
    is_running: bool = False
    last_run: Optional[float] = None  # timestamp
    last_tokens_before: int = 0
    last_tokens_after: int = 0
    last_entries_compressed: int = 0
    error: Optional[str] = None


class BackgroundCompactor:
    """
    Manages background compaction of history.
    
    Usage:
        compactor = BackgroundCompactor(
            history_manager=agent.history_manager,
            counter=agent.counter,
            budget=agent.context_budget,
            gist_fn=agent._sync_gist,
        )
        
        # Check and trigger (non-blocking) before each agent turn
        compactor.check_and_compact()
        
        # Get status
        if compactor.status.is_running:
            print("Compaction in progress...")
    """
    
    def __init__(
        self,
        history_manager: "HistoryManager",
        counter: "TokenCounter",
        budget: int,
        gist_fn: Callable[[str], str],
        trigger_threshold: float = 0.70,  # Start compacting at 70%
        compress_ratio: float = 0.30,     # Compress oldest 30%
        min_entries: int = 6,             # Need at least this many to compact
        cooldown_seconds: float = 30.0,   # Wait between compaction attempts
    ):
        """
        Args:
            history_manager: The HistoryManager to compact
            counter: Token counter
            budget: Token budget (context window limit)
            gist_fn: Sync function that takes prompt string and returns gist
            trigger_threshold: Start compacting when usage exceeds this ratio
            compress_ratio: What fraction of history to compress each time
            min_entries: Minimum entries before compaction is considered
            cooldown_seconds: Minimum time between compaction runs
        """
        self.history_manager = history_manager
        self.counter = counter
        self.budget = budget
        self.gist_fn = gist_fn
        self.trigger_threshold = trigger_threshold
        self.compress_ratio = compress_ratio
        self.min_entries = min_entries
        self.cooldown_seconds = cooldown_seconds
        
        # Thread safety
        self._lock = threading.RLock()
        self._compaction_thread: Optional[threading.Thread] = None
        
        # Status tracking
        self.status = CompactionStatus()
    
    def _count_tokens(self) -> int:
        """Count current working history tokens."""
        total = 0
        for entry in self.history_manager.working.entries:
            total += self.counter.count_message(entry.message)
        return total
    
    def _get_usage_ratio(self) -> float:
        """Get current usage as ratio of budget."""
        tokens = self._count_tokens()
        return tokens / self.budget if self.budget > 0 else 0.0
    
    def should_compact(self) -> bool:
        """
        Check if compaction should be triggered.
        
        Conditions:
        - Usage exceeds threshold
        - Not already running
        - Cooldown has passed
        - Enough entries to compact
        """
        with self._lock:
            # Already running?
            if self.status.is_running:
                return False
            
            # Cooldown check
            if self.status.last_run:
                elapsed = time.time() - self.status.last_run
                if elapsed < self.cooldown_seconds:
                    return False
            
            # Enough entries?
            entries = self.history_manager.working.entries
            if len(entries) < self.min_entries:
                return False
            
            # Check usage
            ratio = self._get_usage_ratio()
            return ratio >= self.trigger_threshold
    
    def check_and_compact(self) -> bool:
        """
        Check if compaction needed and start background thread if so.
        
        Returns:
            True if compaction was started, False otherwise
        """
        if not self.should_compact():
            return False
        
        with self._lock:
            # Double-check under lock
            if self.status.is_running:
                return False
            
            self.status.is_running = True
            self.status.error = None
            
            # Start background thread
            self._compaction_thread = threading.Thread(
                target=self._run_compaction,
                daemon=True,
                name="prism-compaction"
            )
            self._compaction_thread.start()
            
            logger.info("Background compaction started")
            return True
    
    def _run_compaction(self):
        """
        The actual compaction logic, runs in background thread.
        """
        from .query import HistoryQuery
        from .strategies.rolling_gist import DEFAULT_GIST_PROMPT
        
        try:
            with self._lock:
                entries = self.history_manager.working.entries
                
                # Find the last gist - only compact RAW messages after it
                last_gist_idx = -1
                for i, e in enumerate(entries):
                    if e.is_gist:
                        last_gist_idx = i
                
                # Get raw entries after last gist
                raw_start_idx = last_gist_idx + 1
                raw_entries = entries[raw_start_idx:]
                
                if len(raw_entries) < self.min_entries:
                    logger.info("Not enough raw entries to compact")
                    return
                
                # Build query over raw entries
                query = HistoryQuery(raw_entries, self.counter)
                tokens_before = query.total_tokens()
                
                # Select oldest portion to compress
                slice_to_compress = query.first_percent(self.compress_ratio)
                
                if slice_to_compress.is_empty() or slice_to_compress.entry_count() < 2:
                    logger.info("Slice too small to compact")
                    return
                
                # Find safe boundary
                safe_end = query.safe_boundary_near(slice_to_compress.end_idx)
                slice_to_compress = query.range(0, safe_end)
                
                if slice_to_compress.entry_count() < 2:
                    return
                
                # Generate gist input
                gist_input = slice_to_compress.to_gist_input()
                prompt = DEFAULT_GIST_PROMPT.format(content=gist_input)
            
            # Release lock during LLM call (can take seconds)
            logger.info(f"Generating gist for {slice_to_compress.entry_count()} entries...")
            gist_text = self.gist_fn(prompt)
            
            # Re-acquire lock for the atomic swap
            with self._lock:
                # Convert slice indices to full entries list indices
                full_start_idx = raw_start_idx + slice_to_compress.start_idx
                full_end_idx = raw_start_idx + slice_to_compress.end_idx
                
                # Replace range with gist
                self.history_manager.working.replace_range_with_gist(
                    full_start_idx,
                    full_end_idx,
                    gist_text,
                )
                
                # Save to disk
                self.history_manager._auto_save()
                
                # Update status
                tokens_after = self._count_tokens()
                self.status.last_tokens_before = tokens_before
                self.status.last_tokens_after = tokens_after
                self.status.last_entries_compressed = slice_to_compress.entry_count()
                
                logger.info(
                    f"Compaction complete: {tokens_before:,} -> {tokens_after:,} tokens "
                    f"({slice_to_compress.entry_count()} entries compressed)"
                )
        
        except Exception as e:
            logger.error(f"Background compaction failed: {e}")
            with self._lock:
                self.status.error = str(e)
        
        finally:
            with self._lock:
                self.status.is_running = False
                self.status.last_run = time.time()
    
    def wait_for_completion(self, timeout: float = 60.0) -> bool:
        """
        Wait for current compaction to complete.
        
        Args:
            timeout: Max seconds to wait
            
        Returns:
            True if completed (or wasn't running), False if timed out
        """
        if self._compaction_thread is None:
            return True
        
        self._compaction_thread.join(timeout=timeout)
        return not self.status.is_running
    
    def get_status_summary(self) -> str:
        """Get human-readable status."""
        with self._lock:
            if self.status.is_running:
                return "⏳ Compacting in background..."
            
            if self.status.error:
                return f"❌ Last compaction failed: {self.status.error}"
            
            if self.status.last_run:
                ago = time.time() - self.status.last_run
                saved = self.status.last_tokens_before - self.status.last_tokens_after
                return (
                    f"✓ Last compaction {ago:.0f}s ago: "
                    f"saved {saved:,} tokens ({self.status.last_entries_compressed} entries)"
                )
            
            return "No compaction yet"
