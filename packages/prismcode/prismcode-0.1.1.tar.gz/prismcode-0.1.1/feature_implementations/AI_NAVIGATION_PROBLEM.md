# The AI Navigation Problem

## What AI Assistants See by Default

When you start a coding session, AI assistants like Claude only see:
- Folder structure
- File names

That's it. No content. No context about what each file does.

## The Inefficiency

To understand your codebase, the AI must:

1. **Guess** which files might be relevant based on names alone
2. **Read entire files** to determine if they're actually useful
3. **Burn tokens** on files that turn out to be irrelevant
4. **Repeat** until enough context is gathered

This is expensive, slow, and often misses important files while reading unnecessary ones.

## The Solution: A Semantic Map

zdeps2 builds a pre-generated map of your codebase:

```
auth_middleware.py → "Validates JWT tokens and enforces role permissions"
database.py        → "PostgreSQL connection pool and query helpers"
cache.py           → "Redis wrapper for session storage"
```

One sentence per file. Generated once, reused forever.

## How It Changes the Workflow

**Before (current):**
```
AI sees: auth_middleware.py (120 lines)
AI thinks: "Might be relevant? Let me read all 120 lines to find out..."
Result: Wasted tokens if irrelevant
```

**After (with zdeps2):**
```
AI sees: auth_middleware.py → "Validates JWT tokens"
AI thinks: "Not working on auth, skip it"
Result: Zero tokens wasted
```

## The Payoff

- AI reads only what matters
- Faster responses
- Lower costs
- Better accuracy (finds the right files, not just guesses)

The structural map (what connects to what) + the semantic map (what each file does) = an AI that navigates your codebase like someone who's worked on it for months.
