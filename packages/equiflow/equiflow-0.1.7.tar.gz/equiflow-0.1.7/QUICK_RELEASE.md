# Quick Release Checklist

## To Publish a New Version to PyPI

### 1. Update Version Numbers
```bash
# Edit these 3 files:
vim pyproject.toml           # version = "0.1.X"
vim equiflow/__init__.py     # __version__ = "0.1.X"
vim equiflow/equiflow.py     # __version__ = "0.1.X"
```

### 2. Commit Changes
```bash
git add .
git commit -m "Bump version to 0.1.X"
git push origin main
```

### 3. Create and Push Tag
```bash
git tag v0.1.X
git push origin v0.1.X
```

### 4. Done! 🎉
- GitHub Action automatically publishes to PyPI
- Monitor at: https://github.com/YOUR_USERNAME/equiflow-v2/actions

---

## First Time Setup

1. Create PyPI API token: https://pypi.org/manage/account/token/
2. Add to GitHub Secrets as `PYPI_API_TOKEN`
3. Do first manual upload: `python -m build && twine upload dist/*`

---

## Manual Trigger (Alternative)

1. Go to Actions tab
2. Click "Publish to PyPI"
3. Click "Run workflow"
4. Choose Test PyPI or production PyPI

