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
# Option 1: Export as environment variable (temporary)
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here

# Option 2: Add to ~/.pypirc (persistent)
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-your-token-here
EOF
chmod 600 ~/.pypirc
```

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

```bash
twine upload dist/*
```

You'll see:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading prismcode-0.1.X-py3-none-any.whl
Uploading prismcode-0.1.X.tar.gz
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
packages = ["cli", "core", "tools", "prism", "HUD", "static", "templates", "themes"]
```

---

## Quick Commands Summary

```bash
# 1. Update version in pyproject.toml
# 2. Clean old builds
rm -rf dist/ build/ *.egg-info

# 3. Build
python -m build

# 4. Upload
twine upload dist/*

# 5. Test
pip install --upgrade prismcode
prismweb  # Should start server on port 5000
```

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
- Core modules: `cli/`, `core/`, `tools/`, `prism/`, `HUD/`
- Web UI: `static/`, `templates/`, `themes/`
- Entry files: `run_web.py`, `config.py`, `settings.py`

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
  static/
  templates/
  themes/
  run_web.py
  config.py
  settings.py
```

---

## Version History

- **0.1.2** - Workspace UI as default, legacy UI at `/legacy`
- **0.1.1** - Added `prismweb` command
- **0.1.0** - Initial release
