# Agent HUD

## Stats

- **Session ID**: 20260123...
- **Model**: gpt-4o-mini
- **Uptime**: 0s
- **Ground Truth**: 0 entries
- **Working History**: 0 entries
- **Gists**: 0
- **GT Tokens**: 0
- **Working Tokens**: 0

## Project Tree

```
mobius/
├── cli/
│   ├── __init__.py
│   ├── main.py
│   └── tui.py
├── core/
│   ├── context_management/
│   │   ├── strategies/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── rolling_gist.py
│   │   │   └── test_strategies.py
│   │   ├── __init__.py
│   │   ├── ground_truth.py
│   │   ├── query.py
│   │   ├── test_context_management.py
│   │   └── tokens.py
│   ├── legacy/
│   │   ├── context.py
│   │   └── turns.py
│   ├── __init__.py
│   ├── agent.py
│   ├── code_edit.py
│   ├── history.py
│   └── signella.py
├── docs/
│   ├── features_to_add/
│   │   └── archetecture.md
│   └── ideas/
│       ├── history_idea.md
│       ├── mobius_concept.md
│       └── multi-tier-memory.md
├── fancy/
│   ├── __init__.py
│   ├── agent_runner.py
│   ├── app.py
│   ├── autocomplete.py
│   ├── chat_renderer.py
│   ├── commands.py
│   ├── css.py
│   ├── diff.py
│   ├── scroll.py
│   └── session_picker.py
├── scripts/
│   ├── __init__.py
│   └── migrate_python.py
├── static/
│   ├── css/
│   │   ├── highlight.css
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
├── themes/
│   └── __init__.py
├── tools/
│   ├── __init__.py
│   └── tools.py
├── .gitignore
├── .python-version
├── CLAUDE.md
├── config.py
├── GEMINI.md
├── pyproject.toml
├── python_classes_example.py
├── README.md
├── requirements.txt
├── run_47.py
├── run_fancy.py
├── run_mobius.py
├── run_tui.py
├── run_web.py
├── settings.json
├── settings.py
└── uv.lock
```

## Context Management

Active Projections:
- dedupe_file_reads
- keep_recent_tool_results(30)

## Context Usage

## Working History Messages

