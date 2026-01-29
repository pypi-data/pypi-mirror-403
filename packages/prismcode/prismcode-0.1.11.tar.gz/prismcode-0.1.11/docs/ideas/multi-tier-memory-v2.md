# Idea: Multi-Tiered Cognitive Architecture

## Overview
This document outlines a strategy to move beyond chat-driven development toward **Environment-Driven Development**. By expanding the Focus System into specialized "Cognitive Zones," we can give the agent a structured working memory that mimics human executive function (planning, scratchpad, and long-term learning).

---

## 1. The Executive Plane (Objective System)
Currently, plans are just markdown files. We can formalize this into a persistent "Mission Control" in the HUD.

*   **Mechanism**: A specialized `PLAN.md` or `current_objective.json` file.
*   **Agent Interaction**: A tool like `update_plan(step_id, status)` that allows the agent to check off tasks.
*   **HUD Rendering**: Instead of just raw text, the HUD displays a "Current Progress" dashboard showing:
    *   The primary goal.
    *   Completed vs. Remaining steps.
    *   Current blockers.
*   **Benefit**: Eliminates "goal drift" during long refactors.

## 2. The Semantic Scratchpad (Working Memory)
Humans use sticky notes for "non-code" thoughts that don't belong in comments.

*   **Mechanism**: A `.mobius/scratchpad.md` file that is automatically focused.
*   **Agent Interaction**: The agent uses `edit_file` to jot down edge cases, reminders, or "notes to future self."
*   **HUD Rendering**: A dedicated "Scratchpad" section in the HUD preamble.
*   **Benefit**: Persistent reminders that survive turns. If the agent identifies a bug in File A while working on File B, it jots it down and sees it every turn until it's addressed.

## 3. Project-Specific Intelligence (Learning)
A way to capture "lessons learned" about a specific codebase so they aren't lost when history is purged.

*   **Mechanism**: A `MEMORIES.md` or `.mobius/knowledge_base.md` file.
*   **Agent Interaction**: A `learn("fact")` tool that appends architectural insights to this file.
    *   *Example*: "Learned that the SocketIO server requires the `client_id` to be in the session cookie."
*   **Focus Logic**: This file is permanently focused for the project.
*   **Benefit**: The agent builds a "manual" for the project. New sessions start with the accumulated wisdom of previous ones.

## 4. Multi-Tiered HUD Injection (Contextual Zoning)
To save tokens while maximizing awareness, the Focus System can be split into "Visibility Zones":

| Zone | Priority | Detail Level | Examples |
| :--- | :--- | :--- | :--- |
| **Active Zone** | Highest | Full Code | The file(s) being currently edited. |
| **Logic Zone** | Medium | Skeleton/Signatures | Dependencies (Prism-derived) to show API surfaces without bloating tokens. |
| **Strategy Zone** | Constant | Summary | The Plan, Scratchpad, and Project Memories. |

## 5. UI Integration
On the web workspace, these "Zones" could be rendered as separate cards or tabs:
*   **Tab 1**: Chat (Conversation)
*   **Tab 2**: Focus Deps (The Prism Tree)
*   **Tab 3**: Plan (The Task List)
*   **Tab 4**: Scratchpad (The "Notes to Self")

---

## Summary of the "Human" Approach
1.  **Working Memory** = Focused Files (What I'm looking at).
2.  **Procedural Memory** = The Plan (What I'm doing).
3.  **Long-Term Memory** = Memories File (What I've learned).

By categorizing the HUD into these functional zones, we move from the LLM being a "Chatbot" to the LLM having a "Professional Workspace."
