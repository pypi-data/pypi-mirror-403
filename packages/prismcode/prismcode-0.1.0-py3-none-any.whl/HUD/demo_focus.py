#!/usr/bin/env python3
"""
Demo: Focus tool showing files in HUD instead of conversation history.
"""

from tools.tools import focus, unfocus, list_focused
from core.agent import Agent

# Create agent
agent = Agent(
    system_prompt="You are a helpful assistant.",
    tools=[],
    model="gpt-4o-mini",
)

print("=== Focus Tool Demo ===\n")

print("1. Initially, no files focused:")
print(list_focused())
print()

print("2. Focus on config.py:")
print(focus("config.py"))
print()

print("3. Focus on tools/tools.py:")
print(focus("tools/tools.py"))
print()

print("4. List focused files:")
print(list_focused())
print()

print("5. HUD now shows these files (preview):")
hud = agent._build_hud()
lines = hud.split("\n")
for line in lines[:50]:  # First 50 lines
    print(line)

print("\n... (truncated)")
print()

print("6. Unfocus config.py:")
print(unfocus("config.py"))
print()

print("7. Clear all:")
print(unfocus())
print()

print("✓ Demo complete!")
print()
print("Key points:")
print("- focus() adds files to HUD (not conversation history)")
print("- Files auto-update on each turn (always shows latest content)")
print("- Perfect for iterating on files without filling context")
print("- Use unfocus() to remove or unfocus(None) to clear all")
