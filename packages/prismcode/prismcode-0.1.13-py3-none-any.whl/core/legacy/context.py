from typing import List, Protocol, Dict, Any, Optional
from dataclasses import dataclass
from .turns import Turn

@dataclass
class ContextStrategy:
    """Configuration for how to render history."""
    # If True, keeps full tool calls/outputs for all turns
    full_fidelity: bool = False
    
    # If full_fidelity is False:
    # How many recent turns to keep in full detail
    keep_last_n_full: int = 2
    
    # Whether to completely hide tool details for older turns (True) 
    # or just show a summary? (Not implemented yet, assume hide for now)
    fold_older_tools: bool = True

class HistoryProjection(Protocol):
    def render(self, turns: List[Turn]) -> List[Dict[str, Any]]:
        ...

class StandardProjection:
    def __init__(self, strategy: ContextStrategy):
        self.strategy = strategy

    def render(self, turns: List[Turn]) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        
        total_turns = len(turns)
        
        for i, turn in enumerate(turns):
            # Calculate if this turn is "recent"
            is_recent = (total_turns - i) <= self.strategy.keep_last_n_full
            
            show_full = self.strategy.full_fidelity or is_recent
            
            # 1. User Message (Always shown)
            if turn.user_message:
                messages.append(turn.user_message)
            
            # 2. Steps (Tools/Thoughts)
            if show_full:
                messages.extend(turn.steps)
            else:
                # If folding, we currently just OMIT the steps.
                # Future: Insert a summary token?
                pass
                
            # 3. Assistant Message (Always shown)
            if turn.assistant_message:
                messages.append(turn.assistant_message)
                
        return messages

class HistoryManager:
    def __init__(self, turns: List[Turn] = None):
        self.turns: List[Turn] = turns or []

    def add_turn(self, turn: Turn):
        self.turns.append(turn)

    def get_context(self, strategy: ContextStrategy) -> List[Dict[str, Any]]:
        projection = StandardProjection(strategy)
        return projection.render(self.turns)
