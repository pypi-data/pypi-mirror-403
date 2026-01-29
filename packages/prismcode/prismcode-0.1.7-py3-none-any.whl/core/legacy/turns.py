from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any, Dict
import uuid

@dataclass
class Turn:
    """
    Represents a single "turn" in the conversation.
    A turn consists of:
    1. A user message (the trigger)
    2. A sequence of steps (thoughts, tool calls, tool outputs) - "The Middle"
    3. An assistant final response (the result)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    user_message: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    assistant_message: Optional[Dict[str, Any]] = None
    
    # Metadata for future squashing/summarization
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "user_message": self.user_message,
            "steps": self.steps,
            "assistant_message": self.assistant_message,
            "summary": self.summary,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Turn':
        return cls(
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            user_message=data.get("user_message"),
            steps=data.get("steps", []),
            assistant_message=data.get("assistant_message"),
            summary=data.get("summary"),
            tags=data.get("tags", [])
        )

def migrate_messages_to_turns(messages: List[Dict[str, Any]]) -> List[Turn]:
    """
    Heuristic migration:
    - User message starts a new Turn.
    - Assistant message with tool_calls or content adds to current Turn.
    - Tool outputs add to current Turn.
    """
    turns: List[Turn] = []
    current_turn: Optional[Turn] = None

    for msg in messages:
        role = msg.get("role")
        
        # System messages are usually global context, but if they appear in history 
        # as part of a flow, we might need a special place. 
        # For now, we'll treat system messages as separate if they appear (unlikely in mid usage),
        # or just attach to the previous turn if valid, or start a new one?
        # Actually, standard flow: user -> [tools] -> assistant.
        
        if role == "user":
            # Start new turn
            current_turn = Turn(user_message=msg)
            turns.append(current_turn)
            
        elif role == "tool":
            # Tool result - belongs to current turn steps
            if current_turn:
                current_turn.steps.append(msg)
            else:
                # Orphaned tool output? Create a dummy turn or attach to last?
                # Ideally shouldn't happen in well-formed history, but for robustness:
                if turns:
                    turns[-1].steps.append(msg)
                else:
                    # Create a dummy turn if absolutely necessary
                    dummy = Turn(user_message={"role": "user", "content": "[Migration: Orphaned Tool Output]"})
                    dummy.steps.append(msg)
                    turns.append(dummy)
                    current_turn = dummy

        elif role == "assistant":
            if not current_turn:
                 # Orphaned assistant msg? logic same as above
                if turns:
                    current_turn = turns[-1]
                else:
                     dummy = Turn(user_message={"role": "user", "content": "[Migration: Orphaned Assistant MSG]"})
                     turns.append(dummy)
                     current_turn = dummy

            if msg.get("tool_calls"):
                # It's an intermediate step
                current_turn.steps.append(msg)
            else:
                # It's potentially a final response, OR a thought chain.
                # If there are already tool calls in steps, this might be the final response.
                # But sometimes assistant sends text + tool_calls.
                # Simple heuristic: updates the assistant_message slot. 
                # If assistant_message is ALREADY filled, maybe append? 
                # Or if it was a multi-step response.
                
                # Let's say: 
                # If it has tool_calls, it's a step.
                # If it has NO tool_calls, it is the final response (or a text chunk).
                current_turn.assistant_message = msg
        
        else:
             # System or other roles
             pass

    return turns
