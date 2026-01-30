"""
Core Agent class - pure logic, no UI dependencies.
Yields events that can be consumed by any interface (CLI, web, etc.)
"""
import json
from typing import Callable, Generator, List, Optional

import litellm
from litellm.exceptions import ContextWindowExceededError
from dotenv import load_dotenv

from .history import SessionHistory
from .context_management.ground_truth import (
    HistoryManager,
    smart_tool_retention,
)
from .context_management.strategies.rolling_gist import RollingGist
from .signella import Signella
from .project import Project
from .project_manager import ProjectManager
from .filesystem import set_thread_filesystem

from .events import Event, TextDelta, TextDone, ToolStart, ToolDone, ToolProgress
from .tool_utils import convert_tools
from .agent_utils import get_history_path, get_file_tree_for_project

class ContextBudgetExceeded(Exception):
    """Raised when context exceeds model's token limit even after consolidation."""
    pass


load_dotenv()

# Shared Signella store for session state
_store = Signella()


class Agent:
    """
    Core agent class. UI-agnostic - yields events for any interface to consume.
    """

    def __init__(
        self,
        system_prompt: str,
        tools: List[Callable] = None,
        model: str = None,
        session_id: Optional[str] = None,
        project: Optional[Project] = None,
        litellm_params: Optional[dict] = None,
    ):
        self.system_prompt = system_prompt
        self._model = model
        self.tools = tools or []
        self.tool_schemas, self.tool_functions = convert_tools(self.tools) if self.tools else ([], {})
        self.litellm_params = litellm_params or {}

        # Legacy persistence layer (for backward compatibility with TUI)
        self.history = SessionHistory(session_id)
        
        # We'll set the initial model in metadata, but it will be dynamic thereafter
        self.history.metadata["model"] = self.model

        # New ground truth history manager
        history_path = get_history_path(self.history.session_id)
        if history_path.exists():
            self.history_manager = HistoryManager.load(history_path)
        else:
            self.history_manager = HistoryManager(storage_path=history_path)

        # Set default projection - smart tool retention
        self.history_manager.projection = smart_tool_retention(
            max_file_reads=5,
            bash_truncate=10000,
        )

        # Token counting and budget management
        self._refresh_model_profile()
        
        # Consolidation strategy (lazy - only used when needed)
        self._consolidation_strategy = None
        
        # Background compactor - initialize lazily on first use
        self._background_compactor = None
        self._init_background_compactor()

        # Clean up any incomplete tool calls from previous interruptions (if loading existing session)
        if session_id and history_path.exists():
            self.cleanup_incomplete_tool_calls()

        # Project context
        if project is None:
            # Get default project from ProjectManager
            pm = ProjectManager()
            project = pm.get_default()
        self.project = project
        
        # Store project ID in Signella for tools to access
        _store.set('session', self.history.session_id, 'project_id', project.id)

        # Publish current session to Signella for cross-process access
        _store.set('session', 'current', self.history.session_id)

    @property
    def model(self) -> str:
        """Dynamically resolve the model from global config or override."""
        if self._model:
            return self._model
        from .llm_config import get_llm_config
        return get_llm_config().get_active_model()

    def _refresh_model_profile(self):
        """Update model profile and token counters based on current model."""
        from .context_management.tokens import ModelProfile
        current_model = self.model
        self.model_profile = ModelProfile.from_name(current_model)
        # Use accurate LiteLLM counter for precise token counting
        self.counter = self.model_profile.counter(use_litellm=True)
        # Calculate budget: context_window - max_tokens (response buffer)
        # Default max_tokens to 8192 if not specified
        max_tokens = self.litellm_params.get('max_tokens', 8192) if self.litellm_params else 8192
        # Budget = 85% of (context_window - max_tokens) to leave safety margin
        available_window = self.model_profile.context_window - max_tokens
        self.context_budget = int(available_window * 0.85)
        self._last_resolved_model = current_model

    def _init_background_compactor(self):
        """Initialize the background compactor for proactive consolidation."""
        from .context_management.background_compaction import BackgroundCompactor
        
        self._background_compactor = BackgroundCompactor(
            history_manager=self.history_manager,
            counter=self.counter,
            budget=self.context_budget,
            gist_fn=self._sync_gist,
            trigger_threshold=0.70,  # Start at 70% (proactive, not reactive)
            compress_ratio=0.30,     # Compress oldest 30%
            min_entries=6,
            cooldown_seconds=30.0,   # Don't compact more than once per 30s
        )

    def _count_messages(self, messages: list) -> int:
        """Count tokens in a list of messages."""
        return self.counter.count_messages(messages)
    
    def _get_consolidation_strategy(self) -> RollingGist:
        """Get or create consolidation strategy (lazy initialization)."""
        if self._consolidation_strategy is None:
            # Use 80% of budget as threshold, compress 30% at a time
            self._consolidation_strategy = RollingGist(
                budget=self.context_budget,
                threshold=0.80,
                compress_ratio=0.30,
                min_entries_to_keep=4,
            )
        return self._consolidation_strategy
    
    def _sync_gist(self, prompt: str) -> str:
        """
        Synchronous gist generation using the same model.
        Used for emergency consolidation when we hit context limits.
        """
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,  # Gists should be concise
            num_retries=5,    # Handle transient overloading
            vertex_location="global", # Ensure global endpoint for Gemini 3 Pro
        )
        return response.choices[0].message.content
    

    def _emergency_consolidate(self) -> bool:
        """
        Emergency synchronous consolidation when we hit context limits.
        
        Key behavior:
        - Only consolidates RAW messages (skips existing gists)
        - Compresses oldest 30% of raw messages after the last gist
        - Keeps existing gists intact (no "gists of gists")
        
        Returns True if consolidation happened, False otherwise.
        """
        from .context_management.query import HistoryQuery
        from .context_management.strategies.rolling_gist import DEFAULT_GIST_PROMPT
        
        entries = self.history_manager.working.entries
        
        # Check if we have enough entries to consolidate
        if len(entries) < 6:
            return False
        
        # Find the last gist - we only consolidate RAW messages after it
        last_gist_idx = -1
        for i, e in enumerate(entries):
            if e.is_gist:
                last_gist_idx = i
        
        # Calculate range of raw messages to consider
        raw_start_idx = last_gist_idx + 1
        raw_entries = entries[raw_start_idx:]
        
        # Need at least 6 raw messages to consolidate
        if len(raw_entries) < 6:
            return False
        
        # Build query over just the raw entries
        query = HistoryQuery(raw_entries, self.counter)
        
        # Compress 30% of raw messages
        slice_to_compress = query.first_percent(0.3)
        
        if slice_to_compress.is_empty() or slice_to_compress.entry_count() < 2:
            return False
        
        # Find safe boundary (don't split tool call from result)
        safe_end = query.safe_boundary_near(slice_to_compress.end_idx)
        slice_to_compress = query.range(0, safe_end)
        
        if slice_to_compress.entry_count() < 2:
            return False
        
        # Generate gist input from the raw messages
        gist_input = slice_to_compress.to_gist_input()
        
        # Format the prompt
        prompt = DEFAULT_GIST_PROMPT.format(content=gist_input)
        
        # Generate gist synchronously
        try:
            gist_text = self._sync_gist(prompt)
        except Exception as e:
            # If gist generation fails, just truncate instead
            gist_text = f"[Context truncated due to length. {slice_to_compress.entry_count()} messages compressed.]"
        
        # Convert slice indices back to full entries list indices
        full_start_idx = raw_start_idx + slice_to_compress.start_idx
        full_end_idx = raw_start_idx + slice_to_compress.end_idx
        
        # Replace the range with the gist
        self.history_manager.working.replace_range_with_gist(
            full_start_idx,
            full_end_idx,
            gist_text,
        )
        
        # Save
        self.history_manager._auto_save()
        
        return True
    
    def _build_hud_with_budget(self, max_tokens: int = None) -> str:
        """
        Build HUD content with optional token budget.
        If budget exceeded, truncates focused files (keeps most recent).
        """
        from .filesystem import get_current_filesystem, get_project_root
        
        session_id = self.history.session_id
        focused_files = list(_store.get('focus', session_id, 'files', default=[]) or [])
        
        # Start with file tree (always included)
        tree_text = get_file_tree_for_project()
        
        hud_parts = []
        hud_parts.append("# Project Context (Ephemeral - Not Stored)\\n\\n")
        
        # Build focused files section with budget awareness
        files_section = ""
        files_included = 0
        files_skipped = 0
        
        fs = get_current_filesystem()
        project_root = str(get_project_root())
        
        if focused_files:
            files_content = []
            for abs_path in sorted(focused_files):
                try:
                    # Calculate relative path from project root
                    if abs_path.startswith(project_root):
                        rel_path = abs_path[len(project_root):].lstrip('/')
                    else:
                        rel_path = abs_path
                    
                    # Get file extension for syntax highlighting
                    ext = rel_path.split('.')[-1] if '.' in rel_path else ''
                    
                    content = fs.read(abs_path)
                    
                    file_block = f"### {rel_path}\\n\\n"
                    file_block += f"```{ext}\\n"
                    file_block += f"# START OF FILE: {rel_path}\\n"
                    file_block += content
                    file_block += f"\\n# END OF FILE: {rel_path}\\n"
                    file_block += "```\\n\\n"
                    
                    files_content.append((rel_path, file_block, self.counter.count(file_block)))
                except Exception as e:
                    files_content.append((abs_path, f"### {abs_path}\\n\\nError reading: {e}\\n\\n", 50))
            
            # If we have a budget, select files that fit
            if max_tokens:
                # Reserve tokens for tree and stats (~2000 tokens)
                available_for_files = max_tokens - 2000
                selected_files = []
                current_tokens = 0
                
                for rel_path, block, tokens in files_content:
                    if current_tokens + tokens <= available_for_files:
                        selected_files.append(block)
                        current_tokens += tokens
                        files_included += 1
                    else:
                        files_skipped += 1
                
                if selected_files:
                    files_section = "## 📌 Focused Files (Always Visible)\\n\\n"
                    files_section += "".join(selected_files)
                    if files_skipped > 0:
                        files_section += f"\\n*[{files_skipped} file(s) not shown due to context limit]*\\n\\n"
            else:
                # No budget - include all
                files_section = "## 📌 Focused Files (Always Visible)\\n\\n"
                files_section += "".join(block for _, block, _ in files_content)
                files_included = len(files_content)
        
        hud_parts.append(files_section)
        
        # File tree
        hud_parts.append("## 🗂️ File Tree\\n\\n")
        hud_parts.append("```\\n")
        hud_parts.append(tree_text)
        hud_parts.append("\\n```\\n\\n")
        
        # Stats summary
        try:
            stats = self.get_stats()
            hud_parts.append("## 📊 Context Stats\\n\\n")
            hud_parts.append(f"- Working history: {stats.get('working_entries', 0)} entries\\n")
            hud_parts.append(f"- Working tokens: {stats.get('working_tokens', 0):,}\\n")
            hud_parts.append(f"- Focused files: {files_included}")
            if files_skipped:
                hud_parts.append(f" ({files_skipped} truncated)")
            hud_parts.append("\\n")
            files = stats.get('files_read', [])
            if files:
                hud_parts.append(f"- Files in history: {', '.join(f'`{f}`' for f in files[:5])}\\n")
        except Exception:
            pass
        
        return "".join(hud_parts)
    
    def _preflight_check(self, context_messages: list) -> list:
        """
        Check context size and consolidate if needed.
        Returns potentially modified context_messages.
        Raises ContextBudgetExceeded if cannot fit within budget.
        """
        total_tokens = self._count_messages(context_messages)
        
        # If under budget, we're good
        if total_tokens <= self.context_budget:
            return context_messages
        
        # Over budget - try emergency consolidation
        consolidated = self._emergency_consolidate()
        
        if consolidated:
            # Rebuild context with compressed history
            new_context = [{"role": "system", "content": self.system_prompt}]
            hud_content = self._build_hud()
            if hud_content:
                new_context.append({"role": "system", "content": hud_content})
            new_context.extend(self.history_manager.get_context())
            
            new_total = self._count_messages(new_context)
            if new_total <= self.context_budget:
                return new_context
            
            # Still over - try again (recursive, but limited by entry count)
            if len(self.history_manager.working.entries) >= 6:
                return self._preflight_check(new_context)
        
        # Consolidation didn't help enough - try trimming HUD
        system_tokens = self.counter.count(self.system_prompt)
        history_tokens = self._count_messages(self.history_manager.get_context())
        
        # Available for HUD = budget - system - history - buffer for response
        available_for_hud = self.context_budget - system_tokens - history_tokens - 2000
        
        if available_for_hud > 1000:  # Need at least 1000 tokens for minimal HUD
            # Rebuild context with budget-limited HUD
            new_context = [{"role": "system", "content": self.system_prompt}]
            hud_content = self._build_hud_with_budget(max_tokens=available_for_hud)
            if hud_content:
                new_context.append({"role": "system", "content": hud_content})
            new_context.extend(self.history_manager.get_context())
            
            new_total = self._count_messages(new_context)
            if new_total <= self.context_budget:
                return new_context
        
        # Still over budget - raise error with helpful info
        raise ContextBudgetExceeded(
            f"Context size ({total_tokens:,} tokens) exceeds budget ({self.context_budget:,} tokens). "
            f"History: {history_tokens:,}, System: {system_tokens:,}. "
            f"Try: /unfocus to clear focused files, or start a new session."
        )

    def stream(self, message: str) -> Generator[Event, None, str]:
        """
        Send a message and yield events as they occur.
        Returns the final response text.
        """
        # Ensure model profile matches current model
        if not hasattr(self, '_last_resolved_model') or self._last_resolved_model != self.model:
            self._refresh_model_profile()

        # 0. Set this session as current BEFORE tools run
        # This ensures focus/unfocus tools operate on the correct session
        _store.set('session', 'current', self.history.session_id)
        
        # 0.1 Bind this agent's filesystem to the current thread
        # This prevents project switching in other tabs from affecting this agent
        fs = self.project.get_filesystem()
        set_thread_filesystem(fs)
        
        # 1. Add user message to both systems
        self.history.add_message("user", message)
        self.history.add_api_message({"role": "user", "content": message})
        self.history_manager.add_user(message)
        
        # 2. Trigger background compaction if needed (non-blocking)
        # This runs proactively at 70% capacity so we never hit the limit
        if self._background_compactor:
            self._background_compactor.check_and_compact()

        while True:
            # Build context from history manager
            context_messages = [{"role": "system", "content": self.system_prompt}]

            # Inject ephemeral HUD (not persisted to history)
            hud_content = self._build_hud()
            if hud_content:
                context_messages.append({"role": "system", "content": hud_content})

            context_messages.extend(self.history_manager.get_context())

            # Pre-flight check: ensure we're within budget
            context_messages = self._preflight_check(context_messages)

            kwargs = {
                "model": self.model,
                "messages": context_messages,
                "stream": True,
                "num_retries": 5, # Retry on 5xx errors (overloaded, service unavailable)
                "vertex_location": "global", # Ensure Gemini 3 Pro uses the global endpoint
            }
            # Apply configured LiteLLM parameters (timeouts, fallbacks, vertex_location, etc.)
            kwargs.update(self.litellm_params)
            
            if self.tool_schemas:
                kwargs["tools"] = self.tool_schemas

            # Try to make request, auto-repair if incomplete tool calls or context overflow
            try:
                response = litellm.completion(**kwargs)
            except ContextWindowExceededError as e:
                # Context too large - emergency consolidate and retry
                consolidated = self._emergency_consolidate()
                if not consolidated:
                    # Can't consolidate further, re-raise
                    raise ContextBudgetExceeded(
                        f"Context window exceeded and cannot consolidate further. "
                        f"Try: /unfocus to clear focused files, or start a new session. "
                        f"Original error: {e}"
                    )
                
                # Rebuild context with compressed history
                context_messages = [{"role": "system", "content": self.system_prompt}]
                hud_content = self._build_hud()
                if hud_content:
                    context_messages.append({"role": "system", "content": hud_content})
                context_messages.extend(self.history_manager.get_context())
                
                # Check if still over and try HUD trimming
                total_tokens = self._count_messages(context_messages)
                if total_tokens > self.context_budget:
                    system_tokens = self.counter.count(self.system_prompt)
                    history_tokens = self._count_messages(self.history_manager.get_context())
                    available_for_hud = self.context_budget - system_tokens - history_tokens - 2000
                    
                    if available_for_hud > 1000:
                        context_messages = [{"role": "system", "content": self.system_prompt}]
                        hud_content = self._build_hud_with_budget(max_tokens=available_for_hud)
                        if hud_content:
                            context_messages.append({"role": "system", "content": hud_content})
                        context_messages.extend(self.history_manager.get_context())
                
                kwargs["messages"] = context_messages
                # Retry the request
                response = litellm.completion(**kwargs)
            except Exception as e:
                # Check if this is the "tool_use without tool_result" error
                error_str = str(e)
                if "tool_use" in error_str and "tool_result" in error_str:
                    # Auto-repair: cleanup incomplete tool calls and retry
                    self.cleanup_incomplete_tool_calls()
                    # Rebuild context with fixed history
                    context_messages = [{"role": "system", "content": self.system_prompt}]
                    if hud_content:
                        context_messages.append({"role": "system", "content": hud_content})
                    context_messages.extend(self.history_manager.get_context())
                    kwargs["messages"] = context_messages
                    # Retry the request
                    response = litellm.completion(**kwargs)
                elif "prompt is too long" in error_str or "context" in error_str.lower() and "exceed" in error_str.lower():
                    # Catch other context-related errors (different providers format differently)
                    consolidated = self._emergency_consolidate()
                    if not consolidated:
                        raise
                    
                    # Rebuild and retry
                    context_messages = [{"role": "system", "content": self.system_prompt}]
                    hud_content = self._build_hud()
                    if hud_content:
                        context_messages.append({"role": "system", "content": hud_content})
                    context_messages.extend(self.history_manager.get_context())
                    kwargs["messages"] = context_messages
                    response = litellm.completion(**kwargs)
                else:
                    # Different error, re-raise
                    raise

            full_response = ""
            tool_calls = []

            for chunk in response:
                delta = chunk.choices[0].delta

                if delta.content:
                    full_response += delta.content
                    yield TextDelta(content=delta.content)

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index >= len(tool_calls):
                            tool_calls.append({"id": "", "name": "", "arguments": ""})
                        if tc.id:
                            tool_calls[tc.index]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls[tc.index]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls[tc.index]["arguments"] += tc.function.arguments
                                # Emit progress event for tool argument streaming
                                yield ToolProgress(
                                    name=tool_calls[tc.index]["name"],
                                    index=tc.index,
                                    bytes_received=len(tool_calls[tc.index]["arguments"])
                                )

            # No tool calls - done
            if not tool_calls:
                assistant_msg = {"role": "assistant", "content": full_response}

                # Legacy persistence
                self.history.add_message("assistant", full_response)
                self.history.add_api_message(assistant_msg)

                # New history manager
                self.history_manager.add_assistant(content=full_response)

                yield TextDone(content=full_response)
                return full_response

            # Handle tool calls
            formatted_tool_calls = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in tool_calls
            ]

            assistant_tool_msg = {
                "role": "assistant",
                "content": full_response or None,
                "tool_calls": formatted_tool_calls,
            }

            # Legacy persistence
            self.history.add_api_message(assistant_tool_msg)

            # New history manager
            self.history_manager.add_assistant(
                content=full_response or None,
                tool_calls=formatted_tool_calls,
            )

            for tc in tool_calls:
                func_name = tc["name"]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                yield ToolStart(name=func_name, arguments=args)

                if func_name in self.tool_functions:
                    try:
                        result = self.tool_functions[func_name](**args)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Unknown tool: {func_name}"

                yield ToolDone(name=func_name, arguments=args, result=str(result))

                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result),
                }

                # Legacy persistence
                self.history.add_api_message(tool_result_msg)
                self.history.add_tool_call(func_name, args, str(result))

                # New history manager - extract file_path if it's a file operation
                file_path = args.get("file_path") or args.get("path")
                self.history_manager.add_tool_result(
                    tool_call_id=tc["id"],
                    content=str(result),
                    tool_name=func_name,
                    file_path=file_path,
                    tool_args=args,
                )

    def cleanup_incomplete_tool_calls(self):
        """
        Clean up incomplete tool calls (e.g., from cancellation).
        - Removes orphan tool_results not immediately after their tool_use
        - Inserts placeholder results for missing tool_results
        """
        from datetime import datetime
        from .context_management.ground_truth import Entry
        import uuid

        entries = self.history_manager.working.entries
        if not entries:
            return

        # Build new entries list:
        # - Keep user/assistant messages
        # - For tool results: only keep if immediately after assistant with matching tool_use
        # - Add placeholders for missing results
        new_entries = []
        needs_save = False

        i = 0
        while i < len(entries):
            e = entries[i]

            # Skip orphan tool results - they'll be handled when we process their assistant msg
            # or dropped if they're truly orphaned
            if e.role == "tool":
                needs_save = True  # Orphan tool result found, will be removed
                i += 1
                continue

            # Add non-tool entry
            new_entries.append(e)

            # If assistant with tool_calls, process the tool results
            if e.role == "assistant" and e.tool_calls:
                called_ids = {tc["id"] for tc in e.tool_calls}

                # Scan ahead for tool results (they should be immediately after)
                j = i + 1
                found_result_ids = set()

                # First, collect results that immediately follow
                while j < len(entries) and entries[j].role == "tool":
                    tid = entries[j].tool_call_id
                    if tid in called_ids and tid not in found_result_ids:
                        new_entries.append(entries[j])
                        found_result_ids.add(tid)
                    else:
                        # Either orphan or duplicate - skip
                        needs_save = True
                    j += 1

                # Also search rest of history for orphaned results belonging to this call
                for k in range(j, len(entries)):
                    if entries[k].role == "tool":
                        tid = entries[k].tool_call_id
                        if tid in called_ids and tid not in found_result_ids:
                            # Found orphan that belongs here - adopt it
                            new_entries.append(entries[k])
                            found_result_ids.add(tid)
                            needs_save = True

                # Add placeholders for any still missing
                missing = called_ids - found_result_ids
                if missing:
                    needs_save = True
                    for call_id in missing:
                        placeholder = Entry(
                            id=str(uuid.uuid4()),
                            timestamp=datetime.now().isoformat(),
                            message={
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": "[Cancelled by user]"
                            },
                            meta={"tool_name": "unknown", "cleanup": True}
                        )
                        new_entries.append(placeholder)
                        self.history_manager.ground_truth.entries.append(placeholder)
                        self.history_manager.ground_truth._index_entry(placeholder)

                i = j
            else:
                i += 1

        if needs_save:
            self.history_manager.working.entries = new_entries
            self.history_manager._auto_save()

    def load_session(self, session_id: str) -> bool:
        """
        Load a previous session by ID.
        Returns True if successful, False if session not found.
        """
        if not self.history.load_session(session_id):
            return False

        # Load the new history manager
        history_path = get_history_path(session_id)
        if history_path.exists():
            self.history_manager = HistoryManager.load(history_path)
        else:
            # Migrate from legacy format
            self.history_manager = HistoryManager(storage_path=history_path)
            self._migrate_legacy_history()

        # Reset default projection - smart tool retention
        self.history_manager.projection = smart_tool_retention(
            max_file_reads=5,
            bash_truncate=10000,
        )

        # Clean up any incomplete tool calls from previous interruptions
        self.cleanup_incomplete_tool_calls()
        
        # Reinitialize background compactor with new history manager
        self._init_background_compactor()
        
        # NOTE: We intentionally do NOT consolidate on load anymore.
        # Consolidation only happens proactively via background compaction
        # or as emergency fallback in _preflight_check.

        # Update current session in Signella
        _store.set('session', 'current', session_id)

        return True

    def _migrate_legacy_history(self):
        """Migrate legacy api_messages to the new history manager."""
        for msg in self.history.api_messages:
            role = msg.get("role")
            if role == "user":
                self.history_manager.add_user(msg.get("content", ""))
            elif role == "assistant":
                self.history_manager.add_assistant(
                    content=msg.get("content"),
                    tool_calls=msg.get("tool_calls"),
                )
            elif role == "tool":
                self.history_manager.add_tool_result(
                    tool_call_id=msg.get("tool_call_id", ""),
                    content=msg.get("content", ""),
                )

    def new_session(self):
        """Start a fresh session."""
        self.history = SessionHistory()
        self.history.metadata["model"] = self.model

        history_path = get_history_path(self.history.session_id)
        self.history_manager = HistoryManager(storage_path=history_path)
        # Set default projection - smart tool retention
        self.history_manager.projection = smart_tool_retention(
            max_file_reads=5,
            bash_truncate=10000,
        )
        
        # Update current session in Signella
        _store.set('session', 'current', self.history.session_id)

    def ask(self, message: str) -> str:
        """Simple blocking call that returns final response. Consumes all events."""
        result = ""
        for event in self.stream(message):
            if event.type == "text_done":
                result = event.content
        return result

    def get_stats(self) -> dict:
        """Get history statistics."""
        return self.history_manager.stats()

    def get_context_stats(self) -> dict:
        """
        Get detailed token breakdown for context visualization.
        Returns dict with token counts for each component.
        """
        # Ensure model profile matches current model
        if not hasattr(self, '_last_resolved_model') or self._last_resolved_model != self.model:
            self._refresh_model_profile()

        from .filesystem import get_current_filesystem, get_project_root
        
        session_id = self.history.session_id
        focused_files = list(_store.get('focus', session_id, 'files', default=[]) or [])
        
        # Count system prompt
        system_tokens = self.counter.count(self.system_prompt)
        
        # Count history (excluding gists)
        history_tokens = 0
        gist_tokens = 0
        gist_count = 0
        for entry in self.history_manager.working.entries:
            entry_tokens = self.counter.count_message(entry.message)
            if entry.is_gist:
                gist_tokens += entry_tokens
                gist_count += 1
            else:
                history_tokens += entry_tokens
        
        # Count focused files using filesystem abstraction
        focus_tokens = 0
        fs = get_current_filesystem()
        project_root = str(get_project_root())
        
        for abs_path in focused_files:
            try:
                content = fs.read(abs_path)
                # Calculate relative path
                if abs_path.startswith(project_root):
                    rel_path = abs_path[len(project_root):].lstrip('/')
                else:
                    rel_path = abs_path
                # Approximate the formatted block size
                block = f"### {rel_path}\\n```\\n# START OF FILE: {rel_path}\\n{content}\\n# END OF FILE: {rel_path}\\n```\\n"
                focus_tokens += self.counter.count(block)
            except Exception:
                focus_tokens += 50  # Estimate for error message
        
        # File tree estimate (~500-2000 tokens depending on project size)
        tree_text = get_file_tree_for_project()
        tree_tokens = self.counter.count(tree_text) + 50  # Plus markdown wrapper
        
        # Total and budget
        total_tokens = system_tokens + history_tokens + gist_tokens + focus_tokens + tree_tokens
        budget = self.context_budget
        threshold = int(budget * 0.7)  # Consolidation threshold
        
        return {
            "system": system_tokens,
            "history": history_tokens,
            "gists": gist_tokens,
            "gist_count": gist_count,
            "focus": focus_tokens,
            "focus_count": len(focused_files),
            "tree": tree_tokens,
            "total": total_tokens,
            "budget": budget,
            "threshold": threshold,
            "model": self.model_profile.name,
            "context_window": self.model_profile.context_window,
        }
    def _build_hud(self) -> str:
        """Build ephemeral HUD content (not persisted)."""
        from .filesystem import get_current_filesystem, get_project_root
        
        # Get focused files from Signella (session-aware)
        session_id = self.history.session_id
        focused_files = set(_store.get('focus', session_id, 'files', default=[]) or [])

        hud = "# Project Context (Ephemeral - Not Stored)\\n\\n"

        # Focused files section (most important - comes first)
        if focused_files:
            hud += "## 📌 Focused Files (Always Visible)\\n\\n"
            fs = get_current_filesystem()
            project_root = str(get_project_root())
            
            for abs_path in sorted(focused_files):
                try:
                    # Calculate relative path from project root
                    if abs_path.startswith(project_root):
                        rel_path = abs_path[len(project_root):].lstrip('/')
                    else:
                        rel_path = abs_path
                    
                    # Get file extension for syntax highlighting
                    ext = rel_path.split('.')[-1] if '.' in rel_path else ''

                    # Read current content using filesystem abstraction
                    content = fs.read(abs_path)

                    hud += f"### {rel_path}\\n\\n"
                    hud += f"```{ext}\\n"
                    hud += f"# START OF FILE: {rel_path}\\n"
                    hud += content
                    hud += f"\\n# END OF FILE: {rel_path}\\n"
                    hud += "```\\n\\n"
                except Exception as e:
                    hud += f"### {abs_path}\\n\\nError reading: {e}\\n\\n"

        # File tree
        tree_text = get_file_tree_for_project()

        hud += "## 🗂️ File Tree\\n\\n"
        hud += "```\\n"
        hud += tree_text
        hud += "\\n```\\n\\n"

        # Project Guidance (CLAUDE.md)
        try:
            fs = get_current_filesystem()
            if fs.exists("CLAUDE.md"):
                guidance = fs.read("CLAUDE.md")
                hud += "## 📜 Project Guidance (CLAUDE.md)\\n\\n"
                hud += guidance + "\\n\\n"
        except Exception:
            pass

        # Add stats summary
        try:
            stats = self.get_stats()
            hud += "## 📊 Context Stats\\n\\n"
            hud += f"- Working history: {stats.get('working_entries', 0)} entries\\n"
            hud += f"- Working tokens: {stats.get('working_tokens', 0):,}\\n"
            hud += f"- Focused files: {len(focused_files)}\\n"
            files = stats.get('files_read', [])
            if files:
                hud += f"- Files in history: {', '.join(f'`{f}`' for f in files[:5])}\\n"
        except Exception:
            pass

        return hud
