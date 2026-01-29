#!/usr/bin/env python3
"""
Generate titles for chat sessions using the configured LLM.
Handles both new (.gt.json) and legacy (.json) formats.

Usage:
    python -m scripts.generate_titles           # Generate missing titles
    python -m scripts.generate_titles --force   # Regenerate all titles
    python -m scripts.generate_titles --dry-run # Show what would be done
"""
import json
import argparse
from pathlib import Path

import litellm
from dotenv import load_dotenv

from core.history import get_histories_dir, list_sessions, get_session_title, set_session_title
from config import AGENT_CONFIG

load_dotenv()


def extract_conversation_preview(session_id: str, max_messages: int = 8) -> tuple[str, int]:
    """
    Extract first few exchanges for title generation.
    Handles both new and legacy formats.
    
    Returns:
        Tuple of (preview_text, message_count)
    """
    histories_dir = get_histories_dir()
    preview_parts = []
    msg_count = 0
    
    # Try new format first (.gt.json)
    gt_path = histories_dir / f"{session_id}.gt.json"
    if gt_path.exists():
        try:
            data = json.loads(gt_path.read_text())
            working = data.get("working", {})
            entries = working.get("entries", [])
            msg_count = len(entries)
            
            count = 0
            for entry in entries:
                if count >= max_messages:
                    break
                msg = entry.get("message", {})
                role = msg.get("role")
                content = msg.get("content", "")
                
                # Clean up Gist markers
                if "[Conversation gist]" in content:
                    content = content.replace("[Conversation gist]", "").strip()
                if "Memory Archive:" in content:
                    lines = content.split('\n')
                    content = '\n'.join([l for l in lines if not l.startswith("Memory Archive")])
                content = content.strip()

                if role == "user" and content:
                    preview_parts.append(f"User: {content[:300]}")
                    count += 1
                elif role == "assistant" and content:
                    preview_parts.append(f"Assistant: {content[:300]}")
                    count += 1
            
            if preview_parts:
                return "\n".join(preview_parts), msg_count
        except Exception:
            pass
    
    # Fall back to legacy format (.json)
    legacy_path = histories_dir / f"{session_id}.json"
    if legacy_path.exists():
        try:
            data = json.loads(legacy_path.read_text())
            messages = data.get("messages", [])
            msg_count = len(messages)
            
            count = 0
            for msg in messages:
                if count >= max_messages:
                    break
                role = msg.get("role")
                content = msg.get("content", "")

                # Clean up Gist markers
                if "[Conversation gist]" in content:
                    content = content.replace("[Conversation gist]", "").strip()
                
                if role == "user" and content:
                    preview_parts.append(f"User: {content[:300]}")
                    count += 1
                elif role == "assistant" and content:
                    preview_parts.append(f"Assistant: {content[:300]}")
                    count += 1
        except Exception:
            pass
    
    return "\n".join(preview_parts), msg_count


def generate_title(conversation_preview: str, model: str) -> str:
    """Generate a short title for the conversation."""
    response = litellm.completion(
        model=model,
        messages=[
            {
                "role": "user", 
                "content": f"""Summarize this conversation in 2-4 words. Be specific and unique. 
No generic titles like "Code Help" or "Python Script".
No quotes.

Conversation:
{conversation_preview}

Title:"""
            }
        ],
        max_tokens=20,
        temperature=0.3,
    )
    title = response.choices[0].message.content.strip()
    # Clean up: take first line, remove quotes and markdown
    title = title.split('\n')[0]
    title = title.strip('"\'')
    title = title.lstrip('#').strip()
    title = title.strip('*')
    return title[:60]


def main():
    parser = argparse.ArgumentParser(description="Generate titles for chat sessions")
    parser.add_argument("--force", "-f", action="store_true", help="Regenerate titles even if they exist")
    parser.add_argument("--limit", "-n", type=int, default=50, help="Limit number of sessions to process (default: 50)")
    parser.add_argument("--session", "-s", type=str, help="Process a specific session ID")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Show what would be processed without making changes")
    parser.add_argument("--model", "-m", type=str, help="Override model to use")
    args = parser.parse_args()
    
    model = args.model or AGENT_CONFIG["model"]
    print(f"Using model: {model}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()
    
    # Get sessions to process
    if args.session:
        # Single session mode
        sessions = [{"id": args.session, "title": get_session_title(args.session)}]
    else:
        sessions = list_sessions(limit=args.limit)
    
    print(f"Found {len(sessions)} sessions to check")
    print()
    
    processed = 0
    skipped = 0
    errors = 0
    
    for session in sessions:
        session_id = session["id"]
        existing_title = session.get("title") or get_session_title(session_id)
        
        # Skip if already has title (unless force)
        if existing_title and not args.force:
            print(f"  [SKIP] {session_id[:16]}... has title: \"{existing_title}\"")
            skipped += 1
            continue
        
        # Get conversation preview
        preview, msg_count = extract_conversation_preview(session_id)
        
        if not preview:
            print(f"  [SKIP] {session_id[:16]}... no content")
            skipped += 1
            continue
        
        if msg_count < 2:
            print(f"  [SKIP] {session_id[:16]}... only {msg_count} messages")
            skipped += 1
            continue
        
        if args.dry_run:
            print(f"  [WOULD] {session_id[:16]}... generate title (currently: {existing_title or 'None'})")
            processed += 1
            continue
        
        # Generate and save title
        try:
            title = generate_title(preview, model)
            if title:
                set_session_title(session_id, title)
                print(f"  [DONE] {session_id[:16]}... → \"{title}\"")
                processed += 1
            else:
                print(f"  [FAIL] {session_id[:16]}... empty title returned")
                errors += 1
        except Exception as e:
            print(f"  [ERROR] {session_id[:16]}... {e}")
            errors += 1
    
    print()
    print(f"Summary: {processed} {'would be ' if args.dry_run else ''}generated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
