# PyPI Publishing Setup Guide

This guide explains how to set up automatic publishing to PyPI for EquiFlow.

## Overview

The GitHub Action workflow publishes your package to PyPI when:
- ✅ **Tagged releases** (e.g., `v0.1.7`) - **Recommended**
- ✅ **Manual trigger** from GitHub UI
- ⚠️ **Optionally** on every push to main (disabled by default)

---

## Setup Instructions

### 1. Create PyPI API Tokens

#### Production PyPI
1. Go to [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
2. Click "Add API token"
3. **Token name**: `equiflow-github-actions`
4. **Scope**: Select "Project: equiflow" (after first manual upload) or "Entire account"
5. Click "Add token"
6. **Copy the token** (starts with `pypi-...`) - you won't see it again!

#### Test PyPI (Optional, for testing)
1. Go to [https://test.pypi.org/manage/account/token/](https://test.pypi.org/manage/account/token/)
2. Repeat the same steps as above
3. Save this token separately

### 2. Add Secrets to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

   **For Production PyPI:**
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI token (the one starting with `pypi-...`)

   **For Test PyPI (optional):**
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: Paste your Test PyPI token

### 3. First Manual Upload (Required)

Before GitHub Actions can publish, you need to register the package name on PyPI:

```bash
# Build the package
python -m pip install build twine
python -m build

# Upload to PyPI (first time only)
twine upload dist/*
# Enter your PyPI username and password when prompted

# Or upload to Test PyPI first (recommended)
twine upload --repository testpypi dist/*
```

After this first upload, GitHub Actions can publish automatically.

---

## Usage

### Method 1: Tagged Release (Recommended)

This is the **best practice** for version management:

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # Change version = "0.1.7" to "0.1.8"

# 2. Commit the change
git add pyproject.toml
git commit -m "Bump version to 0.1.8"

# 3. Create and push a tag
git tag v0.1.8
git push origin v0.1.8

# 4. GitHub Action automatically:
#    - Builds the package
#    - Verifies version matches tag
#    - Publishes to PyPI
#    - Creates GitHub Release
```

### Method 2: Manual Trigger

For testing or emergency releases:

1. Go to **Actions** tab in your GitHub repo
2. Click **Publish to PyPI** workflow
3. Click **Run workflow**
4. Choose options:
   - ☑️ **Publish to Test PyPI**: For testing
   - ☐ **Publish to PyPI**: For production release
5. Click **Run workflow**

### Method 3: Auto-publish on Push (Optional)

To enable publishing on every push to main:

1. Edit `.github/workflows/publish-to-pypi.yml`
2. Uncomment these lines:
   ```yaml
   push:
     branches:
       - main
   ```

⚠️ **Warning**: This publishes on *every* push to main. Only enable if you:
- Always update version numbers before pushing
- Want rapid iteration
- Understand you can't unpublish from PyPI

---

## Workflow Details

### What the Workflow Does

1. ✅ **Checks out code**
2. ✅ **Sets up Python 3.11**
3. ✅ **Installs build tools** (build, twine)
4. ✅ **Verifies version** matches tag (if applicable)
5. ✅ **Builds package** (`dist/*.whl` and `dist/*.tar.gz`)
6. ✅ **Checks package** with twine
7. ✅ **Publishes to PyPI** (if conditions met)
8. ✅ **Creates GitHub Release** (for tags)

### Triggers

| Trigger | When | Publishes to PyPI? |
|---------|------|-------------------|
| Tag push (`v*`) | `git push origin v0.1.8` | ✅ Yes (production) |
| Manual (Test PyPI) | GitHub Actions UI | ✅ Yes (test) |
| Manual (PyPI) | GitHub Actions UI | ✅ Yes (production) |
| Push to main | Disabled by default | ❌ No (unless enabled) |

---

## Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR**: Breaking changes (e.g., removed `mask` parameter)
- **MINOR**: New features (e.g., added `smd_decimals`)
- **PATCH**: Bug fixes

### Current Version

Your current version is **0.1.7** in:
- ✅ `pyproject.toml`
- ✅ `equiflow/__init__.py`
- ✅ `equiflow/equiflow.py`

### Updating Version

**Before each release**, update the version in:

1. `pyproject.toml`:
   ```toml
   version = "0.1.8"
   ```

2. `equiflow/__init__.py`:
   ```python
   __version__ = "0.1.8"
   ```

3. `equiflow/equiflow.py`:
   ```python
   __version__ = "0.1.8"
   ```

Or use a tool like `bump2version` to update all at once.

---

## Testing Before Publishing

### Test Locally

```bash
# Build the package
python -m build

# Check the build
twine check dist/*

# Install locally
pip install dist/equiflow-0.1.7-py3-none-any.whl

# Test import
python -c "from equiflow import EquiFlow; print(EquiFlow.__module__)"
```

### Test on Test PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ equiflow

# Test it works
python -c "from equiflow import EquiFlow; print('Success!')"
```

---

## Troubleshooting

### Error: "File already exists"

**Problem**: You're trying to upload a version that already exists on PyPI.

**Solution**: 
- You cannot overwrite releases on PyPI
- Increment the version number in `pyproject.toml`
- Create a new tag

### Error: "Invalid or expired token"

**Problem**: PyPI API token is incorrect or expired.

**Solution**:
1. Generate a new token on PyPI
2. Update the `PYPI_API_TOKEN` secret in GitHub

### Error: "Version mismatch"

**Problem**: Tag version doesn't match `pyproject.toml` version.

**Solution**:
```bash
# If tag is v0.1.8 but pyproject.toml says 0.1.7
vim pyproject.toml  # Change to 0.1.8
git add pyproject.toml
git commit --amend --no-edit
git tag -f v0.1.8  # Force update tag
git push -f origin v0.1.8
```

---

## Security Best Practices

1. ✅ **Never commit tokens** to git
2. ✅ **Use scoped tokens** (project-specific, not account-wide)
3. ✅ **Rotate tokens** periodically
4. ✅ **Use separate tokens** for Test PyPI and production PyPI
5. ✅ **Enable 2FA** on your PyPI account

---

## Example Release Workflow

Complete workflow for releasing version 0.1.8:

```bash
# 1. Make your code changes
git add .
git commit -m "Add new feature"

# 2. Update version everywhere
sed -i '' 's/0.1.7/0.1.8/g' pyproject.toml
sed -i '' 's/0.1.7/0.1.8/g' equiflow/__init__.py
sed -i '' 's/0.1.7/0.1.8/g' equiflow/equiflow.py

# 3. Commit version bump
git add pyproject.toml equiflow/__init__.py equiflow/equiflow.py
git commit -m "Bump version to 0.1.8"

# 4. (Optional) Test locally
python -m build
twine check dist/*

# 5. (Optional) Test on Test PyPI
twine upload --repository testpypi dist/*

# 6. Push changes
git push origin main

# 7. Create and push tag
git tag v0.1.8
git push origin v0.1.8

# 8. GitHub Action automatically publishes! 🚀
# Check: https://github.com/YOUR_USERNAME/equiflow-v2/actions
```

---

## GitHub Action Status

After pushing a tag, check the workflow:

1. Go to **Actions** tab in your repo
2. Click on the latest **Publish to PyPI** workflow run
3. Monitor the progress:
   - ✅ Build package
   - ✅ Check distribution
   - ✅ Publish to PyPI
   - ✅ Create GitHub Release

---

## Resources

- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)

---

## Next Steps

1. ✅ Create PyPI account (if you haven't)
2. ✅ Generate API tokens
3. ✅ Add tokens to GitHub Secrets
4. ✅ Do first manual upload to register package
5. ✅ Create your first tag: `git tag v0.1.7 && git push origin v0.1.7`
6. 🎉 Watch it publish automatically!
