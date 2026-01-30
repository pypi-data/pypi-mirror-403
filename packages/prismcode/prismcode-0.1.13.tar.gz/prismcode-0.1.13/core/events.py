from dataclasses import dataclass

@dataclass
class Event:
    """Base event emitted by agent."""
    type: str


@dataclass
class TextDelta(Event):
    """Streaming text chunk."""
    type: str = "text_delta"
    content: str = ""


@dataclass
class TextDone(Event):
    """Final complete text response."""
    type: str = "text_done"
    content: str = ""


@dataclass
class ToolStart(Event):
    """Tool execution starting."""
    type: str = "tool_start"
    name: str = ""
    arguments: dict = None


@dataclass
class ToolDone(Event):
    """Tool execution complete."""
    type: str = "tool_done"
    name: str = ""
    arguments: dict = None
    result: str = ""


@dataclass
class ToolProgress(Event):
    """Tool call arguments streaming."""
    type: str = "tool_progress"
    name: str = ""
    index: int = 0
    bytes_received: int = 0
