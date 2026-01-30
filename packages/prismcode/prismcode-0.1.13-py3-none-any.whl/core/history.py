"""
Session history management using ~/.prism/histories/
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid


def get_prism_dir() -> Path:
    """Get or create ~/.prism directory."""
    prism_dir = Path.home() / ".prism"
    prism_dir.mkdir(exist_ok=True)
    return prism_dir


def get_histories_dir() -> Path:
    """Get or create ~/.prism/histories directory."""
    histories_dir = get_prism_dir() / "histories"
    histories_dir.mkdir(exist_ok=True)
    return histories_dir


class SessionHistory:
    """Manages a single chat session's history."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.file_path = get_histories_dir() / f"{self.session_id}.json"
        self.messages: list[dict] = []  # Display-friendly messages
        self.api_messages: list[dict] = []  # Raw API messages for restoration
        self.metadata: dict = {}

        if self.file_path.exists():
            self._load()
        else:
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

    def _generate_session_id(self) -> str:
        """Generate a session ID: date + short uuid."""
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:6]
        return f"{date_str}_{short_uuid}"

    def _load(self):
        """Load session from disk."""
        try:
            text = self.file_path.read_text()
            if not text.strip():
                # Empty file - treat as new session
                self.metadata = {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
                return
            data = json.loads(text)
            self.messages = data.get("messages", [])
            self.api_messages = data.get("api_messages", [])
            self.metadata = data.get("metadata", {})
        except json.JSONDecodeError:
            # Corrupt file - treat as new session
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

    def _save(self):
        """Save session to disk."""
        self.metadata["updated_at"] = datetime.now().isoformat()
        data = {
            "metadata": self.metadata,
            "messages": self.messages,
            "api_messages": self.api_messages,
        }
        self.file_path.write_text(json.dumps(data, indent=2))

    def add_api_message(self, message: dict):
        """Add a raw API message for lossless restoration."""
        self.api_messages.append(message)
        self._save()

    def add_message(self, role: str, content: str, **extra):
        """Add a message and persist."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **extra,
        }
        self.messages.append(message)
        self._save()

    def add_tool_call(self, tool_name: str, arguments: dict, result: str):
        """Add a tool call record."""
        self.messages.append({
            "role": "tool",
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()


def list_sessions(limit: int = None) -> list[dict]:
    """List recent sessions.
    
    Args:
        limit: Maximum number of sessions to return. None means no limit.
    """
    histories_dir = get_histories_dir()
    sessions = []
    seen_ids = set()

    # Collect all .json files (both .gt.json and legacy .json)
    all_files = list(histories_dir.glob("*.json"))

    for file in sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            # Skip .gt.gt.json files (malformed)
            if file.name.endswith(".gt.gt.json"):
                continue

            # Strip .gt if present to get clean session ID
            session_id = file.stem
            if session_id.endswith(".gt"):
                session_id = session_id[:-3]

            # Skip duplicates (prefer .gt.json over .json)
            if session_id in seen_ids:
                continue
            seen_ids.add(session_id)

            data = json.loads(file.read_text())

            # Try new format first (.gt.json with ground_truth)
            if "ground_truth" in data or "working" in data:
                working = data.get("working", {})
                entries = working.get("entries", [])
                msg_count = len(entries)

                # Get first user message as preview
                preview = ""
                for entry in entries:
                    msg = entry.get("message", {})
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        # Clean up gist markers if present
                        if "[Conversation gist]" in content:
                            content = content.replace("[Conversation gist]", "").strip()
                        preview = content[:50]
                        break

                # Extract metadata from first entry or use defaults
                created_at = entries[0].get("timestamp") if entries else None
                updated_at = entries[-1].get("timestamp") if entries else None

                # Get title from metadata if present
                title = data.get("metadata", {}).get("title")
                
                sessions.append({
                    "id": session_id,
                    "title": title,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "message_count": msg_count,
                    "preview": preview,
                })
            else:
                # Legacy format
                meta = data.get("metadata", {})
                msg_count = len(data.get("messages", []))
                preview = ""
                for msg in data.get("messages", []):
                    if msg.get("role") == "user":
                        preview = msg.get("content", "")[:50]
                        break
                sessions.append({
                    "id": session_id,
                    "title": meta.get("title"),
                    "created_at": meta.get("created_at"),
                    "updated_at": meta.get("updated_at"),
                    "message_count": msg_count,
                    "preview": preview,
                })

            if limit and len(sessions) >= limit:
                break

        except Exception:
            continue

    return sessions


def get_session_title(session_id: str) -> Optional[str]:
    """Get title for a session. Checks both new (.gt.json) and legacy (.json) formats."""
    histories_dir = get_histories_dir()
    
    # Try new format first
    gt_path = histories_dir / f"{session_id}.gt.json"
    if gt_path.exists():
        try:
            data = json.loads(gt_path.read_text())
            title = data.get("metadata", {}).get("title")
            if title:
                return title
        except Exception:
            pass
    
    # Fall back to legacy format
    legacy_path = histories_dir / f"{session_id}.json"
    if legacy_path.exists():
        try:
            data = json.loads(legacy_path.read_text())
            return data.get("metadata", {}).get("title")
        except Exception:
            pass
    
    return None


def set_session_title(session_id: str, title: str) -> bool:
    """Set title for a session. Updates both new (.gt.json) and legacy (.json) formats."""
    histories_dir = get_histories_dir()
    updated = False
    
    # Update new format
    gt_path = histories_dir / f"{session_id}.gt.json"
    if gt_path.exists():
        try:
            data = json.loads(gt_path.read_text())
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["title"] = title
            gt_path.write_text(json.dumps(data, indent=2))
            updated = True
        except Exception:
            pass
    
    # Update legacy format
    legacy_path = histories_dir / f"{session_id}.json"
    if legacy_path.exists():
        try:
            data = json.loads(legacy_path.read_text())
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["title"] = title
            legacy_path.write_text(json.dumps(data, indent=2))
            updated = True
        except Exception:
            pass
    
    return updated
