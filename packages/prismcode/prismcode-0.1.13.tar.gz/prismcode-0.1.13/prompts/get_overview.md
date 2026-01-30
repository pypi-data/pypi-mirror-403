# Project Overview Generator Prompt

You are analyzing a codebase snapshot to create a high-level architectural map for AI agents. Your output should help an AI understand the project quickly without reading every file.

## Your Task

Generate a structured overview with these sections:

### 1. Core Concept (2-3 sentences)
What does this project do? What problem does it solve? Explain it like you're describing it to someone who's never seen the code.

### 2. Architecture Summary
Identify the major layers/components. Most projects have some separation like:
- Core logic / engine
- API / interface layer  
- Frontend / UI
- Utilities / helpers

Name these layers based on what you actually see in the code.

### 3. File Reference Tables

For each architectural layer, create a table:

| File | Purpose |
|------|---------|
| `relative/path/to/file.py` | One-line description of responsibility |

Guidelines:
- Use relative paths from project root
- Describe what the file does - if it has multiple responsibilities, list them briefly
- Group files by their layer/component

### 4. Data Flow

Describe how data moves through the system:
1. Where does input come from?
2. What transforms/processes it?
3. Where does output go?

Use arrows or numbered steps. Example:
```
User Request → API Route → Core Logic → Database → Response
```

### 5. Key Concepts

Define any project-specific terminology or patterns that aren't obvious from file names. Things like:
- Custom data structures
- Domain-specific terms
- Non-obvious relationships between components
- Configuration patterns

---

## Formatting Rules

- Use markdown tables for file listings
- Keep descriptions concrete, not vague ("Handles user authentication" not "Does stuff with users")
- If you're unsure what a file does, say "Appears to..." rather than guessing confidently
- Don't document test files, configs, or boilerplate unless they're unusual
- Prioritize files that would confuse someone new to the codebase

## What NOT to Include

- Line-by-line code explanations
- Implementation details (algorithms, specific functions)
- Setup/installation instructions
- Dependencies list (package.json, requirements.txt contents)
- Standard framework boilerplate explanations
