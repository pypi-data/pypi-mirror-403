# Publishing PrismCode to PyPI

## Quick Reference for AI Agents

This guide shows how to publish a new version of `prismcode` to PyPI.

---

## Prerequisites

### 1. Get PyPI Token

**Where to find it:**
- Go to https://pypi.org/manage/account/token/
- Login with account credentials (ask human for access)
- Create a new API token with scope: "Entire account" or "Project: prismcode"
- Copy the token (starts with `pypi-`)

**Store it securely:**
```bash
# Option 1: Add to .env (recommended - already in use for this project)
echo "PYPI_TOKEN=pypi-your-token-here" >> .env
echo "PYPI_USERNAME=__token__" >> .env

# Option 2: Export as environment variable (temporary)
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here

# Option 3: Add to ~/.pypirc (persistent)
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-your-token-here
EOF
chmod 600 ~/.pypirc
```

**Note:** The project `.env` already has `PYPI_TOKEN` and `PYPI_USERNAME` configured.

### 2. Install Publishing Tools

```bash
pip install build twine
```

---

## Publishing Steps

### 1. Update Version Number

Edit `pyproject.toml`:
```toml
[project]
name = "prismcode"
version = "0.1.X"  # Increment this
```

**Versioning guidelines:**
- `0.1.X` → Bug fixes, minor changes (patch)
- `0.X.0` → New features, backwards compatible (minor)
- `X.0.0` → Breaking changes (major)

### 2. Update Changelog (Optional but Recommended)

Create/update `CHANGELOG.md`:
```markdown
## [0.1.X] - 2025-01-XX

### Added
- New workspace UI as default interface

### Fixed
- Description of bug fixes

### Changed
- What changed from last version
```

### 3. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 4. Build Distribution

```bash
python -m build
```

This creates:
- `dist/prismcode-0.1.X-py3-none-any.whl` (wheel)
- `dist/prismcode-0.1.X.tar.gz` (source)

### 5. Test Upload (Optional)

Test on TestPyPI first:
```bash
twine upload --repository testpypi dist/*
```

Then test install:
```bash
pip install --index-url https://test.pypi.org/simple/ prismcode
```

### 6. Upload to PyPI

**Recommended method (most reliable):**
```bash
source .env && TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" twine upload dist/*
```

**Alternative - direct token:**
```bash
TWINE_USERNAME=__token__ TWINE_PASSWORD='pypi-your-token-here' twine upload dist/*
```

You'll see:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading prismcode-0.1.X-py3-none-any.whl
Uploading prismcode-0.1.X.tar.gz
View at: https://pypi.org/project/prismcode/0.1.X/
```

### 7. Verify

Visit https://pypi.org/project/prismcode/ to confirm the new version is live.

Test install:
```bash
pip install --upgrade prismcode
```

---

## Troubleshooting

### "File already exists"
You can't re-upload the same version. Increment the version number.

### "Invalid or non-existent authentication"
Check your PyPI token is correct and has the right scope.

### "Package name already taken"
The package name `prismcode` is registered. Only the owner can publish.

### Missing files in package
Check `[tool.hatch.build.targets.wheel]` in `pyproject.toml`:
```toml
packages = ["cli", "core", "tools", "prism", "HUD", "static", "templates", "themes", "routes"]
```

### OpenAI env var conflicts (litellm errors)
If you have `OPENAI_API_KEY`/`OPENAI_BASE_URL` pointing to non-OpenAI endpoints (e.g., Cerebras), litellm will fail. The code in `run_web.py` auto-cleans these at startup, but if issues persist, unset them:
```bash
unset OPENAI_API_KEY OPENAI_BASE_URL OPENAI_API_BASE OPENAI_MODEL
```

---

## Quick Commands Summary

```bash
# 1. Update version in pyproject.toml

# 2. Clean old builds
rm -rf dist/ build/ *.egg-info

# 3. Build (use system Python, not venv)
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m build

# 4. Upload (using .env)
source .env && TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_TOKEN" twine upload dist/*

# 5. Test
pip install --upgrade prismcode
prismweb  # Should start server on port 5000 with workspace UI
```

**Note:** Use system Python for building (not venv Python) to avoid module import issues.

---

## Current Package Info

- **Package name:** `prismcode`
- **PyPI URL:** https://pypi.org/project/prismcode/
- **Repository:** https://github.com/yourusername/prismcode
- **Entry points:** 
  - `prism` → CLI interface
  - `prismweb` → Web interface (default: workspace UI on port 5000)

---

## Notes for Future Versions

### What's Included in the Package

Based on `pyproject.toml`:
- Core modules: `cli/`, `core/`, `tools/`, `prism/`, `HUD/`, `routes/`
- Web UI: `static/`, `templates/`, `themes/`
- Entry files: `run_web.py`, `config.py`, `settings.py`

### Dependency Pinning

Dependencies in `pyproject.toml` are pinned to exact versions from `uv.lock` to ensure `pip install prismcode` behaves identically to local `uv run`. When updating dependencies:
1. Update in local dev with `uv add`
2. Copy exact versions from `uv.lock` to `pyproject.toml`

### What's NOT Included

- Development files: `docs/`, `mobius_plans/`, test files
- Local config: `.env`, `settings.json`
- Build artifacts: `dist/`, `*.egg-info`

### File Structure After Install

```
site-packages/
  prismcode-0.1.X.dist-info/
  cli/
  core/
  tools/
  prism/
  HUD/
  routes/
  static/
  templates/
  themes/
  run_web.py
  config.py
  settings.py
```

---

## Version History

- **0.1.12** - Latest stable
- **0.1.7** - Fixed prism tools auto-scan for pip install
- **0.1.6** - Pinned exact dependency versions from uv.lock
- **0.1.5** - Auto-clean conflicting OpenAI env vars at runtime
- **0.1.4** - Added missing `routes` package
- **0.1.2** - Workspace UI as default, legacy UI at `/legacy`
- **0.1.1** - Added `prismweb` command
- **0.1.0** - Initial release
