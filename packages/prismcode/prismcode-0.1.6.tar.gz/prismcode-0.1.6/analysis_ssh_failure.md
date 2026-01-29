# Analysis: Why SSH Project uses Local Tools?

## 1. Trace: Agent Initialization
In `run_web.py`, we see:
```python
agent = Agent(..., project=project, ...)
```

In `core/agent.py`:
```python
class Agent:
    def __init__(self, ..., project=None, ...):
        # ...
        self.project = project
        if self.project:
            # DOES IT DO ANYTHING WITH THIS?
            pass 
```

## 2. Trace: Tool Execution
In `tools/tools.py`:
```python
def ls(path):
    return get_current_filesystem().ls(path)
```

In `core/filesystem.py`:
```python
def get_current_filesystem():
    session_id = _store.get('session', 'current')
    project_id = _store.get('session', session_id, 'project_id')
    # ... logic to get FS for project_id ...
```

## 3. The Missing Link?
I need to check `core/agent.py` to see if it **registers** the project ID in `_store` (Signella) during `__init__`.

If `Agent.__init__` sets `self.project` but *doesn't* update `_store` with the mapping `session_id -> project_id`, then `get_current_filesystem()` will fail to find the project ID for the session.

If it fails to find a project ID, what does `get_current_filesystem()` default to? Likely `Local`.

## 4. Check `core/project.py`
Does the SSH project class actually implement `get_filesystem()` correctly?

## 5. Check `core/filesystem.py`
Does `SSHFileSystem` exist and work?

I will read `core/agent.py` very carefully to see the `__init__` logic.
I will read `core/filesystem.py` to see the resolution logic.
